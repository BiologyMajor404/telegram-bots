"""SplitMates greets a new group only once."""

from splitmate.handlers import group


def test_second_welcome_right_after_join_is_skipped(monkeypatch):
    clock = iter([1000.0, 1001.0, 1000.0 + group.WELCOME_DEDUP_SEC + 5])
    monkeypatch.setattr(group.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(group, "_welcomed_at", {})

    assert group.just_welcomed(-1) is False  # join event: greet
    assert group.just_welcomed(-1) is True  # /start from the same "Add to group" click: skip
    assert group.just_welcomed(-1) is False  # much later: greet again


def test_chats_are_tracked_separately(monkeypatch):
    monkeypatch.setattr(group.time, "monotonic", lambda: 1000.0)
    monkeypatch.setattr(group, "_welcomed_at", {})

    assert group.just_welcomed(-1) is False
    assert group.just_welcomed(-2) is False
