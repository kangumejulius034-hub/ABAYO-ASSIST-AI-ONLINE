import re
import sys
from pathlib import Path

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

from shared_knowledge_engine import (
    get_record_fault,
    get_record_images,
    get_record_number,
    get_record_recipe,
    search_all_knowledge,
)

from troubleshooting_engine import (
    add_solution,
    load_troubleshooting,
    save_troubleshooting,
)


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Smart Troubleshooter | ABAYO",
    page_icon="🧠",
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


IMAGE_ROOT = (
    PROJECT_ROOT
    / "knowledge"
    / "troubleshooting_images"
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def safe_folder_name(text: str) -> str:
    """Convert text into a safe Windows folder name."""

    cleaned_text = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text.strip(),
    )

    return cleaned_text.strip("_") or "unnamed"


def save_uploaded_images(
    uploaded_images,
    folder_name: str,
) -> list[str]:
    """Save uploaded troubleshooting images."""

    saved_paths: list[str] = []

    if not uploaded_images:
        return saved_paths

    destination_folder = (
        IMAGE_ROOT
        / safe_folder_name(folder_name)
    )

    destination_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    for image_number, uploaded_image in enumerate(
        uploaded_images,
        start=1,
    ):
        original_suffix = Path(
            uploaded_image.name
        ).suffix.lower()

        if original_suffix not in {
            ".jpg",
            ".jpeg",
            ".png",
        }:
            original_suffix = ".jpg"

        destination_path = (
            destination_folder
            / (
                f"image_{image_number}"
                f"{original_suffix}"
            )
        )

        duplicate_number = 1

        while destination_path.exists():
            destination_path = (
                destination_folder
                / (
                    f"image_{image_number}_"
                    f"{duplicate_number}"
                    f"{original_suffix}"
                )
            )

            duplicate_number += 1

        with destination_path.open(
            "wb"
        ) as image_file:
            image_file.write(
                uploaded_image.getbuffer()
            )

        relative_path = (
            destination_path
            .relative_to(PROJECT_ROOT)
            .as_posix()
        )

        saved_paths.append(
            relative_path
        )

    return saved_paths


def move_temporary_images(
    solution_number: str,
    temporary_folder_name: str,
    old_image_paths: list[str],
) -> list[str]:
    """Move newly uploaded images into the permanent solution folder."""

    if not old_image_paths:
        return []

    temporary_folder = (
        IMAGE_ROOT
        / safe_folder_name(
            temporary_folder_name
        )
    )

    permanent_folder = (
        IMAGE_ROOT
        / safe_folder_name(
            solution_number
        )
    )

    permanent_folder.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if temporary_folder.exists():
        if permanent_folder.exists():
            for image_file in temporary_folder.iterdir():
                destination_path = (
                    permanent_folder
                    / image_file.name
                )

                duplicate_number = 1

                while destination_path.exists():
                    destination_path = (
                        permanent_folder
                        / (
                            f"{image_file.stem}_"
                            f"{duplicate_number}"
                            f"{image_file.suffix}"
                        )
                    )

                    duplicate_number += 1

                image_file.rename(
                    destination_path
                )

            try:
                temporary_folder.rmdir()
            except OSError:
                pass

        else:
            temporary_folder.rename(
                permanent_folder
            )

    updated_paths: list[str] = []

    for old_path in old_image_paths:
        file_name = Path(
            old_path
        ).name

        new_path = (
            Path("knowledge")
            / "troubleshooting_images"
            / safe_folder_name(
                solution_number
            )
            / file_name
        )

        updated_paths.append(
            new_path.as_posix()
        )

    return updated_paths


def update_solution_image_paths(
    solution_number: str,
    image_paths: list[str],
) -> None:
    """Update the saved troubleshooting record with permanent image paths."""

    records = load_troubleshooting()

    for record in records:
        if (
            record.get("solution_number")
            == solution_number
        ):
            record["image_paths"] = image_paths
            break

    save_troubleshooting(records)


