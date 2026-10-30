"""Conversation states: what the bot expects the next message to be."""

from aiogram.fsm.state import State, StatesGroup


class AddSearch(StatesGroup):
    waiting = State()  # the next text is a new search
