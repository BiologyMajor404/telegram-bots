"""Logging format shared by all bots."""

import logging


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    # aiogram logs every update at INFO, which is too noisy
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
