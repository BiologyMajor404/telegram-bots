"""User-facing texts and formatting, one class per language.
Other languages subclass Russian; tests check that they override every text."""

from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

from slotbook.models import Booking, Service


class Ru:
    LANG = "ru"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = "📅 Онлайн-запись к мастеру за пару нажатий, с напоминаниями о визите"
    BOT_DESCRIPTION = (
        "📅 SlotBook — онлайн-запись к мастеру.\n\n• выберите услугу, день и "
        "свободное время\n• напомню о визите за день и за 2 часа\n• отменить запись "
        "можно в один клик\n\nДля мастера: панель с записями, услугами, рабочими "
        "часами и предоплатой в Telegram Stars.\n\nНажмите «Старт», чтобы записаться "
        "👇"
    )
    WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
    WEEKDAYS_FULL = (
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    )
    MONTHS = (
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    )
    MIN = "мин"
    DAY_OFF = "выходной"
    # The master's currency, same for every language; set from SLOTBOOK_CURRENCY at startup
    currency = "₴"

    def fmt_day(self, d: date) -> str:
        return f"{self.WEEKDAYS[d.weekday()]}, {d.day} {self.MONTHS[d.month - 1]}"

    def fmt_dt(self, dt: datetime, tz: ZoneInfo) -> str:
        local = dt.astimezone(tz)
        return f"{self.fmt_day(local.date())}, {local:%H:%M}"

    def fmt_service(self, s: Service) -> str:
        return f"{escape(s.name)} · {s.duration_min} {self.MIN} · {s.price} {self.currency}"

    def fmt_booking(self, b: Booking, tz: ZoneInfo) -> str:
        text = f"<b>{self.fmt_dt(b.starts_at, tz)}</b>\n{self.fmt_service(b.service)}"
        if b.payment_charge_id and not b.refunded:
            text += "\n" + self.DEPOSIT_PAID.format(stars=b.deposit_stars)
        return text

    # --- Buttons ---
    BTN_BOOK = "📅 Записаться"
    BTN_MY = "🗂 Мои записи"
    BTN_ADMIN = "⚙️ Панель мастера"
    BTN_HOME = "◀️ В меню"
    BTN_SERVICES = "◀️ Услуги"
    BTN_DAYS = "◀️ Дни"
    BTN_CONFIRM = "✅ Подтвердить"
    BTN_OTHER_TIME = "◀️ Другое время"
    BTN_TODAY = "📋 Записи на сегодня"
    BTN_WEEK = "🗓 Записи на неделю"
    BTN_ADMIN_SERVICES = "💈 Услуги"
    BTN_HOURS = "🕘 Рабочие часы"
    BTN_DEPOSIT = "⭐ Предоплата"
    BTN_ADMIN_BACK = "◀️ Панель мастера"
    BTN_ADD_SERVICE = "➕ Добавить услугу"

    # --- Commands ---
    CMD_START = "Записаться"
    CMD_PAYSUPPORT = "Вопросы по оплате"
    CMD_LANGUAGE = "Сменить язык"

    # --- Client ---
    WELCOME = (
        "Привет, {name}! 👋\n\n"
        "Я помогу записаться к мастеру за пару нажатий: выберите услугу, "
        "день и свободное время, а я напомню о визите заранее."
    )
    MAIN_MENU = "Что хотите сделать?"
    UNKNOWN = "Не понял 🙂 Воспользуйтесь кнопками меню."
    LANGUAGE_SET = "Готово, теперь я говорю по-русски 🇷🇺"

    NO_SERVICES = "Сейчас нет доступных услуг"
    CHOOSE_SERVICE = "Выберите услугу:"
    CHOOSE_DAY = "<b>{service}</b>\n\nВыберите день:"
    NO_DAYS = "На ближайшие две недели свободных окошек нет 😔"
    CHOOSE_TIME = (
        "<b>{service}</b>\n{day}\n\n"
        "<i>Услуга длится {duration} мин, мастер работает до {end}</i>\n\n"
        "Выберите время:"
    )
    NO_TIME = "На этот день время уже разобрали, выберите другой"
    CONFIRM = "Проверьте запись:\n\n<b>{dt}</b>\n{service}\n\nВсё верно?"
    SLOT_TAKEN = "Упс, это время только что заняли. Выберите другое 🙏"
    TOO_MANY_BOOKINGS = (
        "У вас уже {limit} предстоящие записи, это максимум. Отмените одну в «Мои "
        "записи», чтобы записаться снова."
    )
    BOOKED = (
        "✅ Вы записаны!\n\n{booking}\n\n"
        "Я напомню за день и за 2 часа до визита. Отменить запись можно в «Мои записи»."
    )

    # --- Deposit in Telegram Stars ---
    DEPOSIT_PAID = "⭐ Депозит {stars} оплачен"
    PAY_REQUIRED = (
        "⏳ Почти готово! Время удержано за вами на {minutes} мин.\n\n{booking}\n\n"
        "Чтобы подтвердить запись, оплатите депозит <b>{stars} ⭐</b> в сообщении ниже. "
        "Он защищает мастера от неявок. Если отмените запись не позже чем за {hours} ч "
        "до визита, депозит вернётся."
    )
    INVOICE_TITLE = "Депозит за запись"
    INVOICE_DESCRIPTION = "{service}, {dt}. Возвращается при отмене за 24 ч до визита."
    PAY_EXPIRED = "Время на оплату вышло, бронь снята. Запишитесь заново, пожалуйста."
    PAY_HOLD_EXPIRED = (
        "⌛ Депозит не был оплачен, и бронь снята:\n\n{booking}\n\nМожно записаться заново."
    )
    PAY_LATE_REFUNDED = (
        "Оплата пришла уже после того, как бронь была снята, поэтому мы вернули Stars. "
        "Запишитесь заново, пожалуйста."
    )
    PAYSUPPORT = (
        "По вопросам оплаты напишите мастеру в этот чат или нажмите /start → «Мои записи». "
        "Депозит возвращается автоматически при отмене не позже чем за 24 часа до визита "
        "или если запись отменил мастер."
    )
    CANCELLED_REFUNDED = "Запись отменена, депозит возвращён ⭐"
    CANCELLED_NO_REFUND = (
        "Запись отменена. До визита меньше 24 часов, поэтому депозит не возвращается."
    )
    DEPOSIT_RETURNED = "\n\nДепозит возвращён ⭐"

    MY_EMPTY = "У вас нет предстоящих записей."
    MY_LIST = "Ваши записи:\n\n{items}\n\nЧтобы отменить, нажмите на запись ниже."
    CANCELLED = "Запись отменена."
    CANT_CANCEL = "Эту запись уже нельзя отменить"

    REMIND_24H = "⏰ Напоминаем: завтра у вас запись\n\n{booking}"
    REMIND_2H = "⏰ Через 2 часа у вас запись\n\n{booking}"

    # --- Notifications to the master ---
    ADMIN_NEW = "🆕 Новая запись\n\n{booking}\nКлиент: {client}"
    ADMIN_CANCELLED_BY_CLIENT = "❌ Клиент отменил запись\n\n{booking}\nКлиент: {client}"
    CLIENT_CANCELLED_BY_ADMIN = (
        "❌ Мастер отменил вашу запись\n\n{booking}\n\nЗапишитесь на другое время 🙏"
    )

    # --- Admin panel ---
    ADMIN_MENU = "⚙️ Панель мастера"
    ADMIN_NO_BOOKINGS = "Записей нет."
    ADMIN_SERVICES = "Услуги:\n\n{items}\n\nНажмите 🗑, чтобы скрыть услугу."
    ADMIN_ASK_NAME = "Название новой услуги? (/cancel — отмена)"
    ADMIN_ASK_DURATION = "Длительность в минутах, кратно 30 (например, 60):"
    ADMIN_ASK_PRICE = "Цена (например, 1500):"
    ADMIN_BAD_NUMBER = "Нужно целое положительное число, попробуйте ещё раз"
    ADMIN_BAD_DURATION = "Длительность должна быть кратна 30 минутам"
    ADMIN_SERVICE_ADDED = "✅ Услуга добавлена"
    ADMIN_HOURS = "Рабочие часы:\n\n{items}\n\nВыберите день, чтобы изменить."
    ADMIN_ASK_HOURS = (
        "<b>{day}</b>\n\nОтправьте часы в формате <code>10:00-19:00</code> "
        "или <code>-</code> для выходного. /cancel — отмена"
    )
    ADMIN_BAD_HOURS = "Не понял формат. Пример: <code>10:00-19:00</code> или <code>-</code>"
    ADMIN_HOURS_SAVED = "✅ Часы сохранены"
    ADMIN_DEPOSIT_OFF_LABEL = "выключен"
    ADMIN_ASK_DEPOSIT = (
        "⭐ <b>Предоплата</b> (сейчас: {current})\n\n"
        "Клиент оплачивает депозит в Telegram Stars при записи, бронь подтверждается после "
        "оплаты. Так меньше неявок.\n\n"
        "Отправьте сумму в ⭐ (например, <code>50</code>) или <code>0</code>, чтобы выключить. "
        "/cancel — отмена"
    )
    ADMIN_BAD_DEPOSIT = "Нужно целое число от 0 до {max}"
    ADMIN_DEPOSIT_ON = "✅ Предоплата включена: {stars} ⭐"
    ADMIN_DEPOSIT_OFF = "✅ Предоплата выключена"
    ADMIN_CANCELLED = "Запись отменена, клиент получил уведомление."
    ACTION_CANCELLED = "Отменено."


