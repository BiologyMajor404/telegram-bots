"""A bare /start in a group may belong to another bot: only /start@this_bot is answered."""

import asyncio
from types import SimpleNamespace

from aiogram.filters import CommandObject

from chatguard.handlers import group as chatguard_group
from chatguard.texts import TEXTS as CG_TEXTS
from splitmate.handlers import group as splitmate_group
from splitmate.texts import TEXTS as SM_TEXTS


class FakeMessage:
    def __init__(self):
        self.chat = SimpleNamespace(id=-1)
        self.sent = []

    async def answer(self, text, **kw):
        self.sent.append(text)


class FakeBot:
    async def me(self):
        return SimpleNamespace(username="test_bot")


def command(mention):
    return CommandObject(prefix="/", command="start", mention=mention)


def test_chatguard_ignores_bare_start():
    bare, mentioned = FakeMessage(), FakeMessage()
    asyncio.run(chatguard_group.start_cmd(bare, command(None), CG_TEXTS["en"]))
    asyncio.run(chatguard_group.start_cmd(mentioned, command("test_bot"), CG_TEXTS["en"]))
    assert bare.sent == [] and len(mentioned.sent) == 1


def test_splitmate_ignores_bare_start(monkeypatch):
    monkeypatch.setattr(splitmate_group, "_welcomed_at", {})
    bare, mentioned = FakeMessage(), FakeMessage()
    asyncio.run(splitmate_group.start_cmd(bare, command(None), FakeBot(), SM_TEXTS["en"]))
    asyncio.run(
        splitmate_group.start_cmd(mentioned, command("test_bot"), FakeBot(), SM_TEXTS["en"])
    )
    assert bare.sent == [] and len(mentioned.sent) == 1
