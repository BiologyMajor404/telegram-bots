"""Inline mode: type `@bot 3000 такси` in any chat's input field to post an expense."""

import hashlib
from html import escape

from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
)

from splitmate.handlers.group import INLINE_PREFIX
from splitmate.money import fmt_money, parse_amount
from splitmate.texts import Ru

router = Router(name="inline")


def plain_amount(minor: int) -> str:
    """125050 -> '1250,50': a form parse_amount reads back unambiguously."""
    whole, frac = divmod(minor, 100)
    return f"{whole},{frac:02d}" if frac else str(whole)


def expense_message(amount: int, description: str) -> str:
    """The text posted to the group, which the group handler parses back. It goes out as
    HTML, like all the bot's messages: "300 pizza <3" must stay text, not become markup."""
    return f"{INLINE_PREFIX}{plain_amount(amount)} {escape(description)}".strip()


@router.inline_query()
async def inline_expense(query: InlineQuery, t: Ru) -> None:
    help_button = InlineQueryResultsButton(text=t.INLINE_HELP_BUTTON, start_parameter="help")
    parsed = parse_amount(query.query)
    if parsed is None:
        await query.answer([], cache_time=0, is_personal=True, button=help_button)
        return
    amount, description = parsed
    message = expense_message(amount, description)
    result = InlineQueryResultArticle(
        id=hashlib.md5(message.encode()).hexdigest(),
        title=t.INLINE_TITLE.format(amount=fmt_money(amount, "").strip()),
        description=t.INLINE_DESCRIPTION.format(
            description=f"{description}. " if description else ""
        ),
        input_message_content=InputTextMessageContent(message_text=message),
    )
    await query.answer([result], cache_time=0, is_personal=True, button=help_button)