class En(Ru):
    LANG = "en"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "📅 Book an appointment with your master in a few taps, with visit reminders"
    )
    BOT_DESCRIPTION = (
        "📅 SlotBook — online booking for appointments.\n\n• pick a service, a day "
        "and a free time\n• get reminders a day and 2 hours before the visit\n• "
        "cancel in one tap\n\nFor the master: a panel with bookings, services, "
        "working hours and prepayment in Telegram Stars.\n\nPress Start to book 👇"
    )
    WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    WEEKDAYS_FULL = (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )
    MONTHS = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    MIN = "min"
    DAY_OFF = "day off"

    BTN_BOOK = "📅 Book"
    BTN_MY = "🗂 My bookings"
    BTN_ADMIN = "⚙️ Master panel"
    BTN_HOME = "◀️ Menu"
    BTN_SERVICES = "◀️ Services"
    BTN_DAYS = "◀️ Days"
    BTN_CONFIRM = "✅ Confirm"
    BTN_OTHER_TIME = "◀️ Other time"
    BTN_TODAY = "📋 Today's bookings"
    BTN_WEEK = "🗓 This week's bookings"
    BTN_ADMIN_SERVICES = "💈 Services"
    BTN_HOURS = "🕘 Working hours"
    BTN_DEPOSIT = "⭐ Prepayment"
    BTN_ADMIN_BACK = "◀️ Master panel"
    BTN_ADD_SERVICE = "➕ Add a service"

    CMD_START = "Book an appointment"
    CMD_PAYSUPPORT = "Payment questions"
    CMD_LANGUAGE = "Change language"

    WELCOME = (
        "Hi, {name}! 👋\n\n"
        "I'll book you in with the master in a few taps: pick a service, a day and a free "
        "time, and I'll remind you about the visit in advance."
    )
    MAIN_MENU = "What would you like to do?"
    UNKNOWN = "Sorry, I didn't get that 🙂 Please use the menu buttons."
    LANGUAGE_SET = "Done, I speak English now 🇬🇧"

    NO_SERVICES = "No services are available right now"
    CHOOSE_SERVICE = "Choose a service:"
    CHOOSE_DAY = "<b>{service}</b>\n\nChoose a day:"
    NO_DAYS = "No free slots in the next two weeks 😔"
    CHOOSE_TIME = (
        "<b>{service}</b>\n{day}\n\n"
        "<i>The service takes {duration} min, the master works until {end}</i>\n\n"
        "Choose a time:"
    )
    NO_TIME = "This day is fully booked, please choose another"
    CONFIRM = "Check your booking:\n\n<b>{dt}</b>\n{service}\n\nIs everything correct?"
    SLOT_TAKEN = "Oops, someone just took this time. Please choose another 🙏"
    TOO_MANY_BOOKINGS = (
        "You already have {limit} upcoming bookings, that's the maximum. Cancel one "
        "in “My bookings” to book again."
    )
    BOOKED = (
        "✅ You're booked!\n\n{booking}\n\n"
        "I'll remind you a day and 2 hours before the visit. "
        "You can cancel in “My bookings”."
    )

    DEPOSIT_PAID = "⭐ Deposit of {stars} paid"
    PAY_REQUIRED = (
        "⏳ Almost done! The time is held for you for {minutes} min.\n\n{booking}\n\n"
        "To confirm the booking, pay a <b>{stars} ⭐</b> deposit in the message below. "
        "It protects the master from no-shows. If you cancel at least {hours} h before "
        "the visit, the deposit is returned."
    )
    INVOICE_TITLE = "Booking deposit"
    INVOICE_DESCRIPTION = "{service}, {dt}. Refunded if you cancel 24 h before the visit."
    PAY_EXPIRED = "The time to pay has run out and the hold was released. Please book again."
    PAY_HOLD_EXPIRED = (
        "⌛ The deposit wasn't paid, so the hold was released:\n\n{booking}\n\nYou can book again."
    )
    PAY_LATE_REFUNDED = (
        "The payment arrived after the hold had been released, so we refunded your Stars. "
        "Please book again."
    )
    PAYSUPPORT = (
        "For payment questions, write to the master in this chat or press /start → "
        "“My bookings”. The deposit is refunded automatically if you cancel at least 24 hours "
        "before the visit or if the master cancels."
    )
    CANCELLED_REFUNDED = "Booking cancelled, the deposit was refunded ⭐"
    CANCELLED_NO_REFUND = (
        "Booking cancelled. It's less than 24 hours before the visit, so the deposit "
        "isn't refunded."
    )
    DEPOSIT_RETURNED = "\n\nThe deposit was refunded ⭐"

    MY_EMPTY = "You have no upcoming bookings."
    MY_LIST = "Your bookings:\n\n{items}\n\nTo cancel, tap a booking below."
    CANCELLED = "Booking cancelled."
    CANT_CANCEL = "This booking can no longer be cancelled"

    REMIND_24H = "⏰ Reminder: you have a booking tomorrow\n\n{booking}"
    REMIND_2H = "⏰ Your booking is in 2 hours\n\n{booking}"

    ADMIN_NEW = "🆕 New booking\n\n{booking}\nClient: {client}"
    ADMIN_CANCELLED_BY_CLIENT = "❌ A client cancelled\n\n{booking}\nClient: {client}"
    CLIENT_CANCELLED_BY_ADMIN = (
        "❌ The master cancelled your booking\n\n{booking}\n\nPlease book another time 🙏"
    )

    ADMIN_MENU = "⚙️ Master panel"
    ADMIN_NO_BOOKINGS = "No bookings."
    ADMIN_SERVICES = "Services:\n\n{items}\n\nTap 🗑 to hide a service."
    ADMIN_ASK_NAME = "Name of the new service? (/cancel to abort)"
    ADMIN_ASK_DURATION = "Duration in minutes, a multiple of 30 (e.g. 60):"
    ADMIN_ASK_PRICE = "Price (e.g. 1500):"
    ADMIN_BAD_NUMBER = "A positive whole number is needed, please try again"
    ADMIN_BAD_DURATION = "The duration must be a multiple of 30 minutes"
    ADMIN_SERVICE_ADDED = "✅ Service added"
    ADMIN_HOURS = "Working hours:\n\n{items}\n\nChoose a day to change it."
    ADMIN_ASK_HOURS = (
        "<b>{day}</b>\n\nSend the hours as <code>10:00-19:00</code> "
        "or <code>-</code> for a day off. /cancel to abort"
    )
    ADMIN_BAD_HOURS = "Wrong format. Example: <code>10:00-19:00</code> or <code>-</code>"
    ADMIN_HOURS_SAVED = "✅ Hours saved"
    ADMIN_DEPOSIT_OFF_LABEL = "off"
    ADMIN_ASK_DEPOSIT = (
        "⭐ <b>Prepayment</b> (now: {current})\n\n"
        "The client pays a deposit in Telegram Stars when booking; the booking is confirmed "
        "after payment. This means fewer no-shows.\n\n"
        "Send the amount in ⭐ (e.g. <code>50</code>) or <code>0</code> to turn it off. "
        "/cancel to abort"
    )
    ADMIN_BAD_DEPOSIT = "A whole number from 0 to {max} is needed"
    ADMIN_DEPOSIT_ON = "✅ Prepayment is on: {stars} ⭐"
    ADMIN_DEPOSIT_OFF = "✅ Prepayment is off"
    ADMIN_CANCELLED = "Booking cancelled, the client has been notified."
    ACTION_CANCELLED = "Cancelled."


