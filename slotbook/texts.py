"""User-facing texts and formatting. Kept in one place to make translation easy."""

from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

from slotbook.models import Booking, Service

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


def fmt_day(d: date) -> str:
    return f"{WEEKDAYS[d.weekday()]}, {d.day} {MONTHS[d.month - 1]}"


def fmt_dt(dt: datetime, tz: ZoneInfo) -> str:
    local = dt.astimezone(tz)
    return f"{fmt_day(local.date())}, {local:%H:%M}"


def fmt_service(s: Service) -> str:
    return f"{escape(s.name)} · {s.duration_min} мин · {s.price} ₽"


def user_link(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'


def fmt_booking(b: Booking, tz: ZoneInfo) -> str:
    return f"<b>{fmt_dt(b.starts_at, tz)}</b>\n{fmt_service(b.service)}"


WELCOME = (
    "Привет, {name}! 👋\n\n"
    "Я помогу записаться к мастеру за пару нажатий: выберите услугу, "
    "день и свободное время, а я напомню о визите заранее."
)
MAIN_MENU = "Что хотите сделать?"
UNKNOWN = "Не понял 🙂 Воспользуйтесь кнопками меню."

NO_SERVICES = "Сейчас нет доступных услуг"
CHOOSE_SERVICE = "Выберите услугу:"
CHOOSE_DAY = "<b>{service}</b>\n\nВыберите день:"
NO_DAYS = "На ближайшие две недели свободных окошек нет 😔"
CHOOSE_TIME = "<b>{service}</b>\n{day}\n\nВыберите время:"
NO_TIME = "На этот день время уже разобрали, выберите другой"
CONFIRM = "Проверьте запись:\n\n<b>{dt}</b>\n{service}\n\nВсё верно?"
SLOT_TAKEN = "Упс, это время только что заняли. Выберите другое 🙏"
BOOKED = (
    "✅ Вы записаны!\n\n{booking}\n\n"
    "Я напомню за день и за 2 часа до визита. Отменить запись можно в «Мои записи»."
)

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
ADMIN_CANCELLED = "Запись отменена, клиент получил уведомление."
ACTION_CANCELLED = "Отменено."
