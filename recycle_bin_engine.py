"""Recycle-bin operations shared by ABAYO Streamlit pages."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


RETENTION_DAYS = 30


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def recycle_bin_is_ready(supabase: Any) -> bool:
    """Return True when the machines.deleted_at column is available."""
    try:
        (
            supabase.table("machines")
            .select("id,deleted_at")
            .limit(1)
            .execute()
        )
        return True
    except Exception:
        return False


def load_active_machines(supabase: Any) -> list[dict]:
    result = (
        supabase.table("machines")
        .select("*")
        .is_("deleted_at", "null")
        .execute()
    )
    return result.data or []


def load_deleted_machines(supabase: Any) -> list[dict]:
    result = (
        supabase.table("machines")
        .select("*")
        .not_.is_("deleted_at", "null")
        .order("deleted_at", desc=True)
        .execute()
    )
    return result.data or []


def soft_delete_machine(supabase: Any, machine_id: Any) -> list[dict]:
    """Move one machine to the recycle bin without losing its data."""
    result = (
        supabase.table("machines")
        .update({"deleted_at": utc_now_iso()})
        .eq("id", machine_id)
        .select("*")
        .execute()
    )
    return result.data or []


def restore_machine(supabase: Any, machine_id: Any) -> list[dict]:
    result = (
        supabase.table("machines")
        .update({"deleted_at": None})
        .eq("id", machine_id)
        .select("*")
        .execute()
    )
    return result.data or []


def permanently_delete_machine(
    supabase: Any,
    machine_id: Any,
) -> list[dict]:
    """Permanently remove one already-deleted machine."""
    result = (
        supabase.table("machines")
        .delete()
        .eq("id", machine_id)
        .not_.is_("deleted_at", "null")
        .select("*")
        .execute()
    )
    return result.data or []


def purge_expired_machines(supabase: Any) -> list[dict]:
    """Permanently remove machines retained for more than 30 days."""
    cutoff = utc_now() - timedelta(days=RETENTION_DAYS)
    result = (
        supabase.table("machines")
        .delete()
        .lt("deleted_at", cutoff.isoformat())
        .select("*")
        .execute()
    )
    return result.data or []


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(
            str(value).strip().replace("Z", "+00:00")
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def format_deleted_at(value: Any) -> str:
    parsed = parse_timestamp(value)
    if parsed is None:
        return "Unknown"
    return parsed.strftime("%d %b %Y, %H:%M UTC")


def days_until_permanent_deletion(value: Any) -> int:
    parsed = parse_timestamp(value)
    if parsed is None:
        return RETENTION_DAYS

    remaining = parsed + timedelta(days=RETENTION_DAYS) - utc_now()
    if remaining.total_seconds() <= 0:
        return 0

    return max(
        1,
        int((remaining.total_seconds() + 86_399) // 86_400),
    )
