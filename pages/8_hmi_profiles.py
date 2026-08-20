from __future__ import annotations

from html import escape
import logging

import pandas as pd
import streamlit as st

from core.access import require_app_access
from core.database import check_database, select_rows
from core.machines import machine_options
from supabase_engine import get_supabase_client
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

LOGGER = logging.getLogger(__name__)


st.set_page_config(
    page_title="Machine HMI Profiles | ABAYO",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html(
    """
    <style>
    :root {
        --navy: #071426;
        --navy-light: #10213c;
        --blue: #2563eb;
        --green: #039855;
        --orange: #f79009;
        --red: #d92d20;
        --text: #101828;
        --muted: #667085;
        --border: #e4e7ec;
        --background: #f6f8fc;
    }

    .stApp { background: var(--background); }

    .block-container {
        max-width: 1250px;
        padding-top: 5rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--navy), var(--navy-light));
        border-right: 1px solid rgba(255,255,255,.06);
    }

    [data-testid="stSidebar"] * { color: white; }

    [data-testid="stSidebar"] [data-testid="stPageLink"] a {
        border-radius: 9px;
        padding: .7rem .8rem;
        margin-bottom: .2rem;
        text-decoration: none;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
        background: rgba(37,99,235,.22);
    }

    #MainMenu, footer { visibility: hidden; }
    header { background: transparent; }

    .page-heading {
        font-size: 31px;
        line-height: 1.2;
        font-weight: 800;
        color: var(--text);
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 15px;
        margin-top: 6px;
        margin-bottom: 24px;
    }

    .info-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 4px 16px rgba(16,24,40,.045);
        margin-bottom: 18px;
    }

    .machine-banner {
        background: linear-gradient(135deg, #eff6ff, #ffffff);
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 18px;
    }

    .machine-title {
        font-size: 21px;
        font-weight: 800;
        color: var(--text);
    }

    .machine-note {
        color: var(--muted);
        margin-top: 4px;
        font-size: 14px;
    }
    </style>
    """
)
apply_theme()
require_app_access()


try:
    supabase = get_supabase_client()
    database_connected = check_database(supabase).connected
    if not database_connected:
        supabase = None
except Exception:
    supabase = None
    database_connected = False


def load_rows(table_name: str) -> list[dict]:
    if not database_connected:
        return []
    try:
        return select_rows(supabase, table_name)
    except Exception:
        return []


def table_is_ready() -> bool:
    if not database_connected:
        return False
    try:
        supabase.table("machine_hmi_profiles").select("id").limit(1).execute()
        supabase.table("machine_hmi_parameters").select("id").limit(1).execute()
        return True
    except Exception:
        return False


machines = load_rows("machines")
hmi_ready = table_is_ready()

render_sidebar(database_connected=database_connected)


st.html(
    """
    <div class="page-heading">Machine HMI Profiles</div>
    <div class="page-subtitle">
        Import, verify and preserve machine-specific HMI parameters without changing the PLC or HMI.
    </div>
    """
)

st.info(
    "This first version is read-only: it records HMI settings in ABAYO but does not write values back to the machine."
)

if not database_connected:
    st.error("Supabase is disconnected. Reconnect the database before importing HMI profiles.")
    st.stop()

if not hmi_ready:
    st.error(
        "The HMI profile tables are not ready. Run supabase_hmi_profiles_setup.sql in the Supabase SQL Editor first."
    )
    st.stop()

if not machines:
    st.warning("No machines are registered. Add a machine from the Home page first.")
    st.stop()

machine_by_id = {machine.get("id"): machine for machine in machines}
machine_choices = machine_options(machines)
machine_names = [label for label, _machine_id in machine_choices]
machine_id_by_label = dict(machine_choices)
selected_id = st.session_state.get("selected_machine_id")
selected_index = 0

for index, (_label, machine_id) in enumerate(machine_choices):
    if machine_id == selected_id:
        selected_index = index
        break

selected_machine_name = st.selectbox(
    "Machine",
    machine_names,
    index=selected_index,
    help="Every imported profile is saved only under this machine.",
)
machine_id = machine_id_by_label[selected_machine_name]
selected_machine = machine_by_id[machine_id]
st.session_state.selected_machine_id = machine_id

st.html(
    f"""
    <div class="machine-banner">
        <div class="machine-title">{escape(selected_machine_name)}</div>
        <div class="machine-note">
            {escape(str(selected_machine.get('manufacturer') or 'Manufacturer not recorded'))}
            · {escape(str(selected_machine.get('model') or 'Model not recorded'))}
            · {escape(str(selected_machine.get('location') or 'Location not recorded'))}
        </div>
    </div>
    """
)

import_tab, profiles_tab, compare_tab = st.tabs(
    ["＋ Import HMI Profile", "Saved Profiles", "Compare Profiles"]
)

with import_tab:
    st.subheader("Create a machine-specific HMI profile")
    st.caption(
        "Upload an HMI photo or screenshot as the source, then verify the parameters before saving."
    )

    left, right = st.columns(2)

    with left:
        profile_name = st.text_input(
            "Profile Name *",
            placeholder="Example: Pakona 500 g Gold Standard",
        )
        recipe_name = st.text_input(
            "Recipe / Product",
            placeholder="Example: 500 g dates pouch",
        )
        imported_by = st.text_input(
            "Imported By",
            value="Kangume Julius",
        )

    with right:
        source_type = st.selectbox(
            "Source Type",
            ["HMI photo", "HMI screenshot", "CSV export", "Manual entry"],
        )
        approval_status = st.selectbox(
            "Approval Status",
            ["Draft", "Verified", "Approved"],
            help="Use Approved only after a responsible technician has checked every value.",
        )
        profile_notes = st.text_area("Profile Notes", height=100)

    source_file = st.file_uploader(
        "Upload HMI image or CSV",
        type=["png", "jpg", "jpeg", "webp", "csv"],
        help="For photos, ABAYO keeps the filename as source evidence in this MVP. Confirm all values manually before saving.",
    )

    if source_file is not None:
        if source_file.type == "text/csv" or source_file.name.lower().endswith(".csv"):
            try:
                imported_df = pd.read_csv(source_file)
                normalized = pd.DataFrame(
                    {
                        "Parameter": imported_df.iloc[:, 0].astype(str),
                        "Value": imported_df.iloc[:, 1].astype(str) if imported_df.shape[1] > 1 else "",
                        "Unit": imported_df.iloc[:, 2].astype(str) if imported_df.shape[1] > 2 else "",
                        "HMI Page": imported_df.iloc[:, 3].astype(str) if imported_df.shape[1] > 3 else "",
                        "Notes": imported_df.iloc[:, 4].astype(str) if imported_df.shape[1] > 4 else "",
                    }
                )
                st.session_state.hmi_parameter_editor = normalized
                st.success("CSV loaded. Check every row before saving.")
            except Exception as error:
                st.error(f"Unable to read CSV: {error}")
        else:
            st.image(source_file, caption="HMI source image", width="stretch")

    default_parameters = pd.DataFrame(
        [
            {"Parameter": "", "Value": "", "Unit": "", "HMI Page": "", "Notes": ""},
            {"Parameter": "", "Value": "", "Unit": "", "HMI Page": "", "Notes": ""},
            {"Parameter": "", "Value": "", "Unit": "", "HMI Page": "", "Notes": ""},
        ]
    )

    if "hmi_parameter_editor" not in st.session_state:
        st.session_state.hmi_parameter_editor = default_parameters

    st.markdown("#### Verify parameters")
    edited_parameters = st.data_editor(
        st.session_state.hmi_parameter_editor,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "Parameter": st.column_config.TextColumn("Parameter *"),
            "Value": st.column_config.TextColumn("Value *"),
            "Unit": st.column_config.TextColumn("Unit"),
            "HMI Page": st.column_config.TextColumn("HMI Page"),
            "Notes": st.column_config.TextColumn("Notes"),
        },
        key="hmi_profile_editor_widget",
    )

    confirm_checked = st.checkbox(
        "I have checked these values against the selected machine's HMI."
    )

    if st.button("Save HMI Profile", type="primary", width="stretch"):
        cleaned = edited_parameters.fillna("").astype(str)
        cleaned = cleaned[
            (cleaned["Parameter"].str.strip() != "")
            & (cleaned["Value"].str.strip() != "")
        ]

        if not profile_name.strip():
            st.error("Profile name is required.")
        elif cleaned.empty:
            st.error("Add at least one parameter with both a name and a value.")
        elif not confirm_checked:
            st.error("Confirm that you checked the values against the HMI.")
        else:
            profile_id = None
            try:
                profile_response = (
                    supabase.table("machine_hmi_profiles")
                    .insert(
                        {
                            "machine_id": machine_id,
                            "profile_name": profile_name.strip(),
                            "recipe_name": recipe_name.strip(),
                            "source_type": source_type,
                            "source_file_name": source_file.name if source_file else None,
                            "notes": profile_notes.strip(),
                            "imported_by": imported_by.strip(),
                            "approval_status": approval_status,
                        }
                    )
                    .execute()
                )

                profile_id = profile_response.data[0]["id"]
                parameter_rows = []

                for sequence_no, (_, row) in enumerate(cleaned.iterrows(), start=1):
                    parameter_rows.append(
                        {
                            "profile_id": profile_id,
                            "parameter_name": row["Parameter"].strip(),
                            "parameter_value": row["Value"].strip(),
                            "unit": row["Unit"].strip(),
                            "hmi_page": row["HMI Page"].strip(),
                            "notes": row["Notes"].strip(),
                            "sequence_no": sequence_no,
                        }
                    )

                supabase.table("machine_hmi_parameters").insert(parameter_rows).execute()
                st.session_state.hmi_parameter_editor = default_parameters
                st.success(f"{profile_name.strip()} was saved under {selected_machine_name}.")
                st.rerun()
            except Exception as error:
                if profile_id is not None:
                    try:
                        (
                            supabase.table("machine_hmi_profiles")
                            .delete()
                            .eq("id", profile_id)
                            .execute()
                        )
                    except Exception as cleanup_error:
                        LOGGER.warning(
                            "Unable to remove incomplete HMI profile %s: %s",
                            profile_id,
                            cleanup_error,
                        )
                st.error(f"Unable to save the HMI profile: {error}")

