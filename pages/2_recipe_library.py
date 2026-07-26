import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from recipe_engine import (
    get_recipe,
    list_recipe_names,
    save_recipe,
)


st.set_page_config(
    page_title="Recipe Library | ABAYO",
    page_icon="📖",
    layout="wide",
)


MACHINES = [
    "Pakona PFS AG",
]

RECIPE_STATUSES = [
    "Awaiting confirmation",
    "Under review",
    "Approved",
    "Gold Standard",
]

IMAGE_ROOT = (
    PROJECT_ROOT
    / "knowledge"
    / "recipe_images"
)


def parse_parameters(
    parameter_text: str,
) -> tuple[dict[str, Any], list[str]]:
    """
    Understand two parameter formats.

    Single value:
    Current Degree = 190

    Delay and Action:
    Compressed Air | Delay = 120 | Action = 300
    """

    parameters: dict[str, Any] = {}
    invalid_lines: list[str] = []

    for line in parameter_text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        if "|" in clean_line:
            sections = [
                section.strip()
                for section in clean_line.split("|")
                if section.strip()
            ]

            if len(sections) < 3:
                invalid_lines.append(clean_line)
                continue

            parameter_name = sections[0]
            timing_values: dict[str, str] = {}

            for section in sections[1:]:
                if "=" not in section:
                    invalid_lines.append(clean_line)
                    timing_values = {}
                    break

                field_name, field_value = section.split(
                    "=",
                    1,
                )

                field_name = field_name.strip().lower()
                field_value = field_value.strip()

                if not field_value:
                    invalid_lines.append(clean_line)
                    timing_values = {}
                    break

                if field_name.startswith("delay"):
                    timing_values["delay_deg"] = field_value

                elif field_name.startswith("action"):
                    timing_values["action_deg"] = field_value

                else:
                    invalid_lines.append(clean_line)
                    timing_values = {}
                    break

            if not timing_values:
                continue

            if (
                "delay_deg" not in timing_values
                or "action_deg" not in timing_values
            ):
                invalid_lines.append(clean_line)
                continue

            parameters[parameter_name] = timing_values
            continue

        if "=" not in clean_line:
            invalid_lines.append(clean_line)
            continue

        parameter_name, parameter_value = clean_line.split(
            "=",
            1,
        )

        parameter_name = parameter_name.strip()
        parameter_value = parameter_value.strip()

        if (
            not parameter_name
            or not parameter_value
        ):
            invalid_lines.append(clean_line)
            continue

        parameters[parameter_name] = parameter_value

    return parameters, invalid_lines


def parameters_to_text(
    parameters: dict[str, Any],
) -> str:
    """
    Convert saved parameters back into editable text.

    This allows an existing recipe to be loaded into
    the Add or Update form.
    """

    lines: list[str] = []

    for parameter_name, value in parameters.items():
        if isinstance(value, dict):
            delay_value = value.get(
                "delay_deg",
                "",
            )

            action_value = value.get(
                "action_deg",
                "",
            )

            lines.append(
                f"{parameter_name} | "
                f"Delay = {delay_value} | "
                f"Action = {action_value}"
            )

        else:
            lines.append(
                f"{parameter_name} = {value}"
            )

    return "\n".join(lines)


def safe_folder_name(
    text: str,
) -> str:
    """Convert text into a Windows-safe folder name."""

    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text.strip(),
    )

    return cleaned.strip("_") or "unnamed"


def save_uploaded_images(
    uploaded_images,
    machine_model: str,
    recipe_name: str,
) -> list[str]:
    """Save uploaded HMI images inside ABAYO."""

    saved_paths: list[str] = []

    if not uploaded_images:
        return saved_paths

    destination_folder = (
        IMAGE_ROOT
        / safe_folder_name(machine_model)
        / safe_folder_name(recipe_name)
    )

    destination_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    for number, uploaded_image in enumerate(
        uploaded_images,
        start=1,
    ):
        suffix = Path(
            uploaded_image.name
        ).suffix.lower()

        if suffix not in [
            ".jpg",
            ".jpeg",
            ".png",
        ]:
            suffix = ".jpg"

        file_name = (
            f"hmi_{timestamp}_{number}{suffix}"
        )

        destination_path = (
            destination_folder
            / file_name
        )

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


