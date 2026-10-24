"""User-facing texts, one class per language.
Other languages subclass Russian; tests check that they override every text."""

from html import escape


def user_link(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'


class Ru:
    LANG = "ru"

    # --- Buttons ---
    BTN_ADD_TO_GROUP = "➕ Добавить в группу"
    BTN_RESTORE = "↩️ Вернуть"
    BTN_ACTION_DELETE = "🗑 Только удалять"
    BTN_ACTION_MUTE = "🔇 Удалять и мутить"
    BTN_ACTION_BAN = "⛔ Удалять и банить"
    BTN_TURN_OFF = "⏸ Выключить защиту"
    BTN_TURN_ON = "▶️ Включить защиту"

    # --- Commands ---
    CMD_START = "Как начать"
    CMD_SETTINGS = "Настройки защиты"
    CMD_LANGUAGE = "Язык бота"
    CMD_HELP = "Как работает бот"

    WELCOME_PRIVATE = (
        "Привет! Я <b>ChatGuard AI</b> 🛡\n\n"
        "Я защищаю групповые чаты от спама: рекламы, «заработка», крипты и зазывания в личку.\n\n"
        "<b>Как подключить:</b>\n"
        "1. Добавьте меня в группу кнопкой ниже\n"
        "2. Дайте мне права администратора: «Удаление сообщений» и «Блокировка "
        "пользователей»\n"
        "3. Готово. Настройки в группе: /settings"
    )
    WELCOME_GROUP = (
        "🛡 <b>ChatGuard AI</b> на страже!\n\n"
        "Я проверяю первые сообщения новых участников: сначала быстрыми правилами, а в "
        "сомнительных случаях нейросетью. Спам удаляю и сообщаю админам почему, с кнопкой "
        "«↩️ Вернуть» на случай ошибки.\n\n"
        "Чтобы я мог удалять спам, сделайте меня администратором с правами «Удаление "
        "сообщений» и «Блокировка пользователей».\n\n"
        "Настройки: /settings · Язык: /language"
    )
    ONLY_GROUPS = "Я защищаю групповые чаты. Добавьте меня в группу кнопкой ниже 👇"
    LANGUAGE_SET = "Готово, в этом чате я говорю по-русски 🇷🇺"
    ONLY_ADMINS = "Это могут только администраторы чата"

    NEED_RIGHTS = (
        "⚠️ Я нашёл спам, но не могу его удалить: у меня нет прав администратора. "
        "Дайте мне права «Удаление сообщений» и «Блокировка пользователей»."
    )
    REPORT = "🛡 Удалено сообщение от {user}{punishment}\nПричина ({source}): {reason}"
    PUNISH_DELETE = ""
    PUNISH_MUTE = ", теперь он в муте"
    PUNISH_BAN = ", он заблокирован"
    SOURCE_RULES = "правила"
    SOURCE_AI = "ИИ"
    REASON_RULES = "подозрительные признаки: {signals}"
    SIGNALS = {
        "invite": "приглашение в чат",
        "link": "ссылка",
        "mention": "упоминание канала или бота",
        "money": "заработок, крипта или казино",
        "dm": "зазывание в личку",
        "forward": "пересылка из канала",
        "buttons": "кнопки-ссылки",
        "phone": "номер телефона",
        "emoji": "много эмодзи",
        "caps": "КАПС",
    }
    RESTORED = "↩️ {admin} вернул(а) {user}. Сообщение было таким:\n<blockquote>{text}</blockquote>"
    ALREADY_RESTORED = "Уже возвращено"

    SETTINGS = (
        "⚙️ <b>Настройки ChatGuard AI</b>\n\n"
        "Защита: {status}\n"
        "Что делать со спамером: {action}\n"
        "Нейросеть: {ai}\n\n"
        "Проверено сообщений: {checked}\n"
        "Поймано спама: {caught}"
    )
    STATUS_ON = "✅ включена"
    STATUS_OFF = "⏸ выключена"
    ACTION_DELETE = "только удалить сообщение"
    ACTION_MUTE = "удалить и замутить"
    ACTION_BAN = "удалить и заблокировать"
    AI_ON = "включена (Haiku, сложные случаи — Opus)"
    AI_OFF = "выключена, работают только правила"
    AI_LIMIT = "дневной лимит исчерпан, до завтра работают только правила"


class En(Ru):
    LANG = "en"

    BTN_ADD_TO_GROUP = "➕ Add to a group"
    BTN_RESTORE = "↩️ Restore"
    BTN_ACTION_DELETE = "🗑 Delete only"
    BTN_ACTION_MUTE = "🔇 Delete and mute"
    BTN_ACTION_BAN = "⛔ Delete and ban"
    BTN_TURN_OFF = "⏸ Turn protection off"
    BTN_TURN_ON = "▶️ Turn protection on"

    CMD_START = "Getting started"
    CMD_SETTINGS = "Protection settings"
    CMD_LANGUAGE = "Bot language"
    CMD_HELP = "How the bot works"

    WELCOME_PRIVATE = (
        "Hi! I'm <b>ChatGuard AI</b> 🛡\n\n"
        "I protect group chats from spam: ads, “easy money”, crypto and “write me in DM” lures.\n\n"
        "<b>How to set me up:</b>\n"
        "1. Add me to a group with the button below\n"
        "2. Make me an admin with the “Delete messages” and “Ban users” rights\n"
        "3. Done. Settings in the group: /settings"
    )
    WELCOME_GROUP = (
        "🛡 <b>ChatGuard AI</b> is on guard!\n\n"
        "I check the first messages of new members: fast rules first, and an AI model for "
        "doubtful cases. I delete spam and tell the admins why, with a “↩️ Restore” button "
        "in case I'm wrong.\n\n"
        "To delete spam I need to be an admin with the “Delete messages” and “Ban users” "
        "rights.\n\n"
        "Settings: /settings · Language: /language"
    )
    ONLY_GROUPS = "I protect group chats. Add me to a group with the button below 👇"
    LANGUAGE_SET = "Done, I speak English in this chat now 🇬🇧"
    ONLY_ADMINS = "Only chat admins can do this"

    NEED_RIGHTS = (
        "⚠️ I found spam but can't delete it: I'm not an admin here. "
        "Give me the “Delete messages” and “Ban users” rights."
    )
    REPORT = "🛡 Deleted a message from {user}{punishment}\nReason ({source}): {reason}"
    PUNISH_DELETE = ""
    PUNISH_MUTE = ", they are muted now"
    PUNISH_BAN = ", they are banned"
    SOURCE_RULES = "rules"
    SOURCE_AI = "AI"
    REASON_RULES = "suspicious signs: {signals}"
    SIGNALS = {
        "invite": "chat invite",
        "link": "link",
        "mention": "channel or bot mention",
        "money": "easy money, crypto or casino",
        "dm": "“write me in DM”",
        "forward": "forwarded from a channel",
        "buttons": "link buttons",
        "phone": "phone number",
        "emoji": "lots of emoji",
        "caps": "CAPS",
    }
    RESTORED = "↩️ {admin} restored {user}. The message was:\n<blockquote>{text}</blockquote>"
    ALREADY_RESTORED = "Already restored"

    SETTINGS = (
        "⚙️ <b>ChatGuard AI settings</b>\n\n"
        "Protection: {status}\n"
        "What to do with a spammer: {action}\n"
        "AI model: {ai}\n\n"
        "Messages checked: {checked}\n"
        "Spam caught: {caught}"
    )
    STATUS_ON = "✅ on"
    STATUS_OFF = "⏸ off"
    ACTION_DELETE = "only delete the message"
    ACTION_MUTE = "delete and mute"
    ACTION_BAN = "delete and ban"
    AI_ON = "on (Haiku, hard cases go to Opus)"
    AI_OFF = "off, only the rules work"
    AI_LIMIT = "daily limit reached, only the rules work until tomorrow"


class Uk(Ru):
    LANG = "uk"

    BTN_ADD_TO_GROUP = "➕ Додати в групу"
    BTN_RESTORE = "↩️ Повернути"
    BTN_ACTION_DELETE = "🗑 Лише видаляти"
    BTN_ACTION_MUTE = "🔇 Видаляти й мутити"
    BTN_ACTION_BAN = "⛔ Видаляти й банити"
    BTN_TURN_OFF = "⏸ Вимкнути захист"
    BTN_TURN_ON = "▶️ Увімкнути захист"

    CMD_START = "Як почати"
    CMD_SETTINGS = "Налаштування захисту"
    CMD_LANGUAGE = "Мова бота"
    CMD_HELP = "Як працює бот"

    WELCOME_PRIVATE = (
        "Привіт! Я <b>ChatGuard AI</b> 🛡\n\n"
        "Я захищаю групові чати від спаму: реклами, «заробітку», крипти та заманювання в "
        "особисті.\n\n"
        "<b>Як підключити:</b>\n"
        "1. Додайте мене в групу кнопкою нижче\n"
        "2. Дайте мені права адміністратора: «Видалення повідомлень» і «Блокування "
        "користувачів»\n"
        "3. Готово. Налаштування в групі: /settings"
    )
    WELCOME_GROUP = (
        "🛡 <b>ChatGuard AI</b> на варті!\n\n"
        "Я перевіряю перші повідомлення нових учасників: спершу швидкими правилами, а в "
        "сумнівних випадках нейромережею. Спам видаляю й пояснюю адмінам чому, з кнопкою "
        "«↩️ Повернути» на випадок помилки.\n\n"
        "Щоб я міг видаляти спам, зробіть мене адміністратором із правами «Видалення "
        "повідомлень» і «Блокування користувачів».\n\n"
        "Налаштування: /settings · Мова: /language"
    )
    ONLY_GROUPS = "Я захищаю групові чати. Додайте мене в групу кнопкою нижче 👇"
    LANGUAGE_SET = "Готово, у цьому чаті я розмовляю українською 🇺🇦"
    ONLY_ADMINS = "Це можуть лише адміністратори чату"

    NEED_RIGHTS = (
        "⚠️ Я знайшов спам, але не можу його видалити: у мене немає прав адміністратора. "
        "Дайте мені права «Видалення повідомлень» і «Блокування користувачів»."
    )
    REPORT = "🛡 Видалено повідомлення від {user}{punishment}\nПричина ({source}): {reason}"
    PUNISH_DELETE = ""
    PUNISH_MUTE = ", тепер він у муті"
    PUNISH_BAN = ", його заблоковано"
    SOURCE_RULES = "правила"
    SOURCE_AI = "ШІ"
    REASON_RULES = "підозрілі ознаки: {signals}"
    SIGNALS = {
        "invite": "запрошення в чат",
        "link": "посилання",
        "mention": "згадка каналу чи бота",
        "money": "заробіток, крипта чи казино",
        "dm": "заманювання в особисті",
        "forward": "пересилання з каналу",
        "buttons": "кнопки-посилання",
        "phone": "номер телефону",
        "emoji": "багато емодзі",
        "caps": "КАПС",
    }
    RESTORED = (
        "↩️ {admin} повернув(ла) {user}. Повідомлення було таким:\n<blockquote>{text}</blockquote>"
    )
    ALREADY_RESTORED = "Уже повернуто"

    SETTINGS = (
        "⚙️ <b>Налаштування ChatGuard AI</b>\n\n"
        "Захист: {status}\n"
        "Що робити зі спамером: {action}\n"
        "Нейромережа: {ai}\n\n"
        "Перевірено повідомлень: {checked}\n"
        "Спіймано спаму: {caught}"
    )
    STATUS_ON = "✅ увімкнено"
    STATUS_OFF = "⏸ вимкнено"
    ACTION_DELETE = "лише видалити повідомлення"
    ACTION_MUTE = "видалити й замутити"
    ACTION_BAN = "видалити й заблокувати"
    AI_ON = "увімкнена (Haiku, складні випадки — Opus)"
    AI_OFF = "вимкнена, працюють лише правила"
    AI_LIMIT = "денний ліміт вичерпано, до завтра працюють лише правила"


class Pl(Ru):
    LANG = "pl"

    BTN_ADD_TO_GROUP = "➕ Dodaj do grupy"
    BTN_RESTORE = "↩️ Przywróć"
    BTN_ACTION_DELETE = "🗑 Tylko usuwaj"
    BTN_ACTION_MUTE = "🔇 Usuwaj i wyciszaj"
    BTN_ACTION_BAN = "⛔ Usuwaj i banuj"
    BTN_TURN_OFF = "⏸ Wyłącz ochronę"
    BTN_TURN_ON = "▶️ Włącz ochronę"

    CMD_START = "Jak zacząć"
    CMD_SETTINGS = "Ustawienia ochrony"
    CMD_LANGUAGE = "Język bota"
    CMD_HELP = "Jak działa bot"

    WELCOME_PRIVATE = (
        "Cześć! Jestem <b>ChatGuard AI</b> 🛡\n\n"
        "Chronię czaty grupowe przed spamem: reklamami, „łatwym zarobkiem”, kryptowalutami "
        "i zaproszeniami na priv.\n\n"
        "<b>Jak mnie podłączyć:</b>\n"
        "1. Dodaj mnie do grupy przyciskiem poniżej\n"
        "2. Nadaj mi uprawnienia administratora: „Usuwanie wiadomości” i „Blokowanie "
        "użytkowników”\n"
        "3. Gotowe. Ustawienia w grupie: /settings"
    )
    WELCOME_GROUP = (
        "🛡 <b>ChatGuard AI</b> na straży!\n\n"
        "Sprawdzam pierwsze wiadomości nowych osób: najpierw szybkimi regułami, a w "
        "wątpliwych przypadkach modelem AI. Spam usuwam i wyjaśniam adminom dlaczego, z "
        "przyciskiem „↩️ Przywróć” na wypadek pomyłki.\n\n"
        "Aby usuwać spam, potrzebuję uprawnień administratora: „Usuwanie wiadomości” i "
        "„Blokowanie użytkowników”.\n\n"
        "Ustawienia: /settings · Język: /language"
    )
    ONLY_GROUPS = "Chronię czaty grupowe. Dodaj mnie do grupy przyciskiem poniżej 👇"
    LANGUAGE_SET = "Gotowe, w tym czacie mówię po polsku 🇵🇱"
    ONLY_ADMINS = "Mogą to zrobić tylko administratorzy czatu"

    NEED_RIGHTS = (
        "⚠️ Znalazłem spam, ale nie mogę go usunąć: nie jestem tu administratorem. "
        "Nadaj mi uprawnienia „Usuwanie wiadomości” i „Blokowanie użytkowników”."
    )
    REPORT = "🛡 Usunięto wiadomość od {user}{punishment}\nPowód ({source}): {reason}"
    PUNISH_DELETE = ""
    PUNISH_MUTE = ", jest teraz wyciszony"
    PUNISH_BAN = ", został zbanowany"
    SOURCE_RULES = "reguły"
    SOURCE_AI = "AI"
    REASON_RULES = "podejrzane oznaki: {signals}"
    SIGNALS = {
        "invite": "zaproszenie do czatu",
        "link": "link",
        "mention": "wzmianka o kanale lub bocie",
        "money": "zarobek, krypto lub kasyno",
        "dm": "zaproszenie na priv",
        "forward": "przekazane z kanału",
        "buttons": "przyciski z linkami",
        "phone": "numer telefonu",
        "emoji": "dużo emoji",
        "caps": "CAPS LOCK",
    }
    RESTORED = (
        "↩️ {admin} przywrócił(a) {user}. Wiadomość brzmiała:\n<blockquote>{text}</blockquote>"
    )
    ALREADY_RESTORED = "Już przywrócono"

    SETTINGS = (
        "⚙️ <b>Ustawienia ChatGuard AI</b>\n\n"
        "Ochrona: {status}\n"
        "Co zrobić ze spamerem: {action}\n"
        "Model AI: {ai}\n\n"
        "Sprawdzone wiadomości: {checked}\n"
        "Złapany spam: {caught}"
    )
    STATUS_ON = "✅ włączona"
    STATUS_OFF = "⏸ wyłączona"
    ACTION_DELETE = "tylko usuń wiadomość"
    ACTION_MUTE = "usuń i wycisz"
    ACTION_BAN = "usuń i zbanuj"
    AI_ON = "włączony (Haiku, trudne przypadki — Opus)"
    AI_OFF = "wyłączony, działają tylko reguły"
    AI_LIMIT = "dzienny limit wyczerpany, do jutra działają tylko reguły"


TEXTS: dict[str, Ru] = {"uk": Uk(), "ru": Ru(), "pl": Pl(), "en": En()}
