"""Regression tests for issues found in the security review."""

import pytest

from chatguard.handlers import guard
from splitmate.handlers.group import CURRENCY_RE


@pytest.mark.parametrize("value", ["₴", "zł", "$", "€", "CHF", "Kč", "руб"])
def test_currency_accepts_symbols_and_codes(value):
    assert CURRENCY_RE.fullmatch(value)


@pytest.mark.parametrize("value", ["<i>", "<b", "a&b", "x y", '"', "123456789"])
def test_currency_rejects_markup_and_garbage(value):
    # Stored currencies go into every HTML message; markup would break the chat
    assert not CURRENCY_RE.fullmatch(value)


def test_guard_catches_every_group_message_including_commands():
    # The guard's handlers have no filters of their own, so "/start <spam>" can't bypass them
    for observer in (guard.router.message, guard.router.edited_message):
        assert len(observer.handlers) == 1 and not observer.handlers[0].filters
