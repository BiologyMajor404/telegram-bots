# Telegram Bots Portfolio

A set of production-style Telegram bots that solve real everyday problems.
All bots share one core (config, database, logging, middlewares) and run with a single `docker compose up`.

| Bot | What it does | Status |
|---|---|---|
| 💈 **[SlotBook](#-slotbook)** · [@slotbook_nl_bot](https://t.me/slotbook_nl_bot) | Online booking for barbers, nail masters, tutors | 🟢 MVP |
| 🛡 **ChatGuard AI** · [@chatguard_nl_bot](https://t.me/chatguard_nl_bot) | AI anti-spam moderator for group chats | 🔜 Planned |
| 💸 **[SplitMates](#-splitmates)** · [@splitmate_nl_bot](https://t.me/splitmate_nl_bot) | "Who owes whom" for trips and shared purchases, right in the group chat | 🟢 MVP |

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
- Turn on a **deposit in Telegram Stars** to cut no-shows

**Deposit in Telegram Stars ⭐**
- The client pays the deposit right in the chat; the slot is held for 15 minutes and released automatically if unpaid
- The booking is confirmed (and the master notified) only after a successful payment
- Fair refunds: the deposit returns automatically if the client cancels 24+ hours ahead or the master cancels
- Edge cases handled: hold expiring between the pre-checkout check and the payment triggers an automatic refund
- `/paysupport` command as required by Telegram for bots that accept Stars

> Stars are used here because they work without a merchant account, which is ideal for a demo.
> For a real offline business (a haircut is a physical service) the same flow should run through a
> payment provider such as ЮKassa or Stripe, per Telegram's payment rules.

### Engineering details
- **No double booking:** the slot is re-validated inside a transaction guarded by a PostgreSQL advisory lock, so two clients can't grab the same time
- **Timezone-correct:** all times are stored in UTC and shown in the master's timezone
- **Stateless booking flow:** every step is encoded in compact callback data (Telegram's 64-byte limit), so the flow survives restarts. FSM (stored in Redis) is used only for multi-step admin forms
- **Pure, unit-tested slot engine** ([`slotbook/slots.py`](slotbook/slots.py)) separated from the DB and Telegram layers
- **Schema migrations with Alembic** run automatically on startup; databases created before migrations existed are detected and stamped
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
  payments.py       # Stars invoice, refund policy, refunds
  repo.py           # all DB queries
  handlers/         # client.py, admin.py, payments.py
  reminders.py      # background jobs: reminders, releasing unpaid holds
  migrations/       # Alembic revisions
  keyboards.py, texts.py
splitmate/
  money.py          # pure money math: parse, split, balances, settle-up
  repo.py           # all DB queries
  handlers/         # group.py, inline.py, private.py
  migrations/       # Alembic revisions
tests/              # pytest
docker-compose.yml  # Postgres, Redis and the bots
```

---

## 💸 SplitMates

Trips, flatmates, a birthday gift: someone always pays, and nobody remembers who owes what.
Apps like Splitwise need everyone to install them, so in practice nobody does. SplitMates lives in the
group chat that already exists.

### Features
- **Add expenses in two ways:** `/add 3000 такси` or straight from the input field with inline mode: `@splitmate_nl_bot 3000 такси`
- Split equally between everyone who pressed **🙋 Я участвую**; the payer can pick who took part with toggle buttons
- **`/balance`** shows each person's balance and the **minimal set of transfers** to settle up
- One tap marks a debt as returned; only the payer or the receiver can confirm it
- History, per-chat currency, delete your own expenses

### Engineering details
- Money is stored in **integer minor units** (kopecks), never floats; equal splits distribute the remainder so shares always add up exactly
- **Settle-up algorithm** ([`splitmate/money.py`](splitmate/money.py)): greedy matching of the largest debtor with the largest creditor, at most *n − 1* transfers
- **Inline mode without knowing the chat:** Telegram doesn't tell the bot where an inline result was sent, so the bot records the expense when it sees the message posted *via itself* in a group (works even with privacy mode on)
- Settling uses the **current** balance, not the amount baked into an old button, so stale buttons can't create wrong records
- Pure functions covered by unit tests; DB logic checked against Postgres

---

## 🚀 Quick start

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Copy the env template and fill it in:
   ```bash
   cp .env.example .env
   ```
   - `SLOTBOOK_TOKEN`: the token from BotFather
   - `SLOTBOOK_ADMIN_IDS`: your Telegram user ID (ask [@userinfobot](https://t.me/userinfobot))
   - `SPLITMATE_TOKEN`: the token of the second bot; enable inline mode for it in BotFather (`/setinline`)
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

### Self-hosting on a Windows PC
The bots use long polling, so they run on any always-on computer: no public IP, domain or open ports needed.
To survive Docker Desktop crashes and reboots, register the watchdog once:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-watchdog.ps1
```
Every 5 minutes it starts Docker Desktop if needed, restarts it if the engine hangs, and brings back
any stopped service. Events go to `logs/watchdog.log`.

### Tests and linting
```bash
pytest
ruff check .
```

## 🗺 Roadmap
- [ ] SlotBook: Telegram Mini App with a calendar view
- [x] SlotBook: prepayment via Telegram Stars to reduce no-shows
- [ ] SlotBook: Google Calendar sync
- [ ] ChatGuard AI: LLM-based spam detection with explanations for admins
- [x] SplitMates: inline expense entry, minimal settle-up transfers
- [ ] SplitMates Pro (Telegram Stars): receipt photo recognition, export to Excel, unequal splits
- [ ] Webhooks + deployment guide

## 📄 License

© 2026 BiologyMajor404. All rights reserved. The code is published for portfolio review only. See [LICENSE](LICENSE).
Want a bot like this for your business? [Contact me on GitHub](https://github.com/BiologyMajor404).
