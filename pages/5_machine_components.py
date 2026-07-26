import re
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from component_engine import (
    add_component,
    component_summary,
    load_components,
    search_components,
)


st.set_page_config(
    page_title="Machine Components | ABAYO",
    page_icon="⚙️",
    layout="wide",
)


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


CATEGORIES = [
    "Mechanical",
    "Electrical",
    "Pneumatic",
    "Sensor",
    "Motor and drive",
    "Heating",
    "Sealing",
    "Vacuum",
    "PLC and control",
    "Other",
]


IMAGE_ROOT = (
    PROJECT_ROOT
    / "knowledge"
    / "component_images"
)


def safe_folder_name(text: str) -> str:
    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text.strip(),
    )

    return cleaned.strip("_") or "unnamed"


def save_component_images(
    uploaded_images,
    folder_name: str,
) -> list[str]:
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

    for number, uploaded_image in enumerate(
        uploaded_images,
        start=1,
    ):
        suffix = Path(
            uploaded_image.name
        ).suffix.lower()

        if suffix not in {
            ".jpg",
            ".jpeg",
            ".png",
        }:
            suffix = ".jpg"

        destination_path = (
            destination_folder
            / f"component_{number}{suffix}"
        )

        duplicate_number = 1

        while destination_path.exists():
            destination_path = (
                destination_folder
                / (
                    f"component_{number}_"
                    f"{duplicate_number}{suffix}"
                )
            )

            duplicate_number += 1

        with destination_path.open(
            "wb"
        ) as file:
            file.write(
                uploaded_image.getbuffer()
            )

        relative_path = (
            destination_path
            .relative_to(PROJECT_ROOT)
            .as_posix()
        )

        saved_paths.append(relative_path)

    return saved_paths


def display_component_images(
    image_paths: list[str],
) -> None:
    if not image_paths:
        return

    st.write("### Component Photos")

    valid_paths = []

    for image_path in image_paths:
        full_path = PROJECT_ROOT / image_path

        if full_path.exists():
            valid_paths.append(full_path)

    if not valid_paths:
        st.warning(
            "The saved image files could not be found."
        )
        return

    columns = st.columns(
        min(len(valid_paths), 2)
    )

    for number, full_path in enumerate(
        valid_paths
    ):
        with columns[
            number % len(columns)
        ]:
            st.image(
                str(full_path),
                caption=full_path.name,
                use_container_width=True,
            )


def parse_related_faults(
    text: str,
) -> list[str]:
    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


st.title("⚙️ Machine Components Library")

st.caption(
    "ABAYO Assist AI — Component identification, "
    "failure symptoms, inspection and replacement knowledge"
)

st.info(
    "Store important machine parts together with their photos, "
    "functions, common failures and maintenance procedures."
)


view_tab, add_tab, summary_tab = st.tabs(
    [
        "🔍 View Components",
        "➕ Add Component",
        "📊 Component Summary",
    ]
)


