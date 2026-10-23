from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter, Command, CommandObject
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from splitmate import keyboards as kb
from splitmate import repo, texts
from splitmate.models import Expense
from splitmate.money import fmt_money, parse_amount, settle_up

GROUPS = {"group", "supergroup"}
INLINE_PREFIX = "💸 "  # messages sent through the bot's inline mode start with this

router = Router(name="group")
router.message.filter(F.chat.type.in_(GROUPS))
router.callback_query.filter(F.message.chat.type.in_(GROUPS))
router.my_chat_member.filter(F.chat.type.in_(GROUPS))


async def welcome_text(bot: Bot) -> str:
    return texts.WELCOME_GROUP.format(bot=(await bot.me()).username)


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, session: AsyncSession, bot: Bot) -> None:
    await repo.ensure_chat(session, event.chat.id, event.chat.title)
    await bot.send_message(event.chat.id, await welcome_text(bot), reply_markup=kb.join())


@router.message(Command("start", "help"))
async def help_cmd(message: Message, session: AsyncSession, bot: Bot) -> None:
    await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await message.answer(await welcome_text(bot), reply_markup=kb.join())


# --- Participants ---


@router.message(Command("join"))
async def join_cmd(message: Message, session: AsyncSession) -> None:
    await repo.ensure_chat(session, message.chat.id, message.chat.title)
    if await repo.ensure_member(session, message.chat.id, message.from_user):
        await message.answer(texts.JOINED.format(name=texts.name(message.from_user.full_name)))
    else:
        await message.reply(texts.ALREADY_JOINED)


@router.callback_query(kb.Join.filter())
async def join_button(cb: CallbackQuery, session: AsyncSession) -> None:
    await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    if await repo.ensure_member(session, cb.message.chat.id, cb.from_user):
        await cb.message.answer(texts.JOINED.format(name=texts.name(cb.from_user.full_name)))
        await cb.answer()
    else:
        await cb.answer(texts.ALREADY_JOINED)


@router.message(Command("members"))
async def members_cmd(message: Message, session: AsyncSession) -> None:
    people = await repo.members(session, message.chat.id)
    listing = ", ".join(escape(m.name) for m in people) or "—"
    await message.answer(texts.MEMBERS.format(names=listing), reply_markup=kb.join())


# --- Expenses ---


async def expense_text(session: AsyncSession, expense: Expense, currency: str) -> str:
    names = await repo.names(session, expense.chat_id)
    parts = sorted({s.amount for s in expense.shares})
    each = fmt_money(parts[0], currency)
    if len(parts) > 1:  # remainder kopecks make some shares one unit bigger
        each = f"{each} – {fmt_money(parts[-1], currency)}"
    return texts.EXPENSE.format(
        payer=texts.name(names.get(expense.payer_id, "?")),
        amount=fmt_money(expense.amount, currency),
        description=texts.with_description(expense.description),
        count=len(expense.shares),
        names=", ".join(escape(names.get(s.user_id, "?")) for s in expense.shares),
        each=each,
    )


async def record_expense(
    message: Message, session: AsyncSession, payer: User, amount: int, description: str
) -> None:
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await repo.ensure_member(session, chat.id, payer)
    people = [m.user_id for m in await repo.members(session, chat.id)]
    expense = await repo.add_expense(session, chat.id, payer.id, amount, description, people)
    await message.reply(
        await expense_text(session, expense, chat.currency), reply_markup=kb.expense(expense.id)
    )


@router.message(Command("add"))
async def add_cmd(message: Message, command: CommandObject, session: AsyncSession) -> None:
    parsed = parse_amount(command.args or "")
    if parsed is None:
        await message.reply(texts.ADD_USAGE)
        return
    await record_expense(message, session, message.from_user, *parsed)


@router.message(F.via_bot, F.text.startswith(INLINE_PREFIX))
async def inline_expense(message: Message, session: AsyncSession, bot: Bot) -> None:
    """An expense typed as `@bot 3000 такси` and sent to the group."""
    if message.via_bot.id != bot.id:
        return
    parsed = parse_amount(message.text.removeprefix(INLINE_PREFIX))
    if parsed:
        await record_expense(message, session, message.from_user, *parsed)


async def load_own_expense(cb: CallbackQuery, session: AsyncSession, expense_id: int):
    expense = await repo.get_expense(session, expense_id)
    if expense is None or expense.is_deleted or expense.chat_id != cb.message.chat.id:
        await cb.answer()
        return None
    if expense.payer_id != cb.from_user.id:
        await cb.answer(texts.ONLY_PAYER, show_alert=True)
        return None
    return expense


@router.callback_query(kb.ExpenseAction.filter(F.action == "people"))
async def edit_people(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession
) -> None:
    expense = await load_own_expense(cb, session, callback_data.id)
    if expense is None:
        return
    await show_participants(cb, session, expense)
    await cb.answer()


