"""User-facing texts and formatting, one class per language.
English subclasses Russian; tests check that it overrides every text."""

from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

from slotbook.models import Booking, Service


def user_link(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'


class Ru:
    LANG = "ru"
    WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    WEEKDAYS_FULL = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ]
    MONTHS = [
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
    ]
    MIN = "мин"
    DAY_OFF = "выходной"

    def fmt_day(self, d: date) -> str:
        return f"{self.WEEKDAYS[d.weekday()]}, {d.day} {self.MONTHS[d.month - 1]}"

    def fmt_dt(self, dt: datetime, tz: ZoneInfo) -> str:
        local = dt.astimezone(tz)
        return f"{self.fmt_day(local.date())}, {local:%H:%M}"

    def fmt_service(self, s: Service) -> str:
        return f"{escape(s.name)} · {s.duration_min} {self.MIN} · {s.price} ₽"

    def fmt_booking(self, b: Booking, tz: ZoneInfo) -> str:
        text = f"<b>{self.fmt_dt(b.starts_at, tz)}</b>\n{self.fmt_service(b.service)}"
        if b.payment_charge_id and not b.refunded:
            text += "\n" + self.DEPOSIT_PAID.format(stars=b.deposit_stars)
        return text

    # --- Buttons ---
    BTN_BOOK = "📅 Записаться"
    BTN_MY = "🗂 Мои записи"
    BTN_ADMIN = "⚙️ Панель мастера"
    BTN_LANGUAGE = "🌐 Language / Язык"
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
    CHOOSE_LANGUAGE = "Выберите язык / Choose language:"
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
    ADMIN_ASK_PRICE = "Цена в рублях (например, 1500):"
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
    WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    WEEKDAYS_FULL = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    MONTHS = [
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
    ]
    MIN = "min"
    DAY_OFF = "day off"

    BTN_BOOK = "📅 Book"
    BTN_MY = "🗂 My bookings"
    BTN_ADMIN = "⚙️ Master panel"
    BTN_LANGUAGE = "🌐 Language / Язык"
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
    CHOOSE_LANGUAGE = "Choose language / Выберите язык:"
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
    ADMIN_ASK_PRICE = "Price in rubles (e.g. 1500):"
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


TEXTS: dict[str, Ru] = {"ru": Ru(), "en": En()}
