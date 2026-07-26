import sys
from pathlib import Path
from typing import Any

import streamlit as st


# ---------------------------------------------------------
# PROJECT PATH SETUP
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# ENGINE IMPORTS
# ---------------------------------------------------------

from knowledge_engine import diagnose_fault
from save_engine import save_fault

from shared_knowledge_engine import (
    get_record_fault,
    get_record_images,
    get_record_number,
    get_record_recipe,
    search_all_knowledge,
)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Fault Diagnosis | ABAYO",
    page_icon="🛠️",
    layout="wide",
)


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

STATIONS = [
    "General machine problem",
    "Pouch elevator",
    "Pouch picking station",
    "Pouch opening station",
    "Filling station",
    "Auger and stirrer",
    "Incline screw",
    "Sealing station",
    "Electrical system",
    "Pneumatic system",
]


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def safe_list(value: Any) -> list[str]:
    """Convert different stored values into a clean list."""

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        lines = value.replace(
            ";",
            "\n",
        ).splitlines()

        return [
            line.strip(" -•\t")
            for line in lines
            if line.strip(" -•\t")
        ]

    return [str(value)]


def get_diagnosis_causes(
    result: Any,
) -> list[str]:
    """Read possible causes from different diagnosis formats."""

    if isinstance(result, dict):
        return safe_list(
            result.get("causes")
            or result.get("possible_causes")
            or result.get("cause")
        )

    return []


def get_diagnosis_checks(
    result: Any,
) -> list[str]:
    """Read recommended checks from different diagnosis formats."""

    if isinstance(result, dict):
        return safe_list(
            result.get("checks")
            or result.get("recommended_checks")
            or result.get("inspection")
            or result.get("corrective_actions")
        )

    return []


def display_images(
    image_paths: list[str],
    heading: str,
) -> None:
    """Display saved images from any ABAYO record."""

    if not image_paths:
        return

    valid_images: list[Path] = []

    for image_path in image_paths:
        full_path = PROJECT_ROOT / image_path

        if full_path.exists():
            valid_images.append(full_path)

    if not valid_images:
        st.warning(
            "The saved image files could not be found."
        )
        return

    st.write(f"### {heading}")

    columns = st.columns(
        min(
            len(valid_images),
            2,
        )
    )

    for number, full_path in enumerate(
        valid_images
    ):
        with columns[
            number % len(columns)
        ]:
            st.image(
                str(full_path),
                caption=full_path.name,
                use_container_width=True,
            )


def display_match_score(
    record: dict[str, Any],
) -> None:
    """Display a match percentage when available."""

    match_score = record.get(
        "match_score"
    )

    if match_score is None:
        return

    try:
        score = float(match_score)
    except (
        TypeError,
        ValueError,
    ):
        return

    score = max(
        0.0,
        min(
            score,
            100.0,
        ),
    )

    st.progress(
        score / 100,
        text=f"{score:.1f}% match",
    )


def record_expander_title(
    record_number: str,
    name: str,
    record: dict[str, Any],
) -> str:
    """Create a consistent expander heading."""

    score = record.get(
        "match_score"
    )

    if score is None:
        return f"{record_number} — {name}"

    return (
        f"{record_number} — "
        f"{name} "
        f"({score}% match)"
    )


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------

st.title("🛠️ Fault Diagnosis")

st.caption(
    "ABAYO Assist AI — Fault knowledge, troubleshooting, "
    "maintenance memory and machine-component guidance"
)

st.warning(
    "Safety: Stop the machine and isolate electrical, "
    "pneumatic and mechanical energy before physical inspection."
)


# ---------------------------------------------------------
# PAGE TABS
# ---------------------------------------------------------

diagnosis_tab, teach_tab = st.tabs(
    [
        "🔍 Diagnose Fault",
        "➕ Add Fault Knowledge",
    ]
)


# =========================================================
# DIAGNOSIS TAB
# =========================================================

