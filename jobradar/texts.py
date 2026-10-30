"""User-facing texts, one class per language.
Other languages subclass Russian; tests check that they override every text."""

from typing import ClassVar


class Ru:
    LANG = "ru"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "📡 Свежая удалённая работа по любой профессии: напишите своими словами, что искать"
    )
    BOT_DESCRIPTION = (
        "📡 JobRadar ищет удалённую работу, которую вы опишете своими словами.\n\n"
        "• проверяю сайты вакансий, Reddit и Telegram-каналы каждые 10 минут\n"
        "• нейросеть отсеивает то, что не подходит под ваши фильтры: офис, график, языки\n"
        "• по каждой вакансии: что делать, программы, страна, ставка и перевод\n"
        "• любая профессия: от монтажа и дизайна до бухгалтерии и поддержки\n"
        "• можно добавить свои каналы, сабреддиты и RSS-ленты"
    )

    CMD_START = "Подписаться на вакансии"
    CMD_SETTINGS = "Настройки"
    CMD_FILTERS = "Какую работу искать"
    CMD_SOURCES = "Мои источники"
    CMD_MAIL = "Подборки вакансий на почту"
    CMD_PRO = "Подписка Pro"
    CMD_STATUS = "Что сейчас с поиском"
    CMD_LANGUAGE = "Язык бота"
    CMD_PAYSUPPORT = "Вопросы по оплате"

    WELCOME = (
        "Привет! Я <b>JobRadar</b> 🎬\n\n"
        "Каждые {minutes} мин. я проверяю сайты вакансий, Reddit и Telegram-каналы и присылаю "
        "свежую удалённую работу.\n\n"
        "🎯 Выбрать работу и условия: /filters\n"
        "📚 Свои источники: /sources\n⭐ Больше вакансий в день: /pro\n\n"
        "Первые вакансии придут после ближайшей проверки."
    )
    NOT_ALLOWED = "Это личный бот, подписка закрыта."
    SETTINGS = "⚙️ <b>Настройки</b>\n\nТариф: {plan}\nПоказывать: {mode}\nРассылка: {state}"
    PLAN_FREE = "бесплатный"
    PLAN_PRO = "⭐ Pro до {until}"
    PLAN_ADMIN = "⭐ Pro (владелец)"
    PLAN_GIFT = "⭐ Pro (подарок, бессрочно)"
    GIFT_USAGE = "Напишите ID пользователя: /gift 123456789. Свой ID человек видит в /status."
    GIFT_NO_USER = "Пользователь {user_id} ещё не запускал бота: пусть сначала нажмёт /start."
    GIFT_DONE = "⭐ Пользователю {user_id} выдан бессрочный Pro."
    UNGIFT_DONE = "Подарочный Pro у пользователя {user_id} отключён."
    GIFT_PAYING = (
        "\nУ пользователя есть и платная подписка до {until}: она продлевается, пока её "
        "не отменят в Telegram (Настройки → Мои звёзды)."
    )
    GIFT_RECEIVED = (
        "🎁 Вам подарили бессрочный ⭐ JobRadar Pro: больше вакансий в день, поисков и "
        "своих источников. Подробнее: /status"
    )
    BTN_SOURCES = "📚 Мои источники"
    BTN_PRO = "⭐ Pro"
    MODE_ALL = "все подходящие вакансии"
    MODE_TOP = "только подкасты и говорящие головы 🔥"
    STATE_ON = "включена ▶️"
    STATE_OFF = "на паузе ⏸"
    BTN_SHOW_ALL = "🎬 Показывать все"
    BTN_PAUSE = "⏸ Пауза"
    BTN_RESUME = "▶️ Включить"
    LANGUAGE_SET = "Готово, пишу по-русски 🇷🇺"

    STATUS = (
        "📡 <b>Поиск</b>\n\n"
        "Последняя проверка: {last}\n"
        "Найдено объявлений: {found}, свежих и по запросам: {fresh}\n\n"
        "Тариф: {plan}\n"
        "Прислано вам сегодня: {sent} из {cards}\n"
        "Своих источников: {sources} из {sources_limit}\n"
        "🆔 Ваш ID: <code>{user_id}</code>"
    )
    STATUS_ADMIN = (
        "\n\n🔧 Нейросеть сегодня: {checked} проверок, ${today} из ${day_budget}\n"
        "За месяц: ${month} из ${budget}\n"
        "Платных подписчиков: {pros}"
    )
    NEVER = "ещё не было"
    LIMIT_REACHED = (
        "Это {cards}-я вакансия за сегодня, дневной лимит. Остальные придут завтра, "
        "если ещё будут свежими."
    )
    LIMIT_UPSELL = "\n\n⭐ С Pro — до {cards} вакансий в день: /pro"

    # --- Filters ---
    FILTERS = (
        "🎯 <b>Фильтры</b>\n\n"
        "👔 Что искать: {searches}\n"
        "🏠 Формат: {remote}\n"
        "🕒 График: {schedule}\n"
        "🗣 Языки, которые вы знаете: {languages}\n"
        "🌍 Работодатели: {regions}\n"
        "📍 Вы живёте: {country}\n\n"
        "Если в вакансии что-то не указано, она всё равно придёт: лучше показать, чем потерять."
    )
    REMOTE_ONLY = "только полная удалёнка"
    REMOTE_HYBRID = "удалёнка или гибрид"
    SCHEDULE_FLEXIBLE = "только свободный"
    SCHEDULE_ANY = "любой"
    BTN_FILTERS = "🎯 Фильтры"
    BTN_F_SEARCHES = "👔 Что искать"
    BTN_F_LANGUAGES = "🗣 Языки"
    BTN_ADD_SEARCH = "➕ Добавить"
    NO_SEARCHES = "пока ничего"
    SEARCHES = (
        "👔 <b>Что искать</b>: {count} из {limit}\n\n{list}\n\n"
        "Чтобы удалить поиск, нажмите на него."
    )
    SEARCH_ASK = (
        "✍️ Напишите своими словами, какую работу искать. Например: моушн-дизайнер, "
        "монтаж подкастов, 3D artist."
    )
    SEARCH_BAD = "Напишите название работы, от 2 до 40 символов."
    SEARCH_PICKING = "Подбираю слова для поиска…"
    SEARCH_ADDED = "✅ Добавлен поиск «{label}». Ищу по словам: {keywords} и другим."
    SEARCH_NOT_WORK = (
        "Не понял, какая это работа. Напишите название профессии, например «моушн-дизайнер»."
    )
    SEARCH_FAILED = "Не получилось подобрать слова, попробуйте ещё раз чуть позже."
    SEARCH_TOO_MANY = "Сегодня уже было много попыток добавить поиск. Попробуйте завтра."
    SEARCH_DUPLICATE = "Такой поиск уже есть."
    SEARCH_LIMIT_FREE = "На бесплатном тарифе можно {limit} поиска. С ⭐ Pro — до {pro_limit}: /pro"
    SEARCH_LIMIT_PRO = "Достигнут лимит: {limit} поисков. Удалите ненужный, чтобы добавить новый."
    SEARCH_REMOVED = "Поиск удалён."
    BTN_F_REGIONS = "🌍 Работодатели"
    BTN_F_COUNTRY = "📍 Страна"
    BTN_BACK = "⬅️ Назад"
    PICK_LANGUAGES = "🗣 Какие языки вы знаете? Вакансии, где нужен другой язык, не придут."
    PICK_REGIONS = (
        "🌍 Работодатели из каких стран подходят? Вакансии «по всему миру» и без страны "
        "приходят всегда."
    )
    PICK_COUNTRY = "📍 Где вы живёте? Вакансии только для жителей других стран не придут."
    AT_LEAST_ONE = "Нужно оставить хотя бы один вариант."
    LANGUAGE_LABELS: ClassVar[dict[str, str]] = {
        "en": "английский",
        "uk": "украинский",
        "ru": "русский",
        "pl": "польский",
        "de": "немецкий",
        "es": "испанский",
    }
    REGION_LABELS: ClassVar[dict[str, str]] = {
        "us": "США",
        "eu": "Европа",
        "ua": "Украина",
        "other": "другие страны",
        "ru_by": "Россия и Беларусь",
    }
    COUNTRY_LABELS: ClassVar[dict[str, str]] = {
        "UA": "🇺🇦 Украина",
        "PL": "🇵🇱 Польша",
        "DE": "🇩🇪 Германия",
        "CZ": "🇨🇿 Чехия",
        "ES": "🇪🇸 Испания",
        "GB": "🇬🇧 Великобритания",
        "US": "🇺🇸 США",
        "XX": "🌍 Другая страна",
    }

    # --- Own sources ---
    SOURCES = (
        "📚 <b>Ваши источники</b>: {count} из {limit}\n\n{list}\n\n"
        "Чтобы добавить, пришлите ссылку:\n"
        "• публичный Telegram-канал: t.me/channel\n"
        "• сабреддит: reddit.com/r/name\n"
        "• RSS-ленту сайта\n\n"
        "Вакансии из ваших источников приходят только вам. Общие источники (robota.ua, "
        "Himalayas, Remote OK, Remotive, Reddit, Telegram-каналы с вакансиями) бот "
        "проверяет и так. Чтобы удалить источник, нажмите на него.\n\n"
        "📬 Подборки вакансий с Upwork, LinkedIn и других сайтов на почту: /mail"
    )
    SOURCES_EMPTY = "пока нет"
    SOURCE_CHECKING = "Проверяю источник…"
    SOURCE_ADDED = "✅ Добавлен источник {name}. Вакансии из него придут после ближайшей проверки."
    SOURCE_DUPLICATE = "Этот источник уже есть в вашем списке."
    OVER_LIMIT = "\n\n⏸ Работают первые {limit}: столько позволяет ваш тариф. Больше: /pro"
    SOURCE_GLOBAL = "Этот источник бот и так проверяет для всех, добавлять его не нужно."
    SOURCE_LIMIT_FREE = (
        "На бесплатном тарифе можно добавить источников: {limit}. С ⭐ Pro — до {pro_limit}: /pro"
    )
    SOURCE_LIMIT_PRO = (
        "Достигнут лимит источников: {limit}. Удалите ненужный в /sources, чтобы добавить новый."
    )
    SOURCE_BAD_LINK = (
        "Не понял ссылку. Пришлите ссылку на публичный Telegram-канал (t.me/channel), "
        "сабреддит (reddit.com/r/name) или RSS-ленту сайта."
    )
    SOURCE_UNREACHABLE = (
        "Не получилось прочитать {name}: канал закрытый или пустой, или это не RSS-лента. "
        "Проверьте ссылку."
    )
    SOURCE_REMOVED = "Источник удалён."
    MAIL = (
        "📬 <b>Подборки вакансий на почту</b>\n\n"
        "Ваш личный адрес: <code>{address}</code>\n\n"
        "1. На Upwork, LinkedIn, Work.ua или другом сайте включите рассылку вакансий "
        "(job alerts) на свою почту.\n"
        "2. В своей почте настройте пересылку этих писем на адрес выше. В Gmail: "
        "Настройки → Пересылка и POP/IMAP → Добавить адрес пересылки, затем фильтр по "
        "отправителю (например, upwork.com) → «Переслать».\n"
        "3. Gmail пришлёт код подтверждения на этот адрес — я перешлю его вам сюда.\n\n"
        "Вакансии из писем приходят только вам и проходят ваши фильтры. "
        "Адрес никому не показывайте."
    )
    MAIL_OFF = "Подборки на почту пока не настроены владельцем бота."
    MAIL_CONFIRM = (
        "📬 Gmail просит подтвердить пересылку писем на ваш адрес бота.\n\n"
        "Код подтверждения: <code>{code}</code>\n"
        "Или откройте ссылку: {link}"
    )

    # --- Pro ---
    PRO_OFFER = (
        "⭐ <b>JobRadar Pro</b>\n\n"
        "• до {pro_cards} вакансий в день вместо {free_cards}\n"
        "• до {pro_sources} своих источников вместо {free_sources}\n"
        "• до {pro_searches} поисков вместо {free_searches}\n"
        "• ваши вакансии проверяются в первую очередь, даже в загруженные дни\n\n"
        "{price} ⭐ в месяц, продлевается автоматически. Отменить можно в любой момент: "
        "Настройки Telegram → Мои звёзды → подписки."
    )
    PRO_ACTIVE = "⭐ Pro уже включён до {until}."
    PRO_INVOICE_TITLE = "JobRadar Pro"
    PRO_INVOICE_DESCRIPTION = (
        "На месяц: до {cards} вакансий в день и до {sources} своих источников."
    )
    BTN_PAY_PRO = "⭐ Оформить Pro: {price} ⭐ в месяц"
    PRO_THANKS = "Спасибо! ⭐ Pro активен до {until}."
    PRO_RENEWED = "⭐ Подписка Pro продлена до {until}."
    PRO_CHECK_FAILED = "Не получилось проверить оплату. Откройте /pro и попробуйте снова."
    PRO_ALREADY = "У вас уже есть ⭐ Pro, платить второй раз не нужно."
    PAYSUPPORT = (
        "Вопросы по оплате JobRadar Pro. Подписку можно отменить в любой момент: "
        "Настройки Telegram → Мои звёзды → подписки. Pro работает до конца "
        "оплаченного месяца."
    )
    PAYSUPPORT_CONTACT = "\nСвязаться с разработчиком: {contact}"

    # --- Job card ---
    CARD_DUTIES = "Что делать"
    CARD_SOFTWARE = "Программы"
    CARD_COUNTRY = "Страна"
    CARD_PAY = "Ставка"
    CARD_SUMMARY = "Коротко"
    CARD_TRANSLATION = "Перевод"
    CARD_SOURCE = "Источник"
    NOT_STATED = "не указано"
    BTN_OPEN = "🔗 Открыть вакансию"
    NICHES: ClassVar[dict[str, str]] = {
        "podcast": "Подкаст",
        "talking_head": "Говорящая голова",
        "short_form": "Рилсы / TikTok / Shorts",
        "youtube": "YouTube",
        "wedding": "Свадьбы и события",
        "ai_video": "ИИ-видео",
        "ads": "Реклама",
        "other": "Другое",
    }


