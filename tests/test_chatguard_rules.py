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
