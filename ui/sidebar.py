"""Canonical navigation used by the dashboard and all feature pages."""

from __future__ import annotations

import streamlit as st

from core.access import configured_access_password, logout
from core.constants import APP_VERSION
from core.machines import machine_label


def _load_sidebar_machines() -> list[dict]:
    """Load active machines so selection follows the user across every page."""

    try:
        from core.database import get_supabase_client

        response = get_supabase_client().table("machines").select("*").execute()
        rows = response.data or []
        return [
            dict(row)
            for row in rows
            if not row.get("deleted_at")
        ]
    except Exception:
        return []


def _render_machine_switcher() -> None:
    machines = _load_sidebar_machines()
    if not machines:
        st.caption("No machine selected")
        return

    ids = [machine.get("id") for machine in machines]
    selected_id = st.session_state.get("selected_machine_id")
    if selected_id not in ids:
        selected_id = ids[0]
        st.session_state.selected_machine_id = selected_id

    labels = [machine_label(machine) for machine in machines]
    selected_index = ids.index(selected_id)

    # Keep this selector self-contained so Streamlit theme/DOM changes cannot
    # make the selected machine unreadable against ABAYO's dark sidebar.
    st.html(
        """
        <style>
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [aria-haspopup="listbox"] {
            background: #0b1f36 !important;
            background-color: #0b1f36 !important;
            border: 2px solid #3b82f6 !important;
            border-radius: 12px !important;
            min-height: 50px !important;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, .18) !important;
            color: #ffffff !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"]:hover,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [aria-haspopup="listbox"]:hover {
            background: #123055 !important;
            background-color: #123055 !important;
            border-color: #60a5fa !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [aria-haspopup="listbox"] * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 700 !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] input {
            background: transparent !important;
            background-color: transparent !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            caret-color: #ffffff !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
            color: #ffffff !important;
            fill: currentColor !important;
            opacity: 1 !important;
        }

        div[data-baseweb="popover"] div[role="listbox"] {
            background: #10213c !important;
            border: 1px solid rgba(96, 165, 250, .55) !important;
            border-radius: 12px !important;
        }

        div[data-baseweb="popover"] div[role="option"] {
            background: #10213c !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        div[data-baseweb="popover"] div[role="option"]:hover {
            background: #173055 !important;
        }

        div[data-baseweb="popover"] div[role="option"][aria-selected="true"] {
            background: #2563eb !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 700 !important;
        }
        </style>
        """
    )

    chosen_label = st.selectbox(
        "Active machine",
        labels,
        index=selected_index,
        key="shared_active_machine_label",
    )
    chosen_id = ids[labels.index(chosen_label)]
    if chosen_id != st.session_state.get("selected_machine_id"):
        st.session_state.selected_machine_id = chosen_id
        for key in (
            "open_component_number",
            "pending_component_delete",
            "pending_fault_delete",
            "selected_edit_option",
        ):
            st.session_state.pop(key, None)
        st.rerun()


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
        st.markdown("#### ACTIVE MACHINE")
        _render_machine_switcher()

        if allow_add_machine and st.button(
            "＋ Add Machine",
            key="shared_sidebar_add_machine",
            width="stretch",
        ):
            st.session_state.show_add_machine = True
            st.switch_page("app.py")

        st.page_link(
            "pages/10_machine_settings.py",
            label="Machine Profile & Status",
            icon="🏭",
            width="stretch",
        )

        st.markdown("#### MACHINE KNOWLEDGE")
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
        st.page_link(
            "pages/9_ai_assistant.py",
            label="AI Assistant",
            icon="🤖",
            width="stretch",
        )
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
