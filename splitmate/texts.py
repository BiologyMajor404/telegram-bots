"""User-facing texts, one class per language.
Other languages subclass Russian; tests check that they override every text."""

from html import escape


def name(n: str) -> str:
    return f"<b>{escape(n)}</b>"


def with_description(description: str) -> str:
    return f" — {escape(description)}" if description else ""


class Ru:
    LANG = "ru"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "💸 Считаю, кто кому должен в групповом чате: поездки, соседи, общие покупки"
    )
    BOT_DESCRIPTION = (
        "💸 SplitMates — общие расходы прямо в групповом чате.\n\n• записывайте "
        "траты: /add 3000 такси\n• делите поровну или задайте, кто сколько платит\n• "
        "/balance покажет, кто кому сколько перевести, за минимум переводов\n• "
        "гривна, злотый, доллар, евро и другие валюты\n\nДобавьте меня в группу, и "
        "начнём 👇"
    )
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
    BTN_ME_TOO = "🙋 Я тоже участвую"
    ALREADY_IN_EXPENSE = "Вы уже участвуете в этом расходе"
    EXPENSE_ALONE_HINT = (
        "\n\n<i>Пока делим только на одного. Кто тоже участвовал, нажмите «🙋 Я тоже участвую»</i>"
    )
    PARTICIPANTS_HINT = (
        "\n\n<i>Нет нужного человека? Бот видит только тех, кто нажал "
        "«🙋 Я тоже участвую» или «🙋 Я участвую»</i>"
    )
    ONLY_PAYER = "Менять расход может только тот, кто его записал"

    BALANCE_EMPTY = "✅ Все в расчёте, никто никому не должен"
    BALANCE = "📊 <b>Баланс</b>\n\n{lines}\n\n💸 <b>Чтобы рассчитаться:</b>\n{transfers}"
    BALANCE_HINT = "\n\nКогда деньги получены, получатель нажимает кнопку с этим переводом."
    SETTLED = "✅ {debtor} вернул(а) {creditor} {amount}"
    SETTLE_STALE = "Баланс уже изменился, откройте /balance заново"
    SETTLE_NOT_YOURS = "Отметить, что долг вернули, может только тот, кто получает деньги"
    ONLY_ADMINS = "Это могут только администраторы чата"

    HISTORY_EMPTY = "Расходов пока нет. Добавьте первый: <code>/add 3000 такси</code>"
    HISTORY = "🧾 <b>Последние расходы</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Укажите валюту: <code>/currency ₴</code>, <code>/currency $</code>, "
        "<code>/currency €</code>"
    )
    CURRENCY_SET = "Валюта чата: {currency}"
    CHOOSE_CURRENCY = "Выберите валюту чата или задайте свою: <code>/currency CHF</code>"

    INLINE_TITLE = "💸 Записать расход: {amount}"
    INLINE_DESCRIPTION = "{description}Отправьте в группу, где есть бот"
    INLINE_HELP_BUTTON = "Как записать расход?"
    INLINE_PRIVATE = "Такие сообщения я записываю только в группах, где я состою"
    BTN_AMOUNTS = "✏️ Кто сколько"
    BTN_EQUAL = "↩️ Поровну"
    EXPENSE_CUSTOM = "💸 <b>{payer}</b> заплатил(а) <b>{amount}</b>{description}\nДоли: {shares}"
    AMOUNTS_EDITOR = (
        "✏️ <b>Кто сколько</b> в расходе {amount}{description}\n\n{shares}\n\n"
        "Нажмите на человека и отправьте его сумму. Остальные делят остаток поровну. "
        "📌 — сумма задана вручную."
    )
    ASK_SHARE = (
        "Сколько из {amount} приходится на {person}? Ответьте на это сообщение "
        "суммой, например <code>150</code>"
    )
    BAD_SHARE = "Не понял сумму. Ответьте числом, например <code>150</code>"
    SHARE_EXCEEDS = "Заданные доли ({total}) больше суммы расхода ({amount}). Укажите меньше."
    SHARE_MISMATCH = (
        "Суммы заданы у всех, но вместе дают {total} вместо {amount}. Поправьте одну "
        "из них или нажмите «↩️ Поровну»."
    )


