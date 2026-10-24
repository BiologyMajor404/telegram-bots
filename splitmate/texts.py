"""User-facing texts, one class per language.
Other languages subclass Russian; tests check that they override every text."""

from html import escape


def name(n: str) -> str:
    return f"<b>{escape(n)}</b>"


def with_description(description: str) -> str:
    return f" — {escape(description)}" if description else ""


class Ru:
    LANG = "ru"
    DEFAULT_CURRENCY = "₴"

    # --- Buttons ---
    BTN_JOIN = "🙋 Я участвую"
    BTN_PEOPLE = "👥 Кто участвует"
    BTN_DELETE = "🗑 Удалить"
    BTN_DONE = "Готово"
    BTN_ADD_TO_GROUP = "➕ Добавить в группу"

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
        "Укажите валюту: <code>/currency ₴</code>, <code>/currency $</code>, "
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
        "<code>/currency ₴</code>"
    )
    CURRENCY_SET = "Chat currency: {currency}"

    INLINE_TITLE = "💸 Record an expense: {amount}"
    INLINE_DESCRIPTION = "{description}Send it to a group the bot is in"
    INLINE_HELP_BUTTON = "How to record an expense?"
    INLINE_PRIVATE = "I record these messages only in groups I'm a member of"


class Uk(Ru):
    LANG = "uk"
    DEFAULT_CURRENCY = "₴"

    BTN_JOIN = "🙋 Я з вами"
    BTN_PEOPLE = "👥 Хто бере участь"
    BTN_DELETE = "🗑 Видалити"
    BTN_DONE = "Готово"
    BTN_ADD_TO_GROUP = "➕ Додати в групу"

    CMD_ADD = "Записати витрату: /add 300 таксі"
    CMD_BALANCE = "Хто кому винен"
    CMD_HISTORY = "Останні витрати"
    CMD_JOIN = "Брати участь у витратах"
    CMD_MEMBERS = "Учасники"
    CMD_CURRENCY = "Валюта чату"
    CMD_LANGUAGE = "Мова бота"
    CMD_HELP = "Як користуватися"
    CMD_START = "Як почати"

    WELCOME_PRIVATE = (
        "Привіт! Я <b>SplitMates</b> 💸\n\n"
        "Я рахую, хто кому винен у подорожах, між сусідами по квартирі та за спільні "
        "покупки.\n\n"
        "<b>Як почати:</b>\n"
        "1. Додайте мене в груповий чат кнопкою нижче\n"
        "2. Кожен учасник натискає «🙋 Я з вами»\n"
        "3. Записуйте витрати: <code>/add 300 таксі</code>\n"
        "4. <code>/balance</code> покаже, хто кому скільки переказати, за мінімум переказів"
    )
    WELCOME_GROUP = (
        "Привіт, я <b>SplitMates</b> 💸 Порахую, хто кому винен.\n\n"
        "1. Кожен, хто бере участь у витратах, натисніть «🙋 Я з вами»\n"
        "2. Записуйте витрати: <code>/add 300 таксі</code>\n"
        "   або швидше, просто в полі введення: <code>@{bot} 300 таксі</code>\n"
        "3. <code>/balance</code> покаже, хто кому скільки переказати\n\n"
        "Ще: /history останні витрати, /currency валюта, /language мова, /help підказка"
    )
    ONLY_GROUPS = "Я працюю в групових чатах. Додайте мене в групу кнопкою нижче 👇"
    LANGUAGE_SET = "Готово, у цьому чаті я розмовляю українською 🇺🇦"

    JOINED = "🙋 {name} бере участь у витратах"
    ALREADY_JOINED = "Ви вже берете участь 👍"
    MEMBERS = "👥 Учасники: {names}"

    ADD_USAGE = "Напишіть суму і за що: <code>/add 300 таксі</code>"
    EXPENSE = (
        "💸 <b>{payer}</b> заплатив(ла) <b>{amount}</b>{description}\n"
        "Ділимо на {count}: {names}\n"
        "Кожному: {each}"
    )
    EXPENSE_DELETED = "🗑 Витрату {amount}{description} видалено"
    CHOOSE_PARTICIPANTS = "Хто бере участь у витраті {amount}{description}?"
    NEED_ONE_PARTICIPANT = "Потрібен хоча б один учасник"
    ONLY_PAYER = "Змінювати витрату може лише той, хто її записав"

    BALANCE_EMPTY = "✅ Усі в розрахунку, ніхто нікому не винен"
    BALANCE = "📊 <b>Баланс</b>\n\n{lines}\n\n💸 <b>Щоб розрахуватися:</b>\n{transfers}"
    BALANCE_HINT = "\n\nКоли борг повернули, натисніть кнопку з цим переказом."
    SETTLED = "✅ {debtor} повернув(ла) {creditor} {amount}"
    SETTLE_STALE = "Баланс уже змінився, відкрийте /balance знову"
    SETTLE_NOT_YOURS = "Позначити переказ може лише той, хто платить, або той, хто отримує"

    HISTORY_EMPTY = "Витрат поки немає. Додайте першу: <code>/add 300 таксі</code>"
    HISTORY = "🧾 <b>Останні витрати</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Вкажіть валюту: <code>/currency ₴</code>, <code>/currency $</code>, "
        "<code>/currency €</code>"
    )
    CURRENCY_SET = "Валюта чату: {currency}"

    INLINE_TITLE = "💸 Записати витрату: {amount}"
    INLINE_DESCRIPTION = "{description}Надішліть у групу, де є бот"
    INLINE_HELP_BUTTON = "Як записати витрату?"
    INLINE_PRIVATE = "Такі повідомлення я записую лише в групах, де я є"


