"""Supabase connection and small, explicit database helpers."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import Client, create_client

LOGGER = logging.getLogger(__name__)


class DatabaseUnavailableError(RuntimeError):
    """Raised when ABAYO cannot safely use its cloud database."""


@dataclass(frozen=True)
class DatabaseStatus:
    """Result of a real database connectivity check."""

    connected: bool
    message: str


@st.cache_resource
def get_supabase_client() -> Client:
    """Create and cache a Supabase client from Streamlit secrets."""

    try:
        settings = st.secrets["supabase"]
        url = str(settings["url"]).strip()
        key = str(settings["key"]).strip()
    except (KeyError, TypeError, StreamlitSecretNotFoundError) as exc:
        raise DatabaseUnavailableError(
            "Supabase secrets are missing. Configure supabase.url and "
            "supabase.key in Streamlit Secrets."
        ) from exc

    if not url or not key:
        raise DatabaseUnavailableError(
            "Supabase URL and key must not be empty."
        )

    return create_client(url, key)


def check_database(client: Any | None = None) -> DatabaseStatus:
    """Verify that credentials work by executing a lightweight query."""

    try:
        active_client = client or get_supabase_client()
        active_client.table("machines").select("id").limit(1).execute()
    except Exception as exc:  # Supabase exposes several transport exceptions.
        LOGGER.warning("Supabase health check failed: %s", exc)
        return DatabaseStatus(False, str(exc))

    return DatabaseStatus(True, "Supabase database is reachable.")


def select_rows(
    client: Any,
    table_name: str,
    *,
    columns: str = "*",
) -> list[dict[str, Any]]:
    """Read a table and return normalized dictionary rows.

    Errors are intentionally allowed to propagate so callers can distinguish
    an empty table from a failed query.
    """

    response = client.table(table_name).select(columns).execute()
    data = response.data or []
    return [row for row in data if isinstance(row, dict)]