class En(Ru):
    LANG = "en"
    BOT_SHORT_DESCRIPTION = (
        "📡 Fresh remote jobs in any field: write in your own words what to look for"
    )
    BOT_DESCRIPTION = (
        "📡 JobRadar finds the remote work you describe in your own words.\n\n"
        "• I check job boards, Reddit and Telegram channels every 10 minutes\n"
        "• AI drops what doesn't fit your filters: office, fixed hours, languages\n"
        "• for each job: duties, software, country, pay and a translation\n"
        "• any profession: from editing and design to accounting and support\n"
        "• add your own channels, subreddits and RSS feeds"
    )

    CMD_START = "Subscribe to jobs"
    CMD_SETTINGS = "Settings"
    CMD_FILTERS = "What work to look for"
    CMD_SOURCES = "My sources"
    CMD_MAIL = "Job alert emails"
    CMD_PRO = "Pro subscription"
    CMD_STATUS = "Search status"
    CMD_LANGUAGE = "Bot language"
    CMD_PAYSUPPORT = "Payment questions"

    WELCOME = (
        "Hi! I'm <b>JobRadar</b> 🎬\n\n"
        "Every {minutes} min I check job boards, Reddit and Telegram channels and send you "
        "fresh remote work.\n\n"
        "🎯 Choose the work and conditions: /filters\n"
        "📚 Your own sources: /sources\n⭐ More jobs a day: /pro\n\n"
        "The first jobs arrive after the next check."
    )
    NOT_ALLOWED = "This is a personal bot, subscriptions are closed."
    SETTINGS = "⚙️ <b>Settings</b>\n\nPlan: {plan}\nShow: {mode}\nNotifications: {state}"
    PLAN_FREE = "free"
    PLAN_PRO = "⭐ Pro until {until}"
    PLAN_ADMIN = "⭐ Pro (owner)"
    PLAN_GIFT = "⭐ Pro (a gift, no end date)"
    GIFT_USAGE = "Send the user's ID: /gift 123456789. People see their ID in /status."
    GIFT_NO_USER = "User {user_id} hasn't started the bot yet: ask them to press /start first."
    GIFT_DONE = "⭐ User {user_id} now has Pro with no end date."
    UNGIFT_DONE = "The gifted Pro of user {user_id} is off."
    GIFT_PAYING = (
        "\nThis user also pays for Pro until {until}: the subscription renews until it is "
        "cancelled in Telegram (Settings → My Stars)."
    )
    GIFT_RECEIVED = (
        "🎁 You've been given ⭐ JobRadar Pro with no end date: more jobs a day, searches and "
        "own sources. Details: /status"
    )
    BTN_SOURCES = "📚 My sources"
    MODE_ALL = "every suitable job"
    MODE_TOP = "only podcasts and talking heads 🔥"
    STATE_ON = "on ▶️"
    STATE_OFF = "paused ⏸"
    BTN_SHOW_ALL = "🎬 Show all"
    BTN_PAUSE = "⏸ Pause"
    BTN_RESUME = "▶️ Resume"
    LANGUAGE_SET = "Done, I'll write in English 🇬🇧"

    STATUS = (
        "📡 <b>Search</b>\n\n"
        "Last check: {last}\n"
        "Posts found: {found}, fresh and on topic: {fresh}\n\n"
        "Plan: {plan}\n"
        "Sent to you today: {sent} of {cards}\n"
        "Your sources: {sources} of {sources_limit}\n"
        "🆔 Your ID: <code>{user_id}</code>"
    )
    STATUS_ADMIN = (
        "\n\n🔧 AI today: {checked} checks, ${today} of ${day_budget}\n"
        "This month: ${month} of ${budget}\n"
        "Paying subscribers: {pros}"
    )
    NEVER = "not yet"
    LIMIT_REACHED = (
        "That's job number {cards} today, the daily limit. The rest will come tomorrow "
        "if they are still fresh."
    )
    LIMIT_UPSELL = "\n\n⭐ With Pro — up to {cards} jobs a day: /pro"

    FILTERS = (
        "🎯 <b>Filters</b>\n\n"
        "👔 Looking for: {searches}\n"
        "🏠 Format: {remote}\n"
        "🕒 Hours: {schedule}\n"
        "🗣 Languages you know: {languages}\n"
        "🌍 Employers: {regions}\n"
        "📍 You live in: {country}\n\n"
        "If a job doesn't mention something, it still comes: better shown than lost."
    )
    REMOTE_ONLY = "fully remote only"
    REMOTE_HYBRID = "remote or hybrid"
    SCHEDULE_FLEXIBLE = "flexible only"
    SCHEDULE_ANY = "any"
    BTN_FILTERS = "🎯 Filters"
    BTN_F_SEARCHES = "👔 What to look for"
    BTN_F_LANGUAGES = "🗣 Languages"
    BTN_ADD_SEARCH = "➕ Add"
    NO_SEARCHES = "nothing yet"
    SEARCHES = (
        "👔 <b>What to look for</b>: {count} of {limit}\n\n{list}\n\nTap a search to remove it."
    )
    SEARCH_ASK = (
        "✍️ Write in your own words what work to look for. For example: motion designer, "
        "podcast editing, 3D artist."
    )
    SEARCH_BAD = "Write the name of the work, 2 to 40 characters."
    SEARCH_PICKING = "Picking search words…"
    SEARCH_ADDED = "✅ Added the search “{label}”. Looking for: {keywords} and more."
    SEARCH_NOT_WORK = (
        "I couldn't tell what work that is. Write a job title, e.g. “motion designer”."
    )
    SEARCH_FAILED = "Couldn't pick search words, please try again a bit later."
    SEARCH_TOO_MANY = "That's a lot of attempts to add a search today. Try again tomorrow."
    SEARCH_DUPLICATE = "You already have this search."
    SEARCH_LIMIT_FREE = (
        "The free plan allows {limit} searches. With ⭐ Pro — up to {pro_limit}: /pro"
    )
    SEARCH_LIMIT_PRO = "You've reached the limit of {limit} searches. Remove one to add a new one."
    SEARCH_REMOVED = "Search removed."
    BTN_F_REGIONS = "🌍 Employers"
    BTN_F_COUNTRY = "📍 Country"
    BTN_BACK = "⬅️ Back"
    PICK_LANGUAGES = "🗣 Which languages do you know? Jobs that need another one won't come."
    PICK_REGIONS = (
        "🌍 Employers from where suit you? Worldwide jobs and jobs without a country always come."
    )
    PICK_COUNTRY = "📍 Where do you live? Jobs only for residents of other countries won't come."
    AT_LEAST_ONE = "Keep at least one option."
    LANGUAGE_LABELS: ClassVar[dict[str, str]] = {
        "en": "English",
        "uk": "Ukrainian",
        "ru": "Russian",
        "pl": "Polish",
        "de": "German",
        "es": "Spanish",
    }
    REGION_LABELS: ClassVar[dict[str, str]] = {
        "us": "USA",
        "eu": "Europe",
        "ua": "Ukraine",
        "other": "other countries",
        "ru_by": "Russia and Belarus",
    }
    COUNTRY_LABELS: ClassVar[dict[str, str]] = {
        "UA": "🇺🇦 Ukraine",
        "PL": "🇵🇱 Poland",
        "DE": "🇩🇪 Germany",
        "CZ": "🇨🇿 Czechia",
        "ES": "🇪🇸 Spain",
        "GB": "🇬🇧 United Kingdom",
        "US": "🇺🇸 USA",
        "XX": "🌍 Another country",
    }

    SOURCES = (
        "📚 <b>Your sources</b>: {count} of {limit}\n\n{list}\n\n"
        "To add one, send a link:\n"
        "• a public Telegram channel: t.me/channel\n"
        "• a subreddit: reddit.com/r/name\n"
        "• a website's RSS feed\n\n"
        "Jobs from your sources are sent only to you. The shared sources (robota.ua, "
        "Himalayas, Remote OK, Remotive, Reddit, Telegram job channels) are checked anyway. "
        "Tap a source to remove it.\n\n"
        "📬 Job alerts from Upwork, LinkedIn and other sites by email: /mail"
    )
    SOURCES_EMPTY = "none yet"
    SOURCE_CHECKING = "Checking the source…"
    SOURCE_ADDED = "✅ Added {name}. Its jobs will come after the next check."
    SOURCE_DUPLICATE = "This source is already on your list."
    OVER_LIMIT = "\n\n⏸ Only the first {limit} work: that's what your plan allows. More: /pro"
    SOURCE_GLOBAL = "The bot already checks this source for everyone, no need to add it."
    SOURCE_LIMIT_FREE = (
        "The free plan allows {limit} own sources. With ⭐ Pro — up to {pro_limit}: /pro"
    )
    SOURCE_LIMIT_PRO = (
        "You've reached the limit of {limit} sources. Remove one in /sources to add a new one."
    )
    SOURCE_BAD_LINK = (
        "I didn't understand the link. Send a link to a public Telegram channel "
        "(t.me/channel), a subreddit (reddit.com/r/name) or a website's RSS feed."
    )
    SOURCE_UNREACHABLE = (
        "Couldn't read {name}: the channel is private or empty, or it isn't an RSS feed. "
        "Check the link."
    )
    SOURCE_REMOVED = "Source removed."
    MAIL = (
        "📬 <b>Job alert emails</b>\n\n"
        "Your personal address: <code>{address}</code>\n\n"
        "1. On Upwork, LinkedIn, Work.ua or another site, turn on job alerts to your email.\n"
        "2. In your email, forward those letters to the address above. In Gmail: Settings → "
        "Forwarding and POP/IMAP → Add a forwarding address, then a filter by sender "
        "(e.g. upwork.com) → “Forward it”.\n"
        "3. Gmail will send a confirmation code to this address — I'll pass it on to you here."
        "\n\nJobs from the letters go only to you and pass your filters. "
        "Don't share the address."
    )
    MAIL_OFF = "Job alert emails aren't set up by the bot owner yet."
    MAIL_CONFIRM = (
        "📬 Gmail asks to confirm forwarding to your bot address.\n\n"
        "Confirmation code: <code>{code}</code>\n"
        "Or open the link: {link}"
    )

    PRO_OFFER = (
        "⭐ <b>JobRadar Pro</b>\n\n"
        "• up to {pro_cards} jobs a day instead of {free_cards}\n"
        "• up to {pro_sources} own sources instead of {free_sources}\n"
        "• up to {pro_searches} searches instead of {free_searches}\n"
        "• your jobs are checked first, even on busy days\n\n"
        "{price} ⭐ a month, renews automatically. Cancel any time: "
        "Telegram Settings → My Stars → subscriptions."
    )
    PRO_ACTIVE = "⭐ Pro is already on until {until}."
    PRO_INVOICE_DESCRIPTION = (
        "For a month: up to {cards} jobs a day and up to {sources} own sources."
    )
    BTN_PAY_PRO = "⭐ Get Pro: {price} ⭐ a month"
    PRO_THANKS = "Thank you! ⭐ Pro is on until {until}."
    PRO_RENEWED = "⭐ Your Pro subscription is renewed until {until}."
    PRO_CHECK_FAILED = "Couldn't verify the payment. Open /pro and try again."
    PRO_ALREADY = "You already have ⭐ Pro, no need to pay again."
    PAYSUPPORT = (
        "Payment questions for JobRadar Pro. You can cancel the subscription any time: "
        "Telegram Settings → My Stars → subscriptions. Pro keeps working until the end of "
        "the paid month."
    )
    PAYSUPPORT_CONTACT = "\nContact the developer: {contact}"

    CARD_DUTIES = "Duties"
    CARD_SOFTWARE = "Software"
    CARD_COUNTRY = "Country"
    CARD_PAY = "Pay"
    CARD_SUMMARY = "In short"
    CARD_TRANSLATION = "Translation"
    CARD_SOURCE = "Source"
    NOT_STATED = "not stated"
    BTN_OPEN = "🔗 Open the job"
    NICHES: ClassVar[dict[str, str]] = {
        "podcast": "Podcast",
        "talking_head": "Talking head",
        "short_form": "Reels / TikTok / Shorts",
        "youtube": "YouTube",
        "wedding": "Weddings and events",
        "ai_video": "AI video",
        "ads": "Ads",
        "other": "Other",
    }


