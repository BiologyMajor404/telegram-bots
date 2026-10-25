"""ChatGuard AI Pro: a monthly Telegram Stars subscription bought by a chat admin."""

import logging
from datetime import UTC, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, LabeledPrice, Message, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard import repo
from chatguard.admins import is_admin
from chatguard.config import Plans
from chatguard.models import Chat
from chatguard.texts import TEXTS, Ru
from shared.formatting import user_link
from shared.notify import safe_send

log = logging.getLogger(__name__)
router = Router(name="payments")

STARS = "XTR"
PRO_PERIOD = timedelta(days=30)  # the only subscription period Telegram supports
PAYLOAD_PREFIX = "pro:"


def pro_payload(chat_id: int) -> str:
    return f"{PAYLOAD_PREFIX}{chat_id}"


def parse_pro_payload(payload: str) -> int | None:
    if not payload.startswith(PAYLOAD_PREFIX):
        return None
    try:
        return int(payload.removeprefix(PAYLOAD_PREFIX))
    except ValueError:
        return None


def fmt_date(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y")


def subscription_end(expiration: int | datetime | None) -> datetime:
    """Telegram sends the subscription end as a Unix timestamp; fall back to a full period."""
    if expiration is None:
        return datetime.now(UTC) + PRO_PERIOD
    if isinstance(expiration, int):
        return datetime.fromtimestamp(expiration, UTC)
    return expiration if expiration.tzinfo else expiration.replace(tzinfo=UTC)


async def pro_offer(
    bot: Bot, chat: Chat, t: Ru, plans: Plans
) -> tuple[str, InlineKeyboardMarkup | None]:
    """The /pro message: either "already active" or the offer with a payment button."""
    if repo.is_pro(chat, datetime.now(UTC)):
        return t.PRO_ACTIVE.format(until=fmt_date(chat.pro_until)), None
    link = await bot.create_invoice_link(
        title=t.PRO_INVOICE_TITLE,
        description=t.PRO_INVOICE_DESCRIPTION.format(chat=chat.title[:60], limit=plans.pro_limit),
        payload=pro_payload(chat.id),
        currency=STARS,
        prices=[LabeledPrice(label=t.PRO_INVOICE_TITLE, amount=plans.pro_price_stars)],
        subscription_period=int(PRO_PERIOD.total_seconds()),
    )
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_PAY_PRO.format(price=plans.pro_price_stars), url=link)
    text = t.PRO_OFFER.format(
        price=plans.pro_price_stars, pro_limit=plans.pro_limit, free_limit=plans.free_limit
    )
    return text, b.as_markup()


@router.pre_checkout_query()
async def pre_checkout(
    query: PreCheckoutQuery, session: AsyncSession, bot: Bot, t: Ru, plans: Plans
) -> None:
    """Last check before Telegram charges: a real chat, the current price, paid by its admin."""
    chat_id = parse_pro_payload(query.invoice_payload)
    chat = await session.get(Chat, chat_id) if chat_id else None
    valid = (
        chat is not None
        and query.currency == STARS
        and query.total_amount == plans.pro_price_stars
        and await is_admin(bot, chat.id, query.from_user.id)
    )
    if valid:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message=t.PRO_CHECK_FAILED)


@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession, bot: Bot, t: Ru) -> None:
    payment = message.successful_payment
    chat_id = parse_pro_payload(payment.invoice_payload)
    chat = await session.get(Chat, chat_id) if chat_id else None
    if chat is None:
        log.error("Pro payment %s for unknown chat", payment.telegram_payment_charge_id)
        return

    until = subscription_end(payment.subscription_expiration_date)
    await repo.activate_pro(
        session, chat, until, message.from_user.id, payment.telegram_payment_charge_id
    )

    group_t = TEXTS[chat.lang]
    if payment.is_recurring and not payment.is_first_recurring:
        # Automatic monthly renewal: tell the group, the payer already gets a Telegram receipt
        await safe_send(bot, chat.id, group_t.PRO_RENEWED.format(until=fmt_date(until)))
        return
    await message.answer(t.PRO_THANKS.format(chat=chat.title, until=fmt_date(until)))
    await safe_send(
        bot,
        chat.id,
        group_t.PRO_ACTIVATED.format(
            user=user_link(message.from_user.id, message.from_user.full_name),
            until=fmt_date(until),
        ),
    )


@router.message(Command("paysupport"))
async def paysupport(message: Message, t: Ru, support_contact: str) -> None:
    # Telegram requires bots that accept Stars to answer /paysupport
    text = t.PAYSUPPORT
    if support_contact:
        text += t.PAYSUPPORT_CONTACT.format(contact=support_contact)
    await message.answer(text)