with profiles_tab:
    try:
        profiles = (
            supabase.table("machine_hmi_profiles")
            .select("*")
            .eq("machine_id", machine_id)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
    except Exception:
        profiles = []

    if not profiles:
        st.info("No HMI profiles have been saved for this machine.")
    else:
        for profile in profiles:
            label = profile.get("profile_name") or f"Profile {profile.get('id')}"
            with st.expander(f"{label} · {profile.get('approval_status', 'Draft')}"):
                st.write(f"**Recipe/Product:** {profile.get('recipe_name') or 'Not recorded'}")
                st.write(f"**Source:** {profile.get('source_type') or 'Not recorded'}")
                st.write(f"**Source file:** {profile.get('source_file_name') or 'Not attached'}")
                st.write(f"**Imported by:** {profile.get('imported_by') or 'Not recorded'}")
                st.write(f"**Created:** {profile.get('created_at') or ''}")

                try:
                    parameters = (
                        supabase.table("machine_hmi_parameters")
                        .select("parameter_name, parameter_value, unit, hmi_page, notes, sequence_no")
                        .eq("profile_id", profile.get("id"))
                        .order("sequence_no")
                        .execute()
                        .data
                        or []
                    )
                except Exception:
                    parameters = []

                if parameters:
                    display_rows = [
                        {
                            "Parameter": row.get("parameter_name", ""),
                            "Value": row.get("parameter_value", ""),
                            "Unit": row.get("unit", ""),
                            "HMI Page": row.get("hmi_page", ""),
                            "Notes": row.get("notes", ""),
                        }
                        for row in parameters
                    ]
                    st.dataframe(display_rows, width="stretch", hide_index=True)
                else:
                    st.warning("This profile contains no parameters.")

with compare_tab:
    try:
        compare_profiles = (
            supabase.table("machine_hmi_profiles")
            .select("id, profile_name")
            .eq("machine_id", machine_id)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
    except Exception:
        compare_profiles = []

    if len(compare_profiles) < 2:
        st.info("Save at least two profiles for this machine before comparing them.")
    else:
        profile_options = {
            (
                f"{row.get('profile_name') or 'Profile'} — "
                f"ID {row.get('id')}"
            ): row.get("id")
            for row in compare_profiles
        }
        left_name, right_name = st.columns(2)
        names = list(profile_options.keys())

        with left_name:
            profile_a_name = st.selectbox("Profile A", names, index=0)
        with right_name:
            profile_b_name = st.selectbox("Profile B", names, index=1)

        if profile_a_name == profile_b_name:
            st.warning("Choose two different profiles.")
        else:
            def load_parameters(profile_id: int) -> dict[str, dict]:
                rows = (
                    supabase.table("machine_hmi_parameters")
                    .select("parameter_name, parameter_value, unit")
                    .eq("profile_id", profile_id)
                    .execute()
                    .data
                    or []
                )
                return {
                    str(row.get("parameter_name", "")).strip().lower(): row
                    for row in rows
                    if str(row.get("parameter_name", "")).strip()
                }

            try:
                params_a = load_parameters(profile_options[profile_a_name])
                params_b = load_parameters(profile_options[profile_b_name])
                all_keys = sorted(set(params_a) | set(params_b))
                comparison_rows = []

                for key in all_keys:
                    row_a = params_a.get(key, {})
                    row_b = params_b.get(key, {})
                    value_a = str(row_a.get("parameter_value", ""))
                    value_b = str(row_b.get("parameter_value", ""))
                    comparison_rows.append(
                        {
                            "Parameter": row_a.get("parameter_name") or row_b.get("parameter_name") or key,
                            profile_a_name: value_a,
                            profile_b_name: value_b,
                            "Unit": row_a.get("unit") or row_b.get("unit") or "",
                            "Match": "Yes" if value_a == value_b and value_a != "" else "No",
                        }
                    )

                st.dataframe(comparison_rows, width="stretch", hide_index=True)
            except Exception as error:
                st.error(f"Unable to compare profiles: {error}")
