"""Optional app-wide access gate for an internal ABAYO deployment."""

from __future__ import annotations

import hmac
from typing import Any, Mapping, MutableMapping

import streamlit as st

_AUTHENTICATED_KEY = "abayo_access_authenticated"


def configured_access_password(secrets: Mapping[str, Any]) -> str:
    """Read the optional launch password without displaying or logging it."""

    try:
        return str(secrets.get("ABAYO_ACCESS_PASSWORD", "")).strip()
    except (AttributeError, TypeError):
        return ""


def verify_access_password(entered: str, expected: str) -> bool:
    """Compare access passwords using a timing-safe operation."""

    return bool(expected) and hmac.compare_digest(entered, expected)


def access_is_authenticated(state: MutableMapping[str, Any]) -> bool:
    return bool(state.get(_AUTHENTICATED_KEY, False))


def logout(state: MutableMapping[str, Any]) -> None:
    state.pop(_AUTHENTICATED_KEY, None)


def require_app_access() -> None:
    """Stop page execution until the optional shared access password is valid."""

    try:
        expected = configured_access_password(st.secrets)
    except Exception:
        expected = ""

    # Preserve existing private deployments while allowing a launch password
    # to be enabled entirely through Streamlit Secrets.
    if not expected or access_is_authenticated(st.session_state):
        return

    st.title("🔷 ABAYO")
    st.caption("Authorized operations personnel only")

    with st.form("abayo_access_form"):
        entered = st.text_input("Access password", type="password")
        submitted = st.form_submit_button(
            "Open ABAYO",
            type="primary",
            width="stretch",
        )

    if submitted:
        if verify_access_password(entered, expected):
            st.session_state[_AUTHENTICATED_KEY] = True
            st.rerun()
        st.error("Incorrect access password.")

    st.stop()
