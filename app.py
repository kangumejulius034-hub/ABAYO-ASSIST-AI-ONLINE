"""ABAYO launch dashboard.

The dashboard coordinates UI and domain services only. Database access,
administrator authorization, machine creation, shared navigation, and visual
components live in focused modules so feature pages can reuse them safely.
"""

from __future__ import annotations

import logging
from typing import Any

import streamlit as st

from activity_engine import log_activity
from core.access import require_app_access
from core.auth import (
    admin_is_unlocked,
    configured_admin_pin,
    lock_admin,
    unlock_admin,
)
from core.constants import APP_VERSION, MACHINE_STATUSES
from core.database import check_database, get_supabase_client, select_rows
from core.machines import create_machine, machine_options
from core.settings import load_app_settings
from knowledge_engine import load_faults
from maintenance_engine import load_maintenance_records
from recycle_bin_engine import (
    load_active_machines,
    load_deleted_machines,
    purge_expired_machines,
    recycle_bin_is_ready,
    soft_delete_machine,
)
from storage.json_store import knowledge_store_is_ready
from ui.components import (
    action_card,
    machine_card,
    metric_card,
    page_header,
    section_heading,
)
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


def connect_database() -> tuple[Any | None, bool, str]:
    """Create a client and verify the database with a real query."""

    try:
        client = get_supabase_client()
    except Exception as exc:
        LOGGER.warning("Unable to configure Supabase: %s", exc)
        return None, False, str(exc)

    status = check_database(client)
    if not status.connected:
        return None, False, status.message
    return client, True, status.message


supabase, database_connected, database_message = connect_database()
query_failures: list[str] = []


def load_dashboard_table(table_name: str) -> list[dict[str, Any]]:
    """Load dashboard data while keeping failures distinct from empty tables."""

    if supabase is None:
        return []

    try:
        return select_rows(supabase, table_name)
    except Exception as exc:
        LOGGER.warning("Unable to load %s: %s", table_name, exc)
        query_failures.append(table_name)
        return []


recycle_bin_ready = False
deleted_machines: list[dict[str, Any]] = []

if supabase is not None:
    recycle_bin_ready = recycle_bin_is_ready(supabase)

if recycle_bin_ready:
    try:
        purge_expired_machines(supabase)
    except Exception as exc:
        LOGGER.warning("Expired machine purge failed: %s", exc)
        query_failures.append("recycle-bin cleanup")

    try:
        machines = load_active_machines(supabase)
        deleted_machines = load_deleted_machines(supabase)
    except Exception as exc:
        LOGGER.warning("Machine recycle-bin query failed: %s", exc)
        query_failures.append("machines")
        machines = []
else:
    machines = load_dashboard_table("machines")

faults = load_faults()
maintenance_records = load_maintenance_records()
app_settings = load_app_settings(supabase)

active_machine_ids = {machine.get("id") for machine in machines}
selected_machine_id = st.session_state.get("selected_machine_id")
if selected_machine_id not in active_machine_ids:
    st.session_state.selected_machine_id = (
        machines[0].get("id") if machines else None
    )

st.session_state.setdefault("show_add_machine", False)
st.session_state.setdefault("pending_machine_delete", None)

render_sidebar(
    database_connected=database_connected,
    recycle_count=len(deleted_machines),
)

display_name = str(app_settings.get("display_name") or "ABAYO User")
welcome_title = str(app_settings.get("welcome_title") or "Welcome back")
welcome_subtitle = str(
    app_settings.get("welcome_subtitle")
    or "Monitor machines and preserve operational knowledge."
)
page_header(f"{welcome_title}, {display_name} 👋", welcome_subtitle)

for flash_key, renderer in (
    ("dashboard_flash_message", st.success),
    ("dashboard_flash_warning", st.warning),
):
    if flash_key in st.session_state:
        renderer(st.session_state.pop(flash_key))

if not database_connected:
    st.error(
        "Cloud data is unavailable. ABAYO is in read-only degraded mode until "
        "the Supabase connection is restored."
    )
elif not recycle_bin_ready:
    st.warning(
        "The machine Recycle Bin is not active. Apply the supplied Supabase "
        "migration before allowing machine deletion."
    )

if supabase is not None and not knowledge_store_is_ready(supabase):
    st.warning(
        "Durable knowledge storage is not installed. Apply the launch schema "
        "before adding recipes, faults, maintenance, or component records."
    )

if query_failures:
    failed_names = ", ".join(dict.fromkeys(query_failures))
    st.warning(f"Some dashboard data could not be loaded: {failed_names}.")

