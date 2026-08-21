from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.access import require_app_access
from core.machine_context import current_machine, machine_display_name, machine_model_label, selected_machine_id
from maintenance_engine import add_maintenance_record, calculate_summary, filter_maintenance_records
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

st.set_page_config(page_title="Maintenance | ABAYO", page_icon="🛠️", layout="wide")
apply_theme()
require_app_access()
render_sidebar()

machine = current_machine()
machine_id = selected_machine_id()
if not machine or machine_id in (None, ""):
    st.warning("Select or add a machine first.")
    st.stop()

machine_name = machine_display_name(machine)
machine_model = machine_model_label(machine)

st.title("🛠️ Maintenance History")
st.caption(f"Active machine: {machine_name} • Maintenance records are isolated to this machine.")

VIEW, ADD = st.tabs(["View History", "Add Maintenance Record"])

with VIEW:
    c1, c2, c3 = st.columns(3)
    with c1:
        station_filter = st.text_input("Station filter")
    with c2:
        status_filter = st.text_input("Production status filter")
    with c3:
        search_text = st.text_input("Search history")

    records = filter_maintenance_records(
        station=station_filter,
        production_status=status_filter,
        search_text=search_text,
        machine_id=machine_id,
    )
    summary = calculate_summary(records)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Records", summary["total_records"])
    m2.metric("Total downtime", f"{summary['total_downtime_minutes']} min")
    m3.metric("Top fault", summary["most_repeated_fault"])
    m4.metric("Most affected station", summary["most_affected_station"])

    if not records:
        st.info(f"No maintenance records are recorded for {machine_name} yet.")
    else:
        for record in records:
            number = record.get("record_number", "Maintenance record")
            fault = record.get("fault", "Unnamed fault")
            with st.expander(f"{number} — {fault}"):
                st.write(f"**Station:** {record.get('station') or 'Not recorded'}")
                st.write(f"**Recipe:** {record.get('recipe_name') or 'Not recorded'}")
                st.write(f"**Confirmed cause:** {record.get('confirmed_cause') or 'Not recorded'}")
                st.write(f"**Corrective action:** {record.get('corrective_action') or 'Not recorded'}")
                st.write(f"**Downtime:** {record.get('downtime_minutes', 0)} minutes")
                if record.get("recorded_by"):
                    st.write(f"**Recorded by:** {record.get('recorded_by')}")
                if record.get("notes"):
                    st.write(f"**Notes:** {record.get('notes')}")

with ADD:
    st.info(f"This maintenance record will be saved only under {machine_name}.")
    c1, c2 = st.columns(2)
    with c1:
        recipe_name = st.text_input("Recipe / product")
        station = st.text_input("Machine station")
        fault = st.text_area("Fault / work description", height=110)
        confirmed_cause = st.text_area("Confirmed cause", height=100)
    with c2:
        corrective_action = st.text_area("Corrective action", height=110)
        downtime = st.number_input("Downtime (minutes)", min_value=0.0, step=1.0)
        recorded_by = st.text_input("Recorded by")
        production_status = st.text_input("Production status")
    production_shift = st.text_input("Production shift")
    batch_number = st.text_input("Batch number")
    notes = st.text_area("Notes", height=100)

    if st.button("Save Maintenance Record", type="primary", width="stretch"):
        if not fault.strip():
            st.error("Fault or work description is required.")
        else:
            number = add_maintenance_record(
                machine_model,
                recipe_name,
                station,
                fault,
                confirmed_cause,
                corrective_action,
                downtime,
                recorded_by,
                production_status=production_status,
                production_shift=production_shift,
                batch_number=batch_number,
                notes=notes,
                machine_id=machine_id,
            )
            st.success(f"Saved {number} under {machine_name}.")
            st.rerun()
