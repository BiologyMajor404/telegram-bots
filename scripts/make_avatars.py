"""Generate the bots' profile pictures (640x640 PNG) into assets/avatars/.

Drawn at 4x and downscaled for smooth edges. Uses a bold system font for the "$" sign.
Run: python scripts/make_avatars.py   (needs Pillow: pip install -r requirements-dev.txt)"""

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SIZE = 640
SCALE = 4
S = SIZE * SCALE
OUT = Path(__file__).resolve().parent.parent / "assets" / "avatars"


# --- Helpers ---


def hex_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def gradient(top: str, bottom: str, size: tuple[int, int] = (S, S)) -> Image.Image:
    (r1, g1, b1), (r2, g2, b2) = hex_rgb(top), hex_rgb(bottom)
    w, h = size
    column = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / (h - 1)
        column.putpixel(
            (0, y),
            (round(r1 + (r2 - r1) * k), round(g1 + (g2 - g1) * k), round(b1 + (b2 - b1) * k)),
        )
    return column.resize((w, h)).convert("RGBA")


def layer() -> Image.Image:
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def shadow(img: Image.Image, offset: tuple[int, int], blur: int, opacity: int) -> Image.Image:
    """A soft shadow of a layer's shape."""
    alpha = img.getchannel("A").point(lambda a: a * opacity // 255)
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shade.putalpha(alpha)
    shade = ImageChops.offset(shade, *offset)
    return shade.filter(ImageFilter.GaussianBlur(blur))


def bezier(p0, p1, p2, p3, n: int = 60) -> list[tuple[float, float]]:
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def bold_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit("No bold system font found; add one to FONT_CANDIDATES")


def check_mark(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, color, width: float):
    pts = [
        (cx - size * 0.5, cy),
        (cx - size * 0.12, cy + size * 0.38),
        (cx + size * 0.55, cy - size * 0.4),
    ]
    draw.line(pts, fill=color, width=round(width), joint="curve")
    for x, y in (pts[0], pts[-1]):  # round caps
        r = width / 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=color)


def sparkle(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color):
    """Four-pointed AI sparkle."""
    pts = []
    for i in range(8):
        angle = math.pi / 4 * i - math.pi / 2
        radius = r if i % 2 == 0 else r * 0.28
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    draw.polygon(pts, fill=color)


def save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    img.resize((SIZE, SIZE), Image.LANCZOS).convert("RGB").save(path, optimize=True)
    return path


# --- SplitMates: a banknote split in two halves ---


def splitmates() -> Image.Image:
    img = gradient("#34D27B", "#0B7A42")
    bill = layer()
    d = ImageDraw.Draw(bill)
    w, h = S * 0.66, S * 0.38
    x0, y0 = (S - w) / 2, (S - h) / 2
    x1, y1 = x0 + w, y0 + h
    d.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=S * 0.035,
        fill="#EFFCF3",
        outline="#0A5C31",
        width=round(S * 0.012),
    )
    inset = S * 0.04
    d.rounded_rectangle(
        (x0 + inset, y0 + inset, x1 - inset, y1 - inset),
        radius=S * 0.02,
        outline="#8FD9AE",
        width=round(S * 0.007),
    )
    cx, cy, r = S / 2, S / 2, S * 0.11
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#16A35C")
    d.text((cx, cy), "$", font=bold_font(round(r * 1.45)), fill="#EFFCF3", anchor="mm")
    for ox in (x0 + S * 0.1, x1 - S * 0.1):  # corner ornaments
        for oy in (y0 + S * 0.09, y1 - S * 0.09):
            rr = S * 0.028
            d.ellipse((ox - rr, oy - rr, ox + rr, oy + rr), fill="#C3EED4")

    # A clean cut down the middle: "split in two", not "torn"
    left_mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(left_mask).rectangle((0, 0, S / 2, S), fill=255)
    left = Image.composite(bill, layer(), left_mask)
    right = Image.composite(bill, layer(), ImageChops.invert(left_mask))

    left = left.rotate(5, center=(S / 2, S / 2), resample=Image.BICUBIC)
    left = ImageChops.offset(left, round(-S * 0.035), round(-S * 0.012))
    right = right.rotate(-5, center=(S / 2, S / 2), resample=Image.BICUBIC)
    right = ImageChops.offset(right, round(S * 0.035), round(S * 0.012))
    for piece in (left, right):
        img.alpha_composite(shadow(piece, (round(S * 0.012), round(S * 0.02)), round(S * 0.02), 90))
    img.alpha_composite(left)
    img.alpha_composite(right)
    return img


