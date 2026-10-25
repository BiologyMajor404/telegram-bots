"""User-facing texts, one class per language.
Other languages subclass Russian; tests check that they override every text."""

from typing import ClassVar


class Ru:
    LANG = "ru"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = "🛡 Защищаю групповые чаты от спама: быстрые правила и нейросеть Claude"
    BOT_DESCRIPTION = (
        "🛡 ChatGuard AI — антиспам для групповых чатов.\n\n• проверяю первые "
        "сообщения новых участников\n• явный спам ловлю правилами, сомнительное "
        "проверяет нейросеть\n• спам удаляю, спамера мучу или баню\n• админам "
        "объясняю причину и даю кнопку «Вернуть» на случай ошибки\n\nБесплатно: до "
        "50 проверок нейросетью в день. Pro: больше и умнее.\n\nДобавьте меня в "
        "группу администратором 👇"
    )

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
    SIGNALS: ClassVar[dict[str, str]] = {
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
        "known": "замечен в спаме в других чатах",
    }
    RESTORED = "↩️ {admin} вернул(а) {user}. Сообщение было таким:\n<blockquote>{text}</blockquote>"
    ALREADY_RESTORED = "Уже возвращено"

    SETTINGS = (
        "⚙️ <b>Настройки ChatGuard AI</b>\n\n"
        "Тариф: {plan}\n"
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
    AI_ON_FREE = "включена (Haiku)"
    AI_ON_PRO = "включена (Haiku, сложные случаи — Opus)"
    AI_OFF = "выключена, работают только правила"
    AI_LIMIT = "дневной лимит исчерпан, до завтра работают только правила"
    BTN_PRO = "⭐ Pro"
    BTN_PAY_PRO = "⭐ Оформить Pro: {price} ⭐ в месяц"
    CMD_PRO = "Подписка Pro"
    CMD_PAYSUPPORT = "Вопросы по оплате"
    PLAN_FREE = "бесплатный"
    PLAN_PRO = "⭐ Pro до {until}"
    PRO_OFFER = (
        "⭐ <b>ChatGuard AI Pro</b>\n\n• сложные случаи перепроверяет Opus, самая "
        "умная модель\n• до {pro_limit} проверок нейросетью в день вместо "
        "{free_limit}\n• общая база спамеров: кого поймали в других чатах, "
        "проверяется строже\n\n{price} ⭐ в месяц, продлевается автоматически. "
        "Отменить можно в любой момент: Настройки Telegram → Мои звёзды → подписки."
    )
    PRO_ACTIVE = "⭐ Pro уже включён до {until}."
    PRO_INVOICE_TITLE = "ChatGuard AI Pro"
    PRO_INVOICE_DESCRIPTION = (
        "Pro для «{chat}» на месяц: Opus для сложных случаев, {limit} проверок в "
        "день, общая база спамеров."
    )
    PRO_THANKS = "Спасибо! ⭐ Pro для «{chat}» активен до {until}."
    PRO_ACTIVATED = (
        "⭐ {user} включил(а) ChatGuard AI Pro до {until}. Сложные случаи теперь "
        "перепроверяет Opus."
    )
    PRO_RENEWED = "⭐ Подписка Pro продлена до {until}."
    PRO_CHECK_FAILED = "Не получилось проверить оплату. Откройте /pro в чате и попробуйте снова."
    PAYSUPPORT = (
        "Вопросы по оплате ChatGuard AI Pro. Подписку можно отменить в любой момент: "
        "Настройки Telegram → Мои звёзды → подписки. Pro работает до конца "
        "оплаченного месяца."
    )
    PAYSUPPORT_CONTACT = "\nСвязаться с разработчиком: {contact}"


class En(Ru):
    LANG = "en"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = "🛡 I protect group chats from spam: fast rules plus the Claude AI model"
    BOT_DESCRIPTION = (
        "🛡 ChatGuard AI — anti-spam for group chats.\n\n• I check the first messages "
        "of new members\n• obvious spam is caught by rules, doubtful cases go to the "
        "AI\n• spam is deleted, the spammer muted or banned\n• admins get the reason "
        "and a “Restore” button in case I'm wrong\n\nFree: up to 50 AI checks a day. "
        "Pro: more and smarter.\n\nAdd me to a group as an admin 👇"
    )

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
    SIGNALS: ClassVar[dict[str, str]] = {
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
        "known": "caught spamming in other chats",
    }
    RESTORED = "↩️ {admin} restored {user}. The message was:\n<blockquote>{text}</blockquote>"
    ALREADY_RESTORED = "Already restored"

    SETTINGS = (
        "⚙️ <b>ChatGuard AI settings</b>\n\n"
        "Plan: {plan}\n"
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
    AI_ON_FREE = "on (Haiku)"
    AI_ON_PRO = "on (Haiku, hard cases go to Opus)"
    AI_OFF = "off, only the rules work"
    AI_LIMIT = "daily limit reached, only the rules work until tomorrow"
    BTN_PRO = "⭐ Pro"
    BTN_PAY_PRO = "⭐ Get Pro: {price} ⭐ a month"
    CMD_PRO = "Pro subscription"
    CMD_PAYSUPPORT = "Payment questions"
    PLAN_FREE = "free"
    PLAN_PRO = "⭐ Pro until {until}"
    PRO_OFFER = (
        "⭐ <b>ChatGuard AI Pro</b>\n\n• hard cases get a second look from Opus, the "
        "smartest model\n• up to {pro_limit} AI checks a day instead of "
        "{free_limit}\n• shared spammer list: people caught in other chats are "
        "checked harder\n\n{price} ⭐ a month, renews automatically. Cancel any time: "
        "Telegram Settings → My Stars → subscriptions."
    )
    PRO_ACTIVE = "⭐ Pro is already on until {until}."
    PRO_INVOICE_TITLE = "ChatGuard AI Pro"
    PRO_INVOICE_DESCRIPTION = (
        "Pro for “{chat}” for a month: Opus for hard cases, {limit} checks a day, "
        "shared spammer list."
    )
    PRO_THANKS = "Thank you! ⭐ Pro for “{chat}” is active until {until}."
    PRO_ACTIVATED = (
        "⭐ {user} turned on ChatGuard AI Pro until {until}. Opus now double-checks hard cases."
    )
    PRO_RENEWED = "⭐ Pro subscription renewed until {until}."
    PRO_CHECK_FAILED = "Couldn't verify the payment. Open /pro in the chat and try again."
    PAYSUPPORT = (
        "Payment questions for ChatGuard AI Pro. You can cancel the subscription any "
        "time: Telegram Settings → My Stars → subscriptions. Pro keeps working until "
        "the end of the paid month."
    )
    PAYSUPPORT_CONTACT = "\nContact the developer: {contact}"


class Uk(Ru):
    LANG = "uk"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = "🛡 Захищаю групові чати від спаму: швидкі правила та нейромережа Claude"
    BOT_DESCRIPTION = (
        "🛡 ChatGuard AI — антиспам для групових чатів.\n\n• перевіряю перші "
        "повідомлення нових учасників\n• явний спам ловлю правилами, сумнівне "
        "перевіряє нейромережа\n• спам видаляю, спамера мучу або баню\n• адмінам "
        "пояснюю причину й даю кнопку «Повернути» на випадок помилки\n\nБезкоштовно: "
        "до 50 перевірок нейромережею на день. Pro: більше й розумніше.\n\nДодайте "
        "мене в групу адміністратором 👇"
    )

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
    SIGNALS: ClassVar[dict[str, str]] = {
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
        "known": "помічений у спамі в інших чатах",
    }
    RESTORED = (
        "↩️ {admin} повернув(ла) {user}. Повідомлення було таким:\n<blockquote>{text}</blockquote>"
    )
    ALREADY_RESTORED = "Уже повернуто"

    SETTINGS = (
        "⚙️ <b>Налаштування ChatGuard AI</b>\n\n"
        "Тариф: {plan}\n"
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
    AI_ON_FREE = "увімкнена (Haiku)"
    AI_ON_PRO = "увімкнена (Haiku, складні випадки — Opus)"
    AI_OFF = "вимкнена, працюють лише правила"
    AI_LIMIT = "денний ліміт вичерпано, до завтра працюють лише правила"
    BTN_PRO = "⭐ Pro"
    BTN_PAY_PRO = "⭐ Оформити Pro: {price} ⭐ на місяць"
    CMD_PRO = "Підписка Pro"
    CMD_PAYSUPPORT = "Питання щодо оплати"
    PLAN_FREE = "безкоштовний"
    PLAN_PRO = "⭐ Pro до {until}"
    PRO_OFFER = (
        "⭐ <b>ChatGuard AI Pro</b>\n\n• складні випадки перевіряє ще й Opus, "
        "найрозумніша модель\n• до {pro_limit} перевірок нейромережею на день "
        "замість {free_limit}\n• спільна база спамерів: кого спіймали в інших чатах, "
        "перевіряється суворіше\n\n{price} ⭐ на місяць, продовжується автоматично. "
        "Скасувати можна будь-коли: Налаштування Telegram → Мої зірки → підписки."
    )
    PRO_ACTIVE = "⭐ Pro вже увімкнено до {until}."
    PRO_INVOICE_TITLE = "ChatGuard AI Pro"
    PRO_INVOICE_DESCRIPTION = (
        "Pro для «{chat}» на місяць: Opus для складних випадків, {limit} перевірок "
        "на день, спільна база спамерів."
    )
    PRO_THANKS = "Дякуємо! ⭐ Pro для «{chat}» активний до {until}."
    PRO_ACTIVATED = (
        "⭐ {user} увімкнув(ла) ChatGuard AI Pro до {until}. Складні випадки тепер перевіряє Opus."
    )
    PRO_RENEWED = "⭐ Підписку Pro продовжено до {until}."
    PRO_CHECK_FAILED = "Не вдалося перевірити оплату. Відкрийте /pro у чаті й спробуйте ще раз."
    PAYSUPPORT = (
        "Питання щодо оплати ChatGuard AI Pro. Підписку можна скасувати будь-коли: "
        "Налаштування Telegram → Мої зірки → підписки. Pro працює до кінця "
        "оплаченого місяця."
    )
    PAYSUPPORT_CONTACT = "\nЗв'язатися з розробником: {contact}"


class Pl(Ru):
    LANG = "pl"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = "🛡 Chronię czaty grupowe przed spamem: szybkie reguły i model AI Claude"
    BOT_DESCRIPTION = (
        "🛡 ChatGuard AI — antyspam dla czatów grupowych.\n\n• sprawdzam pierwsze "
        "wiadomości nowych osób\n• oczywisty spam łapią reguły, wątpliwe przypadki "
        "sprawdza AI\n• spam usuwam, spamera wyciszam lub banuję\n• adminom "
        "wyjaśniam powód i daję przycisk „Przywróć” na wypadek pomyłki\n\nZa darmo: "
        "do 50 sprawdzeń przez AI dziennie. Pro: więcej i mądrzej.\n\nDodaj mnie do "
        "grupy jako administratora 👇"
    )

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
    SIGNALS: ClassVar[dict[str, str]] = {
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
        "known": "przyłapany na spamie w innych czatach",
    }
    RESTORED = (
        "↩️ {admin} przywrócił(a) {user}. Wiadomość brzmiała:\n<blockquote>{text}</blockquote>"
    )
    ALREADY_RESTORED = "Już przywrócono"

    SETTINGS = (
        "⚙️ <b>Ustawienia ChatGuard AI</b>\n\n"
        "Plan: {plan}\n"
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
    AI_ON_FREE = "włączony (Haiku)"
    AI_ON_PRO = "włączony (Haiku, trudne przypadki — Opus)"
    AI_OFF = "wyłączony, działają tylko reguły"
    AI_LIMIT = "dzienny limit wyczerpany, do jutra działają tylko reguły"
    BTN_PRO = "⭐ Pro"
    BTN_PAY_PRO = "⭐ Kup Pro: {price} ⭐ miesięcznie"
    CMD_PRO = "Subskrypcja Pro"
    CMD_PAYSUPPORT = "Pytania o płatność"
    PLAN_FREE = "darmowy"
    PLAN_PRO = "⭐ Pro do {until}"
    PRO_OFFER = (
        "⭐ <b>ChatGuard AI Pro</b>\n\n• trudne przypadki sprawdza dodatkowo Opus, "
        "najmądrzejszy model\n• do {pro_limit} sprawdzeń przez AI dziennie zamiast "
        "{free_limit}\n• wspólna baza spamerów: osoby złapane w innych czatach są "
        "sprawdzane surowiej\n\n{price} ⭐ miesięcznie, odnawia się automatycznie. "
        "Anulujesz w każdej chwili: Ustawienia Telegrama → Moje gwiazdki → "
        "subskrypcje."
    )
    PRO_ACTIVE = "⭐ Pro jest już włączone do {until}."
    PRO_INVOICE_TITLE = "ChatGuard AI Pro"
    PRO_INVOICE_DESCRIPTION = (
        "Pro dla „{chat}” na miesiąc: Opus dla trudnych przypadków, {limit} "
        "sprawdzeń dziennie, wspólna baza spamerów."
    )
    PRO_THANKS = "Dziękujemy! ⭐ Pro dla „{chat}” jest aktywne do {until}."
    PRO_ACTIVATED = (
        "⭐ {user} włączył(a) ChatGuard AI Pro do {until}. Trudne przypadki sprawdza teraz Opus."
    )
    PRO_RENEWED = "⭐ Subskrypcja Pro przedłużona do {until}."
    PRO_CHECK_FAILED = (
        "Nie udało się zweryfikować płatności. Otwórz /pro w czacie i spróbuj ponownie."
    )
    PAYSUPPORT = (
        "Pytania o płatność za ChatGuard AI Pro. Subskrypcję można anulować w każdej "
        "chwili: Ustawienia Telegrama → Moje gwiazdki → subskrypcje. Pro działa do "
        "końca opłaconego miesiąca."
    )
    PAYSUPPORT_CONTACT = "\nKontakt z twórcą: {contact}"


TEXTS: dict[str, Ru] = {"uk": Uk(), "ru": Ru(), "pl": Pl(), "en": En()}
