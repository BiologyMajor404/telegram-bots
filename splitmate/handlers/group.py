import time
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter, Command, CommandObject
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from shared.i18n import CHOOSE_LANGUAGE, SetLang, lang_keyboard
from splitmate import keyboards as kb
from splitmate import repo
from splitmate.i18n import GROUPS
from splitmate.models import Expense
from splitmate.money import fmt_money, parse_amount, settle_up
from splitmate.texts import TEXTS, Ru, name, with_description

INLINE_PREFIX = "💸 "  # messages sent through the bot's inline mode start with this

router = Router(name="group")
router.message.filter(F.chat.type.in_(GROUPS))
router.callback_query.filter(F.message.chat.type.in_(GROUPS))
router.my_chat_member.filter(F.chat.type.in_(GROUPS))


# Adding the bot via the "Add to group" link produces both a join event and a /start
# message; remember recent greetings so the chat gets the welcome only once
WELCOME_DEDUP_SEC = 60
_welcomed_at: dict[int, float] = {}


async def welcome_text(bot: Bot, t: Ru) -> str:
    return t.WELCOME_GROUP.format(bot=(await bot.me()).username)


def just_welcomed(chat_id: int) -> bool:
    now = time.monotonic()
    recent = now - _welcomed_at.get(chat_id, -WELCOME_DEDUP_SEC) < WELCOME_DEDUP_SEC
    _welcomed_at[chat_id] = now
    return recent


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added(event: ChatMemberUpdated, bot: Bot, t: Ru) -> None:
    if not just_welcomed(event.chat.id):
        await bot.send_message(event.chat.id, await welcome_text(bot, t), reply_markup=kb.join(t))


@router.message(Command("start"))
async def start_cmd(message: Message, bot: Bot, t: Ru) -> None:
    if not just_welcomed(message.chat.id):
        await message.answer(await welcome_text(bot, t), reply_markup=kb.join(t))


@router.message(Command("help"))
async def help_cmd(message: Message, bot: Bot, t: Ru) -> None:
    await message.answer(await welcome_text(bot, t), reply_markup=kb.join(t))


# --- Language ---


@router.message(Command("language"))
async def language_cmd(message: Message, t: Ru) -> None:
    await message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())


@router.callback_query(SetLang.filter())
async def set_language(cb: CallbackQuery, callback_data: SetLang, session: AsyncSession) -> None:
    t = TEXTS.get(callback_data.code)
    if t is None:
        await cb.answer()
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    await repo.set_chat_lang(session, chat, t.LANG)
    await cb.message.edit_text(t.LANGUAGE_SET)
    await cb.answer()


# --- Participants ---


@router.message(Command("join"))
async def join_cmd(message: Message, session: AsyncSession, t: Ru) -> None:
    if await repo.ensure_member(session, message.chat.id, message.from_user):
        await message.answer(t.JOINED.format(name=name(message.from_user.full_name)))
    else:
        await message.reply(t.ALREADY_JOINED)


@router.callback_query(kb.Join.filter())
async def join_button(cb: CallbackQuery, session: AsyncSession, t: Ru) -> None:
    if await repo.ensure_member(session, cb.message.chat.id, cb.from_user):
        await cb.message.answer(t.JOINED.format(name=name(cb.from_user.full_name)))
        await cb.answer()
    else:
        await cb.answer(t.ALREADY_JOINED)


@router.message(Command("members"))
async def members_cmd(message: Message, session: AsyncSession, t: Ru) -> None:
    people = await repo.members(session, message.chat.id)
    listing = ", ".join(escape(m.name) for m in people) or "—"
    await message.answer(t.MEMBERS.format(names=listing), reply_markup=kb.join(t))


# --- Expenses ---