# --- SlotBook: a calendar page with a booked day ---


def slotbook() -> Image.Image:
    img = gradient("#7584FF", "#3437C9")
    card = layer()
    d = ImageDraw.Draw(card)
    w = h = S * 0.56
    x0, y0 = (S - w) / 2, (S - h) / 2 + S * 0.03
    x1, y1 = x0 + w, y0 + h
    radius = S * 0.06
    d.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill="#FFFFFF")
    header = y0 + S * 0.15
    d.rounded_rectangle((x0, y0, x1, header), radius=radius, fill="#FF6B6B")
    d.rectangle((x0, header - radius, x1, header), fill="#FF6B6B")

    # Grid of days, one of them booked
    cols, rows = 4, 3
    pad, gap = S * 0.06, S * 0.03
    cell_w = (w - 2 * pad - (cols - 1) * gap) / cols
    cell_h = (y1 - header - 2 * pad + S * 0.01 - (rows - 1) * gap) / rows
    booked = (2, 1)
    for row in range(rows):
        for col in range(cols):
            cx0 = x0 + pad + col * (cell_w + gap)
            cy0 = header + pad * 0.85 + row * (cell_h + gap)
            if (col, row) == booked:
                continue
            d.rounded_rectangle(
                (cx0, cy0, cx0 + cell_w, cy0 + cell_h), radius=S * 0.015, fill="#E6E9FF"
            )
    bx0 = x0 + pad + booked[0] * (cell_w + gap)
    by0 = header + pad * 0.85 + booked[1] * (cell_h + gap)
    bcx, bcy = bx0 + cell_w / 2, by0 + cell_h / 2
    br = min(cell_w, cell_h) * 0.72
    d.ellipse((bcx - br, bcy - br, bcx + br, bcy + br), fill="#3437C9")
    check_mark(d, bcx, bcy + br * 0.04, br * 1.05, "#FFFFFF", S * 0.018)

    # Binder rings sticking out of the top
    for rx in (x0 + w * 0.3, x0 + w * 0.7):
        d.rounded_rectangle(
            (rx - S * 0.02, y0 - S * 0.045, rx + S * 0.02, y0 + S * 0.05),
            radius=S * 0.02,
            fill="#262A80",
        )
    img.alpha_composite(shadow(card, (round(S * 0.01), round(S * 0.025)), round(S * 0.025), 100))
    img.alpha_composite(card)
    return img


# --- ChatGuard AI: a shield guarding a chat bubble, with an AI sparkle ---