def split_parameter_rows(
    parameters: dict[str, Any],
) -> tuple[list[dict], list[dict]]:
    """Separate timing pairs from ordinary parameters."""

    timing_rows: list[dict] = []
    single_rows: list[dict] = []

    for parameter_name, value in parameters.items():
        if (
            isinstance(value, dict)
            and (
                "delay_deg" in value
                or "action_deg" in value
            )
        ):
            timing_rows.append(
                {
                    "Parameter": parameter_name,
                    "Delay (deg)": value.get(
                        "delay_deg",
                        "Not recorded",
                    ),
                    "Action (deg)": value.get(
                        "action_deg",
                        "Not recorded",
                    ),
                }
            )

        else:
            single_rows.append(
                {
                    "Parameter": parameter_name,
                    "Value": value,
                }
            )

    return timing_rows, single_rows


def display_parameter_tables(
    parameters: dict[str, Any],
) -> None:
    """Display recipe settings in HMI-style tables."""

    timing_rows, single_rows = split_parameter_rows(
        parameters
    )

    if timing_rows:
        st.write("### Delay and Action Settings")

        st.dataframe(
            timing_rows,
            use_container_width=True,
            hide_index=True,
        )

    if single_rows:
        st.write("### Single-Value Settings")

        st.dataframe(
            single_rows,
            use_container_width=True,
            hide_index=True,
        )

    if not timing_rows and not single_rows:
        st.warning(
            "No confirmed parameters have been entered."
        )


def display_hmi_images(
    image_paths: list[str],
) -> None:
    """Display saved HMI evidence images."""

    if not image_paths:
        return

    st.write("## Saved HMI Images")

    for image_path in image_paths:
        full_path = PROJECT_ROOT / image_path

        if full_path.exists():
            st.image(
                str(full_path),
                caption=full_path.name,
                use_container_width=True,
            )

        else:
            st.warning(
                f"Image file not found: {image_path}"
            )


def display_recipe(
    recipe: dict,
) -> None:
    """Display one complete recipe."""

    status = recipe.get(
        "status",
        "Not classified",
    )

    st.write("## Recipe Information")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Machine",
        recipe.get(
            "machine_model",
            "Unknown machine",
        ),
    )

    col2.metric(
        "Recipe",
        recipe.get(
            "recipe_name",
            "Unnamed recipe",
        ),
    )

    col3.metric(
        "Status",
        status,
    )

    if status == "Gold Standard":
        st.success(
            "This recipe is marked as the Gold Standard."
        )

    elif status == "Under review":
        st.warning(
            "This recipe is currently under review."
        )

    elif status == "Approved":
        st.info(
            "This recipe is marked as approved."
        )

    st.write("## Default Parameters")

    display_parameter_tables(
        recipe.get(
            "parameters",
            {},
        )
    )

    notes = recipe.get(
        "notes",
        "",
    )

    if notes:
        st.write("## Notes")
        st.write(notes)

    display_hmi_images(
        recipe.get(
            "hmi_images",
            [],
        )
    )


def expand_parameter(
    parameter_name: str,
    value: Any,
) -> list[dict]:
    """Convert one parameter into comparison rows."""

    if isinstance(value, dict):
        return [
            {
                "Parameter": parameter_name,
                "Field": "Delay (deg)",
                "Value": value.get(
                    "delay_deg",
                    "Not recorded",
                ),
            },
            {
                "Parameter": parameter_name,
                "Field": "Action (deg)",
                "Value": value.get(
                    "action_deg",
                    "Not recorded",
                ),
            },
        ]

    return [
        {
            "Parameter": parameter_name,
            "Field": "Value",
            "Value": value,
        }
    ]


