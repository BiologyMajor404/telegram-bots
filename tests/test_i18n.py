"""Every English text class must translate every text of its Russian base class,
otherwise a forgotten string would silently show up in Russian."""

import pytest

from shared.i18n import detect
from slotbook import texts as slotbook_texts
from splitmate import texts as splitmate_texts

# Things that are the same in both languages on purpose
SAME_IN_BOTH = {"BTN_LANGUAGE"}


def translatable(cls: type) -> dict[str, object]:
    return {k: v for k, v in vars(cls).items() if k.isupper() and k != "LANG"}


@pytest.mark.parametrize("module", [slotbook_texts, splitmate_texts], ids=["slotbook", "splitmate"])
def test_english_overrides_every_text(module):
    ru, en = translatable(module.Ru), translatable(module.En)
    missing = sorted(set(ru) - set(en) - SAME_IN_BOTH)
    assert not missing, f"Not translated: {missing}"
    untranslated = sorted(k for k in en if en[k] == ru.get(k) and k not in SAME_IN_BOTH)
    assert not untranslated, f"Same text in both languages: {untranslated}"


@pytest.mark.parametrize("module", [slotbook_texts, splitmate_texts], ids=["slotbook", "splitmate"])
def test_placeholders_match(module):
    """A translation must keep the same {placeholders}, or .format() would crash."""
    import string

    def fields(s: object) -> set[str]:
        if not isinstance(s, str):
            return set()
        return {f for _, f, _, _ in string.Formatter().parse(s) if f}

    ru, en = translatable(module.Ru), translatable(module.En)
    broken = sorted(k for k in en if fields(en[k]) != fields(ru.get(k, "")))
    assert not broken, f"Placeholders differ: {broken}"


@pytest.mark.parametrize(
    ("code", "lang"),
    [
        ("ru", "ru"),
        ("uk", "ru"),
        ("be", "ru"),
        ("kk", "ru"),
        ("en", "en"),
        ("de", "en"),
        ("pt-br", "en"),
        (None, "en"),
    ],
)
def test_detect(code, lang):
    assert detect(code) == lang
