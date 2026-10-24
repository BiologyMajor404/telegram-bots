"""All database queries of the bot live here."""

from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from chatguard.config import Plans
from chatguard.models import Chat, Incident, Member, Spammer

# How many first messages of a new member get checked
CHECK_FIRST = 3


async def ensure_chat(
    session: AsyncSession, chat_id: int, title: str | None, lang: str = "ru"
) -> Chat:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        chat = Chat(id=chat_id, title=title or "", lang=lang, ai_checks=0, checked=0, caught=0)
        session.add(chat)
        await session.commit()
    elif title and chat.title != title:
        chat.title = title
        await session.commit()
    return chat


async def get_member(session: AsyncSession, chat_id: int, user_id: int) -> Member:
    member = await session.get(Member, (chat_id, user_id))
    if member is None:
        member = Member(chat_id=chat_id, user_id=user_id, clean_messages=0, trusted=False)
        session.add(member)
    return member


def needs_check(member: Member) -> bool:
    return not member.trusted and member.clean_messages < CHECK_FIRST


# --- Plans and the daily AI budget ---


def is_pro(chat: Chat, now: datetime) -> bool:
    return chat.pro_until is not None and chat.pro_until > now


def ai_limit(chat: Chat, now: datetime, plans: Plans) -> int:
    return plans.pro_limit if is_pro(chat, now) else plans.free_limit


def ai_budget_left(chat: Chat, today: date, limit: int) -> bool:
    return chat.ai_day != today or chat.ai_checks < limit


def spend_ai_check(chat: Chat, today: date) -> None:
    if chat.ai_day != today:
        chat.ai_day, chat.ai_checks = today, 0
    chat.ai_checks += 1


async def activate_pro(
    session: AsyncSession, chat: Chat, until: datetime, owner_id: int, charge_id: str
) -> None:
    chat.pro_until, chat.pro_owner_id, chat.pro_charge_id = until, owner_id, charge_id
    await session.commit()


# --- Incidents and the shared spammer list ---


async def add_incident(session: AsyncSession, **fields) -> Incident:
    incident = Incident(restored=False, **fields)
    session.add(incident)
    await session.commit()
    return incident


async def get_incident(session: AsyncSession, incident_id: int) -> Incident | None:
    return await session.get(Incident, incident_id)


async def restore(session: AsyncSession, incident: Incident) -> None:
    incident.restored = True
    member = await get_member(session, incident.chat_id, incident.user_id)
    member.trusted = True
    # An admin vouched for this person: drop them from the shared list
    spammer = await session.get(Spammer, incident.user_id)
    if spammer is not None:
        await session.delete(spammer)
    await session.commit()


async def record_spammer(session: AsyncSession, user_id: int, now: datetime) -> None:
    spammer = await session.get(Spammer, user_id)
    if spammer is None:
        spammer = Spammer(user_id=user_id, caught=0)
        session.add(spammer)
    spammer.caught += 1
    spammer.last_caught_at = now


async def is_known_spammer(session: AsyncSession, user_id: int) -> bool:
    return await session.get(Spammer, user_id) is not None
