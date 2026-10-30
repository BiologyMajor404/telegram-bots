"""ChatGuard fast spam rules in four languages."""

import pytest

from chatguard.rules import check


@pytest.mark.parametrize(
    "text",
    [
        "Привет всем! Кто едет завтра на шашлыки?",
        "Дякую, вже отримав",
        "Ok, see you at 7",
        "Cześć, kto ma notatki z wykładu?",
    ],
)
def test_normal_messages_are_clean(text):
    v = check(text)
    assert v.is_clean, v.reasons


@pytest.mark.parametrize(
    "text",
    [
        "💰💰💰 Заработок от 500$ в день! Пиши в лс 👉 t.me/+AbCdEf",
        "Пасивний дохід на крипті, інвестуй від 100$, пиши в особисті @rich_trader_bot",
        "Earn passive income with crypto trading! DM me https://scam.xyz",
        "Praca zdalna, zarobki 1000 zł dziennie, pisz na priv",
    ],
)
def test_obvious_spam_is_caught_by_rules(text):
    v = check(text)
    assert v.is_spam, (v.score, v.reasons)


@pytest.mark.parametrize(
    "text",
    [
        # Stems used to match inside words: "earn" in "learned", "invest" in "investigation"
        "Just learned from @bbcworld about the investigation: https://bbc.com/news/1",
        # "крипт" in "скрипт", "доход" in "доходит", and the everyday "за день"
        "Пытаюсь за день написать скрипт, но доходит до ошибки: https://github.com/x/y",
        # "в приват" in "ПриватБанк"
        "Оплатил в ПриватБанк, чек тут: https://privatbank.ua/check/1 @bank_support",
        "Обсудим в приватном порядке, вот ссылка на встречу https://meet.google.com/abc",
    ],
)
def test_ordinary_words_never_make_spam_by_rules_alone(text):
    v = check(text)
    assert not v.is_spam, (v.score, v.reasons)


@pytest.mark.parametrize(
    "text",
    [
        "Just learned about the investigation",
        "Пишу скрипт, но доходит до ошибки, дохідливо пояснили",
        "Доставка завтра, выставка в субботу",
        "Поезд прибыл, прибуття о 10:00",
        "Подключись к удалённому серверу",
        "He is an earnest man",
    ],
)
def test_words_that_only_contain_a_stem_are_not_money(text):
    assert "money" not in check(text).reasons


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("Криптовалюта растёт", "money"),
        ("Пассивный доход и доходность", "money"),
        ("Investing pays", "money"),
        ("Earnings from home", "money"),
        ("Шукаю віддалену роботу", "money"),
        ("Пиши в приват", "dm"),
        ("Ставки на спорт", "money"),
    ],
)
def test_stems_still_catch_their_word_forms(text, reason):
    assert reason in check(text).reasons


def test_single_link_is_only_doubtful():
    v = check("Вот статья, о которой говорил: https://habr.com/ru/articles/123")
    assert not v.is_clean and not v.is_spam
    assert v.reasons == ["link"]


def test_forward_with_buttons_adds_up():
    v = check("Новый канал про скидки", forwarded_from_channel=True, has_buttons=True)
    assert v.score >= 4 and {"forward", "buttons"} <= set(v.reasons)


def test_caps_and_emoji():
    v = check("СРОЧНО ВСЕМ ЧИТАТЬ ВАЖНАЯ ИНФОРМАЦИЯ 🔥🔥🔥🔥🔥🔥🔥🔥")
    assert {"caps", "emoji"} <= set(v.reasons)
