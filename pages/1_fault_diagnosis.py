from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.access import require_app_access
from core.machine_context import current_machine, is_pakona_machine, machine_display_name, selected_machine_id
import knowledge_engine
from knowledge_engine import diagnose_fault, load_faults
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


def active_fault_records() -> list[dict]:
    """Return only records belonging to the active machine.

    This filter intentionally lives in the page as a deployment-safety fallback.
    Streamlit can briefly reload a page before every imported module has refreshed;
    the page therefore does not require a newly-added engine helper just to start.
    """

    try:
        records = load_faults()
    except Exception:
        return []

    scoped: list[dict] = []
    for record in records:
        if not isinstance(record, dict):
            continue

        saved_id = record.get("machine_id")
        if saved_id not in (None, ""):
            if str(saved_id) == str(machine_id):
                scoped.append(record)
            continue

        # Records created before multi-machine isolation belong only to the
        # original Pakona profile. They must never leak into another machine.
        if legacy:
            scoped.append(record)

    return scoped


def diagnose_active_machine(problem: str, station: str) -> dict:
    """Diagnose with the machine-aware engine, with a safe local fallback."""

    try:
        return diagnose_fault(
            problem,
            station,
            machine_id=machine_id,
            allow_legacy=legacy,
        )
    except TypeError:
        # Compatibility path for a short Streamlit hot-reload window where an
        # older knowledge_engine is still resident in memory.
        scorer = getattr(knowledge_engine, "calculate_match_score", None)
        if not callable(scorer):
            return {
                "matched_faults": [],
                "confidence": 0,
                "causes": ["No matching fault was found for the selected machine."],
                "checks": ["Record this fault under the active machine so ABAYO can use it next time."],
            }

        ranked: list[tuple[int, dict]] = []
        for record in active_fault_records():
            try:
                score = int(scorer(problem, station, record))
            except Exception:
                continue
            if score >= 3:
                ranked.append((score, record))

        ranked.sort(key=lambda item: item[0], reverse=True)
        best = ranked[:3]
        if not best:
            return {
                "matched_faults": [],
                "confidence": 0,
                "causes": ["No matching fault was found for the selected machine."],
                "checks": ["Record this fault under the active machine so ABAYO can use it next time."],
            }

        causes: list[str] = []
        checks: list[str] = []
        names: list[str] = []
        for _score, record in best:
            names.append(str(record.get("fault") or "Unnamed fault"))
            record_causes = record.get("possible_causes") or record.get("causes") or []
            record_checks = record.get("checks") or record.get("recommended_checks") or []
            if isinstance(record_causes, str):
                record_causes = [line for line in record_causes.splitlines() if line.strip()]
            if isinstance(record_checks, str):
                record_checks = [line for line in record_checks.splitlines() if line.strip()]
            causes.extend(str(item) for item in record_causes)
            checks.extend(str(item) for item in record_checks)

        return {
            "matched_faults": list(dict.fromkeys(names)),
            "causes": list(dict.fromkeys(causes)),
            "checks": list(dict.fromkeys(checks)),
            "confidence": min(100, max(30, best[0][0] * 10)),
        }


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
            result = diagnose_active_machine(problem, station)
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
    records = active_fault_records()
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
