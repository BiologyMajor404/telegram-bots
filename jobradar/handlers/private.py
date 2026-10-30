"""Private chat: subscribing, settings, own sources, language and the search status."""

from datetime import UTC, datetime
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from jobradar import keyboards as kb
from jobradar import links, repo
from jobradar.handlers.payments import fmt_date, pro_offer
from jobradar.mail import MailConfig
from jobradar.models import Subscriber
from jobradar.plans import Access
from jobradar.radar import Radar
from jobradar.states import AddSearch
from jobradar.texts import TEXTS, Ru
from shared.i18n import CHOOSE_LANGUAGE, LANGS, SetLang, lang_keyboard

router = Router(name="private")
router.message.filter(F.chat.type == "private")


def allowed(user_id: int, allowed_ids: set[int]) -> bool:
    return not allowed_ids or user_id in allowed_ids


def plan_text(t: Ru, sub: Subscriber, access: Access) -> str:
    now = datetime.now(UTC)
    if sub.gift:
        return t.PLAN_GIFT
    if sub.pro_until is not None and sub.pro_until > now:
        return t.PLAN_PRO.format(until=fmt_date(sub.pro_until))
    return t.PLAN_ADMIN if access.is_pro(sub, now) else t.PLAN_FREE


def settings_text(t: Ru, sub: Subscriber, access: Access) -> str:
    return t.SETTINGS.format(
        plan=plan_text(t, sub, access),
        mode=t.MODE_TOP if sub.only_top else t.MODE_ALL,
        state=t.STATE_ON if sub.active else t.STATE_OFF,
    )


async def sources_view(session: AsyncSession, t: Ru, sub: Subscriber, access: Access):
    items = await repo.user_sources(session, sub.id)
    limit = access.plan(sub, datetime.now(UTC)).sources
    listed = "\n".join(f"• {escape(links.label(s.kind, s.ref))}" for s in items)
    text = t.SOURCES.format(count=len(items), limit=limit, list=listed or t.SOURCES_EMPTY)
    if len(items) > limit:  # e.g. added on Pro, which has ended: the radar uses the first ones
        text += t.OVER_LIMIT.format(limit=limit)
    return text, kb.sources(items)


def source_limit_text(t: Ru, sub: Subscriber, access: Access, limit: int) -> str:
    if access.is_pro(sub, datetime.now(UTC)):
        return t.SOURCE_LIMIT_PRO.format(limit=limit)
    return t.SOURCE_LIMIT_FREE.format(limit=limit, pro_limit=access.plans.pro.sources)


@router.message(CommandStart())
async def start(
    message: Message,
    session: AsyncSession,
    t: Ru,
    lang: str,
    allowed_ids: set[int],
    poll_minutes: int,
    radar: Radar,
    access: Access,
    state: FSMContext,
) -> None:
    if not allowed(message.from_user.id, allowed_ids):
        await message.answer(t.NOT_ALLOWED)
        return
    sub = await repo.subscribe(session, message.from_user.id, lang)
    radar.wake()  # the first jobs come right away, not at the next tick
    await message.answer(t.WELCOME.format(minutes=poll_minutes))
    if not await repo.user_searches(session, sub.id):
        await state.set_state(AddSearch.waiting)
        await message.answer(t.SEARCH_ASK)
        return
    await message.answer(settings_text(t, sub, access), reply_markup=kb.settings(t, sub))


@router.message(Command("language"))
async def choose_language(message: Message) -> None:
    await message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())


@router.message(Command("sources"))
async def show_sources(message: Message, session: AsyncSession, t: Ru, access: Access) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    text, markup = await sources_view(session, t, sub, access)
    await message.answer(text, reply_markup=markup, disable_web_page_preview=True)


@router.message(Command("mail"))
async def show_mail(message: Message, session: AsyncSession, t: Ru, mail: MailConfig) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    if not mail.enabled:
        await message.answer(t.MAIL_OFF)
        return
    address = mail.personal(await repo.mail_token(session, sub))
    await message.answer(t.MAIL.format(address=address), disable_web_page_preview=True)


@router.message(Command("pro"))
async def show_pro(message: Message, session: AsyncSession, t: Ru, access: Access) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    text, markup = await pro_offer(message.bot, sub, t, access)
    await message.answer(text, reply_markup=markup)