class Uk(Ru):
    LANG = "uk"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = (
        "📅 Онлайн-запис до майстра в кілька натискань, з нагадуваннями про візит"
    )
    BOT_DESCRIPTION = (
        "📅 SlotBook — онлайн-запис до майстра.\n\n• оберіть послугу, день і вільний "
        "час\n• нагадаю про візит за день і за 2 години\n• скасувати запис можна в "
        "один клік\n\nДля майстра: панель із записами, послугами, робочими годинами "
        "та передоплатою в Telegram Stars.\n\nНатисніть «Старт», щоб записатися 👇"
    )
    WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "нд")
    WEEKDAYS_FULL = ("Понеділок", "Вівторок", "Середа", "Четвер", "Пʼятниця", "Субота", "Неділя")
    MONTHS = (
        "січня",
        "лютого",
        "березня",
        "квітня",
        "травня",
        "червня",
        "липня",
        "серпня",
        "вересня",
        "жовтня",
        "листопада",
        "грудня",
    )
    MIN = "хв"
    DAY_OFF = "вихідний"

    BTN_BOOK = "📅 Записатися"
    BTN_MY = "🗂 Мої записи"
    BTN_ADMIN = "⚙️ Панель майстра"
    BTN_HOME = "◀️ До меню"
    BTN_SERVICES = "◀️ Послуги"
    BTN_DAYS = "◀️ Дні"
    BTN_CONFIRM = "✅ Підтвердити"
    BTN_OTHER_TIME = "◀️ Інший час"
    BTN_TODAY = "📋 Записи на сьогодні"
    BTN_WEEK = "🗓 Записи на тиждень"
    BTN_ADMIN_SERVICES = "💈 Послуги майстра"
    BTN_HOURS = "🕘 Робочі години"
    BTN_DEPOSIT = "⭐ Передоплата"
    BTN_ADMIN_BACK = "◀️ До панелі майстра"
    BTN_ADD_SERVICE = "➕ Додати послугу"

    CMD_START = "Записатися"
    CMD_PAYSUPPORT = "Питання щодо оплати"
    CMD_LANGUAGE = "Змінити мову"

    WELCOME = (
        "Привіт, {name}! 👋\n\n"
        "Я допоможу записатися до майстра за кілька натискань: оберіть послугу, "
        "день і вільний час, а я нагадаю про візит заздалегідь."
    )
    MAIN_MENU = "Що бажаєте зробити?"
    UNKNOWN = "Не зрозумів 🙂 Скористайтеся кнопками меню."
    LANGUAGE_SET = "Готово, тепер я розмовляю українською 🇺🇦"

    NO_SERVICES = "Зараз немає доступних послуг"
    CHOOSE_SERVICE = "Оберіть послугу:"
    CHOOSE_DAY = "<b>{service}</b>\n\nОберіть день:"
    NO_DAYS = "На найближчі два тижні вільних віконець немає 😔"
    CHOOSE_TIME = (
        "<b>{service}</b>\n{day}\n\n"
        "<i>Послуга триває {duration} хв, майстер працює до {end}</i>\n\n"
        "Оберіть час:"
    )
    NO_TIME = "На цей день час уже розібрали, оберіть інший"
    CONFIRM = "Перевірте запис:\n\n<b>{dt}</b>\n{service}\n\nУсе правильно?"
    SLOT_TAKEN = "Йой, цей час щойно зайняли. Оберіть інший 🙏"
    TOO_MANY_BOOKINGS = (
        "У вас уже {limit} майбутні записи, це максимум. Скасуйте один у «Мої "
        "записи», щоб записатися знову."
    )
    BOOKED = (
        "✅ Ви записані!\n\n{booking}\n\n"
        "Я нагадаю за день і за 2 години до візиту. Скасувати запис можна в «Мої записи»."
    )

    DEPOSIT_PAID = "⭐ Депозит {stars} сплачено"
    PAY_REQUIRED = (
        "⏳ Майже готово! Час закріплено за вами на {minutes} хв.\n\n{booking}\n\n"
        "Щоб підтвердити запис, сплатіть депозит <b>{stars} ⭐</b> у повідомленні нижче. "
        "Він захищає майстра від неявок. Якщо скасуєте запис не пізніше ніж за {hours} год "
        "до візиту, депозит повернеться."
    )
    INVOICE_TITLE = "Депозит за запис"
    INVOICE_DESCRIPTION = "{service}, {dt}. Повертається при скасуванні за 24 год до візиту."
    PAY_EXPIRED = "Час на оплату минув, бронь знято. Запишіться, будь ласка, ще раз."
    PAY_HOLD_EXPIRED = (
        "⌛ Депозит не було сплачено, тож бронь знято:\n\n{booking}\n\nМожна записатися знову."
    )
    PAY_LATE_REFUNDED = (
        "Оплата надійшла вже після того, як бронь знято, тому ми повернули Stars. "
        "Запишіться, будь ласка, ще раз."
    )
    PAYSUPPORT = (
        "З питань оплати напишіть майстру в цей чат або натисніть /start → «Мої записи». "
        "Депозит повертається автоматично, якщо скасувати запис не пізніше ніж за 24 години "
        "до візиту або якщо запис скасував майстер."
    )
    CANCELLED_REFUNDED = "Запис скасовано, депозит повернуто ⭐"
    CANCELLED_NO_REFUND = "Запис скасовано. До візиту менше 24 годин, тому депозит не повертається."
    DEPOSIT_RETURNED = "\n\nДепозит повернуто ⭐"

    MY_EMPTY = "У вас немає майбутніх записів."
    MY_LIST = "Ваші записи:\n\n{items}\n\nЩоб скасувати, натисніть на запис нижче."
    CANCELLED = "Запис скасовано."
    CANT_CANCEL = "Цей запис уже не можна скасувати"

    REMIND_24H = "⏰ Нагадуємо: завтра у вас запис\n\n{booking}"
    REMIND_2H = "⏰ За 2 години у вас запис\n\n{booking}"

    ADMIN_NEW = "🆕 Новий запис\n\n{booking}\nКлієнт: {client}"
    ADMIN_CANCELLED_BY_CLIENT = "❌ Клієнт скасував запис\n\n{booking}\nКлієнт: {client}"
    CLIENT_CANCELLED_BY_ADMIN = (
        "❌ Майстер скасував ваш запис\n\n{booking}\n\nЗапишіться, будь ласка, на інший час 🙏"
    )

    ADMIN_MENU = "⚙️ Панель майстра"
    ADMIN_NO_BOOKINGS = "Записів немає."
    ADMIN_SERVICES = "Послуги:\n\n{items}\n\nНатисніть 🗑, щоб приховати послугу."
    ADMIN_ASK_NAME = "Назва нової послуги? (/cancel — скасувати)"
    ADMIN_ASK_DURATION = "Тривалість у хвилинах, кратна 30 (наприклад, 60):"
    ADMIN_ASK_PRICE = "Ціна (наприклад, 1500):"
    ADMIN_BAD_NUMBER = "Потрібне ціле додатне число, спробуйте ще раз"
    ADMIN_BAD_DURATION = "Тривалість має бути кратною 30 хвилинам"
    ADMIN_SERVICE_ADDED = "✅ Послугу додано"
    ADMIN_HOURS = "Робочі години:\n\n{items}\n\nОберіть день, щоб змінити."
    ADMIN_ASK_HOURS = (
        "<b>{day}</b>\n\nНадішліть години у форматі <code>10:00-19:00</code> "
        "або <code>-</code> для вихідного. /cancel — скасувати"
    )
    ADMIN_BAD_HOURS = "Не зрозумів формат. Приклад: <code>10:00-19:00</code> або <code>-</code>"
    ADMIN_HOURS_SAVED = "✅ Години збережено"
    ADMIN_DEPOSIT_OFF_LABEL = "вимкнено"
    ADMIN_ASK_DEPOSIT = (
        "⭐ <b>Передоплата</b> (зараз: {current})\n\n"
        "Клієнт сплачує депозит у Telegram Stars під час запису, бронь підтверджується після "
        "оплати. Так менше неявок.\n\n"
        "Надішліть суму в ⭐ (наприклад, <code>50</code>) або <code>0</code>, щоб вимкнути. "
        "/cancel — скасувати"
    )
    ADMIN_BAD_DEPOSIT = "Потрібне ціле число від 0 до {max}"
    ADMIN_DEPOSIT_ON = "✅ Передоплату ввімкнено: {stars} ⭐"
    ADMIN_DEPOSIT_OFF = "✅ Передоплату вимкнено"
    ADMIN_CANCELLED = "Запис скасовано, клієнт отримав сповіщення."
    ACTION_CANCELLED = "Скасовано."


