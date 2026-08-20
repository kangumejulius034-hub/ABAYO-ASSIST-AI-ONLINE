"""Application settings stored in the existing app_settings table."""

from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT_SETTINGS: dict[str, Any] = {
    "id": "global",
    "display_name": "Kangume Julius",
    "job_title": "Administrator",
    "company_name": "",
    "welcome_title": "Welcome back",
    "welcome_subtitle": (
        "Monitor machines, diagnose faults and preserve operational knowledge."
    ),
    "support_email": "",
    "default_machine_location": "",
    "default_machine_status": "Online",
}


def load_app_settings(client: Any | None) -> dict[str, Any]:
    """Load global settings, falling back safely when unavailable."""

    if client is None:
        return dict(DEFAULT_SETTINGS)

    try:
        response = (
            client.table("app_settings")
            .select("*")
            .eq("id", "global")
            .limit(1)
            .execute()
        )
    except Exception as exc:
        LOGGER.warning("Unable to load app settings: %s", exc)
        return dict(DEFAULT_SETTINGS)

    if not response.data:
        return dict(DEFAULT_SETTINGS)

    return {**DEFAULT_SETTINGS, **response.data[0]}