with view_tab:
    st.write("## Search Machine Components")

    search_column, station_column, category_column = st.columns(3)

    with search_column:
        search_text = st.text_input(
            "Search",
            placeholder=(
                "Example: suction cup, Omron sensor, "
                "Venturi ejector or auger motor"
            ),
            key="component_search_text",
        )

    with station_column:
        selected_station = st.selectbox(
            "Station filter",
            ["All stations"] + STATIONS,
            key="component_station_filter",
        )

    with category_column:
        selected_category = st.selectbox(
            "Category filter",
            ["All categories"] + CATEGORIES,
            key="component_category_filter",
        )

    station_filter = (
        ""
        if selected_station == "All stations"
        else selected_station
    )

    category_filter = (
        ""
        if selected_category == "All categories"
        else selected_category
    )

    results = search_components(
        search_text=search_text,
        station=station_filter,
        category=category_filter,
    )

    st.write(
        f"### Components Found: {len(results)}"
    )

    if results:
        for component in results:
            component_number = component.get(
                "component_number",
                "Component",
            )

            component_name = component.get(
                "component_name",
                "Unnamed component",
            )

            station = component.get(
                "station",
                "Not recorded",
            )

            with st.expander(
                f"{component_number} — {component_name} — {station}"
            ):
                top_left, top_right = st.columns(2)

                with top_left:
                    st.write(
                        f"**Category:** "
                        f"{component.get('category', 'Not recorded')}"
                    )

                    st.write(
                        f"**Manufacturer:** "
                        f"{component.get('manufacturer', 'Not recorded') or 'Not recorded'}"
                    )

                    st.write(
                        f"**Model number:** "
                        f"{component.get('model_number', 'Not recorded') or 'Not recorded'}"
                    )

                    st.write(
                        f"**Part number:** "
                        f"{component.get('part_number', 'Not recorded') or 'Not recorded'}"
                    )

                with top_right:
                    st.write(
                        f"**Spare-part location:** "
                        f"{component.get('spare_part_location', 'Not recorded') or 'Not recorded'}"
                    )

                    related_faults = component.get(
                        "related_faults",
                        [],
                    )

                    if related_faults:
                        st.write(
                            "**Related faults:** "
                            + ", ".join(
                                str(item)
                                for item in related_faults
                            )
                        )

                st.write("### Function")

                st.write(
                    component.get(
                        "function",
                        "Not recorded",
                    )
                )

                st.write("### Common Failures")

                st.write(
                    component.get(
                        "common_failures",
                        "Not recorded",
                    )
                )

                st.write("### Fault Symptoms")

                st.write(
                    component.get(
                        "fault_symptoms",
                        "Not recorded",
                    )
                )

                st.write("### Inspection Procedure")

                st.write(
                    component.get(
                        "inspection_procedure",
                        "Not recorded",
                    )
                )

                st.write("### Replacement Procedure")

                st.write(
                    component.get(
                        "replacement_procedure",
                        "Not recorded",
                    )
                )

                safety_notes = component.get(
                    "safety_notes"
                )

                if safety_notes:
                    st.warning(
                        f"Safety: {safety_notes}"
                    )

                display_component_images(
                    component.get(
                        "image_paths",
                        [],
                    )
                )

    else:
        st.info(
            "No machine components matched the selected filters."
        )


