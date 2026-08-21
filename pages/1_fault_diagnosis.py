from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.access import require_app_access
from core.machine_context import current_machine, is_pakona_machine, machine_display_name, selected_machine_id
from knowledge_engine import diagnose_fault, faults_for_machine
from save_engine import save_fault
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

st.set_page_config(page_title="Fault Diagnosis | ABAYO", page_icon="🔧", layout="wide")
apply_theme()
require_app_access()
render_sidebar()

machine = current_machine()
machine_id = selected_machine_id()
if not machine or machine_id in (None, ""):
    st.warning("Select or add a machine first.")
    st.stop()

machine_name = machine_display_name(machine)
legacy = is_pakona_machine(machine)

st.title("🔧 Fault Diagnosis")
st.caption(f"Active machine: {machine_name} • Diagnosis only searches this machine's knowledge.")
st.warning("Safety: isolate electrical, pneumatic and mechanical energy before physical inspection.")

DIAGNOSE, SAVED = st.tabs(["Diagnose Fault", "Saved Fault Knowledge"])

with DIAGNOSE:
    station = st.text_input("Machine station", placeholder="Example: infeed conveyor, sealing jaw, dosing unit")
    problem = st.text_area("Describe the problem", height=160, placeholder="What should happen, and what happens instead?")

    if st.button("Diagnose Fault", type="primary", width="stretch"):
        if not problem.strip():
            st.error("Describe the machine problem first.")
        else:
            result = diagnose_fault(
                problem,
                station,
                machine_id=machine_id,
                allow_legacy=legacy,
            )
            st.subheader("Possible Causes")
            for cause in result.get("causes", []):
                st.write(f"- {cause}")
            st.subheader("Recommended Checks")
            for check in result.get("checks", []):
                st.write(f"- {check}")
            if result.get("confidence") is not None:
                st.metric("Knowledge match confidence", f"{result.get('confidence', 0)}%")

    st.divider()
    st.subheader("Add Confirmed Fault Knowledge")
    known_fault = st.text_input("Fault name / symptom")
    causes_text = st.text_area("Possible or confirmed causes", placeholder="One per line")
    checks_text = st.text_area("Recommended checks", placeholder="One per line")

    if st.button("Save Fault Knowledge", width="stretch"):
        if not known_fault.strip():
            st.error("Fault name is required.")
        else:
            causes = [line.strip(" -•\t") for line in causes_text.splitlines() if line.strip(" -•\t")]
            checks = [line.strip(" -•\t") for line in checks_text.splitlines() if line.strip(" -•\t")]
            if save_fault(station, known_fault, causes, checks):
                st.success(f"Fault knowledge saved under {machine_name}.")
                st.rerun()
            else:
                st.error("The fault could not be saved.")

with SAVED:
    records = faults_for_machine(machine_id=machine_id, allow_legacy=legacy)
    if not records:
        st.info(f"No saved fault knowledge exists for {machine_name} yet.")
    else:
        st.write(f"### Saved Faults: {len(records)}")
        for index, record in enumerate(records, start=1):
            title = record.get("fault") or f"Fault {index}"
            with st.expander(str(title)):
                st.write(f"**Station:** {record.get('station') or 'Not recorded'}")
                causes = record.get("possible_causes") or record.get("causes") or []
                checks = record.get("checks") or record.get("recommended_checks") or []
                if isinstance(causes, str):
                    causes = [line for line in causes.splitlines() if line.strip()]
                if isinstance(checks, str):
                    checks = [line for line in checks.splitlines() if line.strip()]
                if causes:
                    st.write("**Causes:**")
                    for cause in causes:
                        st.write(f"- {cause}")
                if checks:
                    st.write("**Checks:**")
                    for check in checks:
                        st.write(f"- {check}")