def display_saved_images(
    image_paths: list[str],
    heading: str,
) -> None:
    """Display saved troubleshooting or maintenance images."""

    if not image_paths:
        return

    st.write(f"### {heading}")

    available_images = []

    for image_path in image_paths:
        full_path = (
            PROJECT_ROOT
            / image_path
        )

        if full_path.exists():
            available_images.append(
                full_path
            )

    if not available_images:
        st.warning(
            "The saved image files could not be found."
        )
        return

    columns = st.columns(
        min(
            len(available_images),
            2,
        )
    )

    for image_number, full_path in enumerate(
        available_images
    ):
        with columns[
            image_number % len(columns)
        ]:
            st.image(
                str(full_path),
                caption=full_path.name,
                use_container_width=True,
            )


def display_match_score(
    record: dict,
) -> None:
    """Display the intelligent matching percentage."""

    match_score = record.get(
        "match_score"
    )

    if match_score is None:
        return

    try:
        score_value = float(
            match_score
        )
    except (
        TypeError,
        ValueError,
    ):
        return

    st.progress(
        min(
            max(
                score_value / 100,
                0.0,
            ),
            1.0,
        ),
        text=f"{score_value:.1f}% match",
    )


def parse_comma_separated_items(
    text: str,
) -> list[str]:
    """Convert comma-separated text into a clean list."""

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------

st.title("🧠 Smart Troubleshooter")

st.caption(
    "ABAYO Assist AI — Intelligent troubleshooting, "
    "maintenance memory and visual fault evidence"
)

st.info(
    "Search one machine problem and ABAYO will check both "
    "shared troubleshooting knowledge and previous maintenance records."
)


# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------

search_tab, teach_tab = st.tabs(
    [
        "🔍 Troubleshoot Fault",
        "➕ Teach ABAYO",
    ]
)


# ---------------------------------------------------------
# SEARCH TAB
# ---------------------------------------------------------

