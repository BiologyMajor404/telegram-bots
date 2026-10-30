"""Inline keyboards and their callback data."""

from collections.abc import Iterable

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from jobradar.links import label
from jobradar.models import Subscriber, UserSearch, UserSource
from jobradar.texts import Ru
from shared.i18n import LANGUAGE_BUTTON


class Setting(CallbackData, prefix="cfg"):
    name: str  # top | active | lang | sources | pro
    value: bool = False


class RemoveSource(CallbackData, prefix="src"):
    id: int


class FilterCb(CallbackData, prefix="flt"):
    screen: str  # main | searches | add | lang | region | country | back
    item: str = ""  # what to toggle or pick on that screen


class RemoveSearch(CallbackData, prefix="srch"):
    id: int


def searches(t: Ru, items: list[UserSearch]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in items:
        b.button(text=f"❌ {s.label}", callback_data=RemoveSearch(id=s.id))
    b.button(text=t.BTN_ADD_SEARCH, callback_data=FilterCb(screen="add"))
    b.button(text=t.BTN_BACK, callback_data=FilterCb(screen="main"))
    b.adjust(1)
    return b.as_markup()


def filters(t: Ru, sub: Subscriber) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_F_SEARCHES, callback_data=FilterCb(screen="searches"))
    remote = t.REMOTE_ONLY if sub.remote_only else t.REMOTE_HYBRID
    schedule = t.SCHEDULE_FLEXIBLE if sub.flexible_only else t.SCHEDULE_ANY
    b.button(text=f"🏠 {remote}", callback_data=FilterCb(screen="main", item="remote"))
    b.button(text=f"🕒 {schedule}", callback_data=FilterCb(screen="main", item="schedule"))
    b.button(text=t.BTN_F_LANGUAGES, callback_data=FilterCb(screen="lang"))
    b.button(text=t.BTN_F_REGIONS, callback_data=FilterCb(screen="region"))
    b.button(text=t.BTN_F_COUNTRY, callback_data=FilterCb(screen="country"))
    b.button(text=t.BTN_BACK, callback_data=FilterCb(screen="back"))
    b.adjust(1, 2, 2, 1, 1)
    return b.as_markup()


def pick(
    screen: str, labels: dict[str, str], chosen: Iterable[str], t: Ru, multi: bool = True
) -> InlineKeyboardMarkup:
    """A list to toggle (✅ / ▫️) or, with multi=False, to pick one from."""
    chosen = set(chosen)
    b = InlineKeyboardBuilder()
    for key, name in labels.items():
        mark = "✅ " if key in chosen else ("▫️ " if multi else "")
        b.button(text=mark + name, callback_data=FilterCb(screen=screen, item=key))
    b.button(text=t.BTN_BACK, callback_data=FilterCb(screen="main"))
    b.adjust(2)
    return b.as_markup()


def settings(t: Ru, sub: Subscriber) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    # "Only podcasts and talking heads" is from the bot's video editing days and would
    # starve any other search, so it is offered no more: only switched off
    if sub.only_top:
        b.button(text=t.BTN_SHOW_ALL, callback_data=Setting(name="top", value=False))
    if sub.active:
        b.button(text=t.BTN_PAUSE, callback_data=Setting(name="active", value=False))
    else:
        b.button(text=t.BTN_RESUME, callback_data=Setting(name="active", value=True))
    b.button(text=t.BTN_FILTERS, callback_data=FilterCb(screen="main"))
    b.button(text=t.BTN_SOURCES, callback_data=Setting(name="sources"))
    b.button(text=t.BTN_PRO, callback_data=Setting(name="pro"))
    b.button(text=LANGUAGE_BUTTON, callback_data=Setting(name="lang"))
    b.adjust(*([1] if sub.only_top else []), 1, 1, 2, 1)
    return b.as_markup()


def sources(items: list[UserSource]) -> InlineKeyboardMarkup | None:
    if not items:
        return None
    b = InlineKeyboardBuilder()
    for source in items:
        b.button(
            text=f"❌ {label(source.kind, source.ref)}", callback_data=RemoveSource(id=source.id)
        )
    b.adjust(1)
    return b.as_markup()


def open_job(t: Ru, url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=t.BTN_OPEN, url=url)
    return b.as_markup()