class Pl(Ru):
    LANG = "pl"
    # Telegram profile: shown before Start (<=512) and in the profile (<=120)
    BOT_SHORT_DESCRIPTION = "📅 Umów wizytę u specjalisty w kilku kliknięciach, z przypomnieniami"
    BOT_DESCRIPTION = (
        "📅 SlotBook — rezerwacja wizyt online.\n\n• wybierz usługę, dzień i wolną "
        "godzinę\n• przypomnę o wizycie dzień i 2 godziny wcześniej\n• wizytę "
        "odwołasz jednym kliknięciem\n\nDla specjalisty: panel z wizytami, usługami, "
        "godzinami pracy i przedpłatą w Telegram Stars.\n\nNaciśnij „Start”, aby się "
        "umówić 👇"
    )
    WEEKDAYS = ("pon", "wt", "śr", "czw", "pt", "sob", "niedz")
    WEEKDAYS_FULL = (
        "Poniedziałek",
        "Wtorek",
        "Środa",
        "Czwartek",
        "Piątek",
        "Sobota",
        "Niedziela",
    )
    MONTHS = (
        "stycznia",
        "lutego",
        "marca",
        "kwietnia",
        "maja",
        "czerwca",
        "lipca",
        "sierpnia",
        "września",
        "października",
        "listopada",
        "grudnia",
    )
    MIN = "min"
    DAY_OFF = "wolne"

    BTN_BOOK = "📅 Umów wizytę"
    BTN_MY = "🗂 Moje wizyty"
    BTN_ADMIN = "⚙️ Panel specjalisty"
    BTN_HOME = "◀️ Menu"
    BTN_SERVICES = "◀️ Usługi"
    BTN_DAYS = "◀️ Dni"
    BTN_CONFIRM = "✅ Potwierdź"
    BTN_OTHER_TIME = "◀️ Inna godzina"
    BTN_TODAY = "📋 Wizyty na dziś"
    BTN_WEEK = "🗓 Wizyty w tym tygodniu"
    BTN_ADMIN_SERVICES = "💈 Usługi specjalisty"
    BTN_HOURS = "🕘 Godziny pracy"
    BTN_DEPOSIT = "⭐ Przedpłata"
    BTN_ADMIN_BACK = "◀️ Panel specjalisty"
    BTN_ADD_SERVICE = "➕ Dodaj usługę"

    CMD_START = "Umów wizytę"
    CMD_PAYSUPPORT = "Pytania o płatność"
    CMD_LANGUAGE = "Zmień język"

    WELCOME = (
        "Cześć, {name}! 👋\n\n"
        "Pomogę Ci umówić wizytę u specjalisty w kilku kliknięciach: wybierz usługę, dzień "
        "i wolną godzinę, a ja przypomnę Ci o wizycie z wyprzedzeniem."
    )
    MAIN_MENU = "Co chcesz zrobić?"
    UNKNOWN = "Nie rozumiem 🙂 Skorzystaj z przycisków menu."
    LANGUAGE_SET = "Gotowe, teraz mówię po polsku 🇵🇱"

    NO_SERVICES = "Obecnie brak dostępnych usług"
    CHOOSE_SERVICE = "Wybierz usługę:"
    CHOOSE_DAY = "<b>{service}</b>\n\nWybierz dzień:"
    NO_DAYS = "Brak wolnych terminów w ciągu najbliższych dwóch tygodni 😔"
    CHOOSE_TIME = (
        "<b>{service}</b>\n{day}\n\n"
        "<i>Usługa trwa {duration} min, specjalista pracuje do {end}</i>\n\n"
        "Wybierz godzinę:"
    )
    NO_TIME = "Ten dzień jest już zajęty, wybierz inny"
    CONFIRM = "Sprawdź wizytę:\n\n<b>{dt}</b>\n{service}\n\nWszystko się zgadza?"
    SLOT_TAKEN = "Ups, ktoś właśnie zajął ten termin. Wybierz inny 🙏"
    TOO_MANY_BOOKINGS = (
        "Masz już {limit} nadchodzące wizyty, to maksimum. Odwołaj jedną w „Moje "
        "wizyty”, aby umówić się ponownie."
    )
    BOOKED = (
        "✅ Wizyta umówiona!\n\n{booking}\n\n"
        "Przypomnę Ci dzień i 2 godziny przed wizytą. Odwołać możesz w „Moje wizyty”."
    )

    DEPOSIT_PAID = "⭐ Zadatek {stars} opłacony"
    PAY_REQUIRED = (
        "⏳ Prawie gotowe! Termin jest zarezerwowany dla Ciebie na {minutes} min.\n\n"
        "{booking}\n\n"
        "Aby potwierdzić wizytę, opłać zadatek <b>{stars} ⭐</b> w wiadomości poniżej. "
        "Chroni on specjalistę przed nieobecnościami. Jeśli odwołasz wizytę co najmniej "
        "{hours} godz. wcześniej, zadatek wróci do Ciebie."
    )
    INVOICE_TITLE = "Zadatek za wizytę"
    INVOICE_DESCRIPTION = "{service}, {dt}. Zwrot przy odwołaniu 24 godz. przed wizytą."
    PAY_EXPIRED = "Czas na płatność minął i rezerwacja została zwolniona. Umów się ponownie."
    PAY_HOLD_EXPIRED = (
        "⌛ Zadatek nie został opłacony, więc rezerwacja została zwolniona:\n\n{booking}\n\n"
        "Możesz umówić się ponownie."
    )
    PAY_LATE_REFUNDED = (
        "Płatność dotarła już po zwolnieniu rezerwacji, więc zwróciliśmy Twoje Stars. "
        "Umów się ponownie."
    )
    PAYSUPPORT = (
        "W sprawie płatności napisz do specjalisty w tym czacie lub naciśnij /start → "
        "„Moje wizyty”. Zadatek jest zwracany automatycznie, jeśli odwołasz wizytę co najmniej "
        "24 godziny wcześniej lub jeśli odwoła ją specjalista."
    )
    CANCELLED_REFUNDED = "Wizyta odwołana, zadatek zwrócony ⭐"
    CANCELLED_NO_REFUND = (
        "Wizyta odwołana. Do wizyty zostało mniej niż 24 godziny, więc zadatek nie jest zwracany."
    )
    DEPOSIT_RETURNED = "\n\nZadatek został zwrócony ⭐"

    MY_EMPTY = "Nie masz nadchodzących wizyt."
    MY_LIST = "Twoje wizyty:\n\n{items}\n\nAby odwołać, naciśnij wizytę poniżej."
    CANCELLED = "Wizyta odwołana."
    CANT_CANCEL = "Tej wizyty nie można już odwołać"

    REMIND_24H = "⏰ Przypomnienie: jutro masz wizytę\n\n{booking}"
    REMIND_2H = "⏰ Twoja wizyta za 2 godziny\n\n{booking}"

    ADMIN_NEW = "🆕 Nowa wizyta\n\n{booking}\nKlient: {client}"
    ADMIN_CANCELLED_BY_CLIENT = "❌ Klient odwołał wizytę\n\n{booking}\nKlient: {client}"
    CLIENT_CANCELLED_BY_ADMIN = (
        "❌ Specjalista odwołał Twoją wizytę\n\n{booking}\n\nUmów się na inny termin 🙏"
    )

    ADMIN_MENU = "⚙️ Panel specjalisty"
    ADMIN_NO_BOOKINGS = "Brak wizyt."
    ADMIN_SERVICES = "Usługi:\n\n{items}\n\nNaciśnij 🗑, aby ukryć usługę."
    ADMIN_ASK_NAME = "Nazwa nowej usługi? (/cancel — anuluj)"
    ADMIN_ASK_DURATION = "Czas trwania w minutach, wielokrotność 30 (np. 60):"
    ADMIN_ASK_PRICE = "Cena (np. 1500):"
    ADMIN_BAD_NUMBER = "Potrzebna jest dodatnia liczba całkowita, spróbuj ponownie"
    ADMIN_BAD_DURATION = "Czas trwania musi być wielokrotnością 30 minut"
    ADMIN_SERVICE_ADDED = "✅ Usługa dodana"
    ADMIN_HOURS = "Godziny pracy:\n\n{items}\n\nWybierz dzień, aby go zmienić."
    ADMIN_ASK_HOURS = (
        "<b>{day}</b>\n\nWyślij godziny w formacie <code>10:00-19:00</code> "
        "lub <code>-</code>, jeśli to dzień wolny. /cancel — anuluj"
    )
    ADMIN_BAD_HOURS = "Nieprawidłowy format. Przykład: <code>10:00-19:00</code> lub <code>-</code>"
    ADMIN_HOURS_SAVED = "✅ Godziny zapisane"
    ADMIN_DEPOSIT_OFF_LABEL = "wyłączona"
    ADMIN_ASK_DEPOSIT = (
        "⭐ <b>Przedpłata</b> (teraz: {current})\n\n"
        "Klient płaci zadatek w Telegram Stars przy rezerwacji, wizyta jest potwierdzana po "
        "płatności. Dzięki temu jest mniej nieobecności.\n\n"
        "Wyślij kwotę w ⭐ (np. <code>50</code>) lub <code>0</code>, aby wyłączyć. "
        "/cancel — anuluj"
    )
    ADMIN_BAD_DEPOSIT = "Potrzebna jest liczba całkowita od 0 do {max}"
    ADMIN_DEPOSIT_ON = "✅ Przedpłata włączona: {stars} ⭐"
    ADMIN_DEPOSIT_OFF = "✅ Przedpłata wyłączona"
    ADMIN_CANCELLED = "Wizyta odwołana, klient otrzymał powiadomienie."
    ACTION_CANCELLED = "Anulowano."


TEXTS: dict[str, Ru] = {"uk": Uk(), "ru": Ru(), "pl": Pl(), "en": En()}
