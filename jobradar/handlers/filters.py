"""The filters screen: what work to look for (in the user's own words) and on which conditions."""

from datetime import UTC, datetime
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from jobradar import keyboards as kb
from jobradar import links, repo
from jobradar.ai import Region
from jobradar.filters import COUNTRIES, LANGUAGES
from jobradar.handlers.private import settings_text
from jobradar.models import Subscriber, UserSearch
from jobradar.plans import Access
from jobradar.radar import Radar
from jobradar.searches import clean_label, normalize
from jobradar.states import AddSearch
from jobradar.texts import Ru

router = Router(name="filters")
router.message.filter(F.chat.type == "private")

# Screen -> the subscriber's list it edits and the keys it offers
LISTS = {
    "lang": ("languages", LANGUAGES),
    "region": ("regions", Region.CHOOSABLE),
}


def names(labels: dict[str, str], keys: list[str]) -> str:
    return ", ".join(labels[k] for k in labels if k in keys) or "—"


def filters_text(t: Ru, sub: Subscriber, searches: list[UserSearch]) -> str:
    return t.FILTERS.format(
        searches=escape(", ".join(s.label for s in searches)) or t.NO_SEARCHES,
        remote=t.REMOTE_ONLY if sub.remote_only else t.REMOTE_HYBRID,
        schedule=t.SCHEDULE_FLEXIBLE if sub.flexible_only else t.SCHEDULE_ANY,
        languages=names(t.LANGUAGE_LABELS, sub.languages),
        regions=names(t.REGION_LABELS, sub.regions),
        country=t.COUNTRY_LABELS.get(sub.country, sub.country),
    )


def searches_text(t: Ru, items: list[UserSearch], limit: int) -> str:
    listed = "\n".join(f"• {escape(s.label)}" for s in items) or t.NO_SEARCHES
    text = t.SEARCHES.format(count=len(items), limit=limit, list=listed)
    if len(items) > limit:  # e.g. added on Pro, which has ended: the radar uses the first ones
        text += t.OVER_LIMIT.format(limit=limit)
    return text


def search_limit_text(t: Ru, sub: Subscriber, access: Access, limit: int) -> str:
    if access.is_pro(sub, datetime.now(UTC)):
        return t.SEARCH_LIMIT_PRO.format(limit=limit)
    return t.SEARCH_LIMIT_FREE.format(limit=limit, pro_limit=access.plans.pro.searches)


async def screen(
    session: AsyncSession, t: Ru, sub: Subscriber, name: str, access: Access
) -> tuple[str, InlineKeyboardMarkup]:
    if name == "searches":
        items = await repo.user_searches(session, sub.id)
        limit = access.plan(sub, datetime.now(UTC)).searches
        return searches_text(t, items, limit), kb.searches(t, items)
    if name == "lang":
        return t.PICK_LANGUAGES, kb.pick(name, t.LANGUAGE_LABELS, sub.languages, t)
    if name == "region":
        return t.PICK_REGIONS, kb.pick(name, t.REGION_LABELS, sub.regions, t)
    if name == "country":
        return t.PICK_COUNTRY, kb.pick(name, t.COUNTRY_LABELS, [sub.country], t, multi=False)
    searches = await repo.user_searches(session, sub.id)
    return filters_text(t, sub, searches), kb.filters(t, sub)


def toggle(sub: Subscriber, screen_name: str, item: str) -> bool:
    """Apply one tap. False when it would leave a list empty."""
    if screen_name == "main":
        if item == "remote":
            sub.remote_only = not sub.remote_only
        elif item == "schedule":
            sub.flexible_only = not sub.flexible_only
        return True
    if screen_name == "country":
        if item in COUNTRIES:
            sub.country = item
        return True
    if screen_name not in LISTS:  # only a forged button gets here
        return True
    field, offered = LISTS[screen_name]
    if item not in offered:
        return True
    current = list(getattr(sub, field))
    if item in current:
        if len(current) == 1:
            return False
        current.remove(item)
    else:
        current.append(item)
    setattr(sub, field, current)  # a new list, so SQLAlchemy sees the change
    return True


async def ask_for_search(message: Message, state: FSMContext, t: Ru) -> None:
    await state.set_state(AddSearch.waiting)
    await message.answer(t.SEARCH_ASK)


@router.message(Command("filters"))
async def show_filters(message: Message, session: AsyncSession, t: Ru, access: Access) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await message.answer(t.NOT_ALLOWED)
        return
    text, markup = await screen(session, t, sub, "main", access)
    await message.answer(text, reply_markup=markup)


