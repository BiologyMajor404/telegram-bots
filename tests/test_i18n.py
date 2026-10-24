"""Every language class must translate every text of its Russian base class,
otherwise a forgotten string would silently show up in Russian."""

import string

import pytest

from chatguard import texts as chatguard_texts
from shared.i18n import LANGS, command_locales, detect
from slotbook import texts as slotbook_texts
from splitmate import texts as splitmate_texts

# Texts that are legitimately identical to Russian (in every language / in a given one)
SAME_EVERYWHERE = {"PUNISH_DELETE"}
SAME_AS_RUSSIAN = {
    "uk": {"DEFAULT_CURRENCY", "BTN_DONE", "SOURCE_RULES"},
}

CASES = [
    (module, code)
    for module in (slotbook_texts, splitmate_texts, chatguard_texts)
    for code in LANGS
    if code != "ru"
]
IDS = [f"{m.__name__.split('.')[0]}-{code}" for m, code in CASES]


def translatable(obj: object) -> dict[str, object]:
    cls = type(obj)
    return {
        k: getattr(obj, k)
        for k in dir(cls)
        if k.isupper() and k != "LANG" and not callable(getattr(obj, k))
    }


def fields(s: object) -> set[str]:
    if not isinstance(s, str):
        return set()
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


@pytest.mark.parametrize("module", [slotbook_texts, splitmate_texts, chatguard_texts])
def test_every_language_is_registered(module):
    assert set(module.TEXTS) == set(LANGS)
    assert all(code == t.LANG for code, t in module.TEXTS.items())


@pytest.mark.parametrize(("module", "code"), CASES, ids=IDS)
def test_language_overrides_every_text(module, code):
    ru, other = translatable(module.TEXTS["ru"]), translatable(module.TEXTS[code])
    allowed = SAME_EVERYWHERE | SAME_AS_RUSSIAN.get(code, set())
    untranslated = sorted(k for k in ru if other[k] == ru[k] and k not in allowed)
    assert not untranslated, f"Still in Russian: {untranslated}"


@pytest.mark.parametrize(("module", "code"), CASES, ids=IDS)
def test_placeholders_match(module, code):
    """A translation must keep the same {placeholders}, or .format() would crash."""
    ru, other = translatable(module.TEXTS["ru"]), translatable(module.TEXTS[code])
    broken = sorted(k for k in ru if fields(other[k]) != fields(ru[k]))
    assert not broken, f"Placeholders differ: {broken}"


@pytest.mark.parametrize(
    ("app_code", "lang"),
    [
        ("uk", "uk"),
        ("ru", "ru"),
        ("be", "ru"),
        ("kk", "ru"),
        ("pl", "pl"),
        ("en", "en"),
        ("de", "en"),
        ("pt-br", "en"),
        (None, "en"),
    ],
)
def test_detect(app_code, lang):
    assert detect(app_code) == lang


def test_command_locales_cover_every_language():
    locales = command_locales()
    assert set(locales) == set(LANGS)
    assert locales["en"] == [None]