online_count = sum(
    str(machine.get("status", "")).lower() == "online" for machine in machines
)

metric_columns = st.columns(4)
metric_specs = (
    {
        "icon": "📡",
        "icon_class": "green-icon",
        "label": "Machines Online",
        "value": online_count,
        "note": f"of {len(machines)} registered machines",
    },
    {
        "icon": "⚠️",
        "icon_class": "red-icon",
        "label": "Fault Records",
        "value": len(faults),
        "note": "Saved fault knowledge",
    },
    {
        "icon": "🗓️",
        "icon_class": "orange-icon",
        "label": "Maintenance Records",
        "value": len(maintenance_records),
        "note": "Recorded service history",
    },
    {
        "icon": "☁️",
        "icon_class": "blue-icon",
        "label": "Cloud Status",
        "value": "Connected" if database_connected else "Offline",
        "note": "Supabase database",
        "value_class": "connected" if database_connected else "offline",
    },
)

for column, specification in zip(metric_columns, metric_specs):
    with column:
        metric_card(**specification)

section_heading("Machine Workspace")

if machines:
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

    switch_column, menu_column, add_column = st.columns([4, 0.65, 1.25])
    with switch_column:
        chosen_label = st.selectbox(
            "Select machine",
            options=option_labels,
            index=selected_index,
            label_visibility="collapsed",
        )
        chosen_id = option_ids[chosen_label]
        if chosen_id != st.session_state.selected_machine_id:
            st.session_state.selected_machine_id = chosen_id
            st.session_state.pending_machine_delete = None
            st.rerun()

    with menu_column:
        with st.popover("⋮", help="Machine options", width="stretch"):
            if st.button(
                "Open",
                key=f"open_machine_{chosen_id}",
                width="stretch",
            ):
                st.session_state.selected_machine_id = chosen_id
                st.session_state.pending_machine_delete = None
                st.rerun()
            if st.button(
                "Delete",
                key=f"menu_delete_machine_{chosen_id}",
                help="Move this machine to the Recycle Bin",
                width="stretch",
            ):
                st.session_state.pending_machine_delete = chosen_id
                st.rerun()

    with add_column:
        if st.button(
            "＋ Add Machine",
            key="workspace_add_machine",
            width="stretch",
        ):
            st.session_state.show_add_machine = True
            st.rerun()

    selected_machine = next(
        (
            machine
            for machine in machines
            if machine.get("id") == st.session_state.selected_machine_id
        ),
        machines[0],
    )
    machine_id = selected_machine.get("id")
    machine_name = str(
        selected_machine.get("machine_name") or "Unnamed Machine"
    )
    machine_card(selected_machine)

    if st.session_state.pending_machine_delete == machine_id:
        st.warning(
            f"Move {machine_name} to the Recycle Bin? It will remain "
            "recoverable for 30 days."
        )
        try:
            expected_pin = configured_admin_pin(st.secrets)
        except Exception:
            expected_pin = ""

        if not recycle_bin_ready:
            st.error("Deletion is unavailable until the recycle-bin migration is applied.")
        elif not expected_pin:
            st.error(
                "Deletion is locked. Configure ABAYO_ADMIN_PIN in Streamlit Secrets."
            )
        elif not admin_is_unlocked(st.session_state):
            entered_pin = st.text_input(
                "Administrator PIN",
                type="password",
                key=f"dashboard_admin_pin_{machine_id}",
            )
            unlock_column, cancel_column = st.columns(2)
            with unlock_column:
                if st.button(
                    "Unlock for 10 minutes",
                    key=f"unlock_delete_{machine_id}",
                    width="stretch",
                ):
                    if unlock_admin(
                        st.session_state,
                        entered_pin,
                        expected_pin,
                    ):
                        st.rerun()
                    st.error("Incorrect administrator PIN.")
            with cancel_column:
                if st.button(
                    "Cancel",
                    key=f"cancel_locked_delete_{machine_id}",
                    width="stretch",
                ):
                    st.session_state.pending_machine_delete = None
                    st.rerun()
        else:
            typed_machine_name = st.text_input(
                f'Type "{machine_name}" to confirm',
                key=f"confirm_machine_name_{machine_id}",
            )
            confirm_column, cancel_column = st.columns(2)
            with confirm_column:
                if st.button(
                    "Move to Recycle Bin",
                    key=f"confirm_soft_delete_{machine_id}",
                    type="primary",
                    width="stretch",
                    disabled=typed_machine_name.strip() != machine_name,
                ):
                    try:
                        deleted = soft_delete_machine(supabase, machine_id)
                        if not deleted:
                            raise RuntimeError("The database did not confirm deletion.")
                    except Exception as exc:
                        LOGGER.exception("Unable to delete machine")
                        st.error(f"Unable to delete machine: {exc}")
                    else:
                        remaining = [
                            machine
                            for machine in machines
                            if machine.get("id") != machine_id
                        ]
                        st.session_state.selected_machine_id = (
                            remaining[0].get("id") if remaining else None
                        )
                        st.session_state.pending_machine_delete = None
                        st.session_state.dashboard_flash_message = (
                            f"{machine_name} was moved to the Recycle Bin."
                        )
                        lock_admin(st.session_state)
                        st.rerun()
            with cancel_column:
                if st.button(
                    "Cancel",
                    key=f"cancel_soft_delete_{machine_id}",
                    width="stretch",
                ):
                    st.session_state.pending_machine_delete = None
                    st.rerun()
