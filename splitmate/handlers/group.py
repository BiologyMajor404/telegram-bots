"""Group chats: participants, expenses, custom shares, balance and settling up."""

import re
import time
from contextlib import suppress
from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ChatMemberUpdated, ForceReply, Message, User
from sqlalchemy.ext.asyncio import AsyncSession

from shared.admins import is_admin, sender_is_admin
from shared.formatting import user_link
from shared.i18n import CHOOSE_LANGUAGE, GROUP_CHATS, SetLang, lang_keyboard
from splitmate import keyboards as kb
from splitmate import repo
from splitmate.models import Expense
from splitmate.money import ShareError, fmt_money, parse_amount, settle_up
from splitmate.texts import TEXTS, Ru, name, with_description

INLINE_PREFIX = "💸 "  # messages sent through the bot's inline mode start with this
# Up to 8 (the chats.currency column) letters, digits or currency signs, no markup
CURRENCY_RE = re.compile(r"[^\s<>&\"']{1,8}")

router = Router(name="group")
router.message.filter(F.chat.type.in_(GROUP_CHATS))
router.callback_query.filter(F.message.chat.type.in_(GROUP_CHATS))
router.my_chat_member.filter(F.chat.type.in_(GROUP_CHATS))


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
async def start_cmd(message: Message, command: CommandObject, bot: Bot, t: Ru) -> None:
    # Telegram hands a bare /start in a group to whichever bot spoke last, so it may be
    # meant for another bot: answer only /start@this_bot (joining is greeted separately)
    if command.mention is None or just_welcomed(message.chat.id):
        return
    await message.answer(await welcome_text(bot, t), reply_markup=kb.join(t))


@router.message(Command("help"))
async def help_cmd(message: Message, bot: Bot, t: Ru) -> None:
    await message.answer(await welcome_text(bot, t), reply_markup=kb.join(t))


# --- Language ---


@router.message(Command("language"))
async def language_cmd(message: Message, bot: Bot, t: Ru) -> None:
    if not await sender_is_admin(bot, message):
        await message.reply(t.ONLY_ADMINS)
        return
    await message.answer(CHOOSE_LANGUAGE, reply_markup=lang_keyboard())


