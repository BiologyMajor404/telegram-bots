"""Owner commands: give someone a permanent free Pro, or take it back."""

from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from jobradar import repo
from jobradar.handlers.payments import fmt_date
from jobradar.plans import Access
from jobradar.texts import TEXTS, Ru
from shared.notify import safe_send

router = Router(name="admin")
router.message.filter(F.chat.type == "private")


def user_id_of(command: CommandObject) -> int | None:
    try:
        return int((command.args or "").strip())
    except ValueError:
        return None


@router.message(Command("gift", "ungift"))
async def gift(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    access: Access,
) -> None:
    if message.from_user.id not in access.admin_ids:
        return  # not the owner: as if the command didn't exist
    user_id = user_id_of(command)
    if user_id is None:
        await message.answer(t.GIFT_USAGE)
        return
    on = command.command == "gift"
    sub = await repo.set_gift(session, user_id, on)
    if sub is None:
        await message.answer(t.GIFT_NO_USER.format(user_id=user_id))
        return
    text = (t.GIFT_DONE if on else t.UNGIFT_DONE).format(user_id=user_id)
    if on and sub.pro_until is not None and sub.pro_until > datetime.now(UTC):
        # Their Stars subscription keeps renewing until they cancel it themselves
        text += t.GIFT_PAYING.format(until=fmt_date(sub.pro_until))
    await message.answer(text)
    if on:
        await safe_send(bot, user_id, TEXTS[sub.lang].GIFT_RECEIVED)