with search_tab:
    st.write("## Describe the Machine Problem")

    search_station = st.selectbox(
        "Machine station",
        STATIONS,
        key="smart_search_station",
    )

    search_text = st.text_area(
        "Fault description",
        placeholder=(
            "Example: The suction cups are failing "
            "to pick the pouch."
        ),
        height=140,
        key="smart_search_text",
    )

    search_button = st.button(
        "Search for Solutions",
        type="primary",
        use_container_width=True,
        key="smart_search_button",
    )

    if search_button:
        if not search_text.strip():
            st.error(
                "Describe the machine fault before searching."
            )

        else:
            with st.spinner(
                "ABAYO is searching troubleshooting "
                "knowledge and maintenance history..."
            ):
                shared_results = search_all_knowledge(
                    fault_text=search_text.strip(),
                    station=search_station,
                    limit=10,
                )

            troubleshooting_results = (
                shared_results.get(
                    "troubleshooting",
                    [],
                )
            )

            maintenance_results = (
                shared_results.get(
                    "maintenance",
                    [],
                )
            )

            st.write(
                "## Shared Troubleshooting Knowledge"
            )

            if troubleshooting_results:
                for result in troubleshooting_results:
                    solution_number = result.get(
                        "solution_number",
                        "Troubleshooting solution",
                    )

                    fault_name = result.get(
                        "fault",
                        "Unnamed fault",
                    )

                    match_score = result.get(
                        "match_score"
                    )

                    if match_score is not None:
                        expander_title = (
                            f"{solution_number} — "
                            f"{fault_name} "
                            f"({match_score}% match)"
                        )
                    else:
                        expander_title = (
                            f"{solution_number} — "
                            f"{fault_name}"
                        )

                    with st.expander(
                        expander_title
                    ):
                        display_match_score(
                            result
                        )

                        st.write(
                            f"**Station:** "
                            f"{result.get('station', 'Not recorded')}"
                        )

                        st.write(
                            f"**Possible cause:** "
                            f"{result.get('cause', 'Not recorded')}"
                        )

                        st.write(
                            f"**Inspection:** "
                            f"{result.get('inspection', 'Not recorded')}"
                        )

                        st.write(
                            f"**Repair:** "
                            f"{result.get('repair', 'Not recorded')}"
                        )

                        notes = result.get(
                            "notes"
                        )

                        if notes:
                            st.write(
                                f"**Shared notes:** {notes}"
                            )

                        keywords = result.get(
                            "keywords",
                            [],
                        )

                        if keywords:
                            st.write(
                                "**Keywords:** "
                                + ", ".join(keywords)
                            )

                        aliases = result.get(
                            "aliases",
                            [],
                        )

                        if aliases:
                            st.write(
                                "**Alternative fault descriptions:** "
                                + ", ".join(aliases)
                            )

                        display_saved_images(
                            get_record_images(
                                result
                            ),
                            "Troubleshooting Photos",
                        )

            else:
                st.warning(
                    "No troubleshooting knowledge matched this fault."
                )

            st.write(
                "## Related Maintenance History"
            )

            if maintenance_results:
                for record in maintenance_results:
                    record_number = get_record_number(
                        record
                    )

                    record_fault = get_record_fault(
                        record
                    )

                    match_score = record.get(
                        "match_score"
                    )

                    if match_score is not None:
                        expander_title = (
                            f"{record_number} — "
                            f"{record_fault} "
                            f"({match_score}% match)"
                        )
                    else:
                        expander_title = (
                            f"{record_number} — "
                            f"{record_fault}"
                        )

                    with st.expander(
                        expander_title
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

                        downtime = record.get(
                            "downtime_minutes",
                            0,
                        )

                        st.write(
                            f"**Downtime:** "
                            f"{downtime} minutes"
                        )

                        recorded_by = record.get(
                            "recorded_by"
                        )

                        if recorded_by:
                            st.write(
                                f"**Recorded by:** "
                                f"{recorded_by}"
                            )

                        record_notes = record.get(
                            "notes"
                        )

                        if record_notes:
                            st.write(
                                f"**Maintenance notes:** "
                                f"{record_notes}"
                            )

                        display_saved_images(
                            get_record_images(
                                record
                            ),
                            "Maintenance Photos",
                        )

            else:
                st.info(
                    "No related maintenance records were found."
                )

            if (
                not troubleshooting_results
                and not maintenance_results
            ):
                st.error(
                    "ABAYO has no strong match yet. "
                    "After confirming the real cause and repair, "
                    "save the solution in the Teach ABAYO tab."
                )


# ---------------------------------------------------------
# TEACH TAB
# ---------------------------------------------------------

with teach_tab:
    st.write(
        "## Teach ABAYO a New Troubleshooting Solution"
    )

    st.caption(
        "Knowledge saved here becomes available in both "
        "Smart Troubleshooter and Fault Diagnosis."
    )

    new_station = st.selectbox(
        "Machine station",
        STATIONS,
        key="teach_station",
    )

    new_fault = st.text_area(
        "Fault description",
        placeholder=(
            "Example: Pouches are not being picked "
            "from the pouch picking station."
        ),
        height=110,
        key="teach_fault",
    )

    new_cause = st.text_area(
        "Confirmed or likely cause",
        placeholder=(
            "Example: Suction cups are dirty, worn, "
            "misaligned or receiving weak vacuum."
        ),
        height=110,
        key="teach_cause",
    )

    new_inspection = st.text_area(
        "Inspection procedure",
        placeholder=(
            "Example: Inspect suction cups, vacuum hoses, "
            "Venturi ejector and pouch alignment."
        ),
        height=130,
        key="teach_inspection",
    )

    new_repair = st.text_area(
        "Repair or corrective action",
        placeholder=(
            "Example: Clean or replace suction cups, "
            "repair vacuum leaks and test pouch pickup."
        ),
        height=130,
        key="teach_repair",
    )

    new_notes = st.text_area(
        "Shared notes",
        placeholder=(
            "Add safety warnings, operator observations, "
            "HMI alarms, recipe effects or useful lessons."
        ),
        height=120,
        key="teach_notes",
    )

    keyword_text = st.text_input(
        "Keywords",
        placeholder=(
            "Example: pouch, pickup, suction cup, vacuum, dust"
        ),
        key="teach_keywords",
    )

    alias_text = st.text_area(
        "Alternative fault descriptions",
        placeholder=(
            "Enter similar descriptions separated by commas. "
            "Example: bag pickup failing, pouch not collected, "
            "suction cups missing pouch"
        ),
        height=100,
        key="teach_aliases",
    )

    uploaded_images = st.file_uploader(
        "Upload troubleshooting photographs",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        accept_multiple_files=True,
        key="teach_uploaded_images",
    )

    if uploaded_images:
        st.write("### Image Preview")

        preview_columns = st.columns(
            min(
                len(uploaded_images),
                2,
            )
        )

        for image_number, uploaded_image in enumerate(
            uploaded_images
        ):
            with preview_columns[
                image_number
                % len(preview_columns)
            ]:
                st.image(
                    uploaded_image,
                    caption=uploaded_image.name,
                    use_container_width=True,
                )

    confirmation = st.checkbox(
        "I confirm that this troubleshooting information "
        "is accurate and safe to use.",
        key="teach_confirmation",
    )

    save_button = st.button(
        "Save Shared Troubleshooting Knowledge",
        type="primary",
        use_container_width=True,
        key="teach_save_button",
    )

    if save_button:
        if not new_fault.strip():
            st.error(
                "Enter the fault description."
            )

        elif not new_cause.strip():
            st.error(
                "Enter the confirmed or likely cause."
            )

        elif not new_inspection.strip():
            st.error(
                "Enter the inspection procedure."
            )

        elif not new_repair.strip():
            st.error(
                "Enter the repair or corrective action."
            )

        elif not confirmation:
            st.error(
                "Confirm that the information is accurate."
            )

        else:
            temporary_folder_name = (
                "pending_solution"
            )

            temporary_image_paths = (
                save_uploaded_images(
                    uploaded_images,
                    temporary_folder_name,
                )
            )

            keywords = (
                parse_comma_separated_items(
                    keyword_text
                )
            )

            aliases = (
                parse_comma_separated_items(
                    alias_text
                )
            )

            try:
                solution_number = add_solution(
                    fault=new_fault.strip(),
                    cause=new_cause.strip(),
                    inspection=new_inspection.strip(),
                    repair=new_repair.strip(),
                    station=new_station,
                    notes=new_notes.strip(),
                    image_paths=temporary_image_paths,
                    keywords=keywords,
                    aliases=aliases,
                )

                permanent_image_paths = (
                    move_temporary_images(
                        solution_number=solution_number,
                        temporary_folder_name=temporary_folder_name,
                        old_image_paths=temporary_image_paths,
                    )
                )

                if permanent_image_paths:
                    update_solution_image_paths(
                        solution_number=solution_number,
                        image_paths=permanent_image_paths,
                    )

                st.success(
                    "Shared troubleshooting knowledge "
                    "was saved successfully."
                )

                st.metric(
                    "Solution Number",
                    solution_number,
                )

                st.info(
                    "This solution is now available in "
                    "Smart Troubleshooter and Fault Diagnosis."
                )

                st.write(
                    "### Saved Summary"
                )

                st.write(
                    f"**Station:** {new_station}"
                )

                st.write(
                    f"**Fault:** {new_fault.strip()}"
                )

                st.write(
                    f"**Cause:** {new_cause.strip()}"
                )

                if keywords:
                    st.write(
                        "**Keywords:** "
                        + ", ".join(keywords)
                    )

                if aliases:
                    st.write(
                        "**Alternative descriptions:** "
                        + ", ".join(aliases)
                    )

                display_saved_images(
                    permanent_image_paths,
                    "Saved Troubleshooting Photos",
                )

            except Exception as error:
                st.error(
                    "The troubleshooting solution could not be saved."
                )

                st.exception(error)


st.divider()

st.caption(
    "Safety: Stop the machine and isolate electrical, "
    "pneumatic and mechanical energy before physical inspection."
)