async def expense_text(t: Ru, session: AsyncSession, expense: Expense, currency: str) -> str:
    names = await repo.names(session, expense.chat_id)
    parts = sorted({s.amount for s in expense.shares})
    each = fmt_money(parts[0], currency)
    if len(parts) > 1:  # remainder kopecks make some shares one unit bigger
        each = f"{each} – {fmt_money(parts[-1], currency)}"
    return t.EXPENSE.format(
        payer=name(names.get(expense.payer_id, "?")),
        amount=fmt_money(expense.amount, currency),
        description=with_description(expense.description),
        count=len(expense.shares),
        names=", ".join(escape(names.get(s.user_id, "?")) for s in expense.shares),
        each=each,
    )


async def record_expense(
    message: Message, session: AsyncSession, t: Ru, payer: User, amount: int, description: str
) -> None:
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await repo.ensure_member(session, chat.id, payer)
    people = [m.user_id for m in await repo.members(session, chat.id)]
    expense = await repo.add_expense(session, chat.id, payer.id, amount, description, people)
    await message.reply(
        await expense_text(t, session, expense, chat.currency),
        reply_markup=kb.expense(t, expense.id),
    )


@router.message(Command("add"))
async def add_cmd(message: Message, command: CommandObject, session: AsyncSession, t: Ru) -> None:
    parsed = parse_amount(command.args or "")
    if parsed is None:
        await message.reply(t.ADD_USAGE)
        return
    await record_expense(message, session, t, message.from_user, *parsed)


@router.message(F.via_bot, F.text.startswith(INLINE_PREFIX))
async def inline_expense(message: Message, session: AsyncSession, bot: Bot, t: Ru) -> None:
    """An expense typed as `@bot 3000 такси` and sent to the group."""
    if message.via_bot.id != bot.id:
        return
    parsed = parse_amount(message.text.removeprefix(INLINE_PREFIX))
    if parsed:
        await record_expense(message, session, t, message.from_user, *parsed)


async def load_own_expense(cb: CallbackQuery, session: AsyncSession, t: Ru, expense_id: int):
    expense = await repo.get_expense(session, expense_id)
    if expense is None or expense.is_deleted or expense.chat_id != cb.message.chat.id:
        await cb.answer()
        return None
    if expense.payer_id != cb.from_user.id:
        await cb.answer(t.ONLY_PAYER, show_alert=True)
        return None
    return expense


@router.callback_query(kb.ExpenseAction.filter(F.action == "people"))
async def edit_people(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession, t: Ru
) -> None:
    expense = await load_own_expense(cb, session, t, callback_data.id)
    if expense is None:
        return
    await show_participants(cb, session, t, expense)
    await cb.answer()


async def show_participants(
    cb: CallbackQuery, session: AsyncSession, t: Ru, expense: Expense
) -> None:
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    people = await repo.members(session, expense.chat_id)
    await cb.message.edit_text(
        t.CHOOSE_PARTICIPANTS.format(
            amount=fmt_money(expense.amount, chat.currency),
            description=with_description(expense.description),
        ),
        reply_markup=kb.participants(t, expense.id, people, {s.user_id for s in expense.shares}),
    )


@router.callback_query(kb.Toggle.filter())
async def toggle_person(
    cb: CallbackQuery, callback_data: kb.Toggle, session: AsyncSession, t: Ru
) -> None:
    expense = await load_own_expense(cb, session, t, callback_data.expense)
    if expense is None:
        return
    selected = {s.user_id for s in expense.shares} ^ {callback_data.user}
    if not selected:
        await cb.answer(t.NEED_ONE_PARTICIPANT, show_alert=True)
        return
    await repo.set_participants(session, expense, list(selected))
    await show_participants(cb, session, t, expense)
    await cb.answer()


@router.callback_query(kb.ExpenseAction.filter(F.action == "done"))
async def people_done(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession, t: Ru
) -> None:
    expense = await load_own_expense(cb, session, t, callback_data.id)
    if expense is None:
        return
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    await cb.message.edit_text(
        await expense_text(t, session, expense, chat.currency),
        reply_markup=kb.expense(t, expense.id),
    )
    await cb.answer()