@router.callback_query(kb.FilterCb.filter())
async def filter_tap(
    cb: CallbackQuery,
    callback_data: kb.FilterCb,
    session: AsyncSession,
    state: FSMContext,
    t: Ru,
    access: Access,
) -> None:
    sub = await repo.get_subscriber(session, cb.from_user.id)
    if sub is None:
        await cb.answer(t.NOT_ALLOWED, show_alert=True)
        return
    name, item = callback_data.screen, callback_data.item
    if name == "back":
        await cb.message.edit_text(settings_text(t, sub, access), reply_markup=kb.settings(t, sub))
        await cb.answer()
        return
    if name == "add":
        await ask_for_search(cb.message, state, t)
        await cb.answer()
        return
    if item:
        if not toggle(sub, name, item):
            await cb.answer(t.AT_LEAST_ONE, show_alert=True)
            return
        await session.commit()
        if name == "country":
            name = "main"  # one choice: back to the overview right away
    text, markup = await screen(session, t, sub, name, access)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.callback_query(kb.RemoveSearch.filter())
async def remove_search(
    cb: CallbackQuery,
    callback_data: kb.RemoveSearch,
    session: AsyncSession,
    t: Ru,
    access: Access,
) -> None:
    sub = await repo.get_subscriber(session, cb.from_user.id)
    if sub is None:
        await cb.answer(t.NOT_ALLOWED, show_alert=True)
        return
    await repo.remove_search(session, sub.id, callback_data.id)
    text, markup = await screen(session, t, sub, "searches", access)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer(t.SEARCH_REMOVED)


@router.message(
    StateFilter(AddSearch.waiting),
    F.text,
    ~F.text.startswith("/"),
    ~F.text.func(links.looks_like_link),  # a link still adds a source
)
async def add_search(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    t: Ru,
    radar: Radar,
    access: Access,
) -> None:
    sub = await repo.get_subscriber(session, message.from_user.id)
    if sub is None:
        await state.clear()
        await message.answer(t.NOT_ALLOWED)
        return
    label = clean_label(message.text)
    if label is None:
        await message.answer(t.SEARCH_BAD)
        return
    refusal = await why_not(session, t, sub, label, radar, access)
    if refusal:
        await state.clear()
        await message.answer(refusal)
        return
    progress = await message.answer(t.SEARCH_PICKING)
    keywords, cost = await radar.analyzer.expand(label)
    await repo.add_ai_cost(session, radar.today(), cost)
    await repo.add_usage(session, sub.id, radar.today(), checks=1)
    if keywords == []:
        await progress.edit_text(t.SEARCH_NOT_WORK)  # the step stays: they can rephrase
        return
    await state.clear()
    await progress.edit_text(await save_search(session, t, sub, label, keywords, radar, access))


async def why_not(
    session: AsyncSession, t: Ru, sub: Subscriber, label: str, radar: Radar, access: Access
) -> str | None:
    """Why this search can't be added now, or None. Each attempt asks the AI, so it counts
    as one of the user's checks of the day and needs room in the AI budget."""
    existing = await repo.user_searches(session, sub.id)
    if any(normalize(s.label) == normalize(label) for s in existing):
        return t.SEARCH_DUPLICATE
    now = datetime.now(UTC)
    plan = access.plan(sub, now)
    if len(existing) >= plan.searches:
        return search_limit_text(t, sub, access, plan.searches)
    day = (await repo.usage(session, radar.today())).get(sub.id)
    if (day.checks if day else 0) >= plan.own_checks:
        return t.SEARCH_TOO_MANY
    if not await radar.take_check(access.is_pro(sub, now)):
        return t.SEARCH_FAILED
    return None


async def save_search(
    session: AsyncSession,
    t: Ru,
    sub: Subscriber,
    label: str,
    keywords: list[str] | None,
    radar: Radar,
    access: Access,
) -> str:
    """Store the search with the AI's keywords (None: the AI failed); the reply to show."""
    if keywords is None:
        return t.SEARCH_FAILED
    limit = access.plan(sub, datetime.now(UTC)).searches
    # Counted again while saving: two searches sent at once are handled side by side
    added = await repo.add_search(session, sub.id, label, keywords, limit)
    if added is None:
        return search_limit_text(t, sub, access, limit)
    if not added:
        return t.SEARCH_DUPLICATE
    radar.wake()
    return t.SEARCH_ADDED.format(label=escape(label), keywords=escape(", ".join(keywords[1:9])))
