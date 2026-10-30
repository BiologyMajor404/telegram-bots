"""SplitMates texts and command menu."""

import pytest

from splitmate.__main__ import group_commands
from splitmate.texts import TEXTS

# settle_up is greedy, not optimal: {+6, +5, -5, -4, -2} takes it 4 transfers where 3 would do
MINIMUM_CLAIMS = ("fewest", "минимум", "мінімум", "najmniejsz")


@pytest.mark.parametrize("lang", TEXTS)
def test_texts_promise_no_minimum_of_transfers(lang):
    t = TEXTS[lang]
    for text in (t.BOT_DESCRIPTION, t.WELCOME_PRIVATE):
        assert not any(claim in text.lower() for claim in MINIMUM_CLAIMS)


@pytest.mark.parametrize("lang", TEXTS)
def test_group_menu_has_leave(lang):
    commands = {c.command: c.description for c in group_commands(TEXTS[lang])}
    assert commands["leave"] == TEXTS[lang].CMD_LEAVE