with diagnosis_tab:
    st.write("## Describe the Machine Problem")

    station = st.selectbox(
        "Machine station",
        STATIONS,
        key="fault_diagnosis_station",
    )

    problem = st.text_area(
        "Fault description",
        placeholder=(
            "Example: The suction cups are failing "
            "to pick the pouches."
        ),
        height=150,
        key="fault_diagnosis_problem",
    )

    uploaded_file = st.file_uploader(
        "Upload a machine or HMI image",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        key="fault_diagnosis_image",
    )

    if uploaded_file is not None:
        st.image(
            uploaded_file,
            caption=uploaded_file.name,
            use_container_width=True,
        )

    diagnose_button = st.button(
        "Diagnose Fault",
        type="primary",
        use_container_width=True,
        key="diagnose_fault_button",
    )

    if diagnose_button:
        if not problem.strip():
            st.error(
                "Describe the machine fault before diagnosing."
            )

        else:
            with st.spinner(
                "ABAYO is searching all connected knowledge..."
            ):
                try:
                    diagnosis_result = diagnose_fault(
                        problem,
                        station,
                    )
                except TypeError:
                    diagnosis_result = diagnose_fault(
                        station,
                        problem,
                    )

                shared_results = search_all_knowledge(
                    fault_text=problem,
                    station=station,
                    limit=5,
                )

            causes = get_diagnosis_causes(
                diagnosis_result
            )

            checks = get_diagnosis_checks(
                diagnosis_result
            )

            troubleshooting_notes = (
                shared_results.get(
                    "troubleshooting",
                    [],
                )
            )

            maintenance_records = (
                shared_results.get(
                    "maintenance",
                    [],
                )
            )

            component_results = (
                shared_results.get(
                    "components",
                    [],
                )
            )

            # -------------------------------------------------
            # POSSIBLE CAUSES
            # -------------------------------------------------

            st.write("## Possible Causes")

            if causes:
                for number, cause in enumerate(
                    causes,
                    start=1,
                ):
                    st.write(
                        f"{number}. {cause}"
                    )

            else:
                st.info(
                    "No possible causes are currently "
                    "recorded in the main fault database."
                )

            # -------------------------------------------------
            # RECOMMENDED CHECKS
            # -------------------------------------------------

            st.write("## Recommended Checks")

            if checks:
                for number, check in enumerate(
                    checks,
                    start=1,
                ):
                    st.write(
                        f"{number}. {check}"
                    )

            else:
                st.info(
                    "No recommended checks are currently recorded."
                )

            # -------------------------------------------------
            # TROUBLESHOOTING KNOWLEDGE
            # -------------------------------------------------

            st.write(
                "## Shared Troubleshooting Knowledge"
            )

            if troubleshooting_notes:
                for note in troubleshooting_notes:
                    solution_number = str(
                        note.get(
                            "solution_number",
                            "Troubleshooting solution",
                        )
                    )

                    fault_name = str(
                        note.get(
                            "fault",
                            "Unnamed fault",
                        )
                    )

                    with st.expander(
                        record_expander_title(
                            solution_number,
                            fault_name,
                            note,
                        )
                    ):
                        display_match_score(
                            note
                        )

                        st.write(
                            f"**Station:** "
                            f"{note.get('station', 'Not recorded')}"
                        )

                        st.write(
                            f"**Possible cause:** "
                            f"{note.get('cause', 'Not recorded')}"
                        )

                        st.write(
                            f"**Inspection:** "
                            f"{note.get('inspection', 'Not recorded')}"
                        )

                        st.write(
                            f"**Repair:** "
                            f"{note.get('repair', 'Not recorded')}"
                        )

                        notes_text = note.get(
                            "notes"
                        )

                        if notes_text:
                            st.write(
                                f"**Shared notes:** "
                                f"{notes_text}"
                            )

                        keywords = note.get(
                            "keywords",
                            [],
                        )

                        if keywords:
                            st.write(
                                "**Keywords:** "
                                + ", ".join(
                                    str(item)
                                    for item in keywords
                                )
                            )

                        aliases = note.get(
                            "aliases",
                            [],
                        )

                        if aliases:
                            st.write(
                                "**Alternative descriptions:** "
                                + ", ".join(
                                    str(item)
                                    for item in aliases
                                )
                            )

                        display_images(
                            get_record_images(
                                note
                            ),
                            "Troubleshooting Photos",
                        )

            else:
                st.info(
                    "No shared troubleshooting notes matched this fault."
                )

            # -------------------------------------------------
            # MAINTENANCE HISTORY
            # -------------------------------------------------

            st.write(
                "## Related Maintenance History"
            )

            if maintenance_records:
                for record in maintenance_records:
                    record_number = (
                        get_record_number(
                            record
                        )
                    )

                    record_fault = (
                        get_record_fault(
                            record
                        )
                    )

                    with st.expander(
                        record_expander_title(
                            record_number,
                            record_fault,
                            record,
                        )
                    ):
                        display_match_score(
                            record
                        )

                        st.write(
                            f"**Recipe:** "
                            f"{get_record_recipe(record)}"
                        )

                        st.write(
                            f"**Station:** "
                            f"{record.get('station', 'Not recorded')}"
                        )

                        st.write(
                            f"**Production status:** "
                            f"{record.get('production_status', 'Not recorded')}"
                        )

                        confirmed_cause = (
                            record.get(
                                "confirmed_cause"
                            )
                            or record.get(
                                "cause"
                            )
                            or "Not recorded"
                        )

                        st.write(
                            f"**Confirmed cause:** "
                            f"{confirmed_cause}"
                        )

                        corrective_action = (
                            record.get(
                                "corrective_action"
                            )
                            or record.get(
                                "repair"
                            )
                            or "Not recorded"
                        )

                        st.write(
                            f"**Corrective action:** "
                            f"{corrective_action}"
                        )

                        st.write(
                            f"**Downtime:** "
                            f"{record.get('downtime_minutes', 0)} minutes"
                        )

                        recorded_by = record.get(
                            "recorded_by"
                        )

                        if recorded_by:
                            st.write(
                                f"**Recorded by:** "
                                f"{recorded_by}"
                            )

                        maintenance_notes = (
                            record.get(
                                "notes"
                            )
                        )

                        if maintenance_notes:
                            st.write(
                                f"**Maintenance notes:** "
                                f"{maintenance_notes}"
                            )

                        display_images(
                            get_record_images(
                                record
                            ),
                            "Maintenance Photos",
                        )

            else:
                st.info(
                    "No related maintenance records matched this fault."
                )

            # -------------------------------------------------
            # MACHINE COMPONENTS
            # -------------------------------------------------

            st.write(
                "## Related Machine Components"
            )

            if component_results:
                for component in component_results:
                    component_number = str(
                        component.get(
                            "component_number",
                            "Component",
                        )
                    )

                    component_name = str(
                        component.get(
                            "component_name",
                            "Unnamed component",
                        )
                    )

                    with st.expander(
                        record_expander_title(
                            component_number,
                            component_name,
                            component,
                        )
                    ):
                        display_match_score(
                            component
                        )

                        st.write(
                            f"**Station:** "
                            f"{component.get('station', 'Not recorded')}"
                        )

                        st.write(
                            f"**Category:** "
                            f"{component.get('category', 'Not recorded')}"
                        )

                        manufacturer = component.get(
                            "manufacturer"
                        )

                        if manufacturer:
                            st.write(
                                f"**Manufacturer:** "
                                f"{manufacturer}"
                            )

                        model_number = component.get(
                            "model_number"
                        )

                        if model_number:
                            st.write(
                                f"**Model number:** "
                                f"{model_number}"
                            )

                        part_number = component.get(
                            "part_number"
                        )

                        if part_number:
                            st.write(
                                f"**Part number:** "
                                f"{part_number}"
                            )

                        st.write("### Function")

                        st.write(
                            component.get(
                                "function",
                                "Not recorded",
                            )
                        )

                        st.write(
                            "### Common Failures"
                        )

                        st.write(
                            component.get(
                                "common_failures",
                                "Not recorded",
                            )
                        )

                        st.write(
                            "### Fault Symptoms"
                        )

                        st.write(
                            component.get(
                                "fault_symptoms",
                                "Not recorded",
                            )
                        )

                        st.write(
                            "### Inspection Procedure"
                        )

                        st.write(
                            component.get(
                                "inspection_procedure",
                                "Not recorded",
                            )
                        )

                        st.write(
                            "### Replacement Procedure"
                        )

                        st.write(
                            component.get(
                                "replacement_procedure",
                                "Not recorded",
                            )
                        )

                        safety_notes = (
                            component.get(
                                "safety_notes"
                            )
                        )

                        if safety_notes:
                            st.warning(
                                f"Safety: {safety_notes}"
                            )

                        spare_location = (
                            component.get(
                                "spare_part_location"
                            )
                        )

                        if spare_location:
                            st.write(
                                f"**Spare-part location:** "
                                f"{spare_location}"
                            )

                        display_images(
                            get_record_images(
                                component
                            ),
                            "Component Photos",
                        )

            else:
                st.info(
                    "No related machine components found."
                )

            # -------------------------------------------------
            # IMAGE PLACEHOLDER
            # -------------------------------------------------

            if uploaded_file is not None:
                st.info(
                    "The uploaded image is displayed, but automatic "
                    "image analysis will be added when the ABAYO "
                    "AI Vision engine is connected."
                )


