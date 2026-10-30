"""All database queries of the bot live here."""

from aiogram.types import User
from sqlalchemy import BigInteger, delete, exists, literal, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from splitmate.models import NAME_LENGTH, Chat, Expense, Member, Settlement, Share
from splitmate.money import net_balances, settle_up, split_with_fixed
from splitmate.texts import TEXTS

HISTORY_LIMIT = 10
# Row locks for read-modify-write. NO KEY: rows referring to the locked one can still be added
NO_KEY_UPDATE = {"key_share": True}


async def ensure_chat(
    session: AsyncSession, chat_id: int, title: str | None, lang: str = "ru"
) -> Chat:
    """Get the chat, creating it on first contact with `lang` and that language's currency."""
    chat = await session.get(Chat, chat_id)
    if chat is None:
        # The first updates from a new chat come in together: only one insert counts
        await session.execute(
            pg_insert(Chat)
            .values(id=chat_id, title=title or "", lang=lang, currency=TEXTS[lang].DEFAULT_CURRENCY)
            .on_conflict_do_nothing()
        )
        await session.commit()
        chat = await session.get(Chat, chat_id)
    elif title and chat.title != title:
        chat.title = title
        await session.commit()
    return chat


def member_name(user: User) -> str:
    return user.full_name[:NAME_LENGTH]


async def ensure_member(
    session: AsyncSession, chat_id: int, user: User, *, rejoin: bool = False
) -> bool:
    """Add the user to the chat's participants; `rejoin` also brings back someone who left.
    Returns True if they just joined (or came back)."""
    name = member_name(user)
    # A double tap inserts twice at the same moment: the second insert does nothing
    result = await session.execute(
        pg_insert(Member)
        .values(chat_id=chat_id, user_id=user.id, name=name, username=user.username)
        .on_conflict_do_nothing()
        .returning(Member.user_id)
    )
    if result.scalar() is not None:
        await session.commit()
        return True
    member = await session.get(Member, (chat_id, user.id))
    came_back = rejoin and not member.active
    if came_back:
        member.active = True
    if member.name != name or member.username != user.username:
        member.name, member.username = name, user.username
    await session.commit()
    return came_back


async def leave(session: AsyncSession, chat_id: int, user_id: int) -> bool:
    """New expenses stop including the person; what they paid and owe so far stays.
    Returns False if they weren't taking part anyway."""
    result = await session.execute(
        update(Member)
        .where(Member.chat_id == chat_id, Member.user_id == user_id, Member.active.is_(True))
        .values(active=False)
        .returning(Member.user_id)
        .execution_options(synchronize_session=False)
    )
    await session.commit()
    return result.scalar() is not None


async def members(session: AsyncSession, chat_id: int) -> list[Member]:
    """Everyone who ever took part, including those who left (see Member.active)."""
    result = await session.scalars(
        select(Member).where(Member.chat_id == chat_id).order_by(Member.joined_at)
    )
    return list(result)


async def names(session: AsyncSession, chat_id: int) -> dict[int, str]:
    return {m.user_id: m.name for m in await members(session, chat_id)}


async def set_chat_lang(session: AsyncSession, chat: Chat, lang: str) -> None:
    chat.lang = lang
    await session.commit()


async def set_currency(session: AsyncSession, chat: Chat, currency: str) -> None:
    chat.currency = currency
    await session.commit()


async def move_chat(session: AsyncSession, old_id: int, new_id: int) -> None:
    """A group upgraded to a supergroup gets a new id: move its participants, expenses and
    settlements there in one transaction. Telegram announces the upgrade in both chats, so
    this runs twice; the second time nothing is left to move. If people already used the
    new chat, its participants are merged and the old chat's currency and language win."""
    old = await session.get(Chat, old_id, with_for_update=True, populate_existing=True)
    if old is None or not await session.scalar(select(exists().where(Member.chat_id == old_id))):
        return
    await session.execute(
        pg_insert(Chat)
        .values(id=new_id, title=old.title, currency=old.currency, lang=old.lang)
        .on_conflict_do_update(
            index_elements=[Chat.id], set_={"currency": old.currency, "lang": old.lang}
        )
    )
    # Someone who already joined in the new chat keeps that row
    moved = select(
        literal(new_id, BigInteger),
        Member.user_id,
        Member.name,
        Member.username,
        Member.joined_at,
        Member.active,
    ).where(Member.chat_id == old_id)
    await session.execute(
        pg_insert(Member)
        .from_select(["chat_id", "user_id", "name", "username", "joined_at", "active"], moved)
        .on_conflict_do_nothing()
    )
    await session.execute(
        delete(Member).where(Member.chat_id == old_id).execution_options(synchronize_session=False)
    )
    for table in (Expense, Settlement):
        await session.execute(
            update(table)
            .where(table.chat_id == old_id)
            .values(chat_id=new_id)
            .execution_options(synchronize_session=False)
        )
    await session.commit()


