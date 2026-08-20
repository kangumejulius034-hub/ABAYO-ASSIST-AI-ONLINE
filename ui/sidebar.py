"""Canonical navigation used by the dashboard and all feature pages."""

from __future__ import annotations

import streamlit as st

from core.access import configured_access_password, logout
from core.constants import APP_VERSION


def render_sidebar(
    *,
    database_connected: bool | None = None,
    recycle_count: int | None = None,
    allow_add_machine: bool = True,
) -> None:
    """Render ABAYO's single shared sidebar."""

    with st.sidebar:
        st.markdown("## 🔷 ABAYO")
        st.caption("AI Operations Assistant")
        st.divider()

        st.page_link("app.py", label="Home", icon="🏠", width="stretch")
        st.markdown("#### MACHINES")

        if allow_add_machine and st.button(
            "＋ Add Machine",
            key="shared_sidebar_add_machine",
            width="stretch",
        ):
            st.session_state.show_add_machine = True
            st.switch_page("app.py")

        st.page_link(
            "pages/1_fault_diagnosis.py",
            label="Fault Diagnosis",
            icon="🔧",
            width="stretch",
        )
        st.page_link(
            "pages/2_recipe_library.py",
            label="Recipe Library",
            icon="📖",
            width="stretch",
        )
        st.page_link(
            "pages/3_maintenance_history.py",
            label="Maintenance",
            icon="🛠️",
            width="stretch",
        )
        st.page_link(
            "pages/4_smart_toubleshooter.py",
            label="Knowledge Base",
            icon="🧠",
            width="stretch",
        )
        st.page_link(
            "pages/5_machine_components.py",
            label="Machine Components",
            icon="⚙️",
            width="stretch",
        )
        st.page_link(
            "pages/8_hmi_profiles.py",
            label="HMI Profiles",
            icon="🖥️",
            width="stretch",
        )

        recycle_label = "Recycle Bin"
        if recycle_count is not None:
            recycle_label += f" ({recycle_count})"
        st.page_link(
            "pages/6_recycle_bin.py",
            label=recycle_label,
            icon="🗑️",
            width="stretch",
        )
        st.page_link(
            "pages/7_settings.py",
            label="Settings",
            icon="⚙️",
            width="stretch",
        )

        st.divider()
        st.markdown("#### ABAYO ASSISTANT")
        st.markdown("🤖 **AI Assistant**")
        st.caption("Coming soon")
        st.divider()

        if database_connected is True:
            st.success("● Cloud system connected")
        elif database_connected is False:
            st.error("● Cloud system disconnected")
        else:
            st.caption("Cloud status available on Home")

        try:
            access_protected = bool(configured_access_password(st.secrets))
        except Exception:
            access_protected = False

        if access_protected and st.button(
            "Sign out",
            key="shared_sidebar_sign_out",
            width="stretch",
        ):
            logout(st.session_state)
            st.rerun()

        st.caption(f"System Version {APP_VERSION}")
