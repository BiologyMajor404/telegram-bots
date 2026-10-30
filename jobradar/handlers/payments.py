"""JobRadar Pro: a monthly Telegram Stars subscription with higher daily limits."""

import logging
from datetime import UTC, datetime, timedelta
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, LabeledPrice, Message, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from jobradar import repo
from jobradar.models import Subscriber
from jobradar.plans import Access
from jobradar.texts import Ru

log = logging.getLogger(__name__)
router = Router(name="payments")

STARS = "XTR"
PRO_PERIOD = timedelta(days=30)  # the only subscription period Telegram supports
RENEWAL_MARGIN = timedelta(days=1)
PAYLOAD_PREFIX = "pro:"


def pro_payload(user_id: int) -> str:
    return f"{PAYLOAD_PREFIX}{user_id}"


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


def already_pro(sub: Subscriber, now: datetime) -> bool:
    """Pro that a new payment would only double. A day's margin: should a renewal ever
    come through pre-checkout, it comes at the very end of the paid month."""
    return sub.gift or (sub.pro_until is not None and sub.pro_until > now + RENEWAL_MARGIN)


async def pro_offer(
    bot: Bot, sub: Subscriber, t: Ru, access: Access
) -> tuple[str, InlineKeyboardMarkup | None]:
    """The /pro message: either "already active" or the offer with a payment button."""
    now = datetime.now(UTC)
    if sub.gift:
        return t.PLAN_GIFT, None
    if sub.pro_until is not None and sub.pro_until > now:
        return t.PRO_ACTIVE.format(until=fmt_date(sub.pro_until)), None
    if access.is_pro(sub, now):
        return t.PLAN_ADMIN, None
    plans = access.plans
    link = await bot.create_invoice_link(
        title=t.PRO_INVOICE_TITLE,
        description=t.PRO_INVOICE_DESCRIPTION.format(
            cards=plans.pro.cards, sources=plans.pro.sources
        ),
        payload=pro_payload(sub.id),
        currency=STARS,
        prices=[LabeledPrice(label=t.PRO_INVOICE_TITLE, amount=plans.pro_price_stars)],
        subscription_period=int(PRO_PERIOD.total_seconds()),
    )
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_PAY_PRO.format(price=plans.pro_price_stars), url=link)
    text = t.PRO_OFFER.format(
        price=plans.pro_price_stars,
        pro_cards=plans.pro.cards,
        free_cards=plans.free.cards,
        pro_sources=plans.pro.sources,
        pro_searches=plans.pro.searches,
        free_searches=plans.free.searches,
        free_sources=plans.free.sources,
    )
    return text, b.as_markup()


@router.pre_checkout_query()
async def pre_checkout(
    query: PreCheckoutQuery, session: AsyncSession, t: Ru, access: Access
) -> None:
    """Last check before Telegram charges: the payer's own subscription, the current price,
    and no Pro running yet: an old offer's link still opens, and Telegram would start a
    second subscription next to the first."""
    user_id = parse_pro_payload(query.invoice_payload)
    sub = await repo.get_subscriber(session, user_id) if user_id == query.from_user.id else None
    if sub is not None and already_pro(sub, datetime.now(UTC)):
        await query.answer(ok=False, error_message=t.PRO_ALREADY)
        return
    valid = (
        sub is not None
        and query.currency == STARS
        and query.total_amount == access.plans.pro_price_stars
    )
    if valid:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message=t.PRO_CHECK_FAILED)


@router.message(F.refunded_payment)
async def refunded_payment(message: Message, session: AsyncSession) -> None:
    """The owner refunded a payment (Telegram tells the bot): the Pro it bought ends."""
    refund = message.refunded_payment
    user_id = parse_pro_payload(refund.invoice_payload)
    if user_id and await repo.revoke_pro(session, user_id, refund.telegram_payment_charge_id):
        log.info("Pro of %s ended by a refund", user_id)


@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession, t: Ru) -> None:
    payment = message.successful_payment
    user_id = parse_pro_payload(payment.invoice_payload)
    sub = await repo.get_subscriber(session, user_id) if user_id else None
    if sub is None:
        log.error("Pro payment %s for unknown user", payment.telegram_payment_charge_id)
        return
    until = subscription_end(payment.subscription_expiration_date)
    await repo.activate_pro(session, sub, until, payment.telegram_payment_charge_id)
    log.info("Pro for %s until %s", sub.id, until.date())
    if payment.is_recurring and not payment.is_first_recurring:
        await message.answer(t.PRO_RENEWED.format(until=fmt_date(until)))
    else:
        await message.answer(t.PRO_THANKS.format(until=fmt_date(until)))


@router.message(Command("paysupport"))
async def paysupport(message: Message, t: Ru, support_contact: str) -> None:
    # Telegram requires bots that accept Stars to answer /paysupport
    text = t.PAYSUPPORT
    if support_contact:
        text += t.PAYSUPPORT_CONTACT.format(contact=escape(support_contact))
    await message.answer(text)
