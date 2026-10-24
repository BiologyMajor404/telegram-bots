"""User-facing texts, one class per language.
English subclasses Russian; tests check that it overrides every text."""

from html import escape


def name(n: str) -> str:
    return f"<b>{escape(n)}</b>"


def with_description(description: str) -> str:
    return f" — {escape(description)}" if description else ""


class Ru:
    LANG = "ru"
    DEFAULT_CURRENCY = "₽"

    # --- Buttons ---
    BTN_JOIN = "🙋 Я участвую"
    BTN_PEOPLE = "👥 Кто участвует"
    BTN_DELETE = "🗑 Удалить"
    BTN_DONE = "Готово"
    BTN_ADD_TO_GROUP = "➕ Добавить в группу"
    BTN_LANGUAGE = "🌐 Language / Язык"

    # --- Commands ---
    CMD_ADD = "Записать расход: /add 3000 такси"
    CMD_BALANCE = "Кто кому должен"
    CMD_HISTORY = "Последние расходы"
    CMD_JOIN = "Участвовать в расходах"
    CMD_MEMBERS = "Участники"
    CMD_CURRENCY = "Валюта чата"
    CMD_LANGUAGE = "Язык бота"
    CMD_HELP = "Как пользоваться"
    CMD_START = "Как начать"

    WELCOME_PRIVATE = (
        "Привет! Я <b>SplitMates</b> 💸\n\n"
        "Я считаю, кто кому должен в поездках, у соседей по квартире и при общих покупках.\n\n"
        "<b>Как начать:</b>\n"
        "1. Добавьте меня в групповой чат кнопкой ниже\n"
        "2. Каждый участник нажимает «🙋 Я участвую»\n"
        "3. Записывайте расходы: <code>/add 3000 такси</code>\n"
        "4. <code>/balance</code> покажет, кто кому сколько перевести, за минимум переводов"
    )
    WELCOME_GROUP = (
        "Привет, я <b>SplitMates</b> 💸 Посчитаю, кто кому должен.\n\n"
        "1. Каждый, кто участвует в расходах, нажмите «🙋 Я участвую»\n"
        "2. Записывайте траты: <code>/add 3000 такси</code>\n"
        "   или быстрее, прямо в поле ввода: <code>@{bot} 3000 такси</code>\n"
        "3. <code>/balance</code> покажет, кто кому сколько перевести\n\n"
        "Ещё: /history последние траты, /currency валюта, /language язык, /help подсказка"
    )
    ONLY_GROUPS = "Я работаю в групповых чатах. Добавьте меня в группу кнопкой ниже 👇"
    CHOOSE_LANGUAGE = "Выберите язык бота в этом чате / Choose the bot language for this chat:"
    LANGUAGE_SET = "Готово, в этом чате я говорю по-русски 🇷🇺"

    JOINED = "🙋 {name} участвует в расходах"
    ALREADY_JOINED = "Вы уже участвуете 👍"
    MEMBERS = "👥 Участники: {names}"

    ADD_USAGE = "Напишите сумму и за что: <code>/add 3000 такси</code>"
    EXPENSE = (
        "💸 <b>{payer}</b> заплатил(а) <b>{amount}</b>{description}\n"
        "Делим на {count}: {names}\n"
        "Каждому: {each}"
    )
    EXPENSE_DELETED = "🗑 Расход {amount}{description} удалён"
    CHOOSE_PARTICIPANTS = "Кто участвует в расходе {amount}{description}?"
    NEED_ONE_PARTICIPANT = "Нужен хотя бы один участник"
    ONLY_PAYER = "Менять расход может только тот, кто его записал"

    BALANCE_EMPTY = "✅ Все в расчёте, никто никому не должен"
    BALANCE = "📊 <b>Баланс</b>\n\n{lines}\n\n💸 <b>Чтобы рассчитаться:</b>\n{transfers}"
    BALANCE_HINT = "\n\nКогда долг вернули, нажмите кнопку с этим переводом."
    SETTLED = "✅ {debtor} вернул(а) {creditor} {amount}"
    SETTLE_STALE = "Баланс уже изменился, откройте /balance заново"
    SETTLE_NOT_YOURS = "Отметить перевод может только тот, кто платит, или тот, кто получает"

    HISTORY_EMPTY = "Расходов пока нет. Добавьте первый: <code>/add 3000 такси</code>"
    HISTORY = "🧾 <b>Последние расходы</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Укажите валюту: <code>/currency ₽</code>, <code>/currency $</code>, "
        "<code>/currency €</code>"
    )
    CURRENCY_SET = "Валюта чата: {currency}"

    INLINE_TITLE = "💸 Записать расход: {amount}"
    INLINE_DESCRIPTION = "{description}Отправьте в группу, где есть бот"
    INLINE_HELP_BUTTON = "Как записать расход?"
    INLINE_PRIVATE = "Такие сообщения я записываю только в группах, где я состою"