else:
    st.info("No machine is registered. Select Add Machine to begin.")

if st.session_state.show_add_machine:
    section_heading("Add New Machine")
    with st.form("add_machine_form", clear_on_submit=False):
        left, right = st.columns(2)
        with left:
            new_machine_name = st.text_input("Machine Name *")
            new_manufacturer = st.text_input("Manufacturer")
            new_model = st.text_input("Model")
        with right:
            default_location = str(
                app_settings.get("default_machine_location") or ""
            )
            default_status = str(
                app_settings.get("default_machine_status") or "Online"
            )
            if default_status not in MACHINE_STATUSES:
                default_status = "Online"
            new_location = st.text_input("Location", value=default_location)
            new_status = st.selectbox(
                "Status",
                MACHINE_STATUSES,
                index=MACHINE_STATUSES.index(default_status),
            )
            new_description = st.text_area("Description")

        save_column, cancel_column = st.columns(2)
        with save_column:
            save_machine = st.form_submit_button(
                "Save Machine",
                type="primary",
                width="stretch",
            )
        with cancel_column:
            cancel_add = st.form_submit_button("Cancel", width="stretch")

        if cancel_add:
            st.session_state.show_add_machine = False
            st.rerun()

        if save_machine:
            if not new_machine_name.strip():
                st.error("Machine name is required.")
            elif supabase is None:
                st.error("The cloud database must be connected before saving.")
            else:
                try:
                    result = create_machine(
                        supabase,
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
                    log_activity(
                        new_id,
                        "Machine",
                        f"Added machine {new_machine_name.strip()}",
                    )
                    st.session_state.dashboard_flash_message = (
                        f"{new_machine_name.strip()} was added successfully."
                    )
                    if not result.modules_created:
                        st.session_state.dashboard_flash_warning = (
                            "The machine was created, but its default modules "
                            "could not be initialized. Check machine_modules."
                        )
                    st.rerun()

section_heading("Quick Actions")
action_columns = st.columns(4)
quick_actions = (
    (
        "🔧",
        "Diagnose a Fault",
        "Find possible causes and recommended checks.",
        "pages/1_fault_diagnosis.py",
        "Open Fault Diagnosis",
    ),
    (
        "📖",
        "Browse Recipes",
        "Search and review machine recipe parameters.",
        "pages/2_recipe_library.py",
        "Open Recipe Library",
    ),
    (
        "📋",
        "Maintenance History",
        "View servicing and maintenance records.",
        "pages/3_maintenance_history.py",
        "Open Maintenance",
    ),
    (
        "⚙️",
        "Machine Components",
        "Explore machine parts and components.",
        "pages/5_machine_components.py",
        "Open Components",
    ),
)

for column, (icon, title, note, page, label) in zip(
    action_columns,
    quick_actions,
):
    with column:
        action_card(icon=icon, title=title, note=note)
        st.page_link(page, label=label, width="stretch")

section_heading("Recent Activity")
activities: list[dict[str, Any]] = []
if supabase is not None:
    try:
        response = (
            supabase.table("machine_activity")
            .select("*, machines(machine_name)")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        activities = response.data or []
    except Exception as exc:
        LOGGER.warning("Unable to load recent activity: %s", exc)

if activities:
    rows = []
    for activity in activities:
        machine_details = activity.get("machines") or {}
        rows.append(
            {
                "Machine": machine_details.get("machine_name", "Unknown Machine"),
                "Activity": activity.get("description", ""),
                "Type": activity.get("activity_type", ""),
                "Status": activity.get("status", ""),
                "Time": activity.get("created_at", ""),
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)
else:
    st.info("Recent operational activities will appear here.")

st.html(
    f'<div class="app-footer">ABAYO AI Operations Assistant • '
    f"System Version {APP_VERSION}</div>"
)