class En(Ru):
    LANG = "en"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "💸 I track who owes whom in your group chat: trips, flatmates, shared purchases"
    )
    BOT_DESCRIPTION = (
        "💸 SplitMates — shared expenses right in your group chat.\n\n• record "
        "expenses: /add 30 taxi\n• split equally or set who pays what\n• /balance "
        "shows who should pay whom, with the fewest transfers\n• dollar, euro, "
        "hryvnia, zloty and other currencies\n\nAdd me to a group to get started 👇"
    )
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
    BTN_ME_TOO = "🙋 Count me in"
    ALREADY_IN_EXPENSE = "You're already in this expense"
    EXPENSE_ALONE_HINT = (
        "\n\n<i>Split with one person so far. Anyone else who took part, press “🙋 Count me in”</i>"
    )
    PARTICIPANTS_HINT = (
        "\n\n<i>Someone missing? The bot only sees people who "
        "pressed “🙋 Count me in” or “🙋 I'm in”</i>"
    )
    ONLY_PAYER = "Only the person who recorded the expense can change it"

    BALANCE_EMPTY = "✅ All square, nobody owes anything"
    BALANCE = "📊 <b>Balance</b>\n\n{lines}\n\n💸 <b>To settle up:</b>\n{transfers}"
    BALANCE_HINT = "\n\nOnce the money arrives, the receiver presses the button with that transfer."
    SETTLED = "✅ {debtor} paid back {creditor} {amount}"
    SETTLE_STALE = "The balance has changed, open /balance again"
    SETTLE_NOT_YOURS = "Only the person receiving the money can confirm the debt was paid back"
    ONLY_ADMINS = "Only chat admins can do this"

    HISTORY_EMPTY = "No expenses yet. Add the first one: <code>/add 30 taxi</code>"
    HISTORY = "🧾 <b>Recent expenses</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Specify the currency: <code>/currency $</code>, <code>/currency €</code>, "
        "<code>/currency ₴</code>"
    )
    CURRENCY_SET = "Chat currency: {currency}"
    CHOOSE_CURRENCY = "Choose the chat currency or set your own: <code>/currency CHF</code>"

    INLINE_TITLE = "💸 Record an expense: {amount}"
    INLINE_DESCRIPTION = "{description}Send it to a group the bot is in"
    INLINE_HELP_BUTTON = "How to record an expense?"
    INLINE_PRIVATE = "I record these messages only in groups I'm a member of"
    BTN_AMOUNTS = "✏️ Who pays what"
    BTN_EQUAL = "↩️ Split equally"
    EXPENSE_CUSTOM = "💸 <b>{payer}</b> paid <b>{amount}</b>{description}\nShares: {shares}"
    AMOUNTS_EDITOR = (
        "✏️ <b>Who pays what</b> in {amount}{description}\n\n{shares}\n\nTap a "
        "person and send their amount. Everyone else splits the rest equally. 📌 "
        "means set by hand."
    )
    ASK_SHARE = (
        "How much of {amount} is on {person}? Reply to this message with the amount, "
        "e.g. <code>15</code>"
    )
    BAD_SHARE = "Couldn't read the amount. Reply with a number, e.g. <code>15</code>"
    SHARE_EXCEEDS = "The set shares ({total}) are more than the expense ({amount}). Enter less."
    SHARE_MISMATCH = (
        "Everyone has an amount set, but together they make {total} instead of "
        "{amount}. Fix one of them or press “↩️ Split equally”."
    )


