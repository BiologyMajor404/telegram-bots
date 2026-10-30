"""Logging format shared by all bots."""

import logging
import re

# A bot token, e.g. inside an API URL that a network error quotes: .../bot123456:AAH.../getMe
BOT_TOKEN = re.compile(r"\d{6,}:[\w-]{30,}")


class RedactingFormatter(logging.Formatter):
    """Masks bot tokens in messages and tracebacks before they reach the log."""

    def format(self, record: logging.LogRecord) -> str:
        return BOT_TOKEN.sub("<token>", super().format(record))


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(RedactingFormatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s"))
    logging.basicConfig(level=level.upper(), handlers=[handler])
    # aiogram logs every update at INFO, which is too noisy
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