@router.callback_query(SetLang.filter())
async def set_language(
    cb: CallbackQuery, callback_data: SetLang, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    if not await is_admin(bot, cb.message.chat.id, cb.from_user.id):
        await cb.answer(t.ONLY_ADMINS, show_alert=True)
        return
    t = TEXTS.get(callback_data.code)
    if t is None:
        await cb.answer()
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    await repo.set_chat_lang(session, chat, t.LANG)
    await cb.message.edit_text(t.LANGUAGE_SET)
    await cb.answer()


# --- Participants ---


async def from_a_person(message: Message, t: Ru) -> bool:
    """Anonymous admins and channels post as a chat, all behind one placeholder account,
    which can't pay or owe anything: they're asked to write as themselves."""
    if message.sender_chat is None:
        return True
    await message.reply(t.POST_AS_YOURSELF)
    return False


@router.message(Command("join"))
async def join_cmd(message: Message, session: AsyncSession, t: Ru) -> None:
    if not await from_a_person(message, t):
        return
    if await repo.ensure_member(session, message.chat.id, message.from_user, rejoin=True):
        await message.answer(t.JOINED.format(name=name(message.from_user.full_name)))
    else:
        await message.reply(t.ALREADY_JOINED)


@router.callback_query(kb.Join.filter())
async def join_button(cb: CallbackQuery, session: AsyncSession, t: Ru) -> None:
    if await repo.ensure_member(session, cb.message.chat.id, cb.from_user, rejoin=True):
        await cb.message.answer(t.JOINED.format(name=name(cb.from_user.full_name)))
        await cb.answer()
    else:
        await cb.answer(t.ALREADY_JOINED)


@router.message(Command("leave"))
async def leave_cmd(message: Message, session: AsyncSession, t: Ru) -> None:
    """New expenses stop including the person; what they paid and owe so far stays."""
    if not await from_a_person(message, t):
        return
    if await repo.leave(session, message.chat.id, message.from_user.id):
        await message.answer(t.LEFT.format(name=name(message.from_user.full_name)))
    else:
        await message.reply(t.NOT_JOINED)


@router.message(F.left_chat_member)
async def member_left(message: Message, session: AsyncSession, bot: Bot) -> None:
    """Leaving the group (or being removed from it) works like /leave."""
    if message.left_chat_member.id != bot.id:
        await repo.leave(session, message.chat.id, message.left_chat_member.id)


@router.message(Command("members"))
async def members_cmd(message: Message, session: AsyncSession, t: Ru) -> None:
    people = [m for m in await repo.members(session, message.chat.id) if m.active]
    listing = ", ".join(escape(m.name) for m in people) or "—"
    await message.answer(t.MEMBERS.format(names=listing), reply_markup=kb.join(t))


@router.message(F.migrate_to_chat_id | F.migrate_from_chat_id)
async def group_upgraded(message: Message, session: AsyncSession) -> None:
    """A group upgraded to a supergroup gets a new id, and its expenses move there.
    Telegram reports the upgrade in both chats; the first report moves everything."""
    if message.migrate_to_chat_id:
        await repo.move_chat(session, message.chat.id, message.migrate_to_chat_id)
    else:
        await repo.move_chat(session, message.migrate_from_chat_id, message.chat.id)


# --- Expenses ---


async def expense_text(t: Ru, session: AsyncSession, expense: Expense, currency: str) -> str:
    names = await repo.names(session, expense.chat_id)
    if any(s.fixed for s in expense.shares):
        return t.EXPENSE_CUSTOM.format(
            payer=name(names.get(expense.payer_id, "?")),
            amount=fmt_money(expense.amount, currency),
            description=with_description(expense.description),
            shares=", ".join(
                f"{escape(names.get(s.user_id, '?'))} {fmt_money(s.amount, currency)}"
                for s in expense.shares
            ),
        )
    parts = sorted({s.amount for s in expense.shares})
    each = fmt_money(parts[0], currency)
    if len(parts) > 1:  # remainder kopecks make some shares one unit bigger
        each = f"{each} – {fmt_money(parts[-1], currency)}"
    text = t.EXPENSE.format(
        payer=name(names.get(expense.payer_id, "?")),
        amount=fmt_money(expense.amount, currency),
        description=with_description(expense.description),
        count=len(expense.shares),
        names=", ".join(escape(names.get(s.user_id, "?")) for s in expense.shares),
        each=each,
    )
    # The bot can't list group members, so people have to add themselves
    return text + t.EXPENSE_ALONE_HINT if len(expense.shares) == 1 else text


async def record_expense(
    message: Message, session: AsyncSession, t: Ru, payer: User, amount: int, description: str
) -> None:
    if not await from_a_person(message, t):
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await repo.ensure_member(session, chat.id, payer)
    # Everyone taking part, and the payer even after /leave: it's their own expense
    people = {m.user_id for m in await repo.members(session, chat.id) if m.active} | {payer.id}
    expense = await repo.add_expense(session, chat.id, payer.id, amount, description, list(people))
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
    # A forwarded copy may still say "via @bot", but the expense was recorded the first time
    if message.via_bot.id != bot.id or message.forward_origin is not None:
        return
    parsed = parse_amount(message.text.removeprefix(INLINE_PREFIX))
    if parsed:
        await record_expense(message, session, t, message.from_user, *parsed)


async def is_chat_member(session: AsyncSession, expense: Expense, user_id: int) -> bool:
    """User ids in callback data come from the client: accept only real participants."""
    return user_id in {m.user_id for m in await repo.members(session, expense.chat_id)}


async def load_editable_expense(
    cb: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    t: Ru,
    expense_id: int,
    *,
    lock: bool = False,
) -> Expense | None:
    """The expense under the pressed button, if the presser may change it: whoever paid, or
    a chat admin (someone has to be able to remove a joke expense). Otherwise the button is
    answered and None returned. `lock` is for changing the expense, see repo.get_expense."""
    expense = await repo.get_expense(session, expense_id, lock=lock)
    if expense is None or expense.is_deleted or expense.chat_id != cb.message.chat.id:
        await cb.answer()
        return None
    if expense.payer_id != cb.from_user.id and not await is_admin(
        bot, expense.chat_id, cb.from_user.id
    ):
        await cb.answer(t.ONLY_PAYER, show_alert=True)
        return None
    return expense


@router.callback_query(kb.ExpenseAction.filter(F.action == "people"))
async def edit_people(
    cb: CallbackQuery, callback_data: kb.ExpenseAction, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    expense = await load_editable_expense(cb, session, bot, t, callback_data.id)
    if expense is None:
        return
    await show_participants(cb, session, t, expense)
    await cb.answer()


async def show_participants(
    cb: CallbackQuery, session: AsyncSession, t: Ru, expense: Expense
) -> None:
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    selected = {s.user_id for s in expense.shares}
    # Those who left are listed only while they're in this expense, so they can be unticked
    people = [
        m for m in await repo.members(session, expense.chat_id) if m.active or m.user_id in selected
    ]
    await cb.message.edit_text(
        t.CHOOSE_PARTICIPANTS.format(
            amount=fmt_money(expense.amount, chat.currency),
            description=with_description(expense.description),
        )
        + t.PARTICIPANTS_HINT,
        reply_markup=kb.participants(t, expense.id, people, selected),
    )


@router.callback_query(kb.Toggle.filter())
async def toggle_person(
    cb: CallbackQuery, callback_data: kb.Toggle, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    expense = await load_editable_expense(cb, session, bot, t, callback_data.expense, lock=True)
    if expense is None:
        return
    if not await is_chat_member(session, expense, callback_data.user):
        await cb.answer()
        return
    selected = {s.user_id for s in expense.shares} ^ {callback_data.user}
    if not selected:
        await cb.answer(t.NEED_ONE_PARTICIPANT, show_alert=True)
        return
    try:
        await repo.set_participants(session, expense, list(selected))
    except ShareError as e:
        await cb.answer(await share_error_text(t, session, expense, e), show_alert=True)
        return
    await show_participants(cb, session, t, expense)
    await cb.answer()


@router.callback_query(kb.ExpenseAction.filter(F.action == "done"))
async def people_done(
    cb: CallbackQuery,
    callback_data: kb.ExpenseAction,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    t: Ru,
) -> None:
    expense = await load_editable_expense(cb, session, bot, t, callback_data.id)
    if expense is None:
        return
    await forget_share_question(state, bot, cb.message.chat.id, expense.id)
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    await cb.message.edit_text(
        await expense_text(t, session, expense, chat.currency),
        reply_markup=kb.expense(t, expense.id),
    )
    await cb.answer()


@router.callback_query(kb.MeToo.filter())
async def me_too(cb: CallbackQuery, callback_data: kb.MeToo, session: AsyncSession, t: Ru) -> None:
    """Anyone who took part adds themselves to the expense (and to the chat's participants)."""
    # Before locking the expense: this commits, and a commit releases the lock
    await repo.ensure_member(session, cb.message.chat.id, cb.from_user)
    expense = await repo.get_expense(session, callback_data.expense, lock=True)
    if expense is None or expense.is_deleted or expense.chat_id != cb.message.chat.id:
        await cb.answer()
        return
    if cb.from_user.id in {s.user_id for s in expense.shares}:
        await cb.answer(t.ALREADY_IN_EXPENSE)
        return
    try:
        await repo.set_participants(
            session, expense, [s.user_id for s in expense.shares] + [cb.from_user.id]
        )
    except ShareError as e:
        await cb.answer(await share_error_text(t, session, expense, e), show_alert=True)
        return
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    await cb.message.edit_text(
        await expense_text(t, session, expense, chat.currency),
        reply_markup=kb.expense(t, expense.id),
    )
    await cb.answer()


# --- Custom amounts ("who pays what") ---


class EnterShare(StatesGroup):
    amount = State()


async def share_error_text(t: Ru, session: AsyncSession, expense: Expense, e: ShareError) -> str:
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    template = t.SHARE_EXCEEDS if e.reason == "exceeds" else t.SHARE_MISMATCH
    return template.format(
        total=fmt_money(e.total, chat.currency), amount=fmt_money(expense.amount, chat.currency)
    )


async def amounts_view(t: Ru, session: AsyncSession, expense: Expense):
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    names = await repo.names(session, expense.chat_id)
    rows = [(s.user_id, names.get(s.user_id, "?"), s.amount, s.fixed) for s in expense.shares]
    lines = "\n".join(
        f"{'📌 ' if fixed else ''}{escape(person)}: {fmt_money(share, chat.currency)}"
        for _, person, share, fixed in rows
    )
    text = t.AMOUNTS_EDITOR.format(
        amount=fmt_money(expense.amount, chat.currency),
        description=with_description(expense.description),
        shares=lines,
    )
    return text, kb.amounts(t, expense.id, rows, chat.currency)


async def tidy_up(bot: Bot, chat_id: int, message_ids: list[int]) -> None:
    """Delete a question about an amount and the attempts to answer it. Others' messages
    need "delete messages" rights, so failing is fine."""
    for message_id in message_ids:
        with suppress(TelegramBadRequest, TelegramForbiddenError):
            await bot.delete_message(chat_id, message_id)


async def forget_share_question(
    state: FSMContext, bot: Bot, chat_id: int, expense_id: int | None = None
) -> None:
    """Drop the unanswered "how much for X?" together with its messages; with `expense_id`,
    only if the question is about that expense."""
    data = await state.get_data()
    if not data or (expense_id is not None and data.get("expense") != expense_id):
        return
    await state.clear()
    await tidy_up(bot, chat_id, [*data.get("prompts", []), *data.get("cleanup", [])])


@router.callback_query(kb.ExpenseAction.filter(F.action.in_({"amounts", "equal"})))
async def edit_amounts(
    cb: CallbackQuery,
    callback_data: kb.ExpenseAction,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    t: Ru,
) -> None:
    equal = callback_data.action == "equal"
    expense = await load_editable_expense(cb, session, bot, t, callback_data.id, lock=equal)
    if expense is None:
        return
    if equal:
        await repo.split_evenly(session, expense)
    await forget_share_question(state, bot, cb.message.chat.id, expense.id)
    text, markup = await amounts_view(t, session, expense)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.callback_query(kb.PickShare.filter())
async def pick_share(
    cb: CallbackQuery,
    callback_data: kb.PickShare,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    t: Ru,
) -> None:
    expense = await load_editable_expense(cb, session, bot, t, callback_data.expense)
    if expense is None:
        return
    if callback_data.user not in {s.user_id for s in expense.shares}:
        await cb.answer()
        return
    # One question at a time: an earlier one (maybe about someone else) goes away
    await forget_share_question(state, bot, cb.message.chat.id)
    chat = await repo.ensure_chat(session, expense.chat_id, None)
    names = await repo.names(session, expense.chat_id)
    # In groups the bot only sees replies to its own messages (privacy mode), hence ForceReply
    prompt = await cb.message.answer(
        f"{user_link(cb.from_user.id, cb.from_user.first_name)}, "
        + t.ASK_SHARE.format(
            amount=fmt_money(expense.amount, chat.currency),
            person=name(names.get(callback_data.user, "?")),
        ),
        reply_markup=ForceReply(selective=True),
    )
    await state.set_state(EnterShare.amount)
    await state.set_data(
        {
            "expense": expense.id,
            "user": callback_data.user,
            "editor": cb.message.message_id,
            # The question, then a hint after each wrong answer: a reply to any of them counts
            "prompts": [prompt.message_id],
        }
    )
    await cb.answer()


async def ask_again(message: Message, state: FSMContext, text: str) -> None:
    """Explain the problem and keep the reply field open: the next message must again be
    a reply to the bot, otherwise privacy mode hides it from the bot."""
    hint = await message.reply(text, reply_markup=ForceReply(selective=True))
    data = await state.get_data()
    await state.update_data(
        prompts=[*data.get("prompts", []), hint.message_id],
        cleanup=[*data.get("cleanup", []), message.message_id],
    )


@router.callback_query(kb.ExpenseAction.filter(F.action == "delete"))
async def delete_expense(
    cb: CallbackQuery,
    callback_data: kb.ExpenseAction,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    t: Ru,
) -> None:
    expense = await load_editable_expense(cb, session, bot, t, callback_data.id, lock=True)
    if expense is None:
        return
    await repo.delete_expense(session, expense)
    await forget_share_question(state, bot, cb.message.chat.id, expense.id)
    chat = await repo.ensure_chat(session, expense.chat_id, None)
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
    if cb.from_user.id != callback_data.creditor:
        await cb.answer(t.SETTLE_NOT_YOURS, show_alert=True)
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    debtor, creditor, amount = callback_data.debtor, callback_data.creditor, callback_data.amount
    # Exactly the transfer on the button: after a new expense its amount no longer matches
    if not await repo.record_settlement(session, chat.id, debtor, creditor, amount):
        await cb.answer(t.SETTLE_STALE, show_alert=True)
        return
    names = await repo.names(session, chat.id)
    await cb.message.answer(
        t.SETTLED.format(
            debtor=name(names.get(debtor, "?")),
            creditor=name(names.get(creditor, "?")),
            amount=fmt_money(amount, chat.currency),
        )
    )
    text, markup = await balance_view(t, session, chat.id, None)
    await cb.message.edit_text(text, reply_markup=markup)
    await cb.answer()


@router.callback_query(F.data.startswith(f"{kb.Settle.__prefix__}:"))
async def old_settle_button(cb: CallbackQuery, t: Ru) -> None:
    """A /balance button from before buttons carried the amount."""
    await cb.answer(t.SETTLE_STALE, show_alert=True)


@router.message(Command("currency"))
async def currency(
    message: Message, command: CommandObject, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    if not await sender_is_admin(bot, message):
        await message.reply(t.ONLY_ADMINS)
        return
    value = (command.args or "").strip()
    if not value:
        await message.answer(t.CHOOSE_CURRENCY, reply_markup=kb.currencies())
        return
    # The currency goes into every HTML message: letters and symbols only, no markup
    if not CURRENCY_RE.fullmatch(value):
        await message.reply(t.CURRENCY_USAGE)
        return
    chat = await repo.ensure_chat(session, message.chat.id, message.chat.title)
    await repo.set_currency(session, chat, value)
    await message.answer(t.CURRENCY_SET.format(currency=escape(value)))


@router.callback_query(kb.SetCurrency.filter())
async def currency_button(
    cb: CallbackQuery, callback_data: kb.SetCurrency, session: AsyncSession, bot: Bot, t: Ru
) -> None:
    if not await is_admin(bot, cb.message.chat.id, cb.from_user.id):
        await cb.answer(t.ONLY_ADMINS, show_alert=True)
        return
    if callback_data.symbol not in {symbol for symbol, _ in kb.POPULAR_CURRENCIES}:
        await cb.answer()
        return
    chat = await repo.ensure_chat(session, cb.message.chat.id, cb.message.chat.title)
    await repo.set_currency(session, chat, callback_data.symbol)
    await cb.message.edit_text(t.CURRENCY_SET.format(currency=escape(callback_data.symbol)))
    await cb.answer()


# --- Answers to "how much for X?" ---
# Registered last, after every command: a pending question must not swallow /balance


@router.message(EnterShare.amount, F.text, ~F.text.startswith("/"), F.reply_to_message)
async def share_entered(
    message: Message, session: AsyncSession, state: FSMContext, bot: Bot, t: Ru
) -> None:
    data = await state.get_data()
    # Only a reply to the current question: the payer may have tapped someone else since
    if message.reply_to_message.message_id not in data.get("prompts", []):
        return
    expense = await repo.get_expense(session, data["expense"], lock=True)
    if (
        expense is None
        or expense.is_deleted
        or data["user"] not in {s.user_id for s in expense.shares}
        or (expense.payer_id != message.from_user.id and not await sender_is_admin(bot, message))
    ):
        await forget_share_question(state, bot, message.chat.id)
        return
    parsed = parse_amount(message.text)
    if parsed is None:
        await ask_again(message, state, t.BAD_SHARE)
        return
    try:
        await repo.set_share(session, expense, data["user"], parsed[0])
    except ShareError as e:
        await ask_again(message, state, await share_error_text(t, session, expense, e))
        return
    await state.clear()
    # The question, wrong attempts and the answer aren't needed any more
    await tidy_up(
        bot, message.chat.id, [*data["prompts"], *data.get("cleanup", []), message.message_id]
    )
    text, markup = await amounts_view(t, session, expense)
    # The same amount again leaves the text as it was, and Telegram refuses such an edit
    with suppress(TelegramBadRequest):
        await bot.edit_message_text(
            text, chat_id=message.chat.id, message_id=data["editor"], reply_markup=markup
        )
