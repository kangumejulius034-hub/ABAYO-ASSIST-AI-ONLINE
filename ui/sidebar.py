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
        return [dict(row) for row in rows if not row.get("deleted_at")]
    except Exception:
        return []


def _render_sidebar_styles() -> None:
    """Apply the compact launch-ready navigation treatment."""

    st.html(
        """
        <style>
        [data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 18% 0%, rgba(37, 99, 235, .18), transparent 30%),
                linear-gradient(180deg, #061426 0%, #0a1c33 58%, #0d213b 100%) !important;
            border-right: 1px solid rgba(148, 163, 184, .12) !important;
        }

        [data-testid="stSidebarUserContent"] {
            padding-top: .85rem !important;
            padding-left: .9rem !important;
            padding-right: .9rem !important;
            padding-bottom: 1.1rem !important;
        }

        .abayo-sidebar-brand {
            display: flex;
            align-items: center;
            gap: .72rem;
            padding: .78rem .72rem;
            margin: 0 0 .45rem;
            border: 1px solid rgba(148, 163, 184, .13);
            border-radius: 14px;
            background: rgba(255, 255, 255, .035);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, .035);
        }

        .abayo-sidebar-mark {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            flex: 0 0 38px;
            border-radius: 11px;
            color: #ffffff !important;
            font-size: 1rem;
            font-weight: 900;
            letter-spacing: -.02em;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            box-shadow: 0 8px 22px rgba(37, 99, 235, .27);
        }

        .abayo-sidebar-brand-name {
            color: #ffffff !important;
            font-size: .96rem;
            line-height: 1.1;
            font-weight: 850;
            letter-spacing: .035em;
        }

        .abayo-sidebar-brand-subtitle {
            color: #9fb2cb !important;
            font-size: .68rem;
            line-height: 1.25;
            margin-top: .18rem;
        }

        .abayo-sidebar-section {
            color: #86a0bf !important;
            font-size: .66rem;
            line-height: 1;
            font-weight: 850;
            letter-spacing: .15em;
            text-transform: uppercase;
            margin: 1.08rem .6rem .42rem;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            min-height: 42px !important;
            display: flex !important;
            align-items: center !important;
            gap: .25rem !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            padding: .54rem .66rem !important;
            margin: .06rem 0 !important;
            color: #dbe7f5 !important;
            font-size: .91rem !important;
            font-weight: 560 !important;
            transition: background .15s ease, border-color .15s ease, transform .15s ease !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background: rgba(59, 130, 246, .11) !important;
            border-color: rgba(96, 165, 250, .17) !important;
            transform: translateX(1px);
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
            background: linear-gradient(
                90deg,
                rgba(37, 99, 235, .24) 0%,
                rgba(37, 99, 235, .10) 100%
            ) !important;
            border-color: rgba(96, 165, 250, .22) !important;
            color: #ffffff !important;
            font-weight: 720 !important;
            box-shadow: inset 3px 0 0 #60a5fa;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] {
            margin-bottom: .2rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] label {
            display: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [aria-haspopup="listbox"] {
            min-height: 46px !important;
            background: rgba(21, 47, 78, .92) !important;
            border: 1px solid rgba(96, 165, 250, .46) !important;
            border-radius: 11px !important;
            box-shadow: 0 5px 18px rgba(0, 0, 0, .12) !important;
            color: #ffffff !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [aria-haspopup="listbox"] *,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] input {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-weight: 700 !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
            color: #c7dcf7 !important;
            fill: currentColor !important;
        }

        [data-testid="stSidebar"] .stButton {
            margin-top: .18rem !important;
        }

        [data-testid="stSidebar"] .stButton button {
            min-height: 40px !important;
            border-radius: 10px !important;
            font-size: .88rem !important;
            font-weight: 650 !important;
        }

        .abayo-cloud-pill {
            display: flex;
            align-items: center;
            gap: .48rem;
            width: 100%;
            box-sizing: border-box;
            padding: .62rem .7rem;
            margin-top: .9rem;
            border: 1px solid rgba(148, 163, 184, .13);
            border-radius: 10px;
            background: rgba(255, 255, 255, .035);
            color: #b9c9dc !important;
            font-size: .73rem;
            font-weight: 620;
        }

        .abayo-cloud-dot {
            width: 7px;
            height: 7px;
            flex: 0 0 7px;
            border-radius: 999px;
            background: #94a3b8;
        }

        .abayo-cloud-dot.online { background: #34d399; }
        .abayo-cloud-dot.offline { background: #f87171; }

        .abayo-sidebar-version {
            color: #6f89aa !important;
            text-align: center;
            font-size: .64rem;
            letter-spacing: .035em;
            margin: .7rem 0 .15rem;
        }

        div[data-baseweb="popover"] div[role="listbox"] {
            background: #10213c !important;
            border: 1px solid rgba(96, 165, 250, .40) !important;
            border-radius: 11px !important;
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
            font-weight: 700 !important;
        }

        @media (max-width: 800px) {
            [data-testid="stSidebarUserContent"] {
                padding-top: .7rem !important;
                padding-left: .72rem !important;
                padding-right: .72rem !important;
            }

            .abayo-sidebar-brand { padding: .68rem; }
            .abayo-sidebar-section {
                margin-top: .9rem;
                margin-bottom: .34rem;
            }

            [data-testid="stSidebar"] [data-testid="stPageLink"] a {
                min-height: 39px !important;
                padding-top: .47rem !important;
                padding-bottom: .47rem !important;
            }
        }
        </style>
        """
    )


