from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from component_engine import add_component, search_components
from core.access import require_app_access
from core.machine_context import current_machine, is_pakona_machine, machine_display_name, machine_model_label, selected_machine_id
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

st.set_page_config(page_title="Machine Components | ABAYO", page_icon="⚙️", layout="wide")
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
legacy = is_pakona_machine(machine)

st.title("⚙️ Machine Components")
st.caption(f"Active machine: {machine_name} • Components are isolated to this machine profile.")

VIEW, ADD = st.tabs(["View Components", "Add Component"])

with VIEW:
    c1, c2, c3 = st.columns(3)
    with c1:
        search_text = st.text_input("Search", placeholder="Sensor, motor, valve, suction cup...")
    with c2:
        station = st.text_input("Station filter", placeholder="Leave blank for all stations")
    with c3:
        category = st.text_input("Category filter", placeholder="Electrical, mechanical...")

    results = search_components(
        search_text=search_text,
        station=station,
        category=category,
        machine_id=machine_id,
        allow_legacy=legacy,
    )

    if not results:
        st.info(f"No components are recorded for {machine_name} yet.")
    else:
        st.write(f"### Components Found: {len(results)}")
        for component in results:
            number = component.get("component_number", "Component")
            name = component.get("component_name", "Unnamed component")
            with st.expander(f"{number} — {name}"):
                left, right = st.columns(2)
                with left:
                    st.write(f"**Station:** {component.get('station') or 'Not recorded'}")
                    st.write(f"**Category:** {component.get('category') or 'Not recorded'}")
                    st.write(f"**Manufacturer:** {component.get('manufacturer') or 'Not recorded'}")
                with right:
                    st.write(f"**Model:** {component.get('model_number') or 'Not recorded'}")
                    st.write(f"**Part number:** {component.get('part_number') or 'Not recorded'}")
                    st.write(f"**Spare location:** {component.get('spare_part_location') or 'Not recorded'}")
                for heading, field in (
                    ("Function", "function"),
                    ("Common failures", "common_failures"),
                    ("Fault symptoms", "fault_symptoms"),
                    ("Inspection", "inspection_procedure"),
                    ("Replacement", "replacement_procedure"),
                ):
                    value = component.get(field)
                    if value:
                        st.write(f"**{heading}:** {value}")
                if component.get("safety_notes"):
                    st.warning(f"Safety: {component.get('safety_notes')}")

with ADD:
    st.info(f"This component will be saved only under {machine_name}.")
    component_name = st.text_input("Component name")
    c1, c2 = st.columns(2)
    with c1:
        station = st.text_input("Machine station")
        category = st.text_input("Category", placeholder="Mechanical, Electrical, Pneumatic...")
        manufacturer = st.text_input("Manufacturer")
        model_number = st.text_input("Model number")
    with c2:
        part_number = st.text_input("Part number")
        spare_location = st.text_input("Spare-part storage location")
        related_faults_text = st.text_area("Related faults", placeholder="Separate with commas")
    function = st.text_area("Function")
    common_failures = st.text_area("Common failures")
    fault_symptoms = st.text_area("Fault symptoms")
    inspection = st.text_area("Inspection procedure")
    replacement = st.text_area("Replacement procedure")
    safety = st.text_area("Safety notes")

    if st.button("Save Component", type="primary", width="stretch"):
        if not component_name.strip():
            st.error("Component name is required.")
        else:
            number = add_component(
                component_name,
                station,
                category,
                function,
                common_failures,
                fault_symptoms,
                inspection,
                replacement,
                safety_notes=safety,
                manufacturer=manufacturer,
                model_number=model_number,
                part_number=part_number,
                spare_part_location=spare_location,
                related_faults=[item.strip() for item in related_faults_text.split(",") if item.strip()],
                machine_id=machine_id,
                machine_model=machine_model,
            )
            st.success(f"Saved {number} under {machine_name}.")
            st.rerun()