def chatguard() -> Image.Image:
    img = gradient("#25335F", "#0A0F22")
    cx, top, bottom, half = S / 2, S * 0.17, S * 0.85, S * 0.27
    corner_y = top + S * 0.07
    left_side = bezier(
        (cx, top),
        (cx - half * 0.5, top + S * 0.05),
        (cx - half * 0.8, corner_y),
        (cx - half, corner_y),
    )
    left_down = bezier(
        (cx - half, corner_y),
        (cx - half, top + S * 0.38),
        (cx - half * 0.55, top + S * 0.55),
        (cx, bottom),
    )
    right = [(2 * cx - x, y) for x, y in reversed(left_side + left_down)]
    outline = left_side + left_down + right

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).polygon(outline, fill=255)
    shield = layer()
    shield.paste(gradient("#38E1F5", "#2563EB"), (0, 0), mask)
    d = ImageDraw.Draw(shield)
    d.line([*outline, outline[0]], fill="#A5F3FC", width=round(S * 0.01), joint="curve")

    # Chat bubble inside the shield
    bw, bh = S * 0.27, S * 0.19
    bx0, by0 = cx - bw / 2, S * 0.38
    d.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=S * 0.05, fill="#FFFFFF")
    d.polygon(
        [
            (bx0 + bw * 0.22, by0 + bh * 0.9),
            (bx0 + bw * 0.12, by0 + bh + S * 0.06),
            (bx0 + bw * 0.45, by0 + bh * 0.9),
        ],
        fill="#FFFFFF",
    )
    check_mark(d, cx, by0 + bh * 0.5, bh * 0.62, "#2563EB", S * 0.022)

    img.alpha_composite(shadow(shield, (0, round(S * 0.02)), round(S * 0.03), 140))
    img.alpha_composite(shield)
    sd = ImageDraw.Draw(img)
    sparkle(sd, cx + half * 0.95, top + S * 0.06, S * 0.075, "#FDE68A")
    sparkle(sd, cx + half * 1.22, top + S * 0.17, S * 0.035, "#FDE68A")
    return img


# --- JobRadar: a radar sweep finding a "hot" job, with a play button at its center ---


def jobradar(radius: float = 0.36) -> Image.Image:
    img = gradient("#FF8A3D", "#C2185B")
    cx, cy, r = S / 2, S / 2, S * radius

    # Dish with rings and cross hairs
    dish = layer()
    d = ImageDraw.Draw(dish)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#3A0A24")
    line = round(S * 0.006)
    for k in (1.0, 0.68, 0.36):
        rr = r * k
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline="#FF9F7A", width=line)
    d.line((cx - r, cy, cx + r, cy), fill="#7A2A45", width=line)
    d.line((cx, cy - r, cx, cy + r), fill="#7A2A45", width=line)

    # The sweep: a wedge that fades out behind the beam
    sweep = layer()
    sd = ImageDraw.Draw(sweep)
    beam = -50  # degrees, PIL angles go clockwise from 3 o'clock
    steps = 30
    for i in range(steps):
        alpha = round(150 * (1 - i / steps))
        sd.pieslice(
            (cx - r, cy - r, cx + r, cy + r),
            beam - (i + 1) * 2,
            beam - i * 2,
            fill=(255, 196, 120, alpha),
        )
    dish.alpha_composite(sweep)
    end = (cx + r * math.cos(math.radians(beam)), cy + r * math.sin(math.radians(beam)))
    d.line((cx, cy, *end), fill="#FFE2B0", width=round(S * 0.01))

    # A hot blip the beam just found, and a fainter older one
    def blip(angle: float, dist: float, size: float, color, glow: int):
        bx = cx + r * dist * math.cos(math.radians(angle))
        by = cy + r * dist * math.sin(math.radians(angle))
        halo = layer()
        ImageDraw.Draw(halo).ellipse(
            (bx - size * 2.2, by - size * 2.2, bx + size * 2.2, by + size * 2.2),
            fill=(255, 214, 102, glow),
        )
        dish.alpha_composite(halo.filter(ImageFilter.GaussianBlur(size * 0.8)))
        ImageDraw.Draw(dish).ellipse((bx - size, by - size, bx + size, by + size), fill=color)

    blip(-62, 0.72, S * 0.03, "#FFF3C4", 220)
    blip(150, 0.55, S * 0.018, "#FFB37A", 90)

    # Play button in the middle: it is video work the radar looks for
    pr = S * 0.1
    pd = ImageDraw.Draw(dish)
    pd.ellipse((cx - pr, cy - pr, cx + pr, cy + pr), fill="#FFFFFF")
    t = pr * 0.5
    pd.polygon(
        [(cx - t * 0.7, cy - t), (cx - t * 0.7, cy + t), (cx + t * 1.05, cy)], fill="#E0245E"
    )

    img.alpha_composite(shadow(dish, (0, round(S * 0.02)), round(S * 0.03), 130))
    img.alpha_composite(dish)
    ImageDraw.Draw(img).ellipse(
        (cx - r, cy - r, cx + r, cy + r), outline="#FFD1B8", width=round(S * 0.012)
    )
    return img