# --- Expenses ---


async def add_expense(
    session: AsyncSession,
    chat_id: int,
    payer_id: int,
    amount: int,
    description: str,
    participant_ids: list[int],
) -> Expense:
    expense = Expense(
        chat_id=chat_id, payer_id=payer_id, amount=amount, description=description, shares=[]
    )
    _apply_shares(expense, participant_ids, fixed={})
    session.add(expense)
    await session.commit()
    return expense


def fixed_shares(expense: Expense) -> dict[int, int]:
    return {s.user_id: s.amount for s in expense.shares if s.fixed}


def _apply_shares(expense: Expense, participant_ids: list[int], fixed: dict[int, int]) -> None:
    """Recalculate shares; raises ShareError (before changing anything) if they can't add up."""
    parts = split_with_fixed(expense.amount, participant_ids, fixed)
    # Update rows in place: re-creating a share with the same primary key in one flush
    # would clash with the pending delete of the old row
    existing = {s.user_id: s for s in expense.shares}
    for uid in existing.keys() - parts.keys():
        expense.shares.remove(existing[uid])
    for uid, part in parts.items():
        share = existing.get(uid)
        if share is None:
            share = Share(user_id=uid)
            expense.shares.append(share)
        share.amount, share.fixed = part, uid in fixed
    expense.shares.sort(key=lambda s: s.user_id)


async def get_expense(
    session: AsyncSession, expense_id: int, *, lock: bool = False
) -> Expense | None:
    """`lock` keeps the expense locked until commit, for changing it: presses at the same
    moment take turns instead of each recalculating the shares from the same old state."""
    return await session.get(
        Expense,
        expense_id,
        with_for_update=NO_KEY_UPDATE if lock else None,
        populate_existing=lock,  # read again: it may have changed since this session loaded it
    )


async def set_participants(
    session: AsyncSession, expense: Expense, participant_ids: list[int]
) -> None:
    """Change who takes part, keeping the custom amounts of those who stay."""
    _apply_shares(expense, participant_ids, fixed_shares(expense))
    await session.commit()


async def set_share(session: AsyncSession, expense: Expense, user_id: int, amount: int) -> None:
    """Give one person a custom amount; everyone without one splits the rest."""
    fixed = fixed_shares(expense) | {user_id: amount}
    _apply_shares(expense, [s.user_id for s in expense.shares], fixed)
    await session.commit()


async def split_evenly(session: AsyncSession, expense: Expense) -> None:
    _apply_shares(expense, [s.user_id for s in expense.shares], fixed={})
    await session.commit()


async def delete_expense(session: AsyncSession, expense: Expense) -> None:
    expense.is_deleted = True
    await session.commit()


async def recent_expenses(session: AsyncSession, chat_id: int) -> list[Expense]:
    result = await session.scalars(
        select(Expense)
        .where(Expense.chat_id == chat_id, Expense.is_deleted.is_(False))
        .order_by(Expense.created_at.desc())
        .limit(HISTORY_LIMIT)
    )
    return list(result)


# --- Balances ---


async def balances(session: AsyncSession, chat_id: int) -> dict[int, int]:
    # Fresh rows, also for expenses this session loaded before: they may have changed since
    expenses = await session.scalars(
        select(Expense)
        .where(Expense.chat_id == chat_id, Expense.is_deleted.is_(False))
        .execution_options(populate_existing=True)
    )
    settlements = await session.scalars(select(Settlement).where(Settlement.chat_id == chat_id))
    return net_balances(
        ((e.payer_id, e.amount, {s.user_id: s.amount for s in e.shares}) for e in expenses),
        ((s.from_id, s.to_id, s.amount) for s in settlements),
    )


async def record_settlement(
    session: AsyncSession, chat_id: int, debtor: int, creditor: int, amount: int
) -> bool:
    """Record that `debtor` paid `creditor` back `amount`, if /balance still suggests exactly
    this transfer; False if the balance has changed since. The chat stays locked meanwhile,
    so a double tap can't record the same transfer twice."""
    await session.execute(
        select(Chat.id).where(Chat.id == chat_id).with_for_update(**NO_KEY_UPDATE)
    )
    if (debtor, creditor, amount) not in settle_up(await balances(session, chat_id)):
        await session.commit()  # nothing to save: just releases the lock
        return False
    session.add(Settlement(chat_id=chat_id, from_id=debtor, to_id=creditor, amount=amount))
    await session.commit()
    return True
