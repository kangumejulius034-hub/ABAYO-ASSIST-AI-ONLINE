"""Canonical navigation used by the dashboard and all feature pages."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.access import configured_access_password, logout
from core.constants import APP_VERSION
from core.machines import machine_label


LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "abayo_logo.svg"


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
    """Apply the launch-ready ABAYO navigation treatment."""

    st.html(
        """
        <style>
        [data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 20% -5%, rgba(37, 99, 235, .30), transparent 30%),
                radial-gradient(circle at 95% 35%, rgba(14, 165, 233, .09), transparent 34%),
                linear-gradient(180deg, #041126 0%, #071a35 58%, #07172d 100%) !important;
            border-right: 1px solid rgba(148, 163, 184, .12) !important;
            box-shadow: 8px 0 28px rgba(3, 12, 28, .08);
        }

        [data-testid="stSidebarUserContent"] {
            padding-top: .72rem !important;
            padding-left: .82rem !important;
            padding-right: .82rem !important;
            padding-bottom: 1.05rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stImage"] {
            padding: .52rem .42rem .44rem !important;
            margin: 0 0 .35rem !important;
            border: 1px solid rgba(148, 163, 184, .11);
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(255,255,255,.045), rgba(255,255,255,.015));
            box-shadow: inset 0 1px 0 rgba(255,255,255,.035);
        }

        [data-testid="stSidebar"] [data-testid="stImage"] img {
            max-height: 58px !important;
            object-fit: contain !important;
            object-position: left center !important;
        }

        .abayo-sidebar-section {
            color: #86a0bf !important;
            font-size: .64rem;
            line-height: 1;
            font-weight: 850;
            letter-spacing: .15em;
            text-transform: uppercase;
            margin: 1.02rem .56rem .4rem;
            padding-bottom: .35rem;
            border-bottom: 1px solid rgba(148,163,184,.10);
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            min-height: 41px !important;
            display: flex !important;
            align-items: center !important;
            gap: .22rem !important;
            border: 1px solid transparent !important;
            border-radius: 10px !important;
            padding: .52rem .62rem !important;
            margin: .045rem 0 !important;
            color: #dce8f7 !important;
            font-size: .89rem !important;
            font-weight: 570 !important;
            transition: background .15s ease, border-color .15s ease, transform .15s ease !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background: rgba(59, 130, 246, .12) !important;
            border-color: rgba(96, 165, 250, .18) !important;
            transform: translateX(1px);
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
            background: linear-gradient(100deg, #0b55d8 0%, #1674f5 100%) !important;
            border-color: rgba(125, 211, 252, .30) !important;
            color: #ffffff !important;
            font-weight: 730 !important;
            box-shadow: 0 9px 22px rgba(2, 86, 214, .24), inset 0 1px 0 rgba(255,255,255,.10);
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] {
            margin-bottom: .16rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] label {
            display: none !important;
        }

        [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"],
        [data-testid="stSidebar"] [data-testid="stSelectbox"] [aria-haspopup="listbox"] {
            min-height: 44px !important;
            background: linear-gradient(180deg, rgba(19,48,83,.98), rgba(13,37,68,.98)) !important;
            border: 1px solid rgba(96, 165, 250, .42) !important;
            border-radius: 10px !important;
            box-shadow: 0 5px 18px rgba(0, 0, 0, .13) !important;
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
            margin-top: .16rem !important;
        }

        [data-testid="stSidebar"] .stButton button {
            min-height: 39px !important;
            border-radius: 10px !important;
            font-size: .86rem !important;
            font-weight: 660 !important;
        }

        .abayo-cloud-pill {
            display: flex;
            align-items: center;
            gap: .48rem;
            width: 100%;
            box-sizing: border-box;
            padding: .62rem .68rem;
            margin-top: .9rem;
            border: 1px solid rgba(52, 211, 153, .19);
            border-radius: 10px;
            background: linear-gradient(135deg, rgba(5,150,105,.10), rgba(255,255,255,.025));
            color: #c9d8e9 !important;
            font-size: .72rem;
            font-weight: 630;
        }

        .abayo-cloud-dot {
            width: 8px;
            height: 8px;
            flex: 0 0 8px;
            border-radius: 999px;
            background: #94a3b8;
            box-shadow: 0 0 0 4px rgba(148,163,184,.08);
        }

        .abayo-cloud-dot.online {
            background: #34d399;
            box-shadow: 0 0 0 4px rgba(52,211,153,.09), 0 0 10px rgba(52,211,153,.35);
        }
        .abayo-cloud-dot.offline { background: #f87171; }

        .abayo-sidebar-version {
            color: #6f89aa !important;
            text-align: center;
            font-size: .63rem;
            letter-spacing: .04em;
            margin: .68rem 0 .14rem;
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
                padding-top: .62rem !important;
                padding-left: .68rem !important;
                padding-right: .68rem !important;
            }

            [data-testid="stSidebar"] [data-testid="stImage"] {
                padding: .45rem .4rem .36rem !important;
            }

            .abayo-sidebar-section {
                margin-top: .84rem;
                margin-bottom: .31rem;
            }

            [data-testid="stSidebar"] [data-testid="stPageLink"] a {
                min-height: 38px !important;
                padding-top: .45rem !important;
                padding-bottom: .45rem !important;
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
        label = "Cloud system connected"
    elif database_connected is False:
        dot_class = "offline"
        label = "Cloud system disconnected"
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

        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=215)
        else:
            st.markdown("### ABAYO")
            st.caption("AI Operations Assistant")

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
        st.page_link("pages/9_ai_assistant.py", label="AI Assistant", icon="✨", width="stretch")

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
