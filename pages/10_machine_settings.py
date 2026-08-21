from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.access import require_app_access
from core.constants import MACHINE_STATUSES
from core.database import get_supabase_client
from core.machine_context import current_machine, machine_display_name
from core.machines import update_machine
from ui.sidebar import render_sidebar
from ui.theme import apply_theme


st.set_page_config(
    page_title="Machine Profile & Status | ABAYO",
    page_icon="🏭",
    layout="wide",
)
apply_theme()
require_app_access()
render_sidebar()

st.title("🏭 Machine Profile & Status")
st.caption(
    "Edit the currently selected machine. Its database ID remains unchanged, "
    "so all recipes, faults, maintenance and components stay attached to it."
)

try:
    supabase = get_supabase_client()
except Exception as exc:
    st.error(f"Cloud database unavailable: {exc}")
    st.stop()

machine = current_machine(supabase)
if not machine:
    st.warning("Select or add a machine first.")
    st.stop()

st.info(f"Editing: **{machine_display_name(machine)}**")

current_status = str(machine.get("status") or "Offline")
if current_status not in MACHINE_STATUSES:
    current_status = "Offline"

with st.form("edit_selected_machine"):
    left, right = st.columns(2)

    with left:
        machine_name = st.text_input(
            "Machine Name *",
            value=str(machine.get("machine_name") or ""),
        )
        manufacturer = st.text_input(
            "Manufacturer",
            value=str(machine.get("manufacturer") or ""),
        )
        model = st.text_input(
            "Model",
            value=str(machine.get("model") or ""),
        )

    with right:
        location = st.text_input(
            "Location",
            value=str(machine.get("location") or ""),
        )
        status = st.selectbox(
            "Status",
            MACHINE_STATUSES,
            index=MACHINE_STATUSES.index(current_status),
            help=(
                "Online means available for production; Maintenance means intentionally "
                "out for service; Offline means not currently operating."
            ),
        )
        description = st.text_area(
            "Description",
            value=str(machine.get("description") or ""),
        )

    save = st.form_submit_button("Save Machine", type="primary", width="stretch")

if save:
    try:
        updated = update_machine(
            supabase,
            machine.get("id"),
            machine_name=machine_name,
            manufacturer=manufacturer,
            model=model,
            location=location,
            description=description,
            status=status,
        )
    except Exception as exc:
        st.error(f"Unable to update machine: {exc}")
    else:
        st.success(
            f"{machine_display_name(updated)} saved. Status is now "
            f"{updated.get('status', status)}."
        )
        st.rerun()
