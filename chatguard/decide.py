"""Combine the rules and the AI into one decision."""

from dataclasses import dataclass

from chatguard.ai import AiVerdict, Classifier
from chatguard.rules import RulesVerdict


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
    ai_allowed: bool,
    allow_opus: bool = False,
) -> Decision:
    if rules.is_spam:
        return Decision(True, "rules", rules=rules)
    if rules.is_clean or classifier is None or not ai_allowed:
        # Without the AI only clear-cut rule hits count; doubtful messages pass
        return Decision(False, "none", rules=rules)
    verdict: AiVerdict | None = await classifier.classify(
        text, lang, rules.reasons, allow_opus=allow_opus
    )
    if verdict is None:
        return Decision(False, "none", rules=rules)
    return Decision(verdict.is_spam, verdict.model, verdict.reason, rules=rules)
