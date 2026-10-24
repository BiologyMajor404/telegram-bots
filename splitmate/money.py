"""Pure money math: parsing, formatting, splitting and settling up. No DB or Telegram here."""

import re
from collections.abc import Iterable

# "3000 такси", "1 250,50 продукты", "99.9 кофе"
AMOUNT_RE = re.compile(r"^\s*(\d{1,7}(?:[  ]\d{3})*(?:[.,]\d{1,2})?)(?:\s+(.*))?$", re.S)
MAX_AMOUNT = 100_000_000 * 100  # 100M in minor units, a sanity limit
DESCRIPTION_LIMIT = 128

Transfer = tuple[int, int, int]  # (from_user, to_user, amount)


def parse_amount(text: str) -> tuple[int, str] | None:
    """'1 250,50 продукты' -> (125050, 'продукты'). Amount in minor units."""
    m = AMOUNT_RE.match(text)
    if not m:
        return None
    number = m[1].replace(" ", "").replace(" ", "").replace(",", ".")
    whole, _, frac = number.partition(".")
    minor = int(whole) * 100 + int(frac.ljust(2, "0") or 0)
    if not 0 < minor <= MAX_AMOUNT:
        return None
    description = (m[2] or "").strip()[:DESCRIPTION_LIMIT]
    return minor, description


def fmt_money(minor: int, currency: str = "₴") -> str:
    whole, frac = divmod(abs(minor), 100)
    text = f"{whole:,}".replace(",", " ")
    if frac:
        text += f",{frac:02d}"
    return f"{'-' if minor < 0 else ''}{text} {currency}"


def split_equally(amount: int, user_ids: Iterable[int]) -> dict[int, int]:
    """Split so shares differ by at most one minor unit and add up exactly to `amount`."""
    ids = sorted(set(user_ids))
    if not ids:
        raise ValueError("Nobody to split between")
    base, remainder = divmod(amount, len(ids))
    return {uid: base + (1 if i < remainder else 0) for i, uid in enumerate(ids)}


def net_balances(
    expenses: Iterable[tuple[int, int, dict[int, int]]],
    settlements: Iterable[Transfer],
) -> dict[int, int]:
    """Positive = the group owes this person, negative = this person owes.
    expenses: (payer, amount, shares); settlements: (from, to, amount)."""
    net: dict[int, int] = {}
    for payer, amount, shares in expenses:
        net[payer] = net.get(payer, 0) + amount
        for uid, share in shares.items():
            net[uid] = net.get(uid, 0) - share
    for from_id, to_id, amount in settlements:
        net[from_id] = net.get(from_id, 0) + amount
        net[to_id] = net.get(to_id, 0) - amount
    return {uid: v for uid, v in net.items() if v}


def settle_up(net: dict[int, int]) -> list[Transfer]:
    """Few transfers that zero out all balances: the biggest debtor pays the biggest creditor."""
    debtors = sorted(((-v, uid) for uid, v in net.items() if v < 0), reverse=True)
    creditors = sorted(((v, uid) for uid, v in net.items() if v > 0), reverse=True)
    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        owe, debtor = debtors[i]
        due, creditor = creditors[j]
        paid = min(owe, due)
        transfers.append((debtor, creditor, paid))
        debtors[i] = (owe - paid, debtor)
        creditors[j] = (due - paid, creditor)
        if debtors[i][0] == 0:
            i += 1
        if creditors[j][0] == 0:
            j += 1
    return transfers
