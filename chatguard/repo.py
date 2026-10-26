"""All database queries of the bot live here."""

from datetime import date, datetime

from sqlalchemy import case, or_, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard.config import Plans
from chatguard.models import AiUsage, Chat, Incident, Member, Spammer

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
    """For display only; spending goes through the atomic reserve_* functions."""
    return chat.ai_day != today or chat.ai_checks < limit


async def reserve_ai_check(session: AsyncSession, chat_id: int, today: date, limit: int) -> bool:
    """Take one AI check from the chat's daily budget in a single UPDATE, so concurrent
    messages can't all pass a stale "budget left" check."""
    result = await session.execute(
        update(Chat)
        .where(Chat.id == chat_id, or_(Chat.ai_day.is_distinct_from(today), Chat.ai_checks < limit))
        .values(ai_checks=case((Chat.ai_day == today, Chat.ai_checks + 1), else_=1), ai_day=today)
        .returning(Chat.id)
        .execution_options(synchronize_session=False)
    )
    await session.commit()
    return result.first() is not None


async def reserve_global_ai_check(session: AsyncSession, today: date, limit: int) -> bool:
    """The same for the whole bot, so many small chats can't add up to a huge bill."""
    stmt = pg_insert(AiUsage).values(day=today, checks=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=[AiUsage.day],
        set_={"checks": AiUsage.checks + 1},
        where=AiUsage.checks < limit,
    ).returning(AiUsage.checks)
    result = await session.execute(stmt)
    await session.commit()
    return result.first() is not None


async def bump_stats(
    session: AsyncSession, chat_id: int, checked: int = 0, caught: int = 0
) -> None:
    await session.execute(
        update(Chat)
        .where(Chat.id == chat_id)
        .values(checked=Chat.checked + checked, caught=Chat.caught + caught)
        .execution_options(synchronize_session=False)
    )


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
