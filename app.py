"""ABAYO machine intelligence command center."""

from __future__ import annotations

from html import escape
import logging
from typing import Any

import streamlit as st

from activity_engine import log_activity
from component_engine import components_for_machine
from core.access import require_app_access
from core.auth import (
    admin_is_unlocked,
    configured_admin_pin,
    lock_admin,
    unlock_admin,
)
from core.constants import MACHINE_STATUSES
from core.database import check_database, get_supabase_client, select_rows
from core.machine_context import is_pakona_machine, machine_model_label
from core.machines import create_machine, machine_options
from core.settings import load_app_settings
from knowledge_engine import faults_for_machine
from maintenance_engine import calculate_summary, filter_maintenance_records
from recipe_engine import recipes_for_machine
from recycle_bin_engine import (
    load_active_machines,
    load_deleted_machines,
    purge_expired_machines,
    recycle_bin_is_ready,
    soft_delete_machine,
)
from storage.json_store import knowledge_store_is_ready
from ui.components import page_header, section_heading
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

LOGGER = logging.getLogger(__name__)

st.set_page_config(
    page_title="ABAYO",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()
require_app_access()


# Home-specific presentation. The shared theme remains deliberately conservative
# so feature pages stay stable while Home can evolve into the command center.
st.html(
    """
    <style>
    .command-hero,
    .ai-command-card,
    .snapshot-card,
    .insight-card,
    .knowledge-card,
    .activity-card {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 16px;
        box-shadow: 0 5px 20px rgba(16, 24, 40, .055);
    }

    .command-hero {
        padding: 1.35rem;
        min-height: 248px;
        border-left: 4px solid #2563eb;
        background: linear-gradient(135deg, #ffffff 0%, #f7faff 100%);
    }

    .eyebrow {
        color: #667085;
        font-size: .72rem;
        font-weight: 800;
        letter-spacing: .09em;
        text-transform: uppercase;
        margin-bottom: .55rem;
    }

    .command-machine-name {
        color: #101828;
        font-size: clamp(1.55rem, 3vw, 2rem);
        line-height: 1.15;
        font-weight: 850;
        margin-bottom: .25rem;
    }

    .command-machine-meta {
        color: #667085;
        font-size: .9rem;
        line-height: 1.5;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: .4rem;
        margin-top: .9rem;
        padding: .42rem .72rem;
        border-radius: 999px;
        font-size: .78rem;
        font-weight: 750;
    }

    .status-pill.online { background: #ecfdf3; color: #027a48; }
    .status-pill.offline { background: #fef3f2; color: #b42318; }
    .status-pill.maintenance { background: #fffaeb; color: #b54708; }

    .hero-details {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .65rem;
        margin-top: 1rem;
        padding-top: .9rem;
        border-top: 1px solid #eaecf0;
    }

    .hero-detail-label { color: #98a2b3; font-size: .68rem; margin-bottom: .2rem; }
    .hero-detail-value { color: #344054; font-size: .82rem; font-weight: 700; }

    .ai-command-card {
        min-height: 248px;
        padding: 1.35rem;
        background: linear-gradient(145deg, #0b1f36 0%, #132a4a 100%);
        border-color: #193b65;
        color: #ffffff;
    }

    .ai-icon {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(96, 165, 250, .16);
        font-size: 1.35rem;
        margin-bottom: .85rem;
    }

    .ai-command-title { color: #ffffff; font-size: 1.2rem; font-weight: 800; }
    .ai-command-copy { color: #c4d4e8; font-size: .86rem; line-height: 1.55; margin-top: .45rem; }
    .ai-command-scope { color: #8fb4df; font-size: .72rem; margin-top: .8rem; }

    .snapshot-card { padding: 1.05rem 1.1rem; min-height: 132px; }
    .snapshot-icon { font-size: 1.25rem; margin-bottom: .6rem; }
    .snapshot-label { color: #667085; font-size: .75rem; font-weight: 700; }
    .snapshot-value { color: #101828; font-size: 1.45rem; font-weight: 850; margin-top: .2rem; }
    .snapshot-note { color: #98a2b3; font-size: .72rem; margin-top: .25rem; line-height: 1.35; }

    .insight-card {
        padding: 1.2rem 1.25rem;
        background: linear-gradient(135deg, #f5f3ff 0%, #eff6ff 100%);
        border-color: #ddd6fe;
    }
    .insight-kicker { color: #6941c6; font-size: .72rem; font-weight: 850; letter-spacing: .08em; text-transform: uppercase; }
    .insight-title { color: #101828; font-size: 1.05rem; font-weight: 800; margin-top: .35rem; }
    .insight-copy { color: #475467; font-size: .86rem; line-height: 1.55; margin-top: .35rem; }

    .knowledge-card { padding: .9rem 1rem; min-height: 100px; }
    .knowledge-name { color: #475467; font-size: .76rem; font-weight: 700; }
    .knowledge-number { color: #101828; font-size: 1.45rem; font-weight: 850; margin-top: .15rem; }
    .knowledge-note { color: #98a2b3; font-size: .7rem; margin-top: .12rem; }

    .activity-card {
        padding: .78rem .9rem;
        margin-bottom: .5rem;
        display: flex;
        gap: .75rem;
        align-items: flex-start;
    }
    .activity-icon {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 34px;
        background: #f2f4f7;
    }
    .activity-title { color: #101828; font-size: .84rem; font-weight: 750; }
    .activity-meta { color: #98a2b3; font-size: .7rem; margin-top: .18rem; }

    .command-caption {
        color: #667085;
        font-size: .78rem;
        margin: -.25rem 0 .65rem;
    }

    @media (max-width: 800px) {
        .command-hero, .ai-command-card { min-height: 0; }
        .hero-details { grid-template-columns: 1fr; gap: .45rem; }
        .snapshot-card { min-height: 0; }
    }
    </style>
    """
)


def _safe(value: Any, fallback: str = "") -> str:
    text = value if value not in (None, "") else fallback
    return escape(str(text))


def _connect_database() -> tuple[Any | None, bool, str]:
    try:
        client = get_supabase_client()
    except Exception as exc:
        LOGGER.warning("Unable to configure Supabase: %s", exc)
        return None, False, str(exc)

    status = check_database(client)
    if not status.connected:
        return None, False, status.message
    return client, True, status.message


def _load_dashboard_table(client: Any | None, table_name: str) -> list[dict[str, Any]]:
    if client is None:
        return []
    try:
        return select_rows(client, table_name)
    except Exception as exc:
        LOGGER.warning("Unable to load %s: %s", table_name, exc)
        return []


def _short_time(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value).replace("T", " ")[:16]


def _activity_icon(activity_type: Any) -> str:
    text = str(activity_type or "").lower()
    if "maint" in text:
        return "🛠️"
    if "fault" in text or "alarm" in text:
        return "⚠️"
    if "recipe" in text:
        return "📖"
    if "component" in text:
        return "⚙️"
    if "machine" in text:
        return "🏭"
    return "•"


def _render_add_machine_form(client: Any | None, app_settings: dict[str, Any]) -> None:
    if not st.session_state.get("show_add_machine"):
        return

    section_heading("Add New Machine")
    with st.form("add_machine_form", clear_on_submit=False):
        left, right = st.columns(2)
        with left:
            new_machine_name = st.text_input("Machine Name *", placeholder="e.g. Pakona PFS AG")
            new_manufacturer = st.text_input("Manufacturer", placeholder="e.g. Pakona")
            new_model = st.text_input("Model", placeholder="e.g. PFS AG")
        with right:
            default_location = str(app_settings.get("default_machine_location") or "")
            default_status = str(app_settings.get("default_machine_status") or "Online")
            if default_status not in MACHINE_STATUSES:
                default_status = "Online"
            new_location = st.text_input("Location", value=default_location)
            new_status = st.selectbox(
                "Status",
                MACHINE_STATUSES,
                index=MACHINE_STATUSES.index(default_status),
            )
            new_description = st.text_area(
                "Description",
                placeholder="What this machine does, production line, or useful identifying notes.",
            )

        save_column, cancel_column = st.columns(2)
        with save_column:
            save_machine = st.form_submit_button("Save Machine", type="primary", width="stretch")
        with cancel_column:
            cancel_add = st.form_submit_button("Cancel", width="stretch")

        if cancel_add:
            st.session_state.show_add_machine = False
            st.rerun()

        if save_machine:
            if not new_machine_name.strip():
                st.error("Machine name is required.")
            elif client is None:
                st.error("The cloud database must be connected before saving.")
            else:
                try:
                    result = create_machine(
                        client,
                        machine_name=new_machine_name,
                        manufacturer=new_manufacturer,
                        model=new_model,
                        location=new_location,
                        description=new_description,
                        status=new_status,
                    )
                except Exception as exc:
                    LOGGER.exception("Unable to create machine")
                    st.error(f"Unable to save machine: {exc}")
                else:
                    new_id = result.machine.get("id")
                    st.session_state.selected_machine_id = new_id
                    st.session_state.show_add_machine = False
                    log_activity(new_id, "Machine", f"Added machine {new_machine_name.strip()}")
                    st.session_state.dashboard_flash_message = f"{new_machine_name.strip()} was added successfully."
                    if not result.modules_created:
                        st.session_state.dashboard_flash_warning = (
                            "The machine was created, but its default modules could not be initialized."
                        )
                    st.rerun()


def _render_delete_flow(client: Any | None, machine: dict[str, Any], recycle_ready: bool) -> None:
    machine_id = machine.get("id")
    if st.session_state.get("pending_machine_delete") != machine_id:
        return

    machine_name = str(machine.get("machine_name") or "Unnamed Machine")
    st.warning(f"Move {machine_name} to the Recycle Bin? It will remain recoverable for 30 days.")

    try:
        expected_pin = configured_admin_pin(st.secrets)
    except Exception:
        expected_pin = ""

    if not recycle_ready:
        st.error("Deletion is unavailable until the recycle-bin migration is applied.")
        return
    if client is None:
        st.error("Deletion is unavailable while the database is offline.")
        return
    if not expected_pin:
        st.error("Deletion is locked. Configure ABAYO_ADMIN_PIN in Streamlit Secrets.")
        return

    if not admin_is_unlocked(st.session_state):
        entered_pin = st.text_input("Administrator PIN", type="password", key=f"dashboard_admin_pin_{machine_id}")
        unlock_column, cancel_column = st.columns(2)
        with unlock_column:
            if st.button("Unlock for 10 minutes", key=f"unlock_delete_{machine_id}", width="stretch"):
                if unlock_admin(st.session_state, entered_pin, expected_pin):
                    st.rerun()
                st.error("Incorrect administrator PIN.")
        with cancel_column:
            if st.button("Cancel", key=f"cancel_locked_delete_{machine_id}", width="stretch"):
                st.session_state.pending_machine_delete = None
                st.rerun()
        return

    typed_name = st.text_input(f'Type "{machine_name}" to confirm', key=f"confirm_machine_name_{machine_id}")
    confirm_column, cancel_column = st.columns(2)
    with confirm_column:
        if st.button(
            "Move to Recycle Bin",
            key=f"confirm_soft_delete_{machine_id}",
            type="primary",
            width="stretch",
            disabled=typed_name.strip() != machine_name,
        ):
            try:
                deleted = soft_delete_machine(client, machine_id)
                if not deleted:
                    raise RuntimeError("The database did not confirm deletion.")
            except Exception as exc:
                LOGGER.exception("Unable to delete machine")
                st.error(f"Unable to delete machine: {exc}")
            else:
                st.session_state.selected_machine_id = None
                st.session_state.pending_machine_delete = None
                st.session_state.dashboard_flash_message = f"{machine_name} was moved to the Recycle Bin."
                lock_admin(st.session_state)
                st.rerun()
    with cancel_column:
        if st.button("Cancel", key=f"cancel_soft_delete_{machine_id}", width="stretch"):
            st.session_state.pending_machine_delete = None
            st.rerun()


def _render_snapshot_card(icon: str, label: str, value: Any, note: str) -> None:
    st.html(
        f"""
        <div class="snapshot-card">
            <div class="snapshot-icon">{_safe(icon)}</div>
            <div class="snapshot-label">{_safe(label)}</div>
            <div class="snapshot-value">{_safe(value)}</div>
            <div class="snapshot-note">{_safe(note)}</div>
        </div>
        """
    )


def _render_knowledge_card(name: str, number: int, note: str) -> None:
    st.html(
        f"""
        <div class="knowledge-card">
            <div class="knowledge-name">{_safe(name)}</div>
            <div class="knowledge-number">{number}</div>
            <div class="knowledge-note">{_safe(note)}</div>
        </div>
        """
    )


supabase, database_connected, database_message = _connect_database()
query_failures: list[str] = []
recycle_bin_ready = False
deleted_machines: list[dict[str, Any]] = []

if supabase is not None:
    recycle_bin_ready = recycle_bin_is_ready(supabase)

if recycle_bin_ready:
    try:
        purge_expired_machines(supabase)
        machines = load_active_machines(supabase)
        deleted_machines = load_deleted_machines(supabase)
    except Exception as exc:
        LOGGER.warning("Machine recycle-bin query failed: %s", exc)
        query_failures.append("machines")
        machines = []
else:
    machines = _load_dashboard_table(supabase, "machines")

app_settings = load_app_settings(supabase)
active_machine_ids = {machine.get("id") for machine in machines}
selected_machine_id = st.session_state.get("selected_machine_id")
if selected_machine_id not in active_machine_ids:
    st.session_state.selected_machine_id = machines[0].get("id") if machines else None

st.session_state.setdefault("show_add_machine", False)
st.session_state.setdefault("pending_machine_delete", None)

render_sidebar(database_connected=database_connected, recycle_count=len(deleted_machines))

display_name = str(app_settings.get("display_name") or "ABAYO User")
welcome_title = str(app_settings.get("welcome_title") or "Welcome back")
welcome_subtitle = str(
    app_settings.get("welcome_subtitle")
    or "Monitor. Diagnose. Maintain. Preserve machine knowledge."
)
page_header(f"{welcome_title}, {display_name} 👋", welcome_subtitle)

for flash_key, renderer in (
    ("dashboard_flash_message", st.success),
    ("dashboard_flash_warning", st.warning),
):
    if flash_key in st.session_state:
        renderer(st.session_state.pop(flash_key))

notices: list[str] = []
if not database_connected:
    notices.append("Cloud data is unavailable. ABAYO is in read-only degraded mode until Supabase reconnects.")
elif not recycle_bin_ready:
    notices.append("The machine Recycle Bin is not active yet.")
if supabase is not None and not knowledge_store_is_ready(supabase):
    notices.append("Durable knowledge storage is not installed yet.")
if query_failures:
    notices.append("Some dashboard data could not be loaded: " + ", ".join(dict.fromkeys(query_failures)) + ".")
if notices:
    with st.expander("System notices", expanded=False):
        for notice in notices:
            st.warning(notice)

if not machines:
    st.info("No machine is registered yet. Add your first machine to start building its operational memory.")
    if st.button("＋ Add first machine", type="primary", width="stretch"):
        st.session_state.show_add_machine = True
        st.rerun()
    _render_add_machine_form(supabase, app_settings)
    st.stop()

# Compact machine context bar. The sidebar remains the persistent machine switcher,
# but Home also makes current context obvious before any operator action.
options = machine_options(machines)
option_labels = [label for label, _machine_id in options]
option_ids = dict(options)
selected_index = next(
    (
        index
        for index, (_label, machine_id) in enumerate(options)
        if machine_id == st.session_state.selected_machine_id
    ),
    0,
)

selector_column, add_column, menu_column = st.columns([5.4, 1.35, .7])
with selector_column:
    chosen_label = st.selectbox(
        "Current machine",
        options=option_labels,
        index=selected_index,
        label_visibility="collapsed",
    )
    chosen_id = option_ids[chosen_label]
    if chosen_id != st.session_state.selected_machine_id:
        st.session_state.selected_machine_id = chosen_id
        st.session_state.pending_machine_delete = None
        st.rerun()
with add_column:
    if st.button("＋ Add Machine", key="home_add_machine", width="stretch"):
        st.session_state.show_add_machine = True
        st.rerun()
with menu_column:
    with st.popover("⋯", help="Machine options", width="stretch"):
        st.page_link("pages/10_machine_settings.py", label="Profile & Status", icon="🏭", width="stretch")
        if st.button("Delete", key=f"home_delete_{chosen_id}", width="stretch"):
            st.session_state.pending_machine_delete = chosen_id
            st.rerun()

selected_machine = next(
    (machine for machine in machines if machine.get("id") == st.session_state.selected_machine_id),
    machines[0],
)
machine_id = selected_machine.get("id")
machine_name = str(selected_machine.get("machine_name") or "Unnamed Machine")
machine_model = machine_model_label(selected_machine)
legacy_knowledge = is_pakona_machine(selected_machine)

machine_faults = faults_for_machine(machine_id=machine_id, allow_legacy=legacy_knowledge)
machine_maintenance = filter_maintenance_records(machine_id=machine_id)
machine_recipes = recipes_for_machine(
    machine_id=machine_id,
    machine_model=machine_model,
    allow_legacy=legacy_knowledge,
)
machine_components = components_for_machine(machine_id=machine_id, allow_legacy=legacy_knowledge)
maintenance_summary = calculate_summary(machine_maintenance)
knowledge_total = len(machine_faults) + len(machine_recipes) + len(machine_components)

_render_delete_flow(supabase, selected_machine, recycle_bin_ready)
_render_add_machine_form(supabase, app_settings)

st.html('<div class="command-caption">Everything below is scoped to the selected machine only.</div>')

hero_column, ai_column = st.columns([1.65, 1])
with hero_column:
    status = str(selected_machine.get("status") or "Unknown")
    status_class = status.lower() if status.lower() in {"online", "offline", "maintenance"} else "offline"
    st.html(
        f"""
        <div class="command-hero">
            <div class="eyebrow">Selected machine</div>
            <div class="command-machine-name">{_safe(machine_name)}</div>
            <div class="command-machine-meta">{_safe(selected_machine.get('manufacturer'), 'Manufacturer not recorded')} · {_safe(selected_machine.get('model'), 'Model not recorded')}</div>
            <div class="status-pill {_safe(status_class)}">● {_safe(status)} <span style="font-weight:500;opacity:.75">recorded status</span></div>
            <div class="hero-details">
                <div><div class="hero-detail-label">Location</div><div class="hero-detail-value">{_safe(selected_machine.get('location'), 'Not recorded')}</div></div>
                <div><div class="hero-detail-label">Machine memory</div><div class="hero-detail-value">{knowledge_total + len(machine_maintenance)} records</div></div>
                <div><div class="hero-detail-label">Knowledge scope</div><div class="hero-detail-value">This machine only</div></div>
            </div>
        </div>
        """
    )
    st.page_link("pages/10_machine_settings.py", label="Open Profile & Status", icon="🏭", width="stretch")

with ai_column:
    st.html(
        f"""
        <div class="ai-command-card">
            <div class="ai-icon">✨</div>
            <div class="eyebrow" style="color:#8fb4df">Industrial copilot</div>
            <div class="ai-command-title">Ask ABAYO</div>
            <div class="ai-command-copy">Search faults, maintenance history, recipes, components and troubleshooting evidence for <strong>{_safe(machine_name)}</strong>.</div>
            <div class="ai-command-scope">Grounded to the selected machine · no cross-machine mixing</div>
        </div>
        """
    )
    if st.button("Ask ABAYO about this machine →", type="primary", width="stretch"):
        st.switch_page("pages/9_ai_assistant.py")

section_heading("Quick Actions")
quick_actions = (
    ("🔧", "Diagnose", "pages/1_fault_diagnosis.py", "Diagnose a fault"),
    ("🛠️", "Maintenance", "pages/3_maintenance_history.py", "Record or review maintenance"),
    ("📖", "Recipes", "pages/2_recipe_library.py", "Open machine recipes"),
    ("⚙️", "Components", "pages/5_machine_components.py", "Find machine components"),
)
quick_columns = st.columns(4)
for column, (icon, title, page, help_text) in zip(quick_columns, quick_actions):
    with column:
        st.page_link(page, label=title, icon=icon, help=help_text, width="stretch")

section_heading("Machine Snapshot")
snapshot_columns = st.columns(4)
with snapshot_columns[0]:
    _render_snapshot_card("🏭", "Recorded status", status, "Status saved in the machine profile")
with snapshot_columns[1]:
    _render_snapshot_card(
        "⏱️",
        "Recorded downtime",
        f"{maintenance_summary.get('total_downtime_minutes', 0):g} min",
        "Sum of this machine's maintenance records",
    )
with snapshot_columns[2]:
    _render_snapshot_card("🛠️", "Maintenance cases", len(machine_maintenance), "History attached to this machine")
with snapshot_columns[3]:
    _render_snapshot_card("🧠", "Knowledge items", knowledge_total, "Faults + recipes + components")

summary_station = str(maintenance_summary.get("most_affected_station") or "None")
summary_fault = str(maintenance_summary.get("most_repeated_fault") or "None")
if machine_maintenance:
    if summary_station != "None":
        insight_title = f"{summary_station} appears most often in maintenance history"
    else:
        insight_title = "Maintenance history is building"
    insight_copy = (
        f"ABAYO has {len(machine_maintenance)} maintenance case(s) for this machine with "
        f"{maintenance_summary.get('total_downtime_minutes', 0):g} recorded downtime minutes. "
        f"Most repeated recorded fault: {summary_fault}."
    )
elif machine_faults:
    insight_title = "Fault intelligence is available"
    insight_copy = (
        f"ABAYO has {len(machine_faults)} saved fault record(s) for {machine_name}. "
        "Maintenance evidence will make future recommendations stronger as confirmed repairs are recorded."
    )
elif knowledge_total:
    insight_title = "Machine knowledge is taking shape"
    insight_copy = (
        f"ABAYO currently has {knowledge_total} recipe/component/fault knowledge item(s) for this machine. "
        "Continue recording confirmed faults and corrective actions to strengthen diagnosis."
    )
else:
    insight_title = "Build this machine's operational memory"
    insight_copy = (
        "Start with confirmed faults, stable recipes and identified components. ABAYO will use those records as grounded evidence later."
    )

section_heading("ABAYO Insight")
st.html(
    f"""
    <div class="insight-card">
        <div class="insight-kicker">Evidence-based summary</div>
        <div class="insight-title">{_safe(insight_title)}</div>
        <div class="insight-copy">{_safe(insight_copy)}</div>
    </div>
    """
)
if st.button("Explore this with ABAYO →", key="insight_ask_abayo", width="stretch"):
    st.switch_page("pages/9_ai_assistant.py")

section_heading("Machine Knowledge")
knowledge_columns = st.columns(4)
with knowledge_columns[0]:
    _render_knowledge_card("Known faults", len(machine_faults), "Diagnostic evidence")
    st.page_link("pages/1_fault_diagnosis.py", label="Open faults", width="stretch")
with knowledge_columns[1]:
    _render_knowledge_card("Recipes", len(machine_recipes), "Saved production settings")
    st.page_link("pages/2_recipe_library.py", label="Open recipes", width="stretch")
with knowledge_columns[2]:
    _render_knowledge_card("Components", len(machine_components), "Identified machine parts")
    st.page_link("pages/5_machine_components.py", label="Open components", width="stretch")
with knowledge_columns[3]:
    _render_knowledge_card("Maintenance", len(machine_maintenance), "Confirmed service history")
    st.page_link("pages/3_maintenance_history.py", label="Open maintenance", width="stretch")

activity_column, evidence_column = st.columns([1.45, 1])
with activity_column:
    section_heading("Recent Activity")
    activities: list[dict[str, Any]] = []
    if supabase is not None:
        try:
            response = (
                supabase.table("machine_activity")
                .select("*")
                .eq("machine_id", machine_id)
                .order("created_at", desc=True)
                .limit(6)
                .execute()
            )
            activities = response.data or []
        except Exception as exc:
            LOGGER.warning("Unable to load recent activity: %s", exc)

    if activities:
        for activity in activities:
            st.html(
                f"""
                <div class="activity-card">
                    <div class="activity-icon">{_activity_icon(activity.get('activity_type'))}</div>
                    <div>
                        <div class="activity-title">{_safe(activity.get('description'), 'Machine activity')}</div>
                        <div class="activity-meta">{_safe(activity.get('activity_type'), 'Activity')} · {_safe(_short_time(activity.get('created_at')), 'Time not recorded')}</div>
                    </div>
                </div>
                """
            )
    else:
        st.caption("No activity has been recorded for this machine yet.")

with evidence_column:
    section_heading("Latest Evidence")
    if machine_maintenance:
        latest = machine_maintenance[0]
        st.html(
            f"""
            <div class="knowledge-card" style="min-height:0;margin-bottom:.6rem">
                <div class="knowledge-name">Latest maintenance</div>
                <div style="color:#101828;font-weight:800;margin-top:.3rem">{_safe(latest.get('fault'), 'Maintenance record')}</div>
                <div class="knowledge-note">{_safe(latest.get('station'), 'Station not recorded')} · {_safe(latest.get('record_number'), 'Record')}</div>
            </div>
            """
        )
    if machine_recipes:
        latest_recipe = machine_recipes[-1]
        st.html(
            f"""
            <div class="knowledge-card" style="min-height:0;margin-bottom:.6rem">
                <div class="knowledge-name">Saved recipe</div>
                <div style="color:#101828;font-weight:800;margin-top:.3rem">{_safe(latest_recipe.get('recipe_name'), 'Unnamed recipe')}</div>
                <div class="knowledge-note">{_safe(latest_recipe.get('status'), 'Status not recorded')}</div>
            </div>
            """
        )
    if machine_components:
        latest_component = machine_components[-1]
        st.html(
            f"""
            <div class="knowledge-card" style="min-height:0;margin-bottom:.6rem">
                <div class="knowledge-name">Identified component</div>
                <div style="color:#101828;font-weight:800;margin-top:.3rem">{_safe(latest_component.get('component_name'), 'Unnamed component')}</div>
                <div class="knowledge-note">{_safe(latest_component.get('station'), 'Station not recorded')}</div>
            </div>
            """
        )
    if not (machine_maintenance or machine_recipes or machine_components):
        st.caption("Add maintenance, recipes or components and the newest evidence will appear here.")

st.html('<div class="app-footer">ABAYO · machine intelligence grounded in recorded evidence</div>')