class Uk(Ru):
    LANG = "uk"
    BOT_SHORT_DESCRIPTION = (
        "📡 Свіжа віддалена робота з будь-якої професії: напишіть своїми словами, що шукати"
    )
    BOT_DESCRIPTION = (
        "📡 JobRadar шукає віддалену роботу, яку ви опишете своїми словами.\n\n"
        "• перевіряю сайти вакансій, Reddit і Telegram-канали кожні 10 хвилин\n"
        "• нейромережа відсіює те, що не підходить під ваші фільтри: офіс, графік, мови\n"
        "• по кожній вакансії: що робити, програми, країна, ставка і переклад\n"
        "• будь-яка професія: від монтажу й дизайну до бухгалтерії та підтримки\n"
        "• можна додати свої канали, сабреддити й RSS-стрічки"
    )

    CMD_START = "Підписатися на вакансії"
    CMD_SETTINGS = "Налаштування"
    CMD_FILTERS = "Яку роботу шукати"
    CMD_SOURCES = "Мої джерела"
    CMD_MAIL = "Добірки вакансій на пошту"
    CMD_PRO = "Підписка Pro"
    CMD_STATUS = "Що зараз із пошуком"
    CMD_LANGUAGE = "Мова бота"
    CMD_PAYSUPPORT = "Питання щодо оплати"

    WELCOME = (
        "Привіт! Я <b>JobRadar</b> 🎬\n\n"
        "Кожні {minutes} хв. я перевіряю сайти вакансій, Reddit і Telegram-канали та надсилаю "
        "свіжу віддалену роботу.\n\n"
        "🎯 Вибрати роботу та умови: /filters\n"
        "📚 Свої джерела: /sources\n⭐ Більше вакансій на день: /pro\n\n"
        "Перші вакансії прийдуть після найближчої перевірки."
    )
    NOT_ALLOWED = "Це особистий бот, підписка закрита."
    SETTINGS = "⚙️ <b>Налаштування</b>\n\nТариф: {plan}\nПоказувати: {mode}\nРозсилка: {state}"
    PLAN_FREE = "безкоштовний"
    PLAN_PRO = "⭐ Pro до {until}"
    PLAN_ADMIN = "⭐ Pro (власник)"
    PLAN_GIFT = "⭐ Pro (подарунок, безстроково)"
    GIFT_USAGE = "Напишіть ID користувача: /gift 123456789. Свій ID людина бачить у /status."
    GIFT_NO_USER = "Користувач {user_id} ще не запускав бота: хай спершу натисне /start."
    GIFT_DONE = "⭐ Користувачу {user_id} видано безстроковий Pro."
    UNGIFT_DONE = "Подарунковий Pro у користувача {user_id} вимкнено."
    GIFT_PAYING = (
        "\nКористувач також платить за Pro до {until}: підписка продовжується, доки її "
        "не скасують у Telegram (Налаштування → Мої зірки)."
    )
    GIFT_RECEIVED = (
        "🎁 Вам подарували безстроковий ⭐ JobRadar Pro: більше вакансій на день, пошуків і "
        "своїх джерел. Докладніше: /status"
    )
    BTN_SOURCES = "📚 Мої джерела"
    MODE_ALL = "усі вакансії, що підходять"
    MODE_TOP = "лише подкасти й говорящі голови 🔥"
    STATE_ON = "увімкнена ▶️"
    STATE_OFF = "на паузі ⏸"
    BTN_SHOW_ALL = "🎬 Показувати всі"
    BTN_PAUSE = "⏸ Пауза"
    BTN_RESUME = "▶️ Увімкнути"
    LANGUAGE_SET = "Готово, пишу українською 🇺🇦"

    STATUS = (
        "📡 <b>Пошук</b>\n\n"
        "Остання перевірка: {last}\n"
        "Знайдено оголошень: {found}, свіжих і за запитами: {fresh}\n\n"
        "Тариф: {plan}\n"
        "Надіслано вам сьогодні: {sent} з {cards}\n"
        "Своїх джерел: {sources} з {sources_limit}\n"
        "🆔 Ваш ID: <code>{user_id}</code>"
    )
    STATUS_ADMIN = (
        "\n\n🔧 Нейромережа сьогодні: {checked} перевірок, ${today} з ${day_budget}\n"
        "За місяць: ${month} з ${budget}\n"
        "Платних підписників: {pros}"
    )
    NEVER = "ще не було"
    LIMIT_REACHED = (
        "Це {cards}-та вакансія за сьогодні, денний ліміт. Решта прийде завтра, "
        "якщо ще буде свіжою."
    )
    LIMIT_UPSELL = "\n\n⭐ З Pro — до {cards} вакансій на день: /pro"

    FILTERS = (
        "🎯 <b>Фільтри</b>\n\n"
        "👔 Що шукати: {searches}\n"
        "🏠 Формат: {remote}\n"
        "🕒 Графік: {schedule}\n"
        "🗣 Мови, які ви знаєте: {languages}\n"
        "🌍 Роботодавці: {regions}\n"
        "📍 Ви живете: {country}\n\n"
        "Якщо у вакансії щось не вказано, вона все одно прийде: краще показати, ніж втратити."
    )
    REMOTE_ONLY = "лише повна віддалена"
    REMOTE_HYBRID = "віддалена або гібрид"
    SCHEDULE_FLEXIBLE = "лише вільний"
    SCHEDULE_ANY = "будь-який"
    BTN_FILTERS = "🎯 Фільтри"
    BTN_F_SEARCHES = "👔 Що шукати"
    BTN_F_LANGUAGES = "🗣 Мови"
    BTN_ADD_SEARCH = "➕ Додати"
    NO_SEARCHES = "поки нічого"
    SEARCHES = (
        "👔 <b>Що шукати</b>: {count} з {limit}\n\n{list}\n\n"
        "Щоб видалити пошук, натисніть на нього."
    )
    SEARCH_ASK = (
        "✍️ Напишіть своїми словами, яку роботу шукати. Наприклад: моушн-дизайнер, "
        "монтаж подкастів, 3D artist."
    )
    SEARCH_BAD = "Напишіть назву роботи, від 2 до 40 символів."
    SEARCH_PICKING = "Підбираю слова для пошуку…"
    SEARCH_ADDED = "✅ Додано пошук «{label}». Шукаю за словами: {keywords} та іншими."
    SEARCH_NOT_WORK = (
        "Не зрозумів, яка це робота. Напишіть назву професії, наприклад «моушн-дизайнер»."
    )
    SEARCH_FAILED = "Не вдалося підібрати слова, спробуйте ще раз трохи пізніше."
    SEARCH_TOO_MANY = "Сьогодні вже було багато спроб додати пошук. Спробуйте завтра."
    SEARCH_DUPLICATE = "Такий пошук уже є."
    SEARCH_LIMIT_FREE = (
        "На безкоштовному тарифі можна {limit} пошуки. З ⭐ Pro — до {pro_limit}: /pro"
    )
    SEARCH_LIMIT_PRO = "Досягнуто ліміту: {limit} пошуків. Видаліть непотрібний, щоб додати новий."
    SEARCH_REMOVED = "Пошук видалено."
    BTN_F_REGIONS = "🌍 Роботодавці"
    BTN_F_COUNTRY = "📍 Країна"
    BTN_BACK = "⬅️ Назад"
    PICK_LANGUAGES = "🗣 Які мови ви знаєте? Вакансії, де потрібна інша мова, не прийдуть."
    PICK_REGIONS = (
        "🌍 Роботодавці з яких країн підходять? Вакансії «по всьому світу» і без країни "
        "приходять завжди."
    )
    PICK_COUNTRY = "📍 Де ви живете? Вакансії лише для жителів інших країн не прийдуть."
    AT_LEAST_ONE = "Потрібно залишити хоча б один варіант."
    LANGUAGE_LABELS: ClassVar[dict[str, str]] = {
        "en": "англійська",
        "uk": "українська",
        "ru": "російська",
        "pl": "польська",
        "de": "німецька",
        "es": "іспанська",
    }
    REGION_LABELS: ClassVar[dict[str, str]] = {
        "us": "США",
        "eu": "Європа",
        "ua": "Україна",
        "other": "інші країни",
        "ru_by": "Росія та Білорусь",
    }
    COUNTRY_LABELS: ClassVar[dict[str, str]] = {
        "UA": "🇺🇦 Україна",
        "PL": "🇵🇱 Польща",
        "DE": "🇩🇪 Німеччина",
        "CZ": "🇨🇿 Чехія",
        "ES": "🇪🇸 Іспанія",
        "GB": "🇬🇧 Велика Британія",
        "US": "🇺🇸 США",
        "XX": "🌍 Інша країна",
    }

    SOURCES = (
        "📚 <b>Ваші джерела</b>: {count} з {limit}\n\n{list}\n\n"
        "Щоб додати, надішліть посилання:\n"
        "• публічний Telegram-канал: t.me/channel\n"
        "• сабреддит: reddit.com/r/name\n"
        "• RSS-стрічку сайту\n\n"
        "Вакансії з ваших джерел приходять лише вам. Спільні джерела (robota.ua, "
        "Himalayas, Remote OK, Remotive, Reddit, Telegram-канали з вакансіями) бот "
        "перевіряє й так. Щоб видалити джерело, натисніть на нього.\n\n"
        "📬 Добірки вакансій з Upwork, LinkedIn та інших сайтів на пошту: /mail"
    )
    SOURCES_EMPTY = "поки немає"
    SOURCE_CHECKING = "Перевіряю джерело…"
    SOURCE_ADDED = "✅ Додано джерело {name}. Вакансії з нього прийдуть після найближчої перевірки."
    SOURCE_DUPLICATE = "Це джерело вже є у вашому списку."
    OVER_LIMIT = "\n\n⏸ Працюють перші {limit}: стільки дозволяє ваш тариф. Більше: /pro"
    SOURCE_GLOBAL = "Це джерело бот і так перевіряє для всіх, додавати його не потрібно."
    SOURCE_LIMIT_FREE = (
        "На безкоштовному тарифі можна додати джерел: {limit}. З ⭐ Pro — до {pro_limit}: /pro"
    )
    SOURCE_LIMIT_PRO = (
        "Досягнуто ліміту джерел: {limit}. Видаліть непотрібне в /sources, щоб додати нове."
    )
    SOURCE_BAD_LINK = (
        "Не зрозумів посилання. Надішліть посилання на публічний Telegram-канал "
        "(t.me/channel), сабреддит (reddit.com/r/name) або RSS-стрічку сайту."
    )
    SOURCE_UNREACHABLE = (
        "Не вдалося прочитати {name}: канал закритий чи порожній, або це не RSS-стрічка. "
        "Перевірте посилання."
    )
    SOURCE_REMOVED = "Джерело видалено."
    MAIL = (
        "📬 <b>Добірки вакансій на пошту</b>\n\n"
        "Ваша особиста адреса: <code>{address}</code>\n\n"
        "1. На Upwork, LinkedIn, Work.ua чи іншому сайті увімкніть розсилку вакансій "
        "(job alerts) на свою пошту.\n"
        "2. У своїй пошті налаштуйте пересилання цих листів на адресу вище. У Gmail: "
        "Налаштування → Пересилання та POP/IMAP → Додати адресу пересилання, потім фільтр "
        "за відправником (наприклад, upwork.com) → «Переслати».\n"
        "3. Gmail надішле код підтвердження на цю адресу — я перешлю його вам сюди.\n\n"
        "Вакансії з листів приходять лише вам і проходять ваші фільтри. "
        "Адресу нікому не показуйте."
    )
    MAIL_OFF = "Добірки на пошту ще не налаштовані власником бота."
    MAIL_CONFIRM = (
        "📬 Gmail просить підтвердити пересилання листів на вашу адресу бота.\n\n"
        "Код підтвердження: <code>{code}</code>\n"
        "Або відкрийте посилання: {link}"
    )

    PRO_OFFER = (
        "⭐ <b>JobRadar Pro</b>\n\n"
        "• до {pro_cards} вакансій на день замість {free_cards}\n"
        "• до {pro_sources} своїх джерел замість {free_sources}\n"
        "• до {pro_searches} пошуків замість {free_searches}\n"
        "• ваші вакансії перевіряються першими, навіть у завантажені дні\n\n"
        "{price} ⭐ на місяць, продовжується автоматично. Скасувати можна будь-коли: "
        "Налаштування Telegram → Мої зірки → підписки."
    )
    PRO_ACTIVE = "⭐ Pro вже увімкнено до {until}."
    PRO_INVOICE_DESCRIPTION = "На місяць: до {cards} вакансій на день і до {sources} своїх джерел."
    BTN_PAY_PRO = "⭐ Оформити Pro: {price} ⭐ на місяць"
    PRO_THANKS = "Дякуємо! ⭐ Pro активний до {until}."
    PRO_RENEWED = "⭐ Підписку Pro продовжено до {until}."
    PRO_CHECK_FAILED = "Не вдалося перевірити оплату. Відкрийте /pro і спробуйте ще раз."
    PRO_ALREADY = "У вас уже є ⭐ Pro, платити вдруге не потрібно."
    PAYSUPPORT = (
        "Питання щодо оплати JobRadar Pro. Підписку можна скасувати будь-коли: "
        "Налаштування Telegram → Мої зірки → підписки. Pro працює до кінця "
        "оплаченого місяця."
    )
    PAYSUPPORT_CONTACT = "\nЗв'язатися з розробником: {contact}"

    CARD_DUTIES = "Що робити"
    CARD_SOFTWARE = "Програми"
    CARD_COUNTRY = "Країна"
    CARD_PAY = "Ставка"
    CARD_SUMMARY = "Коротко"
    CARD_TRANSLATION = "Переклад"
    CARD_SOURCE = "Джерело"
    NOT_STATED = "не вказано"
    BTN_OPEN = "🔗 Відкрити вакансію"
    NICHES: ClassVar[dict[str, str]] = {
        "podcast": "Подкаст",
        "talking_head": "Говоряща голова",
        "short_form": "Рілси / TikTok / Shorts",
        "youtube": "YouTube",
        "wedding": "Весілля та події",
        "ai_video": "ШІ-відео",
        "ads": "Реклама",
        "other": "Інше",
    }