# =========================================================
# ADD FAULT KNOWLEDGE TAB
# =========================================================

with teach_tab:
    st.write(
        "## Add General Fault Knowledge"
    )

    st.caption(
        "Use this section for general possible causes and checks. "
        "Use Smart Troubleshooter for confirmed causes, repairs, "
        "notes and photographs."
    )

    new_station = st.selectbox(
        "Machine station",
        STATIONS,
        key="new_fault_station",
    )

    new_fault = st.text_area(
        "Fault description",
        placeholder=(
            "Example: Pouch is not picked "
            "from the pouch picking station."
        ),
        height=110,
        key="new_fault_description",
    )

    causes_text = st.text_area(
        "Possible causes",
        placeholder=(
            "Enter one cause per line.\n"
            "Dirty suction cups\n"
            "Vacuum hose leaking\n"
            "Venturi ejector blocked"
        ),
        height=150,
        key="new_fault_causes",
    )

    checks_text = st.text_area(
        "Checks or corrective actions",
        placeholder=(
            "Enter one check per line.\n"
            "Inspect the suction cups\n"
            "Check the vacuum hose\n"
            "Clean the Venturi ejector"
        ),
        height=150,
        key="new_fault_checks",
    )

    confirmation = st.checkbox(
        "I confirm that this fault information is accurate.",
        key="new_fault_confirmation",
    )

    if st.button(
        "Save Fault Knowledge",
        type="primary",
        use_container_width=True,
        key="save_fault_knowledge_button",
    ):
        causes = safe_list(
            causes_text
        )

        checks = safe_list(
            checks_text
        )

        if not new_fault.strip():
            st.error(
                "Enter the fault description."
            )

        elif not causes:
            st.error(
                "Enter at least one possible cause."
            )

        elif not checks:
            st.error(
                "Enter at least one check or corrective action."
            )

        elif not confirmation:
            st.error(
                "Confirm that the information is accurate."
            )

        else:
            try:
                save_fault(
                    station=new_station,
                    fault=new_fault.strip(),
                    causes=causes,
                    checks=checks,
                )

                st.success(
                    "Fault knowledge saved successfully."
                )

                st.info(
                    "The fault is now available in Fault Diagnosis."
                )

            except TypeError:
                try:
                    save_fault(
                        new_station,
                        new_fault.strip(),
                        causes,
                        checks,
                    )

                    st.success(
                        "Fault knowledge saved successfully."
                    )

                except Exception as error:
                    st.error(
                        "The fault knowledge could not be saved."
                    )

                    st.exception(
                        error
                    )

            except Exception as error:
                st.error(
                    "The fault knowledge could not be saved."
                )

                st.exception(
                    error
                )


st.divider()

st.caption(
    "ABAYO Assist AI — Pakona PFS AG maintenance knowledge system"
)