with add_tab:
    st.write("## Add a Machine Component")

    component_name = st.text_input(
        "Component name",
        placeholder=(
            "Example: Pouch-picking suction cup"
        ),
        key="add_component_name",
    )

    first_column, second_column = st.columns(2)

    with first_column:
        station = st.selectbox(
            "Machine station",
            STATIONS,
            key="add_component_station",
        )

        category = st.selectbox(
            "Component category",
            CATEGORIES,
            key="add_component_category",
        )

        manufacturer = st.text_input(
            "Manufacturer",
            placeholder="Example: Omron",
            key="add_component_manufacturer",
        )

    with second_column:
        model_number = st.text_input(
            "Model number",
            key="add_component_model",
        )

        part_number = st.text_input(
            "Part number",
            key="add_component_part",
        )

        spare_part_location = st.text_input(
            "Spare-part storage location",
            placeholder=(
                "Example: Engineering store, shelf B2"
            ),
            key="add_component_location",
        )

    component_function = st.text_area(
        "Component function",
        placeholder=(
            "Explain what the component does "
            "during normal machine operation."
        ),
        height=110,
        key="add_component_function",
    )

    common_failures = st.text_area(
        "Common failures",
        placeholder=(
            "Example: Wear, dust contamination, "
            "vacuum leakage and misalignment."
        ),
        height=120,
        key="add_component_failures",
    )

    fault_symptoms = st.text_area(
        "Fault symptoms",
        placeholder=(
            "Example: Pouches are missed, picked late "
            "or dropped during transfer."
        ),
        height=120,
        key="add_component_symptoms",
    )

    inspection_procedure = st.text_area(
        "Inspection procedure",
        placeholder=(
            "Write the safe inspection steps "
            "in the correct order."
        ),
        height=140,
        key="add_component_inspection",
    )

    replacement_procedure = st.text_area(
        "Replacement procedure",
        placeholder=(
            "Write the safe replacement or adjustment steps."
        ),
        height=140,
        key="add_component_replacement",
    )

    safety_notes = st.text_area(
        "Safety notes",
        placeholder=(
            "Example: Isolate electrical and pneumatic energy "
            "before removing the component."
        ),
        height=100,
        key="add_component_safety",
    )

    related_fault_text = st.text_area(
        "Related faults",
        placeholder=(
            "Separate faults with commas. Example: "
            "pouch not picked, weak suction, pouch dropped"
        ),
        height=100,
        key="add_component_faults",
    )

    uploaded_images = st.file_uploader(
        "Upload component photographs",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        accept_multiple_files=True,
        key="add_component_images",
    )

    if uploaded_images:
        st.write("### Image Preview")

        preview_columns = st.columns(
            min(len(uploaded_images), 2)
        )

        for number, uploaded_image in enumerate(
            uploaded_images
        ):
            with preview_columns[
                number % len(preview_columns)
            ]:
                st.image(
                    uploaded_image,
                    caption=uploaded_image.name,
                    use_container_width=True,
                )

    confirmation = st.checkbox(
        "I confirm that the component information is accurate.",
        key="add_component_confirmation",
    )

    if st.button(
        "Save Machine Component",
        type="primary",
        use_container_width=True,
        key="save_component_button",
    ):
        if not component_name.strip():
            st.error(
                "Enter the component name."
            )

        elif not component_function.strip():
            st.error(
                "Enter the component function."
            )

        elif not common_failures.strip():
            st.error(
                "Enter at least one common failure."
            )

        elif not fault_symptoms.strip():
            st.error(
                "Enter the fault symptoms."
            )

        elif not inspection_procedure.strip():
            st.error(
                "Enter the inspection procedure."
            )

        elif not replacement_procedure.strip():
            st.error(
                "Enter the replacement procedure."
            )

        elif not confirmation:
            st.error(
                "Confirm that the information is accurate."
            )

        else:
            temporary_folder = "pending_component"

            image_paths = save_component_images(
                uploaded_images,
                temporary_folder,
            )

            component_number = add_component(
                component_name=component_name,
                station=station,
                category=category,
                function=component_function,
                common_failures=common_failures,
                fault_symptoms=fault_symptoms,
                inspection_procedure=inspection_procedure,
                replacement_procedure=replacement_procedure,
                safety_notes=safety_notes,
                manufacturer=manufacturer,
                model_number=model_number,
                part_number=part_number,
                spare_part_location=spare_part_location,
                related_faults=parse_related_faults(
                    related_fault_text
                ),
                image_paths=image_paths,
            )

            st.success(
                "Machine component saved successfully."
            )

            st.metric(
                "Component Number",
                component_number,
            )

            st.info(
                "This component is now available "
                "in the Machine Components Library."
            )


with summary_tab:
    st.write("## Component Library Summary")

    summary = component_summary()

    total_components = summary.get(
        "total_components",
        0,
    )

    st.metric(
        "Total Components",
        total_components,
    )

    station_counts = summary.get(
        "station_counts",
        {},
    )

    category_counts = summary.get(
        "category_counts",
        {},
    )

    left_column, right_column = st.columns(2)

    with left_column:
        st.write("### Components by Station")

        if station_counts:
            for station_name, count in sorted(
                station_counts.items()
            ):
                st.write(
                    f"**{station_name}:** {count}"
                )
        else:
            st.info(
                "No station statistics are available yet."
            )

    with right_column:
        st.write("### Components by Category")

        if category_counts:
            for category_name, count in sorted(
                category_counts.items()
            ):
                st.write(
                    f"**{category_name}:** {count}"
                )
        else:
            st.info(
                "No category statistics are available yet."
            )


st.divider()

st.caption(
    "Safety: Stop the machine and isolate electrical, "
    "pneumatic and mechanical energy before inspection "
    "or component replacement."
)