@router.callback_query(kb.ExpenseAction.filter(F.action == "delete"))
async def delete_expense(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession, t: Ru
) -> None:
    expense = await load_own_expense(cb, session, t, callback_data.id)
    if expense is None:
        return
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    await repo.delete_expense(session, expense)
    await cb.message.edit_text(
        t.EXPENSE_DELETED.format(
            amount=fmt_money(expense.amount, chat.currency),
            description=with_description(expense.description),
        )
    )
    await cb.answer()


@router.message(Command("history"))
async def history(message: Message, session: AsyncSession, t: Ru) -> None:
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    items = await repo.recent_expenses(session, chat.id)
    if not items:
        await message.answer(t.HISTORY_EMPTY)
        return
    names = await repo.names(session, chat.id)
    lines = [
        f"{e.created_at:%d.%m} · {escape(names.get(e.payer_id, '?'))} · "
        f"{fmt_money(e.amount, chat.currency)}{with_description(e.description)}"
        for e in items
    ]
    await message.answer(t.HISTORY.format(lines="\n".join(lines)))


# --- Balance ---


async def balance_view(t: Ru, session: AsyncSession, chat_id: int, title: str | None):
    chat = await repo.ensure_chat(session, chat_id, title)
    net = await repo.balances(session, chat_id)
    if not net:
        return t.BALANCE_EMPTY, None
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
    text = t.BALANCE.format(lines="\n".join(lines), transfers="\n".join(transfer_lines))
    return text + t.BALANCE_HINT, kb.settle(transfers, names, chat.currency)


@router.message(Command("balance"))
async def balance(message: Message, session: AsyncSession, t: Ru) -> None:
    text, markup = await balance_view(t, session, message.chat.id, message.chat.title)
    await message.answer(text, reply_markup=markup)


@router.callback_query(kb.Settle.filter())
async def settle(cb: CallbackQuery, callback_data: kb.Settle, session: AsyncSession, t: Ru) -> None:
    if cb.from_user.id not in (callback_data.debtor, callback_data.creditor):
        await cb.answer(t.SETTLE_NOT_YOURS, show_alert=True)
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    # Take the amount from the current balance, not from the (possibly old) button
    current = {(d, c): a for d, c, a in settle_up(await repo.balances(session, chat.id))}
    amount = current.get((callback_data.debtor, callback_data.creditor))
    if amount is None:
        await cb.answer(t.SETTLE_STALE, show_alert=True)
        return
    await repo.add_settlement(
        session, chat.id, callback_data.debtor, callback_data.creditor, amount
    )
    names = await repo.names(session, chat.id)
    await cb.message.answer(
        t.SETTLED.format(
            debtor=name(names.get(callback_data.debtor, "?")),
            creditor=name(names.get(callback_data.creditor, "?")),
            amount=fmt_money(amount, chat.currency),
        )
    )
    text, markup = await balance_view(t, session, chat.id, None)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.message(Command("currency"))
async def currency(message: Message, command: CommandObject, session: AsyncSession, t: Ru) -> None:
    value = (command.args or "").strip()
    if not value:
        await message.answer(t.CHOOSE_CURRENCY, reply_markup=kb.currencies())
        return
    if len(value) > 8:
        await message.reply(t.CURRENCY_USAGE)
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await repo.set_currency(session, chat, value)
    await message.answer(t.CURRENCY_SET.format(currency=escape(value)))


@router.callback_query(kb.SetCurrency.filter())
async def currency_button(
    cb: CallbackQuery, callback_data: kb.SetCurrency, session: AsyncSession, t: Ru
) -> None:
    if callback_data.symbol not in {symbol for symbol, _ in kb.POPULAR_CURRENCIES}:
        await cb.answer()
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    await repo.set_currency(session, chat, callback_data.symbol)
    await cb.message.edit_text(t.CURRENCY_SET.format(currency=escape(callback_data.symbol)))
    await cb.answer()
