from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.access import require_app_access
from core.machine_context import current_machine, is_pakona_machine, machine_display_name, machine_model_label, selected_machine_id
from recipe_engine import get_recipe, list_recipe_names, save_recipe
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

st.set_page_config(page_title="Recipe Library | ABAYO", page_icon="📖", layout="wide")
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

st.title("📖 Recipe Library")
st.caption(f"Active machine: {machine_name} • Recipes are isolated to this machine profile.")

VIEW, EDIT = st.tabs(["View Recipes", "Add / Update Recipe"])

with VIEW:
    names = list_recipe_names(machine_model, machine_id=machine_id, allow_legacy=legacy)
    if not names:
        st.info(f"No recipes are recorded for {machine_name} yet.")
    else:
        selected = st.selectbox("Recipe", names)
        recipe = get_recipe(machine_model, selected, machine_id=machine_id, allow_legacy=legacy)
        if recipe:
            c1, c2, c3 = st.columns(3)
            c1.metric("Machine", machine_name)
            c2.metric("Recipe", recipe.get("recipe_name", selected))
            c3.metric("Status", recipe.get("status", "Not classified"))
            parameters = recipe.get("parameters") or {}
            st.subheader("Parameters")
            if isinstance(parameters, dict) and parameters:
                rows: list[dict[str, Any]] = []
                for key, value in parameters.items():
                    if isinstance(value, dict):
                        rows.append({"Parameter": key, "Value": f"Delay {value.get('delay_deg', '')} • Action {value.get('action_deg', '')}"})
                    else:
                        rows.append({"Parameter": key, "Value": value})
                st.dataframe(rows, hide_index=True, width="stretch")
            else:
                st.info("No parameters recorded.")
            if recipe.get("notes"):
                st.subheader("Notes")
                st.write(recipe.get("notes"))

with EDIT:
    existing_names = list_recipe_names(machine_model, machine_id=machine_id, allow_legacy=legacy)
    option = st.selectbox("Mode", ["Create new recipe", *existing_names])
    existing = None
    if option != "Create new recipe":
        existing = get_recipe(machine_model, option, machine_id=machine_id, allow_legacy=legacy)

    recipe_name = st.text_input("Recipe name", value=str((existing or {}).get("recipe_name") or ""))
    status_options = ["Awaiting confirmation", "Under review", "Approved", "Gold Standard"]
    current_status = str((existing or {}).get("status") or status_options[0])
    if current_status not in status_options:
        current_status = status_options[0]
    status = st.selectbox("Recipe status", status_options, index=status_options.index(current_status))

    existing_parameters = (existing or {}).get("parameters") or {}
    parameter_lines = []
    if isinstance(existing_parameters, dict):
        for key, value in existing_parameters.items():
            if isinstance(value, dict):
                parameter_lines.append(f"{key} | Delay = {value.get('delay_deg', '')} | Action = {value.get('action_deg', '')}")
            else:
                parameter_lines.append(f"{key} = {value}")

    parameter_text = st.text_area(
        "Parameters",
        value="\n".join(parameter_lines),
        height=220,
        help="One setting per line. Use Name = Value, or Name | Delay = 120 | Action = 300.",
    )
    notes = st.text_area("Notes", value=str((existing or {}).get("notes") or ""), height=120)

    if st.button("Save Recipe", type="primary", width="stretch"):
        if not recipe_name.strip():
            st.error("Recipe name is required.")
        else:
            parameters: dict[str, Any] = {}
            invalid: list[str] = []
            for raw in parameter_text.splitlines():
                line = raw.strip()
                if not line:
                    continue
                if "|" in line:
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) != 3 or "=" not in parts[1] or "=" not in parts[2]:
                        invalid.append(line)
                        continue
                    _, delay = parts[1].split("=", 1)
                    _, action = parts[2].split("=", 1)
                    parameters[parts[0]] = {"delay_deg": delay.strip(), "action_deg": action.strip()}
                elif "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() and value.strip():
                        parameters[key.strip()] = value.strip()
                    else:
                        invalid.append(line)
                else:
                    invalid.append(line)

            if invalid:
                st.error("Fix these parameter lines before saving: " + "; ".join(invalid))
            else:
                result = save_recipe(
                    machine_model,
                    recipe_name,
                    status,
                    parameters,
                    notes,
                    machine_id=machine_id,
                )
                st.success(f"Recipe {result} for {machine_name}.")
                st.rerun()
