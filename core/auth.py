"""Short-lived administrator authorization for destructive actions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hmac
from typing import Any, Mapping, MutableMapping

ADMIN_UNLOCK_TTL = timedelta(minutes=10)
_UNLOCKED_UNTIL_KEY = "admin_unlocked_until"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def configured_admin_pin(secrets: Mapping[str, Any]) -> str:
    """Return the configured administrator PIN without logging it."""

    try:
        return str(secrets.get("ABAYO_ADMIN_PIN", "")).strip()
    except (AttributeError, TypeError):
        return ""


def admin_is_unlocked(
    state: MutableMapping[str, Any],
    *,
    now: datetime | None = None,
) -> bool:
    """Return whether the current session has an unexpired unlock."""

    value = state.get(_UNLOCKED_UNTIL_KEY)
    if not value:
        return False

    try:
        unlocked_until = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        lock_admin(state)
        return False

    if unlocked_until.tzinfo is None:
        unlocked_until = unlocked_until.replace(tzinfo=timezone.utc)

    if (now or utc_now()) >= unlocked_until.astimezone(timezone.utc):
        lock_admin(state)
        return False

    return True


def unlock_admin(
    state: MutableMapping[str, Any],
    entered_pin: str,
    expected_pin: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Unlock destructive actions for a limited time after PIN validation."""

    if not expected_pin or not hmac.compare_digest(entered_pin, expected_pin):
        return False

    expires_at = (now or utc_now()) + ADMIN_UNLOCK_TTL
    state[_UNLOCKED_UNTIL_KEY] = expires_at.isoformat()
    return True


def lock_admin(state: MutableMapping[str, Any]) -> None:
    """Immediately remove administrator authorization from the session."""

    state.pop(_UNLOCKED_UNTIL_KEY, None)
    # Remove the legacy never-expiring flag when upgrading an existing session.
    state.pop("admin_actions_unlocked", None)