class Uk(Ru):
    LANG = "uk"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "💸 Рахую, хто кому винен у груповому чаті: подорожі, сусіди, спільні покупки"
    )
    BOT_DESCRIPTION = (
        "💸 SplitMates — спільні витрати просто в груповому чаті.\n\n• записуйте "
        "витрати: /add 300 таксі\n• діліть порівну або вкажіть, хто скільки платить\n"
        "• /balance покаже, хто кому скільки переказати, за мінімум переказів\n• "
        "гривня, злотий, долар, євро та інші валюти\n\nДодайте мене в групу, і "
        "почнемо 👇"
    )
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
    BTN_ME_TOO = "🙋 Я теж беру участь"
    ALREADY_IN_EXPENSE = "Ви вже берете участь у цій витраті"
    EXPENSE_ALONE_HINT = (
        "\n\n<i>Поки ділимо лише на одного. Хто теж брав "
        "участь, натисніть «🙋 Я теж беру участь»</i>"
    )
    PARTICIPANTS_HINT = (
        "\n\n<i>Немає потрібної людини? Бот бачить лише тих, хто "
        "натиснув «🙋 Я теж беру участь» або «🙋 Я з вами»</i>"
    )
    ONLY_PAYER = "Змінювати витрату може лише той, хто її записав"

    BALANCE_EMPTY = "✅ Усі в розрахунку, ніхто нікому не винен"
    BALANCE = "📊 <b>Баланс</b>\n\n{lines}\n\n💸 <b>Щоб розрахуватися:</b>\n{transfers}"
    BALANCE_HINT = "\n\nКоли гроші отримано, отримувач натискає кнопку з цим переказом."
    SETTLED = "✅ {debtor} повернув(ла) {creditor} {amount}"
    SETTLE_STALE = "Баланс уже змінився, відкрийте /balance знову"
    SETTLE_NOT_YOURS = "Позначити, що борг повернули, може лише той, хто отримує гроші"
    ONLY_ADMINS = "Це можуть лише адміністратори чату"

    HISTORY_EMPTY = "Витрат поки немає. Додайте першу: <code>/add 300 таксі</code>"
    HISTORY = "🧾 <b>Останні витрати</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Вкажіть валюту: <code>/currency ₴</code>, <code>/currency $</code>, "
        "<code>/currency €</code>"
    )
    CURRENCY_SET = "Валюта чату: {currency}"
    CHOOSE_CURRENCY = "Оберіть валюту чату або вкажіть свою: <code>/currency CHF</code>"

    INLINE_TITLE = "💸 Записати витрату: {amount}"
    INLINE_DESCRIPTION = "{description}Надішліть у групу, де є бот"
    INLINE_HELP_BUTTON = "Як записати витрату?"
    INLINE_PRIVATE = "Такі повідомлення я записую лише в групах, де я є"
    BTN_AMOUNTS = "✏️ Хто скільки"
    BTN_EQUAL = "↩️ Порівну"
    EXPENSE_CUSTOM = "💸 <b>{payer}</b> заплатив(ла) <b>{amount}</b>{description}\nЧастки: {shares}"
    AMOUNTS_EDITOR = (
        "✏️ <b>Хто скільки</b> у витраті {amount}{description}\n\n{shares}\n\n"
        "Натисніть на людину й надішліть її суму. Решта ділять залишок порівну. 📌 — "
        "суму задано вручну."
    )
    ASK_SHARE = (
        "Скільки з {amount} припадає на {person}? Дайте відповідь на це повідомлення "
        "сумою, наприклад <code>150</code>"
    )
    BAD_SHARE = "Не зрозумів суму. Відповідайте числом, наприклад <code>150</code>"
    SHARE_EXCEEDS = "Задані частки ({total}) більші за суму витрати ({amount}). Вкажіть менше."
    SHARE_MISMATCH = (
        "Суми задано всім, але разом вони дають {total} замість {amount}. Виправте "
        "одну з них або натисніть «↩️ Порівну»."
    )


