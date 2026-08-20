import logging
from typing import Any

from supabase_engine import get_supabase_client

LOGGER = logging.getLogger(__name__)


def log_activity(
    machine_id: Any,
    activity_type: str,
    description: str,
    status: str = "Completed",
) -> bool:
    """Record an activity without interrupting the user's main action."""

    try:
        supabase = get_supabase_client()

        supabase.table("machine_activity").insert(
            {
                "machine_id": machine_id,
                "activity_type": activity_type,
                "description": description,
                "status": status,
            }
        ).execute()

        return True

    except Exception as error:
        LOGGER.warning("Activity logging failed: %s", error)
        return False
