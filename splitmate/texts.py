"""User-facing texts. Kept in one place to make translation easy."""

from html import escape

WELCOME_PRIVATE = (
    "Привет! Я <b>SplitMate</b> 💸\n\n"
    "Я считаю, кто кому должен в поездках, у соседей по квартире и при общих покупках.\n\n"
    "<b>Как начать:</b>\n"
    "1. Добавьте меня в групповой чат кнопкой ниже\n"
    "2. Каждый участник нажимает «🙋 Я участвую»\n"
    "3. Записывайте расходы: <code>/add 3000 такси</code>\n"
    "4. <code>/balance</code> покажет, кто кому сколько перевести, за минимум переводов"
)
WELCOME_GROUP = (
    "Привет, я <b>SplitMate</b> 💸 Посчитаю, кто кому должен.\n\n"
    "1. Каждый, кто участвует в расходах, нажмите «🙋 Я участвую»\n"
    "2. Записывайте траты: <code>/add 3000 такси</code>\n"
    "   или быстрее, прямо в поле ввода: <code>@{bot} 3000 такси</code>\n"
    "3. <code>/balance</code> покажет, кто кому сколько перевести\n\n"
    "Ещё: /history последние траты, /currency валюта, /help подсказка"
)
HELP = WELCOME_GROUP
ONLY_GROUPS = "Я работаю в групповых чатах. Добавьте меня в группу кнопкой ниже 👇"

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
    "Укажите валюту: <code>/currency ₽</code>, <code>/currency $</code>, <code>/currency €</code>"
)
CURRENCY_SET = "Валюта чата: {currency}"

INLINE_TITLE = "💸 Записать расход: {amount}"
INLINE_DESCRIPTION = "{description}Отправьте в группу, где есть бот"
INLINE_HELP_BUTTON = "Как записать расход?"
INLINE_PRIVATE = "Такие сообщения я записываю только в группах, где я состою"


def name(n: str) -> str:
    return f"<b>{escape(n)}</b>"


def with_description(description: str) -> str:
    return f" — {escape(description)}" if description else ""