def _section_label(label: str) -> None:
    st.html(f'<div class="abayo-sidebar-section">{label}</div>')


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

    chosen_label = st.selectbox(
        "Machine",
        labels,
        index=selected_index,
        key="shared_active_machine_label",
        label_visibility="collapsed",
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


def _render_cloud_status(database_connected: bool | None) -> None:
    if database_connected is True:
        dot_class = "online"
        label = "Cloud connected"
    elif database_connected is False:
        dot_class = "offline"
        label = "Cloud disconnected"
    else:
        dot_class = ""
        label = "Cloud status on Home"

    st.html(
        f"""
        <div class="abayo-cloud-pill">
            <span class="abayo-cloud-dot {dot_class}"></span>
            <span>{label}</span>
        </div>
        """
    )


def render_sidebar(
    *,
    database_connected: bool | None = None,
    recycle_count: int | None = None,
    allow_add_machine: bool = True,
) -> None:
    """Render ABAYO's single shared sidebar."""

    with st.sidebar:
        _render_sidebar_styles()

        st.html(
            """
            <div class="abayo-sidebar-brand">
                <div class="abayo-sidebar-mark">A</div>
                <div>
                    <div class="abayo-sidebar-brand-name">ABAYO</div>
                    <div class="abayo-sidebar-brand-subtitle">AI Operations Assistant</div>
                </div>
            </div>
            """
        )

        st.page_link("app.py", label="Home", icon="🏠", width="stretch")

        _section_label("Machine")
        _render_machine_switcher()

        if allow_add_machine and st.button(
            "＋ Add Machine",
            key="shared_sidebar_add_machine",
            type="primary",
            width="stretch",
        ):
            st.session_state.show_add_machine = True
            st.switch_page("app.py")

        st.page_link(
            "pages/10_machine_settings.py",
            label="Profile & Status",
            icon="🏭",
            width="stretch",
        )

        _section_label("Knowledge")
        st.page_link("pages/1_fault_diagnosis.py", label="Fault Diagnosis", icon="🔧", width="stretch")
        st.page_link("pages/2_recipe_library.py", label="Recipe Library", icon="📖", width="stretch")
        st.page_link("pages/3_maintenance_history.py", label="Maintenance", icon="🛠️", width="stretch")
        st.page_link("pages/4_smart_toubleshooter.py", label="Knowledge Base", icon="🧠", width="stretch")
        st.page_link("pages/5_machine_components.py", label="Machine Components", icon="⚙️", width="stretch")
        st.page_link("pages/8_hmi_profiles.py", label="HMI Profiles", icon="🖥️", width="stretch")

        _section_label("Tools")
        st.page_link("pages/9_ai_assistant.py", label="AI Assistant", icon="🤖", width="stretch")

        recycle_label = "Recycle Bin"
        if recycle_count is not None:
            recycle_label += f" ({recycle_count})"
        st.page_link("pages/6_recycle_bin.py", label=recycle_label, icon="🗑️", width="stretch")
        st.page_link("pages/7_settings.py", label="Settings", icon="⚙️", width="stretch")

        _render_cloud_status(database_connected)

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

        st.html(f'<div class="abayo-sidebar-version">ABAYO · v{APP_VERSION}</div>')