class En(Ru):
    LANG = "en"
    DEFAULT_CURRENCY = "$"

    BTN_JOIN = "🙋 I'm in"
    BTN_PEOPLE = "👥 Who took part"
    BTN_DELETE = "🗑 Delete"
    BTN_DONE = "Done"
    BTN_ADD_TO_GROUP = "➕ Add to a group"

    CMD_ADD = "Add an expense: /add 30 taxi"
    CMD_BALANCE = "Who owes whom"
    CMD_HISTORY = "Recent expenses"
    CMD_JOIN = "Take part in expenses"
    CMD_MEMBERS = "Participants"
    CMD_CURRENCY = "Chat currency"
    CMD_LANGUAGE = "Bot language"
    CMD_HELP = "How to use"
    CMD_START = "Getting started"

    WELCOME_PRIVATE = (
        "Hi! I'm <b>SplitMates</b> 💸\n\n"
        "I keep track of who owes whom on trips, between flatmates and for shared purchases.\n\n"
        "<b>Getting started:</b>\n"
        "1. Add me to a group chat with the button below\n"
        "2. Everyone taking part presses “🙋 I'm in”\n"
        "3. Record expenses: <code>/add 30 taxi</code>\n"
        "4. <code>/balance</code> shows who should pay whom, with the fewest transfers"
    )
    WELCOME_GROUP = (
        "Hi, I'm <b>SplitMates</b> 💸 I'll work out who owes whom.\n\n"
        "1. Everyone who shares the expenses, press “🙋 I'm in”\n"
        "2. Record expenses: <code>/add 30 taxi</code>\n"
        "   or faster, right in the input field: <code>@{bot} 30 taxi</code>\n"
        "3. <code>/balance</code> shows who should pay whom\n\n"
        "Also: /history recent expenses, /currency currency, /language language, /help help"
    )
    ONLY_GROUPS = "I work in group chats. Add me to a group with the button below 👇"
    CHOOSE_LANGUAGE = "Choose the bot language for this chat / Выберите язык бота в этом чате:"
    LANGUAGE_SET = "Done, I speak English in this chat now 🇬🇧"

    JOINED = "🙋 {name} is in"
    ALREADY_JOINED = "You're already in 👍"
    MEMBERS = "👥 Participants: {names}"

    ADD_USAGE = "Send the amount and what it was for: <code>/add 30 taxi</code>"
    EXPENSE = (
        "💸 <b>{payer}</b> paid <b>{amount}</b>{description}\n"
        "Split between {count}: {names}\n"
        "Each: {each}"
    )
    EXPENSE_DELETED = "🗑 Expense {amount}{description} deleted"
    CHOOSE_PARTICIPANTS = "Who took part in the expense {amount}{description}?"
    NEED_ONE_PARTICIPANT = "At least one participant is needed"
    ONLY_PAYER = "Only the person who recorded the expense can change it"

    BALANCE_EMPTY = "✅ All square, nobody owes anything"
    BALANCE = "📊 <b>Balance</b>\n\n{lines}\n\n💸 <b>To settle up:</b>\n{transfers}"
    BALANCE_HINT = "\n\nOnce a debt is paid back, press the button with that transfer."
    SETTLED = "✅ {debtor} paid back {creditor} {amount}"
    SETTLE_STALE = "The balance has changed, open /balance again"
    SETTLE_NOT_YOURS = "Only the person paying or the person receiving can mark this transfer"

    HISTORY_EMPTY = "No expenses yet. Add the first one: <code>/add 30 taxi</code>"
    HISTORY = "🧾 <b>Recent expenses</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Specify the currency: <code>/currency $</code>, <code>/currency €</code>, "
        "<code>/currency ₽</code>"
    )
    CURRENCY_SET = "Chat currency: {currency}"

    INLINE_TITLE = "💸 Record an expense: {amount}"
    INLINE_DESCRIPTION = "{description}Send it to a group the bot is in"
    INLINE_HELP_BUTTON = "How to record an expense?"
    INLINE_PRIVATE = "I record these messages only in groups I'm a member of"


TEXTS: dict[str, Ru] = {"ru": Ru(), "en": En()}
