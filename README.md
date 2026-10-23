# Telegram Bots Portfolio

A set of production-style Telegram bots that solve real everyday problems.
All bots share one core (config, database, logging, middlewares) and run with a single `docker compose up`.

| Bot | What it does | Status |
|---|---|---|
| 💈 **[SlotBook](#-slotbook)** · [@slotbook_nl_bot](https://t.me/slotbook_nl_bot) | Online booking for barbers, nail masters, tutors | 🟢 MVP |
| 🛡 **ChatGuard AI** · [@chatguard_nl_bot](https://t.me/chatguard_nl_bot) | AI anti-spam moderator for group chats | 🔜 Planned |
| 💸 **SplitMate** · [@splitmate_nl_bot](https://t.me/splitmate_nl_bot) | "Who owes whom" for trips and shared purchases, right in the group chat | 🔜 Planned |

**Stack:** Python 3.14 · aiogram 3 · SQLAlchemy 2 (async) · PostgreSQL · Redis · Docker · pytest · GitHub Actions

---

## 💈 SlotBook

Solo specialists usually take bookings in DMs and keep them in a notebook, and full CRM systems are too
expensive and complex for one person. SlotBook gives clients a 3-tap booking flow, and the master gets a
panel to manage everything without leaving Telegram.

### Features

**For clients**
- Pick a service → a day → a free time slot, all with inline buttons
- Only days and times that are really free are shown, based on working hours, service duration and existing bookings
- Automatic reminders **24 hours** and **2 hours** before the visit
- "My bookings" with one-tap cancellation

**For the master** (`/admin` or the button in the menu)
- Bookings for today / the week, grouped by day, with client contact links
- Instant notifications about new and cancelled bookings
- Add and hide services (name, duration, price)
- Edit working hours per weekday, including days off
- Cancel a booking, and the client is notified automatically

### Engineering details
- **No double booking:** the slot is re-validated inside a transaction guarded by a PostgreSQL advisory lock, so two clients can't grab the same time
- **Timezone-correct:** all times are stored in UTC and shown in the master's timezone
- **Stateless booking flow:** every step is encoded in compact callback data (Telegram's 64-byte limit), so the flow survives restarts. FSM (stored in Redis) is used only for multi-step admin forms
- **Pure, unit-tested slot engine** ([`slotbook/slots.py`](slotbook/slots.py)) separated from the DB and Telegram layers
- Demo data (services + working hours) is seeded on the first run, so the bot is usable immediately

### Project structure
```
shared/             # code reused by every bot
  config.py         #   settings from .env (pydantic-settings)
  db.py             #   async SQLAlchemy engine + session factory
  middlewares.py    #   DB session per update
  storage.py        #   Redis FSM storage
  notify.py         #   safe sending (ignores users who blocked the bot)
slotbook/
  models.py         # Service, WorkDay, Booking
  slots.py          # pure slot calculation
  scheduling.py     # free days/slots, safe booking
  repo.py           # all DB queries
  handlers/         # client.py, admin.py
  reminders.py      # background reminder loop
  keyboards.py, texts.py
tests/              # pytest
docker-compose.yml  # Postgres, Redis and the bots
```

---

## 🚀 Quick start

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Copy the env template and fill it in:
   ```bash
   cp .env.example .env
   ```
   - `SLOTBOOK_TOKEN`: the token from BotFather
   - `SLOTBOOK_ADMIN_IDS`: your Telegram user ID (ask [@userinfobot](https://t.me/userinfobot))
3. Run everything:
   ```bash
   docker compose up -d --build
   ```
4. Open the bot in Telegram and press **Start**.

### Local development
```bash
docker compose up -d postgres redis      # only the infrastructure
python -m venv .venv && .venv/Scripts/activate   # Windows; on Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m slotbook
```

### Tests and linting
```bash
pytest
ruff check .
```

## 🗺 Roadmap
- [ ] SlotBook: Telegram Mini App with a calendar view
- [ ] SlotBook: prepayment via Telegram Stars to reduce no-shows
- [ ] SlotBook: Google Calendar sync
- [ ] ChatGuard AI: LLM-based spam detection with explanations for admins
- [ ] SplitMate: inline expense entry, receipt photo recognition, minimal settle-up transfers
- [ ] Webhooks + deployment guide