class Pl(Ru):
    LANG = "pl"
    BOT_SHORT_DESCRIPTION = (
        "📡 Świeża praca zdalna w każdym zawodzie: napisz własnymi słowami, czego szukać"
    )
    BOT_DESCRIPTION = (
        "📡 JobRadar szuka pracy zdalnej, którą opiszesz własnymi słowami.\n\n"
        "• sprawdzam portale z ofertami, Reddit i kanały Telegram co 10 minut\n"
        "• AI odrzuca to, co nie pasuje do twoich filtrów: biuro, godziny, języki\n"
        "• przy każdej ofercie: zadania, programy, kraj, stawka i tłumaczenie\n"
        "• każdy zawód: od montażu i grafiki po księgowość i obsługę klienta\n"
        "• możesz dodać własne kanały, subreddity i kanały RSS"
    )

    CMD_START = "Subskrybuj oferty"
    CMD_SETTINGS = "Ustawienia"
    CMD_FILTERS = "Jakiej pracy szukać"
    CMD_SOURCES = "Moje źródła"
    CMD_MAIL = "Powiadomienia o ofertach na e-mail"
    CMD_PRO = "Subskrypcja Pro"
    CMD_STATUS = "Stan wyszukiwania"
    CMD_LANGUAGE = "Język bota"
    CMD_PAYSUPPORT = "Pytania o płatność"

    WELCOME = (
        "Cześć! Jestem <b>JobRadar</b> 🎬\n\n"
        "Co {minutes} min sprawdzam portale z ofertami, Reddit i kanały Telegram i wysyłam "
        "świeżą pracę zdalną.\n\n"
        "🎯 Wybierz pracę i warunki: /filters\n"
        "📚 Własne źródła: /sources\n⭐ Więcej ofert dziennie: /pro\n\n"
        "Pierwsze oferty przyjdą po najbliższym sprawdzeniu."
    )
    NOT_ALLOWED = "To prywatny bot, subskrypcja jest zamknięta."
    SETTINGS = "⚙️ <b>Ustawienia</b>\n\nPlan: {plan}\nPokazuj: {mode}\nPowiadomienia: {state}"
    PLAN_FREE = "darmowy"
    PLAN_PRO = "⭐ Pro do {until}"
    PLAN_ADMIN = "⭐ Pro (właściciel)"
    PLAN_GIFT = "⭐ Pro (prezent, bezterminowo)"
    GIFT_USAGE = "Podaj ID użytkownika: /gift 123456789. Swoje ID każdy widzi w /status."
    GIFT_NO_USER = (
        "Użytkownik {user_id} jeszcze nie uruchomił bota: niech najpierw naciśnie /start."
    )
    GIFT_DONE = "⭐ Użytkownik {user_id} ma teraz bezterminowy Pro."
    UNGIFT_DONE = "Podarowany Pro użytkownika {user_id} jest wyłączony."
    GIFT_PAYING = (
        "\nTen użytkownik płaci też za Pro do {until}: subskrypcja odnawia się, dopóki "
        "nie zostanie anulowana w Telegramie (Ustawienia → Moje gwiazdki)."
    )
    GIFT_RECEIVED = (
        "🎁 Otrzymujesz w prezencie bezterminowy ⭐ JobRadar Pro: więcej ofert dziennie, "
        "wyszukiwań i własnych źródeł. Szczegóły: /status"
    )
    BTN_SOURCES = "📚 Moje źródła"
    MODE_ALL = "wszystkie pasujące oferty"
    MODE_TOP = "tylko podcasty i gadające głowy 🔥"
    STATE_ON = "włączone ▶️"
    STATE_OFF = "wstrzymane ⏸"
    BTN_SHOW_ALL = "🎬 Pokazuj wszystkie"
    BTN_PAUSE = "⏸ Wstrzymaj"
    BTN_RESUME = "▶️ Włącz"
    LANGUAGE_SET = "Gotowe, piszę po polsku 🇵🇱"

    STATUS = (
        "📡 <b>Wyszukiwanie</b>\n\n"
        "Ostatnie sprawdzenie: {last}\n"
        "Znalezione ogłoszenia: {found}, świeże i na temat: {fresh}\n\n"
        "Plan: {plan}\n"
        "Wysłane do ciebie dzisiaj: {sent} z {cards}\n"
        "Twoje źródła: {sources} z {sources_limit}\n"
        "🆔 Twoje ID: <code>{user_id}</code>"
    )
    STATUS_ADMIN = (
        "\n\n🔧 AI dzisiaj: {checked} sprawdzeń, ${today} z ${day_budget}\n"
        "W tym miesiącu: ${month} z ${budget}\n"
        "Płacący subskrybenci: {pros}"
    )
    NEVER = "jeszcze nie było"
    LIMIT_REACHED = (
        "To {cards}. oferta dzisiaj, dzienny limit. Reszta przyjdzie jutro, "
        "jeśli nadal będzie świeża."
    )
    LIMIT_UPSELL = "\n\n⭐ Z Pro — do {cards} ofert dziennie: /pro"

    FILTERS = (
        "🎯 <b>Filtry</b>\n\n"
        "👔 Czego szukać: {searches}\n"
        "🏠 Tryb: {remote}\n"
        "🕒 Godziny: {schedule}\n"
        "🗣 Języki, które znasz: {languages}\n"
        "🌍 Pracodawcy: {regions}\n"
        "📍 Mieszkasz w: {country}\n\n"
        "Jeśli oferta czegoś nie podaje, i tak przyjdzie: lepiej pokazać, niż stracić."
    )
    REMOTE_ONLY = "tylko w pełni zdalnie"
    REMOTE_HYBRID = "zdalnie lub hybrydowo"
    SCHEDULE_FLEXIBLE = "tylko elastyczne"
    SCHEDULE_ANY = "dowolne"
    BTN_FILTERS = "🎯 Filtry"
    BTN_F_SEARCHES = "👔 Czego szukać"
    BTN_F_LANGUAGES = "🗣 Języki"
    BTN_ADD_SEARCH = "➕ Dodaj"
    NO_SEARCHES = "na razie nic"
    SEARCHES = (
        "👔 <b>Czego szukać</b>: {count} z {limit}\n\n{list}\n\n"
        "Aby usunąć wyszukiwanie, kliknij je."
    )
    SEARCH_ASK = (
        "✍️ Napisz własnymi słowami, jakiej pracy szukać. Na przykład: motion designer, "
        "montaż podcastów, grafik 3D."
    )
    SEARCH_BAD = "Napisz nazwę pracy, od 2 do 40 znaków."
    SEARCH_PICKING = "Dobieram słowa do wyszukiwania…"
    SEARCH_ADDED = "✅ Dodano wyszukiwanie „{label}”. Szukam po słowach: {keywords} i innych."
    SEARCH_NOT_WORK = "Nie rozumiem, jaka to praca. Napisz nazwę zawodu, np. „motion designer”."
    SEARCH_FAILED = "Nie udało się dobrać słów, spróbuj ponownie trochę później."
    SEARCH_TOO_MANY = "Dziś było już wiele prób dodania wyszukiwania. Spróbuj jutro."
    SEARCH_DUPLICATE = "Takie wyszukiwanie już jest."
    SEARCH_LIMIT_FREE = (
        "W darmowym planie możesz mieć {limit} wyszukiwania. Z ⭐ Pro — do {pro_limit}: /pro"
    )
    SEARCH_LIMIT_PRO = "Osiągnięto limit: {limit} wyszukiwań. Usuń niepotrzebne, aby dodać nowe."
    SEARCH_REMOVED = "Wyszukiwanie usunięte."
    BTN_F_REGIONS = "🌍 Pracodawcy"
    BTN_F_COUNTRY = "📍 Kraj"
    BTN_BACK = "⬅️ Wstecz"
    PICK_LANGUAGES = "🗣 Jakie języki znasz? Oferty wymagające innego języka nie przyjdą."
    PICK_REGIONS = (
        "🌍 Pracodawcy z jakich krajów ci pasują? Oferty „z całego świata” i bez kraju "
        "przychodzą zawsze."
    )
    PICK_COUNTRY = "📍 Gdzie mieszkasz? Oferty tylko dla mieszkańców innych krajów nie przyjdą."
    AT_LEAST_ONE = "Zostaw co najmniej jedną opcję."
    LANGUAGE_LABELS: ClassVar[dict[str, str]] = {
        "en": "angielski",
        "uk": "ukraiński",
        "ru": "rosyjski",
        "pl": "polski",
        "de": "niemiecki",
        "es": "hiszpański",
    }
    REGION_LABELS: ClassVar[dict[str, str]] = {
        "us": "USA",
        "eu": "Europa",
        "ua": "Ukraina",
        "other": "inne kraje",
        "ru_by": "Rosja i Białoruś",
    }
    COUNTRY_LABELS: ClassVar[dict[str, str]] = {
        "UA": "🇺🇦 Ukraina",
        "PL": "🇵🇱 Polska",
        "DE": "🇩🇪 Niemcy",
        "CZ": "🇨🇿 Czechy",
        "ES": "🇪🇸 Hiszpania",
        "GB": "🇬🇧 Wielka Brytania",
        "US": "🇺🇸 USA",
        "XX": "🌍 Inny kraj",
    }

    SOURCES = (
        "📚 <b>Twoje źródła</b>: {count} z {limit}\n\n{list}\n\n"
        "Aby dodać, wyślij link:\n"
        "• publiczny kanał Telegram: t.me/channel\n"
        "• subreddit: reddit.com/r/name\n"
        "• kanał RSS strony\n\n"
        "Oferty z twoich źródeł trafiają tylko do ciebie. Wspólne źródła (robota.ua, "
        "Himalayas, Remote OK, Remotive, Reddit, kanały Telegram z ofertami) bot "
        "sprawdza i tak. Aby usunąć źródło, kliknij je.\n\n"
        "📬 Powiadomienia o ofertach z Upwork, LinkedIn i innych stron na e-mail: /mail"
    )
    SOURCES_EMPTY = "na razie brak"
    SOURCE_CHECKING = "Sprawdzam źródło…"
    SOURCE_ADDED = "✅ Dodano źródło {name}. Oferty z niego przyjdą po najbliższym sprawdzeniu."
    SOURCE_DUPLICATE = "To źródło jest już na twojej liście."
    OVER_LIMIT = "\n\n⏸ Działa tylko pierwszych {limit}: tyle pozwala twój plan. Więcej: /pro"
    SOURCE_GLOBAL = "Bot i tak sprawdza to źródło dla wszystkich, nie trzeba go dodawać."
    SOURCE_LIMIT_FREE = (
        "W darmowym planie możesz dodać źródeł: {limit}. Z ⭐ Pro — do {pro_limit}: /pro"
    )
    SOURCE_LIMIT_PRO = (
        "Osiągnięto limit źródeł: {limit}. Usuń niepotrzebne w /sources, aby dodać nowe."
    )
    SOURCE_BAD_LINK = (
        "Nie rozumiem linku. Wyślij link do publicznego kanału Telegram (t.me/channel), "
        "subreddita (reddit.com/r/name) lub kanału RSS strony."
    )
    SOURCE_UNREACHABLE = (
        "Nie udało się odczytać {name}: kanał jest prywatny lub pusty albo to nie jest "
        "kanał RSS. Sprawdź link."
    )
    SOURCE_REMOVED = "Źródło usunięte."
    MAIL = (
        "📬 <b>Powiadomienia o ofertach na e-mail</b>\n\n"
        "Twój osobisty adres: <code>{address}</code>\n\n"
        "1. Na Upwork, LinkedIn, Work.ua lub innej stronie włącz powiadomienia o ofertach "
        "(job alerts) na swój e-mail.\n"
        "2. W swojej poczcie ustaw przekazywanie tych listów na adres powyżej. W Gmail: "
        "Ustawienia → Przekazywanie i POP/IMAP → Dodaj adres przekazywania, potem filtr "
        "według nadawcy (np. upwork.com) → „Przekaż”.\n"
        "3. Gmail wyśle kod potwierdzenia na ten adres — przekażę ci go tutaj.\n\n"
        "Oferty z listów trafiają tylko do ciebie i przechodzą przez twoje filtry. "
        "Nie pokazuj nikomu tego adresu."
    )
    MAIL_OFF = "Powiadomienia e-mail nie zostały jeszcze skonfigurowane przez właściciela bota."
    MAIL_CONFIRM = (
        "📬 Gmail prosi o potwierdzenie przekazywania listów na twój adres bota.\n\n"
        "Kod potwierdzenia: <code>{code}</code>\n"
        "Lub otwórz link: {link}"
    )

    PRO_OFFER = (
        "⭐ <b>JobRadar Pro</b>\n\n"
        "• do {pro_cards} ofert dziennie zamiast {free_cards}\n"
        "• do {pro_sources} własnych źródeł zamiast {free_sources}\n"
        "• do {pro_searches} wyszukiwań zamiast {free_searches}\n"
        "• twoje oferty są sprawdzane w pierwszej kolejności, nawet w zatłoczone dni\n\n"
        "{price} ⭐ miesięcznie, odnawia się automatycznie. Anulować można w każdej chwili: "
        "Ustawienia Telegram → Moje gwiazdki → subskrypcje."
    )
    PRO_ACTIVE = "⭐ Pro jest już włączony do {until}."
    PRO_INVOICE_DESCRIPTION = (
        "Na miesiąc: do {cards} ofert dziennie i do {sources} własnych źródeł."
    )
    BTN_PAY_PRO = "⭐ Kup Pro: {price} ⭐ miesięcznie"
    PRO_THANKS = "Dziękujemy! ⭐ Pro jest aktywny do {until}."
    PRO_RENEWED = "⭐ Subskrypcja Pro przedłużona do {until}."
    PRO_CHECK_FAILED = "Nie udało się sprawdzić płatności. Otwórz /pro i spróbuj ponownie."
    PRO_ALREADY = "Masz już ⭐ Pro, nie trzeba płacić drugi raz."
    PAYSUPPORT = (
        "Pytania o płatność za JobRadar Pro. Subskrypcję można anulować w każdej chwili: "
        "Ustawienia Telegram → Moje gwiazdki → subskrypcje. Pro działa do końca "
        "opłaconego miesiąca."
    )
    PAYSUPPORT_CONTACT = "\nKontakt z twórcą: {contact}"

    CARD_DUTIES = "Zadania"
    CARD_SOFTWARE = "Programy"
    CARD_COUNTRY = "Kraj"
    CARD_PAY = "Stawka"
    CARD_SUMMARY = "W skrócie"
    CARD_TRANSLATION = "Tłumaczenie"
    CARD_SOURCE = "Źródło"
    NOT_STATED = "nie podano"
    BTN_OPEN = "🔗 Otwórz ofertę"
    NICHES: ClassVar[dict[str, str]] = {
        "podcast": "Podcast",
        "talking_head": "Gadająca głowa",
        "short_form": "Rolki / TikTok / Shorts",
        "youtube": "YouTube",
        "wedding": "Wesela i wydarzenia",
        "ai_video": "Wideo AI",
        "ads": "Reklama",
        "other": "Inne",
    }


TEXTS: dict[str, Ru] = {"uk": Uk(), "ru": Ru(), "pl": Pl(), "en": En()}