class Pl(Ru):
    LANG = "pl"
    DEFAULT_CURRENCY = "zł"

    BTN_JOIN = "🙋 Wchodzę"
    BTN_PEOPLE = "👥 Kto się dorzuca"
    BTN_DELETE = "🗑 Usuń"
    BTN_DONE = "Gotowe"
    BTN_ADD_TO_GROUP = "➕ Dodaj do grupy"

    CMD_ADD = "Dodaj wydatek: /add 50 taxi"
    CMD_BALANCE = "Kto komu wisi"
    CMD_HISTORY = "Ostatnie wydatki"
    CMD_JOIN = "Dołącz do rozliczeń"
    CMD_MEMBERS = "Uczestnicy"
    CMD_CURRENCY = "Waluta czatu"
    CMD_LANGUAGE = "Język bota"
    CMD_HELP = "Jak używać"
    CMD_START = "Jak zacząć"

    WELCOME_PRIVATE = (
        "Cześć! Jestem <b>SplitMates</b> 💸\n\n"
        "Liczę, kto komu ile oddać: na wyjazdach, między współlokatorami i przy wspólnych "
        "zakupach.\n\n"
        "<b>Jak zacząć:</b>\n"
        "1. Dodaj mnie do czatu grupowego przyciskiem poniżej\n"
        "2. Każdy uczestnik naciska „🙋 Wchodzę”\n"
        "3. Zapisujcie wydatki: <code>/add 50 taxi</code>\n"
        "4. <code>/balance</code> pokaże, kto komu ile przelać, przy jak najmniejszej "
        "liczbie przelewów"
    )
    WELCOME_GROUP = (
        "Cześć, jestem <b>SplitMates</b> 💸 Policzę, kto komu ile winien.\n\n"
        "1. Każdy, kto dzieli wydatki, niech naciśnie „🙋 Wchodzę”\n"
        "2. Zapisujcie wydatki: <code>/add 50 taxi</code>\n"
        "   albo szybciej, prosto w polu wiadomości: <code>@{bot} 50 taxi</code>\n"
        "3. <code>/balance</code> pokaże, kto komu ile przelać\n\n"
        "Poza tym: /history ostatnie wydatki, /currency waluta, /language język, /help pomoc"
    )
    ONLY_GROUPS = "Działam w czatach grupowych. Dodaj mnie do grupy przyciskiem poniżej 👇"
    LANGUAGE_SET = "Gotowe, w tym czacie mówię po polsku 🇵🇱"

    JOINED = "🙋 {name} dzieli wydatki"
    ALREADY_JOINED = "Już jesteś w rozliczeniach 👍"
    MEMBERS = "👥 Uczestnicy: {names}"

    ADD_USAGE = "Podaj kwotę i za co: <code>/add 50 taxi</code>"
    EXPENSE = (
        "💸 <b>{payer}</b> zapłacił(a) <b>{amount}</b>{description}\n"
        "Dzielimy na {count}: {names}\n"
        "Na osobę: {each}"
    )
    EXPENSE_DELETED = "🗑 Wydatek {amount}{description} usunięty"
    CHOOSE_PARTICIPANTS = "Kto dzieli wydatek {amount}{description}?"
    NEED_ONE_PARTICIPANT = "Potrzebny jest co najmniej jeden uczestnik"
    ONLY_PAYER = "Wydatek może zmienić tylko osoba, która go dodała"

    BALANCE_EMPTY = "✅ Wszyscy są rozliczeni, nikt nikomu nic nie wisi"
    BALANCE = "📊 <b>Bilans</b>\n\n{lines}\n\n💸 <b>Aby się rozliczyć:</b>\n{transfers}"
    BALANCE_HINT = "\n\nGdy dług zostanie oddany, naciśnij przycisk z tym przelewem."
    SETTLED = "✅ {debtor} oddał(a) {creditor} {amount}"
    SETTLE_STALE = "Bilans się zmienił, otwórz /balance ponownie"
    SETTLE_NOT_YOURS = "Przelew może oznaczyć tylko osoba, która płaci, albo ta, która dostaje"

    HISTORY_EMPTY = "Nie ma jeszcze wydatków. Dodaj pierwszy: <code>/add 50 taxi</code>"
    HISTORY = "🧾 <b>Ostatnie wydatki</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Podaj walutę: <code>/currency zł</code>, <code>/currency €</code>, "
        "<code>/currency $</code>"
    )
    CURRENCY_SET = "Waluta czatu: {currency}"

    INLINE_TITLE = "💸 Dodaj wydatek: {amount}"
    INLINE_DESCRIPTION = "{description}Wyślij do grupy, w której jest bot"
    INLINE_HELP_BUTTON = "Jak dodać wydatek?"
    INLINE_PRIVATE = "Takie wiadomości zapisuję tylko w grupach, w których jestem"


TEXTS: dict[str, Ru] = {"uk": Uk(), "ru": Ru(), "pl": Pl(), "en": En()}
