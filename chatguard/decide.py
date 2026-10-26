"""Combine the rules and the AI into one decision."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from chatguard.ai import CONFIDENT, AiVerdict, Classifier
from chatguard.rules import RulesVerdict

# Haiku alone must be as sure as it has to be to skip Opus; Opus is the final word
# but still shouldn't act on a coin flip
MIN_SPAM_CONFIDENCE = {"haiku": CONFIDENT, "opus": 65}


@dataclass
class Decision:
    is_spam: bool
    source: str  # rules | haiku | opus | none
    reason: str = ""  # AI explanation; for rules the handler shows the matched signals
    rules: RulesVerdict | None = None


async def decide(
    text: str,
    rules: RulesVerdict,
    lang: str,
    classifier: Classifier | None,
    reserve_ai: Callable[[], Awaitable[bool]],
    allow_opus: bool = False,
) -> Decision:
    """`reserve_ai` takes one AI check from the budgets; it's called only when the AI is
    really needed, so clear-cut messages never use the budget."""
    if rules.is_spam:
        return Decision(True, "rules", rules=rules)
    if rules.is_clean or classifier is None or not await reserve_ai():
        # Without the AI only clear-cut rule hits count; doubtful messages pass
        return Decision(False, "none", rules=rules)
    verdict: AiVerdict | None = await classifier.classify(
        text, lang, rules.reasons, allow_opus=allow_opus
    )
    if verdict is None:
        return Decision(False, "none", rules=rules)
    # Removing a real person is worse than missing one ad: an unsure "spam" doesn't count
    is_spam = verdict.is_spam and verdict.confidence >= MIN_SPAM_CONFIDENCE[verdict.model]
    return Decision(is_spam, verdict.model, verdict.reason, rules=rules)
