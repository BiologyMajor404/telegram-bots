from aiogram import Bot, F, Router
from aiogram.types import Message

from chatguard import keyboards as kb
from chatguard.texts import Ru

router = Router(name="private")
router.message.filter(F.chat.type == "private")


@router.message()
async def anything(message: Message, bot: Bot, t: Ru) -> None:
    await message.answer(
        t.WELCOME_PRIVATE, reply_markup=kb.add_as_admin(t, (await bot.me()).username)
    )