async def show_participants(cb: CallbackQuery, session: AsyncSession, expense: Expense) -> None:
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    people = await repo.members(session, expense.chat_id)
    await cb.message.edit_text(
        texts.CHOOSE_PARTICIPANTS.format(
            amount=fmt_money(expense.amount, chat.currency),
            description=texts.with_description(expense.description),
        ),
        reply_markup=kb.participants(expense.id, people, {s.user_id for s in expense.shares}),
    )


@router.callback_query(kb.Toggle.filter())
async def toggle_person(cb: CallbackQuery, callback_data: kb.Toggle, session: AsyncSession) -> None:
    expense = await load_own_expense(cb, session, callback_data.expense)
    if expense is None:
        return
    selected = {s.user_id for s in expense.shares} ^ {callback_data.user}
    if not selected:
        await cb.answer(texts.NEED_ONE_PARTICIPANT, show_alert=True)
        return
    await repo.set_participants(session, expense, list(selected))
    await show_participants(cb, session, expense)
    await cb.answer()


@router.callback_query(kb.ExpenseAction.filter(F.action == "done"))
async def people_done(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession
) -> None:
    expense = await load_own_expense(cb, session, callback_data.id)
    if expense is None:
        return
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    await cb.message.edit_text(
        await expense_text(session, expense, chat.currency), reply_markup=kb.expense(expense.id)
    )
    await cb.answer()


@router.callback_query(kb.ExpenseAction.filter(F.action == "delete"))
async def delete_expense(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession
) -> None:
    expense = await load_own_expense(cb, session, callback_data.id)
    if expense is None:
        return
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    await repo.delete_expense(session, expense)
    await cb.message.edit_text(
        texts.EXPENSE_DELETED.format(
            amount=fmt_money(expense.amount, chat.currency),
            description=texts.with_description(expense.description),
        )
    )
    await cb.answer()


@router.message(Command("history"))
async def history(message: Message, session: AsyncSession) -> None:
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    items = await repo.recent_expenses(session, chat.id)
    if not items:
        await message.answer(texts.HISTORY_EMPTY)
        return
    names = await repo.names(session, chat.id)
    lines = [
        f"{e.created_at:%d.%m} · {escape(names.get(e.payer_id, '?'))} · "
        f"{fmt_money(e.amount, chat.currency)}{texts.with_description(e.description)}"
        for e in items
    ]
    await message.answer(texts.HISTORY.format(lines="\n".join(lines)))


# --- Balance ---


async def balance_view(session: AsyncSession, chat_id: int, title: str | None):
    chat = await repo.ensure_chat(session, chat_id, title)
    net = await repo.balances(session, chat_id)
    if not net:
        return texts.BALANCE_EMPTY, None
    names = await repo.names(session, chat_id)
    lines = [
        f"{escape(names.get(uid, '?'))}: {'+' if v > 0 else ''}{fmt_money(v, chat.currency)}"
        for uid, v in sorted(net.items(), key=lambda kv: -kv[1])
    ]
    transfers = settle_up(net)
    transfer_lines = [
        f"{escape(names.get(d, '?'))} → {escape(names.get(c, '?'))}: "
        f"<b>{fmt_money(a, chat.currency)}</b>"
        for d, c, a in transfers
    ]
    text = texts.BALANCE.format(lines="\n".join(lines), transfers="\n".join(transfer_lines))
    return text + texts.BALANCE_HINT, kb.settle(transfers, names, chat.currency)


@router.message(Command("balance"))
async def balance(message: Message, session: AsyncSession) -> None:
    text, markup = await balance_view(session, message.chat.id, message.chat.title)
    await message.answer(text, reply_markup=markup)


@router.callback_query(kb.Settle.filter())
async def settle(cb: CallbackQuery, callback_data: kb.Settle, session: AsyncSession) -> None:
    if cb.from_user.id not in (callback_data.debtor, callback_data.creditor):
        await cb.answer(texts.SETTLE_NOT_YOURS, show_alert=True)
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    # Take the amount from the current balance, not from the (possibly old) button
    current = {(d, c): a for d, c, a in settle_up(await repo.balances(session, chat.id))}
    amount = current.get((callback_data.debtor, callback_data.creditor))
    if amount is None:
        await cb.answer(texts.SETTLE_STALE, show_alert=True)
        return
    await repo.add_settlement(
        session, chat.id, callback_data.debtor, callback_data.creditor, amount
    )
    names = await repo.names(session, chat.id)
    await cb.message.answer(
        texts.SETTLED.format(
            debtor=texts.name(names.get(callback_data.debtor, "?")),
            creditor=texts.name(names.get(callback_data.creditor, "?")),
            amount=fmt_money(amount, chat.currency),
        )
    )
    text, markup = await balance_view(session, chat.id, None)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.message(Command("currency"))
async def currency(message: Message, command: CommandObject, session: AsyncSession) -> None:
    value = (command.args or "").strip()
    if not value or len(value) > 8:
        await message.reply(texts.CURRENCY_USAGE)
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await repo.set_currency(session, chat, value)
    await message.answer(texts.CURRENCY_SET.format(currency=escape(value)))