@router.message(Command("status"))
async def status(
    message: Message, session: AsyncSession, t: Ru, radar: Radar, access: Access
) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    now = datetime.now(UTC)
    last = radar.last
    plan = access.plan(sub, now)
    day = (await repo.usage(session, radar.today())).get(sub.id)
    text = t.STATUS.format(
        last=last.at.astimezone(radar.tz).strftime("%d.%m %H:%M") if last.at else t.NEVER,
        found=last.found,
        fresh=last.fresh,
        plan=plan_text(t, sub, access),
        sent=day.cards if day else 0,
        cards=plan.cards,
        sources=len(await repo.user_sources(session, sub.id)),
        sources_limit=plan.sources,
        user_id=sub.id,
    )
    if sub.id in access.admin_ids:
        today_usd, month_usd = await radar.spent()
        monthly = await radar.monthly_usd()
        text += t.STATUS_ADMIN.format(
            checked=await repo.ai_checks(session, radar.today()),
            today=f"{today_usd:.3f}",
            day_budget=f"{monthly / radar.days_in_month():.3f}",
            month=f"{month_usd:.2f}",
            budget=f"{monthly:.2f}",
            pros=await repo.paying_count(session, now),
        )
    await message.answer(text)


@router.callback_query(kb.Setting.filter(F.name == "lang"))
async def language_menu(cb: CallbackQuery) -> None:
    await cb.message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())
    await cb.answer()


@router.callback_query(kb.Setting.filter())
async def change_setting(
    cb: CallbackQuery, callback_data: kb.Setting, session: AsyncSession, t: Ru, access: Access
) -> None:
    sub = await repo.get_subscriber(session, cb.from_user.id)
    if sub is None:
        await cb.answer(t.NOT_ALLOWED, show_alert=True)
        return
    if callback_data.name == "sources":
        text, markup = await sources_view(session, t, sub, access)
        await cb.message.answer(text, reply_markup=markup, disable_web_page_preview=True)
        await cb.answer()
        return
    if callback_data.name == "pro":
        text, markup = await pro_offer(cb.bot, sub, t, access)
        await cb.message.answer(text, reply_markup=markup)
        await cb.answer()
        return
    if callback_data.name == "top":
        sub.only_top = sub.only_top and callback_data.value  # it can only be switched off
    else:
        sub.active = callback_data.value
    await session.commit()
    await cb.message.edit_text(settings_text(t, sub, access), reply_markup=kb.settings(t, sub))
    await cb.answer()


@router.callback_query(kb.RemoveSource.filter())
async def remove_source(
    cb: CallbackQuery,
    callback_data: kb.RemoveSource,
    session: AsyncSession,
    t: Ru,
    access: Access,
) -> None:
    sub = await repo.get_subscriber(session, cb.from_user.id)
    if sub is None:
        await cb.answer(t.NOT_ALLOWED, show_alert=True)
        return
    await repo.remove_source(session, sub.id, callback_data.id)
    text, markup = await sources_view(session, t, sub, access)
    await cb.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    await cb.answer(t.SOURCE_REMOVED)


@router.callback_query(SetLang.filter(F.code.in_(LANGS)))
async def set_language(cb: CallbackQuery, callback_data: SetLang, session: AsyncSession) -> None:
    sub = await repo.get_subscriber(session, cb.from_user.id)
    if sub is not None:
        sub.lang = callback_data.code
        await session.commit()
    await cb.message.edit_text(TEXTS[callback_data.code].LANGUAGE_SET)
    await cb.answer()


async def add_source(
    message: Message, session: AsyncSession, t: Ru, sub: Subscriber, radar: Radar, access: Access
) -> None:
    link = links.parse(message.text)
    if link is None:
        await message.answer(t.SOURCE_BAD_LINK, disable_web_page_preview=True)
        return
    if link.key in radar.global_keys:
        await message.answer(t.SOURCE_GLOBAL)
        return
    existing = await repo.user_sources(session, sub.id)
    if any(s.key == link.key for s in existing):
        await message.answer(t.SOURCE_DUPLICATE)
        return
    limit = access.plan(sub, datetime.now(UTC)).sources
    if len(existing) >= limit:
        await message.answer(source_limit_text(t, sub, access, limit))
        return
    progress = await message.answer(t.SOURCE_CHECKING)
    name = escape(link.label)
    if not await links.readable(link):
        await progress.edit_text(t.SOURCE_UNREACHABLE.format(name=name))
        return
    # Counted again while saving: several links sent at once are checked side by side
    added = await repo.add_source(session, sub.id, link.kind, link.ref, limit)
    if added is None:
        await progress.edit_text(source_limit_text(t, sub, access, limit))
        return
    await progress.edit_text(t.SOURCE_ADDED.format(name=name) if added else t.SOURCE_DUPLICATE)
    radar.wake()


@router.message(F.text)
async def text_message(
    message: Message, session: AsyncSession, t: Ru, radar: Radar, access: Access
) -> None:
    """A link adds a source; /settings and any other text show the settings."""
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    if links.looks_like_link(message.text):
        await add_source(message, session, t, sub, radar, access)
        return
    await message.answer(settings_text(t, sub, access), reply_markup=kb.settings(t, sub))


@router.message()
async def other_message(message: Message, session: AsyncSession, t: Ru, access: Access) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    await message.answer(settings_text(t, sub, access), reply_markup=kb.settings(t, sub))
