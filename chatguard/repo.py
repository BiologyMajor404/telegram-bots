"""All database queries of the bot live here."""

from datetime import date, datetime

from sqlalchemy import case, delete, exists, or_, select, update
from sqlalchemy.dialects.postgresql import Insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from chatguard.config import Plans
from chatguard.models import AiUsage, Chat, Incident, Member, Spammer

# How many first messages of a new member get checked
CHECK_FIRST = 3


def _insert_chat(chat_id: int, title: str, lang: str) -> Insert:
    """A chat with the default settings; does nothing if the chat is already there, so
    parallel updates from a new chat can't trip over each other."""
    return (
        pg_insert(Chat)
        .values(id=chat_id, title=title, lang=lang, ai_checks=0, checked=0, caught=0)
        .on_conflict_do_nothing()
    )


async def ensure_chat(
    session: AsyncSession, chat_id: int, title: str | None, lang: str = "ru"
) -> Chat:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        await session.execute(_insert_chat(chat_id, title or "", lang))
        await session.commit()
        chat = await session.get(Chat, chat_id)
    elif title and chat.title != title:
        chat.title = title
        await session.commit()
    return chat


async def get_member(session: AsyncSession, chat_id: int, user_id: int) -> Member:
    member = await session.get(Member, (chat_id, user_id))
    if member is None:
        # Two quick first messages are handled in parallel: the second one finds this row.
        # Committed at once, so no lock on it is held while Telegram and the AI are called
        await session.execute(
            pg_insert(Member)
            .values(chat_id=chat_id, user_id=user_id, clean_messages=0, trusted=False)
            .on_conflict_do_nothing()
        )
        await session.commit()
        member = await session.get(Member, (chat_id, user_id))
    return member


def needs_check(member: Member) -> bool:
    return not member.trusted and member.clean_messages < CHECK_FIRST


async def count_clean(session: AsyncSession, chat_id: int, user_id: int) -> None:
    """One more clean message towards trust, counted in the database so parallel messages
    don't overwrite each other's count."""
    await session.execute(
        update(Member)
        .where(Member.chat_id == chat_id, Member.user_id == user_id)
        .values(clean_messages=Member.clean_messages + 1)
        .execution_options(synchronize_session=False)
    )


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
    """The same for the whole bot, so many small chats can't add up to a huge bill. Free
    chats pass a lower limit than Pro ones, which keeps the rest of the day's checks for Pro."""
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
    """Locks the chat's row until the commit: call it after the Telegram calls, not before."""
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


async def chat_for_payment(session: AsyncSession, chat_id: int) -> Chat | None:
    """The chat a Pro payload names. A group that became a supergroup has a new id, while
    its renewals and old invoice links still carry the old one."""
    migrated = await session.scalar(select(Chat).where(Chat.migrated_from == chat_id))
    return migrated or await session.get(Chat, chat_id)


# --- A group becoming a supergroup ---


def take_over(new: Chat, old: Chat) -> None:
    """The old group's settings and plan replace the defaults the new id got from its first
    updates; the statistics and today's AI checks add up."""
    new.lang, new.enabled, new.action = old.lang, old.enabled, old.action
    if old.pro_until is not None and (new.pro_until is None or old.pro_until > new.pro_until):
        new.pro_until, new.pro_owner_id = old.pro_until, old.pro_owner_id
        new.pro_charge_id = old.pro_charge_id
    new.checked += old.checked
    new.caught += old.caught
    if old.ai_day == new.ai_day:
        new.ai_checks += old.ai_checks
    elif old.ai_day is not None and (new.ai_day is None or old.ai_day > new.ai_day):
        new.ai_day, new.ai_checks = old.ai_day, old.ai_checks
    new.migrated_from = old.id


async def migrate_chat(session: AsyncSession, old_id: int, new_id: int) -> None:
    """Move a group's settings, plan, members, incidents and spammer records to its new
    supergroup id, in one transaction. Telegram reports the move in both chats, so this
    runs twice; the second run only clears a row that an update may have re-created."""
    old = await session.get(Chat, old_id, with_for_update=True, populate_existing=True)
    if old is None:
        return
    # The first update from the supergroup may be creating its row right now
    await session.execute(_insert_chat(new_id, old.title, old.lang))
    new = await session.get(Chat, new_id, with_for_update=True, populate_existing=True)
    if new.migrated_from != old_id:
        take_over(new, old)
    await session.flush()  # the rows moved below point at the new chat
    await _move_people(session, Member, old_id, new_id)
    await _move_people(session, Spammer, old_id, new_id)
    await session.execute(
        update(Incident)
        .where(Incident.chat_id == old_id)
        .values(chat_id=new_id)
        .execution_options(synchronize_session=False)
    )
    await session.delete(old)
    await session.commit()


async def _move_people(
    session: AsyncSession, table: type[Member] | type[Spammer], old_id: int, new_id: int
) -> None:
    """Re-key a chat's per-person rows. Where the new id already has a row for the same
    person (made in the moments before the move), the group's own history wins."""
    moving = select(table.user_id).where(table.chat_id == old_id)
    await session.execute(
        delete(table)
        .where(table.chat_id == new_id, table.user_id.in_(moving))
        .execution_options(synchronize_session=False)
    )
    await session.execute(
        update(table)
        .where(table.chat_id == old_id)
        .values(chat_id=new_id)
        .execution_options(synchronize_session=False)
    )


# --- Incidents and the shared spammer list ---


async def add_incident(session: AsyncSession, **fields) -> Incident:
    incident = Incident(restored=False, **fields)
    session.add(incident)
    await session.commit()
    return incident


async def get_incident(session: AsyncSession, incident_id: int) -> Incident | None:
    return await session.get(Incident, incident_id)


async def restore(session: AsyncSession, incident: Incident) -> None:
    """An admin vouched for this person: trust them in this chat and drop this chat's
    spammer record. Records from other chats stay, so a spammer can't clear their name
    everywhere by getting caught and restored in a group of their own."""
    incident.restored = True
    stmt = pg_insert(Member).values(
        chat_id=incident.chat_id, user_id=incident.user_id, clean_messages=0, trusted=True
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[Member.chat_id, Member.user_id], set_={"trusted": True}
        )
    )
    await session.execute(
        delete(Spammer)
        .where(Spammer.user_id == incident.user_id, Spammer.chat_id == incident.chat_id)
        .execution_options(synchronize_session=False)
    )
    await session.commit()


async def record_spammer(session: AsyncSession, user_id: int, chat_id: int, now: datetime) -> None:
    """One upsert, so two catches of the same person at once can't collide."""
    stmt = pg_insert(Spammer).values(user_id=user_id, chat_id=chat_id, caught=1, last_caught_at=now)
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[Spammer.user_id, Spammer.chat_id],
            set_={"caught": Spammer.caught + 1, "last_caught_at": now},
        )
    )


async def is_known_spammer(session: AsyncSession, user_id: int) -> bool:
    return bool(await session.scalar(select(exists().where(Spammer.user_id == user_id))))
