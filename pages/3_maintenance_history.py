import re
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from maintenance_engine import (
    add_maintenance_record,
    calculate_summary,
    filter_maintenance_records,
    get_maintenance_record,
    list_record_numbers,
    load_maintenance_records,
)

from recipe_engine import list_recipe_names


st.set_page_config(
    page_title="Maintenance History | ABAYO",
    page_icon="📝",
    layout="wide",
)


MACHINES = [
    "Pakona PFS AG",
]


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


PRODUCTION_STATUSES = [
    "Machine stopped",
    "Machine running",
    "Trial production",
    "Maintenance mode",
    "Changeover",
]


PRODUCTION_SHIFTS = [
    "Not recorded",
    "Morning shift",
    "Afternoon shift",
    "Night shift",
]


MAINTENANCE_IMAGE_ROOT = (
    PROJECT_ROOT
    / "knowledge"
    / "maintenance_images"
)


def safe_folder_name(text: str) -> str:
    """Convert text into a Windows-safe folder name."""

    cleaned_text = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text.strip(),
    )

    return cleaned_text.strip("_") or "unnamed"


def save_maintenance_images(
    uploaded_images,
    record_number: str,
) -> list[str]:
    """Save maintenance images inside the ABAYO project."""

    saved_paths: list[str] = []

    if not uploaded_images:
        return saved_paths

    record_folder = (
        MAINTENANCE_IMAGE_ROOT
        / safe_folder_name(record_number)
    )

    record_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    for image_number, uploaded_image in enumerate(
        uploaded_images,
        start=1,
    ):
        file_suffix = Path(
            uploaded_image.name
        ).suffix.lower()

        if file_suffix not in [
            ".jpg",
            ".jpeg",
            ".png",
        ]:
            file_suffix = ".jpg"

        file_name = (
            f"maintenance_image_"
            f"{image_number}"
            f"{file_suffix}"
        )

        destination_path = (
            record_folder
            / file_name
        )

        duplicate_number = 1

        while destination_path.exists():
            file_name = (
                f"maintenance_image_"
                f"{image_number}_"
                f"{duplicate_number}"
                f"{file_suffix}"
            )

            destination_path = (
                record_folder
                / file_name
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

        saved_paths.append(relative_path)

    return saved_paths


def display_record_images(
    image_paths: list[str],
) -> None:
    """Display photographs attached to a maintenance record."""

    if not image_paths:
        return

    st.write("### Attached Images")

    image_columns = st.columns(
        min(
            len(image_paths),
            2,
        )
    )

    for image_number, image_path in enumerate(
        image_paths
    ):
        full_image_path = (
            PROJECT_ROOT
            / image_path
        )

        image_column = image_columns[
            image_number
            % len(image_columns)
        ]

        with image_column:
            if full_image_path.exists():
                st.image(
                    str(full_image_path),
                    caption=full_image_path.name,
                    use_container_width=True,
                )

            else:
                st.warning(
                    f"Image not found: {image_path}"
                )


def display_maintenance_record(
    record: dict,
) -> None:
    """Display one maintenance event clearly."""

    record_number = record.get(
        "record_number",
        "Unknown record",
    )

    st.write(
        f"## 🛠️ {record_number}"
    )

    information_col1, information_col2, information_col3 = (
        st.columns(3)
    )

    information_col1.metric(
        "Machine",
        record.get(
            "machine_model",
            "Not recorded",
        ),
    )

    information_col2.metric(
        "Recipe",
        record.get(
            "recipe_name",
            "",
        )
        or "Not recipe-related",
    )

    information_col3.metric(
        "Station",
        record.get(
            "station",
            "Not recorded",
        ),
    )

    status_col1, status_col2, status_col3 = (
        st.columns(3)
    )

    status_col1.metric(
        "Production Status",
        record.get(
            "production_status",
            "",
        )
        or "Not recorded",
    )

    status_col2.metric(
        "Downtime",
        (
            f"{record.get('downtime_minutes', 0)} "
            f"minutes"
        ),
    )

    status_col3.metric(
        "Recorded By",
        record.get(
            "recorded_by",
            "Not recorded",
        ),
    )

    st.write("### Fault Description")

    st.write(
        record.get(
            "fault",
            "Not recorded",
        )
    )

    st.write("### Confirmed Cause")

    st.write(
        record.get(
            "confirmed_cause",
            "Not recorded",
        )
    )

    st.write("### Corrective Action")

    st.write(
        record.get(
            "corrective_action",
            "Not recorded",
        )
    )

    production_shift = record.get(
        "production_shift",
        "",
    )

    batch_number = record.get(
        "batch_number",
        "",
    )

    details_col1, details_col2 = st.columns(2)

    details_col1.write(
        "**Production shift**"
    )

    details_col1.write(
        production_shift
        or "Not recorded"
    )

    details_col2.write(
        "**Batch number**"
    )

    details_col2.write(
        batch_number
        or "Not recorded"
    )

    notes = record.get(
        "notes",
        "",
    )

    if notes:
        st.write("### Additional Notes")
        st.write(notes)

    display_record_images(
        record.get(
            "image_paths",
            [],
        )
    )


st.title("📝 Maintenance History")

st.caption(
    "ABAYO Assist AI — Permanent Machine Memory"
)

st.info(
    "Every saved maintenance event receives a permanent "
    "sequential number. Calendar dates are not required."
)


tab1, tab2, tab3 = st.tabs(
    [
        "➕ Record Maintenance",
        "📚 View History",
        "📊 Maintenance Summary",
    ]
)


with tab1:
    st.write("## Record a Maintenance Event")

    machine_model = st.selectbox(
        "Machine model",
        MACHINES,
        key="record_machine",
    )

    available_recipes = list_recipe_names(
        machine_model
    )

    recipe_options = [
        "Not recipe-related",
        *available_recipes,
    ]

    recipe_name = st.selectbox(
        "Recipe",
        recipe_options,
        key="record_recipe",
    )

    station = st.selectbox(
        "Machine station",
        STATIONS,
        key="record_station",
    )

    production_status = st.selectbox(
        "Production status",
        PRODUCTION_STATUSES,
        key="record_production_status",
    )

    fault = st.text_area(
        "Fault description",
        placeholder=(
            "Example: Pouch was not picked "
            "by the suction cups."
        ),
        height=110,
        key="record_fault",
    )

    confirmed_cause = st.text_area(
        "Confirmed cause",
        placeholder=(
            "Example: The vacuum hose was loose "
            "and leaking air."
        ),
        height=110,
        key="record_cause",
    )

    corrective_action = st.text_area(
        "Corrective action",
        placeholder=(
            "Example: Reconnected and secured "
            "the vacuum hose, then tested pickup."
        ),
        height=130,
        key="record_action",
    )

    downtime_minutes = st.number_input(
        "Downtime in minutes",
        min_value=0.0,
        step=1.0,
        format="%.1f",
        key="record_downtime",
    )

    recorded_by = st.text_input(
        "Recorded by",
        placeholder="Example: Kangume Julius",
        key="recorded_by",
    )

    option_col1, option_col2 = st.columns(2)

    with option_col1:
        production_shift = st.selectbox(
            "Production shift — optional",
            PRODUCTION_SHIFTS,
            key="record_shift",
        )

    with option_col2:
        batch_number = st.text_input(
            "Batch number — optional",
            placeholder="Example: BATCH-500-01",
            key="record_batch",
        )

    notes = st.text_area(
        "Additional notes — optional",
        placeholder=(
            "Example: Machine remained stable "
            "after the repair."
        ),
        height=100,
        key="record_notes",
    )

    st.write("### Attach Maintenance Evidence")

    uploaded_images = st.file_uploader(
        "Upload HMI or machine photographs",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        accept_multiple_files=True,
        key="maintenance_uploaded_images",
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
            preview_column = preview_columns[
                image_number
                % len(preview_columns)
            ]

            with preview_column:
                st.image(
                    uploaded_image,
                    caption=uploaded_image.name,
                    use_container_width=True,
                )

    confirmation = st.checkbox(
        "I confirm that this maintenance record is accurate.",
        key="record_confirmation",
    )

    if st.button(
        "Save Maintenance Record",
        type="primary",
        use_container_width=True,
    ):
        if not fault.strip():
            st.error(
                "Enter the fault description."
            )

        elif not confirmed_cause.strip():
            st.error(
                "Enter the confirmed cause."
            )

        elif not corrective_action.strip():
            st.error(
                "Enter the corrective action."
            )

        elif not recorded_by.strip():
            st.error(
                "Enter the name of the person "
                "recording this event."
            )

        elif not confirmation:
            st.error(
                "Confirm that the maintenance "
                "record is accurate."
            )

        else:
            saved_recipe_name = recipe_name

            if recipe_name == "Not recipe-related":
                saved_recipe_name = ""

            saved_production_shift = production_shift

            if production_shift == "Not recorded":
                saved_production_shift = ""

            temporary_record_number = (
                "pending_record"
            )

            image_paths = save_maintenance_images(
                uploaded_images,
                temporary_record_number,
            )

            record_number = add_maintenance_record(
                machine_model=machine_model,
                recipe_name=saved_recipe_name,
                station=station,
                fault=fault,
                confirmed_cause=confirmed_cause,
                corrective_action=corrective_action,
                downtime_minutes=downtime_minutes,
                recorded_by=recorded_by,
                production_status=production_status,
                production_shift=saved_production_shift,
                batch_number=batch_number,
                notes=notes,
                image_paths=image_paths,
            )

            if image_paths:
                temporary_folder = (
                    MAINTENANCE_IMAGE_ROOT
                    / temporary_record_number
                )

                permanent_folder = (
                    MAINTENANCE_IMAGE_ROOT
                    / safe_folder_name(
                        record_number
                    )
                )

                if (
                    temporary_folder.exists()
                    and not permanent_folder.exists()
                ):
                    temporary_folder.rename(
                        permanent_folder
                    )

                    updated_paths: list[str] = []

                    for image_path in image_paths:
                        old_path = Path(
                            image_path
                        )

                        new_relative_path = (
                            Path("knowledge")
                            / "maintenance_images"
                            / safe_folder_name(
                                record_number
                            )
                            / old_path.name
                        )

                        updated_paths.append(
                            new_relative_path.as_posix()
                        )

                    all_records = (
                        load_maintenance_records()
                    )

                    for record in all_records:
                        if (
                            record.get(
                                "record_number"
                            )
                            == record_number
                        ):
                            record["image_paths"] = (
                                updated_paths
                            )

                    from maintenance_engine import (
                        save_all_maintenance_records,
                    )

                    save_all_maintenance_records(
                        all_records
                    )

            st.success(
                "Maintenance event saved successfully."
            )

            st.metric(
                "Permanent Record Number",
                record_number,
            )

            st.info(
                "Use this permanent number to locate "
                "the event in View History."
            )


with tab2:
    st.write("## Search Maintenance History")

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        machine_filter = st.selectbox(
            "Filter by machine",
            [
                "All machines",
                *MACHINES,
            ],
            key="history_machine_filter",
        )

        station_filter = st.selectbox(
            "Filter by station",
            [
                "All stations",
                *STATIONS,
            ],
            key="history_station_filter",
        )

        production_status_filter = st.selectbox(
            "Filter by production status",
            [
                "All statuses",
                *PRODUCTION_STATUSES,
            ],
            key="history_status_filter",
        )

    with filter_col2:
        recipe_filter = st.selectbox(
            "Filter by recipe",
            [
                "All recipes",
                "Not recipe-related",
                *list_recipe_names(
                    "Pakona PFS AG"
                ),
            ],
            key="history_recipe_filter",
        )

        search_text = st.text_input(
            "Search records",
            placeholder=(
                "Search fault, cause, action, "
                "technician, batch or record number"
            ),
            key="history_search",
        )

    selected_machine = ""

    if machine_filter != "All machines":
        selected_machine = machine_filter

    selected_station = ""

    if station_filter != "All stations":
        selected_station = station_filter

    selected_status = ""

    if production_status_filter != "All statuses":
        selected_status = production_status_filter

    selected_recipe = ""

    if recipe_filter not in [
        "All recipes",
        "Not recipe-related",
    ]:
        selected_recipe = recipe_filter

    filtered_records = filter_maintenance_records(
        machine_model=selected_machine,
        recipe_name=selected_recipe,
        station=selected_station,
        production_status=selected_status,
        search_text=search_text,
    )

    if recipe_filter == "Not recipe-related":
        filtered_records = [
            record
            for record in filtered_records
            if not record.get(
                "recipe_name"
            )
        ]

    st.metric(
        "Records Found",
        len(filtered_records),
    )

    if filtered_records:
        for record in filtered_records:
            expander_title = (
                f"{record.get('record_number', '')} — "
                f"{record.get('fault', 'Unnamed fault')}"
            )

            with st.expander(
                expander_title
            ):
                display_maintenance_record(
                    record
                )

    else:
        st.warning(
            "No maintenance records match "
            "the selected filters."
        )

    st.divider()

    st.write("## Open a Record Directly")

    record_numbers = list_record_numbers()

    if record_numbers:
        selected_record_number = st.selectbox(
            "Select permanent record number",
            record_numbers,
            key="direct_record_number",
        )

        if st.button(
            "Open Maintenance Record",
            use_container_width=True,
        ):
            selected_record = get_maintenance_record(
                selected_record_number
            )

            if selected_record:
                display_maintenance_record(
                    selected_record
                )

            else:
                st.error(
                    "The maintenance record "
                    "could not be found."
                )

    else:
        st.info(
            "No maintenance records have "
            "been saved yet."
        )


with tab3:
    st.write("## Maintenance Summary")

    all_records = load_maintenance_records()

    summary = calculate_summary(
        all_records
    )

    summary_col1, summary_col2, summary_col3 = (
        st.columns(3)
    )

    summary_col1.metric(
        "Total Records",
        summary["total_records"],
    )

    summary_col2.metric(
        "Total Downtime",
        (
            f"{summary['total_downtime_minutes']} "
            f"minutes"
        ),
    )

    summary_col3.metric(
        "Average Downtime",
        (
            f"{summary['average_downtime_minutes']} "
            f"minutes"
        ),
    )

    summary_detail_col1, summary_detail_col2 = (
        st.columns(2)
    )

    with summary_detail_col1:
        st.write("### Most Repeated Fault")

        st.info(
            summary["most_repeated_fault"]
        )

        st.write("### Most Affected Recipe")

        st.info(
            summary["most_affected_recipe"]
        )

    with summary_detail_col2:
        st.write("### Most Affected Station")

        st.info(
            summary["most_affected_station"]
        )

    if all_records:
        st.write("## Maintenance Events by Station")

        station_counts: dict[str, int] = {}

        for record in all_records:
            station_name = record.get(
                "station",
                "Unknown station",
            )

            station_counts[station_name] = (
                station_counts.get(
                    station_name,
                    0,
                )
                + 1
            )

        station_rows = [
            {
                "Station": station_name,
                "Maintenance Events": count,
            }
            for station_name, count in sorted(
                station_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        st.dataframe(
            station_rows,
            use_container_width=True,
            hide_index=True,
        )

        st.write("## Maintenance Events by Recipe")

        recipe_counts: dict[str, int] = {}

        for record in all_records:
            saved_recipe = (
                record.get(
                    "recipe_name",
                    "",
                )
                or "Not recipe-related"
            )

            recipe_counts[saved_recipe] = (
                recipe_counts.get(
                    saved_recipe,
                    0,
                )
                + 1
            )

        recipe_rows = [
            {
                "Recipe": recipe_name,
                "Maintenance Events": count,
            }
            for recipe_name, count in sorted(
                recipe_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        st.dataframe(
            recipe_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info(
            "Save the first maintenance record "
            "to begin building the machine memory."
        )