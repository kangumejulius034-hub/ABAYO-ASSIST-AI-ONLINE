from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.access import require_app_access
from core.machine_context import current_machine, machine_display_name, selected_machine_id
from troubleshooting_engine import add_solution, search_fault
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

st.set_page_config(page_title="Knowledge Base | ABAYO", page_icon="🧠", layout="wide")
apply_theme()
require_app_access()
render_sidebar()

machine = current_machine()
machine_id = selected_machine_id()
if not machine or machine_id in (None, ""):
    st.warning("Select or add a machine first.")
    st.stop()

machine_name = machine_display_name(machine)
st.title("🧠 Smart Troubleshooter")
st.caption(f"Active machine: {machine_name} • Troubleshooting knowledge is isolated to this machine.")

SEARCH, ADD = st.tabs(["Search Knowledge", "Add Solution"])

with SEARCH:
    station = st.text_input("Machine station", placeholder="Optional")
    query = st.text_area("Describe the fault", height=150)
    if st.button("Search Troubleshooting Knowledge", type="primary", width="stretch"):
        if not query.strip():
            st.error("Describe the fault first.")
        else:
            results = search_fault(
                query,
                station=station,
                limit=10,
                minimum_score=10.0,
                machine_id=machine_id,
            )
            if not results:
                st.info(f"No troubleshooting knowledge matched for {machine_name}.")
            else:
                for result in results:
                    number = result.get("solution_number", "Solution")
                    fault = result.get("fault", "Unnamed fault")
                    score = result.get("match_score")
                    label = f"{number} — {fault}"
                    if score is not None:
                        label += f" ({score}% match)"
                    with st.expander(label):
                        st.write(f"**Station:** {result.get('station') or 'Not recorded'}")
                        st.write(f"**Cause:** {result.get('cause') or 'Not recorded'}")
                        st.write(f"**Inspection:** {result.get('inspection') or 'Not recorded'}")
                        st.write(f"**Repair:** {result.get('repair') or 'Not recorded'}")
                        if result.get("notes"):
                            st.write(f"**Notes:** {result.get('notes')}")

with ADD:
    st.info(f"This solution will be saved only under {machine_name}.")
    station = st.text_input("Station", key="add_solution_station")
    fault = st.text_area("Fault / symptom", key="add_solution_fault")
    cause = st.text_area("Cause", key="add_solution_cause")
    inspection = st.text_area("Inspection steps", key="add_solution_inspection")
    repair = st.text_area("Repair / corrective action", key="add_solution_repair")
    notes = st.text_area("Notes", key="add_solution_notes")
    keywords_text = st.text_input("Keywords", placeholder="Comma separated")
    aliases_text = st.text_input("Alternative descriptions", placeholder="Comma separated")

    if st.button("Save Troubleshooting Solution", width="stretch"):
        if not fault.strip():
            st.error("Fault or symptom is required.")
        else:
            number = add_solution(
                fault,
                cause,
                inspection,
                repair,
                station,
                notes=notes,
                keywords=[item.strip() for item in keywords_text.split(",") if item.strip()],
                aliases=[item.strip() for item in aliases_text.split(",") if item.strip()],
                machine_id=machine_id,
            )
            st.success(f"Saved {number} under {machine_name}.")
            st.rerun()
