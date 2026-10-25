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


if __name__ == "__main__":
    for name, draw in (
        ("splitmates", splitmates),
        ("slotbook", slotbook),
        ("chatguard", chatguard),
    ):
        print("saved", save(draw(), name))