# --- JobRadar mascot: a job application form that has become a monster ---

INK = "#2B1A1A"
PAPER = "#F3EEDC"
FANG = "#FFFDF2"


def monster_arms() -> Image.Image:
    """Skinny clawed arms reaching out from behind the sheet."""
    arms = layer()
    ad = ImageDraw.Draw(arms)
    arm_w = round(S * 0.022)
    claw = S * 0.012
    for side in (-1, 1):

        def p(x: float, y: float, side: int = side) -> tuple[float, float]:
            return (S / 2 + side * S * x, S * y)

        elbow, wrist = p(0.36, 0.6), p(0.4, 0.4)
        ad.line([p(0.2, 0.62), elbow, wrist], fill="#C9C0A6", width=arm_w, joint="curve")
        for dx, dy in ((-0.05, -0.08), (0.0, -0.1), (0.05, -0.07)):
            tip = p(0.4 + dx, 0.4 + dy)
            ad.line([wrist, tip], fill="#C9C0A6", width=round(arm_w * 0.7))
            ad.ellipse((tip[0] - claw, tip[1] - claw, tip[0] + claw, tip[1] + claw), fill="#E23B3B")
    return arms


def monster_eyes(paper: Image.Image) -> None:
    """Angry glowing eyes with slit pupils, form lines bent into brows."""
    cx, eye_y, eye_dx, ew, eh = S / 2, S * 0.385, S * 0.11, S * 0.075, S * 0.055
    glow = layer()
    for side in (-1, 1):
        ex = cx + side * eye_dx
        ImageDraw.Draw(glow).ellipse(
            (ex - ew * 1.6, eye_y - eh * 1.8, ex + ew * 1.6, eye_y + eh * 1.8),
            fill=(255, 60, 30, 150),
        )
    paper.alpha_composite(glow.filter(ImageFilter.GaussianBlur(S * 0.02)))
    d = ImageDraw.Draw(paper)
    for side in (-1, 1):
        ex = cx + side * eye_dx
        inner, outer = ex - side * ew * 1.3, ex + side * ew * 1.3
        # The brow cuts the top of the eye at an angle, towards the nose
        below_brow = Image.new("L", (S, S), 0)
        ImageDraw.Draw(below_brow).polygon(
            [(inner, eye_y + eh * 0.1), (outer, eye_y - eh * 0.9), (outer, S), (inner, S)],
            fill=255,
        )
        eye = layer()
        ed = ImageDraw.Draw(eye)
        ed.ellipse((ex - ew, eye_y - eh, ex + ew, eye_y + eh), fill="#FFD23F")
        ed.ellipse((ex - ew * 0.18, eye_y - eh * 0.85, ex + ew * 0.18, eye_y + eh * 0.85), fill=INK)
        paper.alpha_composite(Image.composite(eye, layer(), below_brow))
        d.line(
            [(inner, eye_y + eh * 0.1), (outer, eye_y - eh * 0.9)],
            fill=INK,
            width=round(S * 0.022),
        )


