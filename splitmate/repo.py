"""All database queries of the bot live here."""

from aiogram.types import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from splitmate.models import Chat, Expense, Member, Settlement, Share
from splitmate.money import net_balances, split_equally

HISTORY_LIMIT = 10


async def ensure_chat(session: AsyncSession, chat_id: int, title: str | None) -> Chat:
    chat = await session.get(Chat, chat_id)
    if chat is None:
        chat = Chat(id=chat_id, title=title or "", currency="₽")
        session.add(chat)
        await session.commit()
    elif title and chat.title != title:
        chat.title = title
        await session.commit()
    return chat


async def ensure_member(session: AsyncSession, chat_id: int, user: User) -> bool:
    """Add the user to the chat's participants. Returns True if they just joined."""
    member = await session.get(Member, (chat_id, user.id))
    if member is None:
        session.add(
            Member(chat_id=chat_id, user_id=user.id, name=user.full_name, username=user.username)
        )
        await session.commit()
        return True
    if member.name != user.full_name or member.username != user.username:
        member.name, member.username = user.full_name, user.username
        await session.commit()
    return False


async def members(session: AsyncSession, chat_id: int) -> list[Member]:
    result = await session.scalars(
        select(Member).where(Member.chat_id == chat_id).order_by(Member.joined_at)
    )
    return list(result)


async def names(session: AsyncSession, chat_id: int) -> dict[int, str]:
    return {m.user_id: m.name for m in await members(session, chat_id)}


async def set_currency(session: AsyncSession, chat: Chat, currency: str) -> None:
    chat.currency = currency
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
    _apply_shares(expense, participant_ids)
    session.add(expense)
    await session.commit()
    return expense


def _apply_shares(expense: Expense, participant_ids: list[int]) -> None:
    # Update rows in place: re-creating a share with the same primary key in one flush
    # would clash with the pending delete of the old row
    parts = split_equally(expense.amount, participant_ids)
    existing = {s.user_id: s for s in expense.shares}
    for uid in existing.keys() - parts.keys():
        expense.shares.remove(existing[uid])
    for uid, part in parts.items():
        if uid in existing:
            existing[uid].amount = part
        else:
            expense.shares.append(Share(user_id=uid, amount=part))
    expense.shares.sort(key=lambda s: s.user_id)


async def get_expense(session: AsyncSession, expense_id: int) -> Expense | None:
    return await session.get(Expense, expense_id)


async def set_participants(
    session: AsyncSession, expense: Expense, participant_ids: list[int]
) -> None:
    _apply_shares(expense, participant_ids)
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
    expenses = await session.scalars(
        select(Expense).where(Expense.chat_id == chat_id, Expense.is_deleted.is_(False))
    )
    settlements = await session.scalars(select(Settlement).where(Settlement.chat_id == chat_id))
    return net_balances(
        ((e.payer_id, e.amount, {s.user_id: s.amount for s in e.shares}) for e in expenses),
        ((s.from_id, s.to_id, s.amount) for s in settlements),
    )


async def add_settlement(
    session: AsyncSession, chat_id: int, from_id: int, to_id: int, amount: int
) -> None:
    session.add(Settlement(chat_id=chat_id, from_id=from_id, to_id=to_id, amount=amount))
    await session.commit()
