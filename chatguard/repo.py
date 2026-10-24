"""All database queries of the bot live here."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from chatguard.models import Chat, Incident, Member

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


def ai_budget_left(chat: Chat, today: date, limit: int) -> bool:
    return chat.ai_day != today or chat.ai_checks < limit


def spend_ai_check(chat: Chat, today: date) -> None:
    if chat.ai_day != today:
        chat.ai_day, chat.ai_checks = today, 0
    chat.ai_checks += 1


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
    await session.commit()