def monster_mouth(d: ImageDraw.ImageDraw) -> None:
    """A wide grin full of fangs, the corner ones longest."""
    cx = S / 2
    mx0, mx1, my0, my1 = S * 0.31, S * 0.69, S * 0.5, S * 0.7
    mouth = bezier(
        (mx0, my0), (cx - S * 0.1, my0 + S * 0.03), (cx + S * 0.1, my0 + S * 0.03), (mx1, my0)
    )
    mouth += bezier((mx1, my0), (mx1, my1), (mx0, my1), (mx0, my0))
    d.polygon(mouth, fill="#5E0B17")
    d.line([*mouth, mouth[0]], fill=INK, width=round(S * 0.012), joint="curve")
    fangs = 6
    span = (mx1 - mx0) * 0.84
    left = mx0 + (mx1 - mx0) * 0.08
    top = my0 + S * 0.022
    for i in range(fangs):
        fx, fw = left + span * i / fangs, span / fangs
        long = S * (0.07 if i in (0, fangs - 1) else 0.045)
        d.polygon([(fx, top), (fx + fw, top), (fx + fw / 2, top + long)], fill=FANG)
    bottom = my0 + S * 0.135
    for i in range(fangs - 2):
        fx = left + span * 0.1 + span * 0.8 * i / (fangs - 2)
        fw = span * 0.8 / (fangs - 2)
        d.polygon([(fx, bottom), (fx + fw, bottom), (fx + fw / 2, bottom - S * 0.04)], fill=FANG)


def job_monster() -> Image.Image:
    img = gradient("#4A0D24", "#0D0410")
    cx = S / 2

    # Faint radar rings behind it, so it still reads as "JobRadar"
    rings = layer()
    rd = ImageDraw.Draw(rings)
    for k in (0.46, 0.36, 0.26):
        rr = S * k
        rd.ellipse(
            (cx - rr, S / 2 - rr, cx + rr, S / 2 + rr),
            outline=(255, 90, 90, 60),
            width=round(S * 0.005),
        )
    img.alpha_composite(rings)
    img.alpha_composite(monster_arms())

    # The sheet: folded top corner, torn bottom edge
    paper = layer()
    d = ImageDraw.Draw(paper)
    x0, y0, x1, y1 = S * 0.25, S * 0.17, S * 0.75, S * 0.83
    fold = S * 0.08
    torn = [(x1, y1)]
    teeth = 9
    for i in range(1, teeth + 1):
        x = x1 - (x1 - x0) * i / teeth
        torn.append((x + (x1 - x0) / teeth / 2, y1 + (S * 0.03 if i % 2 else 0)))
        torn.append((x, y1))
    d.polygon([(x0, y0), (x1 - fold, y0), (x1, y0 + fold), *torn], fill=PAPER)
    d.polygon([(x1 - fold, y0), (x1 - fold, y0 + fold), (x1, y0 + fold)], fill="#C9C0A6")
    d.text(
        (cx - S * 0.03, y0 + S * 0.055),
        "JOB APPLICATION",
        font=bold_font(round(S * 0.038)),
        fill=INK,
        anchor="mm",
    )
    d.line((x0 + S * 0.04, y0 + S * 0.09, x1 - S * 0.1, y0 + S * 0.09), fill=INK, width=8)
    monster_eyes(paper)
    d = ImageDraw.Draw(paper)
    monster_mouth(d)

    # A form field below the mouth: a checkbox nobody wants to tick
    fy = S * 0.755
    d.rectangle(
        (x0 + S * 0.05, fy - S * 0.018, x0 + S * 0.086, fy + S * 0.018), outline=INK, width=7
    )
    d.line((x0 + S * 0.11, fy, x1 - S * 0.06, fy), fill="#9C9283", width=7)

    paper = paper.rotate(-5, center=(cx, S / 2), resample=Image.BICUBIC)
    img.alpha_composite(shadow(paper, (round(S * 0.012), round(S * 0.025)), round(S * 0.03), 160))
    img.alpha_composite(paper)
    return img


if __name__ == "__main__":
    for name, draw in (
        ("splitmates", splitmates),
        ("slotbook", slotbook),
        ("chatguard", chatguard),
        ("jobradar", jobradar),
        ("jobradar_monster", job_monster),
    ):
        print("saved", save(draw(), name))
