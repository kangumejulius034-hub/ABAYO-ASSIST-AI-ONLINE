from datetime import datetime, timedelta, timezone

from core.auth import admin_is_unlocked, lock_admin, unlock_admin


def test_admin_unlock_expires_after_ten_minutes() -> None:
    state: dict[str, str] = {}
    start = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)

    assert unlock_admin(state, "2468", "2468", now=start)
    assert admin_is_unlocked(state, now=start + timedelta(minutes=9))
    assert not admin_is_unlocked(state, now=start + timedelta(minutes=10))


def test_wrong_pin_does_not_unlock_and_lock_clears_legacy_state() -> None:
    state: dict[str, object] = {"admin_actions_unlocked": True}

    assert not unlock_admin(state, "wrong", "correct")
    lock_admin(state)

    assert not admin_is_unlocked(state)
    assert "admin_actions_unlocked" not in state
