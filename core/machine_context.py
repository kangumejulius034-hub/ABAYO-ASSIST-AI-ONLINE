"""Resolve the currently selected machine without coupling feature pages to IDs.

Every machine-specific ABAYO feature should derive its scope from the database
machine ID stored in Streamlit session state. Names, manufacturers and models
are display metadata only and are never used as the primary identity.
"""

from __future__ import annotations

from typing import Any, MutableMapping


def selected_machine_id(session_state: MutableMapping[str, Any] | None = None) -> Any | None:
    """Return the current database machine ID from Streamlit session state."""

    if session_state is not None:
        return session_state.get("selected_machine_id")

    try:
        import streamlit as st

        return st.session_state.get("selected_machine_id")
    except Exception:
        return None


def fetch_machine(client: Any, machine_id: Any) -> dict[str, Any] | None:
    """Fetch one active machine by its true database ID."""

    if client is None or machine_id in (None, ""):
        return None

    try:
        response = (
            client.table("machines")
            .select("*")
            .eq("id", machine_id)
            .limit(1)
            .execute()
        )
    except Exception:
        return None

    if not response.data:
        return None
    return dict(response.data[0])


def current_machine(client: Any | None = None) -> dict[str, Any] | None:
    """Return the selected machine, lazily creating a database client if needed."""

    machine_id = selected_machine_id()
    if machine_id in (None, ""):
        return None

    if client is None:
        try:
            from core.database import get_supabase_client

            client = get_supabase_client()
        except Exception:
            return None

    return fetch_machine(client, machine_id)


def machine_display_name(machine: dict[str, Any] | None) -> str:
    """Return a concise display name for a machine."""

    if not machine:
        return "No machine selected"

    name = str(machine.get("machine_name") or "").strip()
    manufacturer = str(machine.get("manufacturer") or "").strip()
    model = str(machine.get("model") or "").strip()

    if name:
        return name
    if manufacturer and model:
        return f"{manufacturer} {model}".strip()
    return model or manufacturer or "Unnamed machine"


def machine_model_label(machine: dict[str, Any] | None) -> str:
    """Return the best model label for recipe/maintenance display fields."""

    if not machine:
        return "Selected machine"

    model = str(machine.get("model") or "").strip()
    manufacturer = str(machine.get("manufacturer") or "").strip()
    name = str(machine.get("machine_name") or "").strip()

    if model:
        return model
    if manufacturer:
        return manufacturer
    return name or "Selected machine"


def is_pakona_machine(machine: dict[str, Any] | None) -> bool:
    """Identify the legacy Pakona profile so old seed knowledge stays Pakona-only."""

    if not machine:
        return False

    text = " ".join(
        str(machine.get(field) or "")
        for field in ("machine_name", "manufacturer", "model", "description")
    ).lower()

    return "pakona" in text or "pfs" in text