class Pl(Ru):
    LANG = "pl"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "💸 Liczę, kto komu ile winien w czacie grupowym: wyjazdy, współlokatorzy, zakupy"
    )
    BOT_DESCRIPTION = (
        "💸 SplitMates — wspólne wydatki prosto w czacie grupowym.\n\n• zapisuj "
        "wydatki: /add 50 taxi\n• dziel po równo albo ustal, kto ile płaci\n• "
        "/balance pokaże, kto komu ile przelać, przy jak najmniejszej liczbie "
        "przelewów\n• złoty, hrywna, dolar, euro i inne waluty\n\nDodaj mnie do "
        "grupy i zaczynamy 👇"
    )
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
    BTN_ME_TOO = "🙋 Ja też się dorzucam"
    ALREADY_IN_EXPENSE = "Już jesteś w tym wydatku"
    EXPENSE_ALONE_HINT = (
        "\n\n<i>Na razie dzielimy na jedną osobę. Kto też brał udział, "
        "niech naciśnie „🙋 Ja też się dorzucam”</i>"
    )
    PARTICIPANTS_HINT = (
        "\n\n<i>Brakuje kogoś? Bot widzi tylko osoby, które nacisnęły "
        "„🙋 Ja też się dorzucam” lub „🙋 Wchodzę”</i>"
    )
    ONLY_PAYER = "Wydatek może zmienić tylko osoba, która go dodała"

    BALANCE_EMPTY = "✅ Wszyscy są rozliczeni, nikt nikomu nic nie wisi"
    BALANCE = "📊 <b>Bilans</b>\n\n{lines}\n\n💸 <b>Aby się rozliczyć:</b>\n{transfers}"
    BALANCE_HINT = "\n\nGdy pieniądze dotrą, odbiorca naciska przycisk z tym przelewem."
    SETTLED = "✅ {debtor} oddał(a) {creditor} {amount}"
    SETTLE_STALE = "Bilans się zmienił, otwórz /balance ponownie"
    SETTLE_NOT_YOURS = "Potwierdzić zwrot długu może tylko osoba, która dostaje pieniądze"
    ONLY_ADMINS = "Mogą to zrobić tylko administratorzy czatu"

    HISTORY_EMPTY = "Nie ma jeszcze wydatków. Dodaj pierwszy: <code>/add 50 taxi</code>"
    HISTORY = "🧾 <b>Ostatnie wydatki</b>\n\n{lines}"

    CURRENCY_USAGE = (
        "Podaj walutę: <code>/currency zł</code>, <code>/currency €</code>, "
        "<code>/currency $</code>"
    )
    CURRENCY_SET = "Waluta czatu: {currency}"
    CHOOSE_CURRENCY = "Wybierz walutę czatu albo podaj własną: <code>/currency CHF</code>"

    INLINE_TITLE = "💸 Dodaj wydatek: {amount}"
    INLINE_DESCRIPTION = "{description}Wyślij do grupy, w której jest bot"
    INLINE_HELP_BUTTON = "Jak dodać wydatek?"
    INLINE_PRIVATE = "Takie wiadomości zapisuję tylko w grupach, w których jestem"
    BTN_AMOUNTS = "✏️ Kto ile"
    BTN_EQUAL = "↩️ Po równo"
    EXPENSE_CUSTOM = "💸 <b>{payer}</b> zapłacił(a) <b>{amount}</b>{description}\nUdziały: {shares}"
    AMOUNTS_EDITOR = (
        "✏️ <b>Kto ile</b> w wydatku {amount}{description}\n\n{shares}\n\nNaciśnij "
        "osobę i wyślij jej kwotę. Pozostali dzielą resztę po równo. 📌 — kwota "
        "ustawiona ręcznie."
    )
    ASK_SHARE = (
        "Ile z {amount} przypada na {person}? Odpowiedz na tę wiadomość kwotą, np. <code>50</code>"
    )
    BAD_SHARE = "Nie rozumiem kwoty. Odpowiedz liczbą, np. <code>50</code>"
    SHARE_EXCEEDS = "Ustawione udziały ({total}) są większe niż wydatek ({amount}). Podaj mniej."
    SHARE_MISMATCH = (
        "Wszyscy mają ustawioną kwotę, ale razem dają {total} zamiast {amount}. "
        "Popraw jedną z nich albo naciśnij „↩️ Po równo”."
    )


TEXTS: dict[str, Ru] = {"uk": Uk(), "ru": Ru(), "pl": Pl(), "en": En()}
