"""Private chat with the bot: explains how to add it to a group."""

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from splitmate import keyboards as kb
from splitmate.texts import Ru

router = Router(name="private")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def start(message: Message, bot: Bot, t: Ru) -> None:
    await message.answer(
        t.WELCOME_PRIVATE, reply_markup=kb.add_to_group(t, (await bot.me()).username)
    )


@router.message(F.via_bot)
async def inline_in_private(message: Message, t: Ru) -> None:
    await message.answer(t.INLINE_PRIVATE)


@router.message()
async def anything_else(message: Message, bot: Bot, t: Ru) -> None:
    await message.answer(t.ONLY_GROUPS, reply_markup=kb.add_to_group(t, (await bot.me()).username))
