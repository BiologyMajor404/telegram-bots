import pytest

from splitmate.handlers.inline import plain_amount
from splitmate.money import fmt_money, net_balances, parse_amount, settle_up, split_equally

A, B, C, D = 1, 2, 3, 4


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3000 такси", (300000, "такси")),
        ("1 250,50 продукты", (125050, "продукты")),
        ("99.9 кофе", (9990, "кофе")),
        ("500", (50000, "")),
        ("  42   пицца на всех ", (4200, "пицца на всех")),
    ],
)
def test_parse_amount(text, expected):
    assert parse_amount(text) == expected


@pytest.mark.parametrize("text", ["", "такси", "0 такси", "-5 такси", "1,234 x", "abc 100"])
def test_parse_amount_rejects(text):
    assert parse_amount(text) is None


@pytest.mark.parametrize("minor", [1, 50, 300000, 125050, 99999999])
def test_inline_amount_roundtrip(minor):
    # The inline message must be parsed back to exactly the same amount
    assert parse_amount(f"{plain_amount(minor)} x") == (minor, "x")


def test_fmt_money():
    assert fmt_money(125050) == "1 250,50 ₽"
    assert fmt_money(300000, "$") == "3 000 $"
    assert fmt_money(-500) == "-5 ₽"


def test_split_equally_adds_up_exactly():
    shares = split_equally(1000, [C, A, B])  # 10.00 between three
    assert shares == {A: 334, B: 333, C: 333}
    assert sum(shares.values()) == 1000


def test_split_needs_people():
    with pytest.raises(ValueError):
        split_equally(100, [])


def test_net_balances_and_settlement():
    # A paid 300 for A, B, C; B paid 90 for B and C
    expenses = [(A, 300, {A: 100, B: 100, C: 100}), (B, 90, {B: 45, C: 45})]
    net = net_balances(expenses, [])
    assert net == {A: 200, B: -55, C: -145}
    assert settle_up(net) == [(C, A, 145), (B, A, 55)]


def test_settlement_reduces_debt():
    expenses = [(A, 200, {A: 100, B: 100})]
    assert net_balances(expenses, [(B, A, 100)]) == {}


def test_settle_up_total_matches_and_is_short():
    net = {A: 500, B: 300, C: -400, D: -400}
    transfers = settle_up(net)
    assert len(transfers) <= len(net) - 1
    result = dict(net)
    for frm, to, amount in transfers:
        result[frm] += amount
        result[to] -= amount
    assert all(v == 0 for v in result.values())