def comparison_value(
    parameters: dict[str, Any],
    parameter_name: str,
    field_name: str,
) -> str:
    """Read one value for recipe comparison."""

    if parameter_name not in parameters:
        return "Not recorded"

    value = parameters[parameter_name]

    if field_name == "Value":
        if isinstance(value, dict):
            return "Not recorded"

        return str(value)

    if not isinstance(value, dict):
        return "Not recorded"

    if field_name == "Delay (deg)":
        return str(
            value.get(
                "delay_deg",
                "Not recorded",
            )
        )

    if field_name == "Action (deg)":
        return str(
            value.get(
                "action_deg",
                "Not recorded",
            )
        )

    return "Not recorded"


def compare_recipes(
    recipe_a: dict,
    recipe_b: dict,
) -> None:
    """Compare single values and Delay/Action values."""

    parameters_a = recipe_a.get(
        "parameters",
        {},
    )

    parameters_b = recipe_b.get(
        "parameters",
        {},
    )

    parameter_fields: set[tuple[str, str]] = set()

    for parameter_name, value in parameters_a.items():
        for row in expand_parameter(
            parameter_name,
            value,
        ):
            parameter_fields.add(
                (
                    row["Parameter"],
                    row["Field"],
                )
            )

    for parameter_name, value in parameters_b.items():
        for row in expand_parameter(
            parameter_name,
            value,
        ):
            parameter_fields.add(
                (
                    row["Parameter"],
                    row["Field"],
                )
            )

    if not parameter_fields:
        st.warning(
            "Neither recipe has confirmed parameters."
        )
        return

    recipe_a_name = recipe_a.get(
        "recipe_name",
        "Recipe A",
    )

    recipe_b_name = recipe_b.get(
        "recipe_name",
        "Recipe B",
    )

    comparison_rows = []
    matching_count = 0
    difference_count = 0

    for parameter_name, field_name in sorted(
        parameter_fields
    ):
        value_a = comparison_value(
            parameters_a,
            parameter_name,
            field_name,
        )

        value_b = comparison_value(
            parameters_b,
            parameter_name,
            field_name,
        )

        if value_a == value_b:
            status = "Same"
            matching_count += 1

        elif value_a == "Not recorded":
            status = "Missing from Recipe A"
            difference_count += 1

        elif value_b == "Not recorded":
            status = "Missing from Recipe B"
            difference_count += 1

        else:
            status = "Different"
            difference_count += 1

        comparison_rows.append(
            {
                "Parameter": parameter_name,
                "Field": field_name,
                recipe_a_name: value_a,
                recipe_b_name: value_b,
                "Comparison": status,
            }
        )

    st.write("## Comparison Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Values Compared",
        len(comparison_rows),
    )

    col2.metric(
        "Matching Values",
        matching_count,
    )

    col3.metric(
        "Differences Found",
        difference_count,
    )

    if difference_count:
        st.warning(
            f"{difference_count} difference(s) found."
        )

    else:
        st.success(
            "The recorded parameter values are identical."
        )

    st.write("## Full Comparison")

    st.dataframe(
        comparison_rows,
        use_container_width=True,
        hide_index=True,
    )

    differences_only = [
        row
        for row in comparison_rows
        if row["Comparison"] != "Same"
    ]

    st.write("## Differences Only")

    if differences_only:
        st.dataframe(
            differences_only,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success(
            "No differences were found."
        )


def initialise_editing_state() -> None:
    """Create the editing form session values."""

    defaults = {
        "edit_recipe_name": "",
        "edit_recipe_status": (
            "Awaiting confirmation"
        ),
        "edit_parameter_text": "",
        "edit_recipe_notes": "",
        "loaded_recipe_name": "",
        "loaded_image_paths": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_recipe_for_editing(
    machine_model: str,
    recipe_name: str,
) -> bool:
    """Load a saved recipe into the editing form."""

    recipe = get_recipe(
        machine_model,
        recipe_name,
    )

    if recipe is None:
        return False

    saved_status = recipe.get(
        "status",
        "Awaiting confirmation",
    )

    if saved_status not in RECIPE_STATUSES:
        saved_status = "Awaiting confirmation"

    st.session_state.edit_recipe_name = (
        recipe.get(
            "recipe_name",
            recipe_name,
        )
    )

    st.session_state.edit_recipe_status = (
        saved_status
    )

    st.session_state.edit_parameter_text = (
        parameters_to_text(
            recipe.get(
                "parameters",
                {},
            )
        )
    )

    st.session_state.edit_recipe_notes = (
        recipe.get(
            "notes",
            "",
        )
    )

    st.session_state.loaded_recipe_name = (
        recipe_name
    )

    st.session_state.loaded_image_paths = (
        recipe.get(
            "hmi_images",
            [],
        )
    )

    return True


initialise_editing_state()


st.title("📖 Recipe Parameter Library")
st.caption("ABAYO Assist AI — Version 0.6")

st.info(
    "ABAYO supports ordinary values, HMI Delay/Action "
    "timing pairs and loading existing recipes for editing."
)

tab1, tab2, tab3 = st.tabs(
    [
        "📖 View Recipe",
        "📊 Compare Recipes",
        "➕ Add or Update",
    ]
)


with tab1:
    machine_model = st.selectbox(
        "Select machine",
        MACHINES,
        key="view_machine",
    )

    recipe_names = list_recipe_names(
        machine_model
    )

    if recipe_names:
        selected_recipe = st.selectbox(
            "Select recipe",
            recipe_names,
            key="view_recipe",
        )

        recipe = get_recipe(
            machine_model,
            selected_recipe,
        )

        if recipe:
            display_recipe(recipe)

        else:
            st.error(
                "The selected recipe could not be loaded."
            )

    else:
        st.warning(
            "No recipes have been saved."
        )


with tab2:
    st.write("## Compare Two Recipes")

    comparison_machine = st.selectbox(
        "Select machine",
        MACHINES,
        key="comparison_machine",
    )

    comparison_names = list_recipe_names(
        comparison_machine
    )

    if len(comparison_names) < 2:
        st.warning(
            "At least two recipes are required."
        )

    else:
        left_column, right_column = st.columns(2)

        with left_column:
            recipe_a_name = st.selectbox(
                "Recipe A",
                comparison_names,
                index=0,
                key="recipe_a",
            )

        with right_column:
            recipe_b_name = st.selectbox(
                "Recipe B",
                comparison_names,
                index=1,
                key="recipe_b",
            )

        if st.button(
            "Compare Recipes",
            type="primary",
            use_container_width=True,
        ):
            if recipe_a_name == recipe_b_name:
                st.error(
                    "Select two different recipes."
                )

            else:
                recipe_a = get_recipe(
                    comparison_machine,
                    recipe_a_name,
                )

                recipe_b = get_recipe(
                    comparison_machine,
                    recipe_b_name,
                )

                if recipe_a and recipe_b:
                    compare_recipes(
                        recipe_a,
                        recipe_b,
                    )

                else:
                    st.error(
                        "One or both recipes could not be loaded."
                    )


with tab3:
    st.write("## Add or Update a Recipe")

    edit_machine = st.selectbox(
        "Machine model",
        MACHINES,
        key="edit_machine",
    )

    saved_recipe_names = list_recipe_names(
        edit_machine
    )

    load_options = [
        "Create a new recipe",
        *saved_recipe_names,
    ]

    selected_edit_option = st.selectbox(
        "Choose an existing recipe to edit",
        load_options,
        key="selected_edit_option",
    )

    if selected_edit_option != "Create a new recipe":
        if st.button(
            "Load Recipe for Editing",
            use_container_width=True,
        ):
            loaded = load_recipe_for_editing(
                edit_machine,
                selected_edit_option,
            )

            if loaded:
                st.rerun()

            else:
                st.error(
                    "The recipe could not be loaded."
                )

    else:
        if st.button(
            "Clear Form for New Recipe",
            use_container_width=True,
        ):
            st.session_state.edit_recipe_name = ""
            st.session_state.edit_recipe_status = (
                "Awaiting confirmation"
            )
            st.session_state.edit_parameter_text = ""
            st.session_state.edit_recipe_notes = ""
            st.session_state.loaded_recipe_name = ""
            st.session_state.loaded_image_paths = []

            st.rerun()

    if st.session_state.loaded_recipe_name:
        st.success(
            "Loaded for editing: "
            f"{st.session_state.loaded_recipe_name}"
        )

    recipe_name = st.text_input(
        "Recipe name",
        key="edit_recipe_name",
        placeholder="Example: 500 g",
    )

    recipe_status = st.selectbox(
        "Recipe status",
        RECIPE_STATUSES,
        key="edit_recipe_status",
    )

    existing_images = (
        st.session_state.loaded_image_paths
    )

    if existing_images:
        st.write("### Existing HMI Images")

        display_hmi_images(
            existing_images
        )

        st.info(
            "These existing images will remain attached "
            "when the recipe is updated."
        )

    st.write("### Upload Additional HMI Evidence")

    uploaded_images = st.file_uploader(
        "Upload one or more additional HMI photographs",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        accept_multiple_files=True,
        key="edit_uploaded_images",
    )

    if uploaded_images:
        st.write("### New Image Preview")

        for uploaded_image in uploaded_images:
            st.image(
                uploaded_image,
                caption=uploaded_image.name,
                use_container_width=True,
            )

    st.write("### Enter or Edit Verified Parameters")

    st.code(
        "Compressed Air | Delay = 120 | Action = 300\n"
        "Cold Seal | Delay = 30 | Action = 170\n"
        "Current Degree = 190",
        language=None,
    )

    parameter_text = st.text_area(
        "Parameters copied from the HMI",
        key="edit_parameter_text",
        placeholder=(
            "Compressed Air | Delay = 120 | Action = 300\n"
            "Cold Seal | Delay = 30 | Action = 170\n"
            "Top Seal | Delay = 30 | Action = 220\n"
            "Current Degree = 190"
        ),
        height=350,
    )

    if parameter_text.strip():
        preview_parameters, preview_errors = (
            parse_parameters(
                parameter_text
            )
        )

        st.write("### Parsed Preview")

        if preview_parameters:
            display_parameter_tables(
                preview_parameters
            )

        if preview_errors:
            st.warning(
                "Some lines could not be interpreted."
            )

            for error_line in preview_errors:
                st.write(
                    f"- {error_line}"
                )

    recipe_notes = st.text_area(
        "Recipe notes",
        key="edit_recipe_notes",
        placeholder=(
            "Example: Parameters copied from "
            "Setting 1 during stable production."
        ),
        height=130,
    )

    confirmation = st.checkbox(
        "I have verified these values against the HMI.",
        key="edit_confirmation",
    )

    if st.button(
        "Save Recipe and HMI Images",
        type="primary",
        use_container_width=True,
    ):
        parameters, invalid_lines = (
            parse_parameters(
                parameter_text
            )
        )

        if not recipe_name.strip():
            st.error(
                "Enter the recipe name."
            )

        elif invalid_lines:
            st.error(
                "Correct the lines ABAYO could not interpret."
            )

            for invalid_line in invalid_lines:
                st.write(
                    f"- {invalid_line}"
                )

        elif not parameters:
            st.error(
                "Enter at least one confirmed parameter."
            )

        elif not confirmation:
            st.error(
                "Confirm that you checked the values "
                "against the HMI."
            )

        else:
            saved_image_paths = save_uploaded_images(
                uploaded_images,
                edit_machine,
                recipe_name.strip(),
            )

            save_result = save_recipe(
                machine_model=edit_machine,
                recipe_name=recipe_name.strip(),
                status=recipe_status,
                parameters=parameters,
                notes=recipe_notes,
                hmi_images=saved_image_paths,
            )

            st.session_state.loaded_recipe_name = (
                recipe_name.strip()
            )

            updated_recipe = get_recipe(
                edit_machine,
                recipe_name.strip(),
            )

            if updated_recipe:
                st.session_state.loaded_image_paths = (
                    updated_recipe.get(
                        "hmi_images",
                        [],
                    )
                )

            if save_result == "updated":
                st.success(
                    "The existing recipe was updated successfully."
                )

            else:
                st.success(
                    "The new recipe was created successfully."
                )

            st.info(
                "Open View Recipe to inspect the saved version."
            )