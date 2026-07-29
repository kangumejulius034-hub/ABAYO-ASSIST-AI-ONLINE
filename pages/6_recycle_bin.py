from __future__ import annotations

import hmac
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import component_engine
from maintenance_engine import (
    load_maintenance_records,
    save_all_maintenance_records,
)
from recipe_engine import save_recipe
from recycle_bin_engine import (
    RETENTION_DAYS,
    days_until_permanent_deletion,
    format_deleted_at,
    load_deleted_machines,
    permanently_delete_machine,
    purge_expired_machines,
    recycle_bin_is_ready,
    restore_machine,
)
from supabase_engine import get_supabase_client
from troubleshooting_engine import (
    load_troubleshooting,
    save_troubleshooting,
)


st.set_page_config(
    page_title="Recycle Bin | ABAYO",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.html(
    """
    <style>
    :root {
        --navy: #071426;
        --navy-light: #10213c;
        --green: #039855;
        --red: #d92d20;
        --text: #101828;
        --muted: #667085;
        --border: #e4e7ec;
        --background: #f6f8fc;
    }

    .stApp {
        background: var(--background);
    }

    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.75rem !important;
        left: 0.75rem !important;
        z-index: 999999 !important;
        background: var(--navy) !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.22) !important;
    }

    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] svg {
        color: white !important;
        fill: white !important;
        stroke: white !important;
        opacity: 1 !important;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            var(--navy) 0%,
            var(--navy-light) 100%
        );
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink"] a {
        border-radius: 9px;
        padding: 0.7rem 0.8rem;
        margin-bottom: 0.2rem;
        text-decoration: none;
    }

    [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
        background: rgba(37, 99, 235, 0.22);
    }

    [data-testid="stSidebar"] .stButton button {
        width: 100%;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.05);
        border-radius: 9px;
        min-height: 44px;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(37, 99, 235, 0.28);
        border-color: #3b82f6;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }

    .page-heading {
        font-size: 31px;
        line-height: 1.2;
        font-weight: 800;
        color: var(--text);
        margin: 0;
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 15px;
        margin-top: 6px;
        margin-bottom: 24px;
    }

    .recycle-summary {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.045);
        margin-bottom: 18px;
    }

    .summary-title {
        color: var(--text);
        font-size: 15px;
        font-weight: 800;
    }

    .summary-note {
        color: var(--muted);
        font-size: 13px;
        margin-top: 5px;
    }

    .app-footer {
        color: #98a2b3;
        text-align: center;
        margin-top: 35px;
        font-size: 12px;
    }
    </style>
    """
)


LOCAL_RECYCLE_BINS = {
    "Faults": {
        "icon": "🔧",
        "file": PROJECT_ROOT / "knowledge" / "recycle_bin_faults.json",
    },
    "Recipes": {
        "icon": "📖",
        "file": PROJECT_ROOT / "knowledge" / "recycle_bin_recipes.json",
    },
    "Maintenance": {
        "icon": "🛠️",
        "file": PROJECT_ROOT / "knowledge" / "recycle_bin_maintenance.json",
    },
    "Troubleshooting": {
        "icon": "🧠",
        "file": (
            PROJECT_ROOT
            / "knowledge"
            / "recycle_bin_troubleshooting.json"
        ),
    },
    "Components": {
        "icon": "⚙️",
        "file": PROJECT_ROOT / "knowledge" / "recycle_bin_components.json",
    },
}


def load_json_list(file_path: Path) -> list[dict[str, Any]]:
    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    return [
        record
        for record in data
        if isinstance(record, dict)
    ]


def save_json_list(
    file_path: Path,
    records: list[dict[str, Any]],
) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=4, ensure_ascii=False)


def local_record_name(
    record_type: str,
    record: dict[str, Any],
    number: int,
) -> str:
    preferred_fields = {
        "Faults": ("fault", "fault_name", "title"),
        "Recipes": ("recipe_name", "name"),
        "Maintenance": ("record_number", "fault"),
        "Troubleshooting": ("solution_number", "fault"),
        "Components": ("component_name", "component_number"),
    }

    for field_name in preferred_fields.get(record_type, ()):
        value = record.get(field_name)

        if value not in (None, ""):
            return str(value)

    return f"{record_type.rstrip('s')} {number}"


def deleted_date_text(value: Any) -> str:
    if not value:
        return "Deletion date not recorded"

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return parsed.astimezone().strftime("%d %b %Y, %H:%M")
    except (TypeError, ValueError):
        return str(value)


def days_left_for_local_record(value: Any) -> int:
    try:
        deleted_at = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if deleted_at.tzinfo is None:
            deleted_at = deleted_at.replace(tzinfo=timezone.utc)

        elapsed_days = (
            datetime.now(timezone.utc) - deleted_at
        ).days
        return max(RETENTION_DAYS - elapsed_days, 0)
    except (TypeError, ValueError):
        return RETENTION_DAYS


def clean_recycled_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.items()
        if key not in {"_deleted_at", "_deleted_from"}
    }


def save_active_components(records: list[dict[str, Any]]) -> None:
    for function_name in ("save_components", "save_all_components"):
        save_function = getattr(
            component_engine,
            function_name,
            None,
        )

        if callable(save_function):
            save_function(records)
            return

    component_file_candidates = (
        PROJECT_ROOT / "knowledge" / "components.json",
        PROJECT_ROOT / "knowledge" / "machine_components.json",
    )
    component_file = next(
        (
            path
            for path in component_file_candidates
            if path.exists()
        ),
        component_file_candidates[0],
    )
    save_json_list(component_file, records)


def restore_local_record(
    record_type: str,
    record: dict[str, Any],
) -> None:
    active_record = clean_recycled_record(record)

    if record_type == "Faults":
        active_file = PROJECT_ROOT / "knowledge" / "faults.json"
        active_records = load_json_list(active_file)
        active_records.append(active_record)
        save_json_list(active_file, active_records)

    elif record_type == "Recipes":
        save_recipe(
            machine_model=active_record.get(
                "machine_model",
                "Pakona PFS AG",
            ),
            recipe_name=active_record.get(
                "recipe_name",
                "Restored recipe",
            ),
            status=active_record.get(
                "status",
                "Awaiting confirmation",
            ),
            parameters=active_record.get("parameters", {}),
            notes=active_record.get("notes", ""),
            hmi_images=active_record.get("hmi_images", []),
        )

    elif record_type == "Maintenance":
        active_records = load_maintenance_records()
        active_records.append(active_record)
        save_all_maintenance_records(active_records)

    elif record_type == "Troubleshooting":
        active_records = load_troubleshooting()
        active_records.append(active_record)
        save_troubleshooting(active_records)

    elif record_type == "Components":
        active_records = component_engine.load_components()
        active_records.append(active_record)
        save_active_components(active_records)


def display_local_record(record: dict[str, Any]) -> None:
    for field_name, value in clean_recycled_record(record).items():
        readable_name = str(field_name).replace("_", " ").title()

        if isinstance(value, list):
            st.markdown(f"**{readable_name}**")

            if value:
                for item in value:
                    st.write(f"• {item}")
            else:
                st.write("Not recorded")

        elif isinstance(value, dict):
            st.markdown(f"**{readable_name}**")

            rows = []

            for item_name, item_value in value.items():
                if isinstance(item_value, dict):
                    for sub_name, sub_value in item_value.items():
                        rows.append(
                            {
                                "Parameter": item_name,
                                "Field": str(sub_name).replace(
                                    "_",
                                    " ",
                                ).title(),
                                "Value": sub_value,
                            }
                        )
                else:
                    rows.append(
                        {
                            "Parameter": item_name,
                            "Field": "Value",
                            "Value": item_value,
                        }
                    )

            if rows:
                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

        else:
            st.markdown(f"**{readable_name}:** {value or 'Not recorded'}")


def configured_admin_pin() -> str:
    try:
        return str(st.secrets.get("ABAYO_ADMIN_PIN", "")).strip()
    except Exception:
        return ""


def admin_is_unlocked() -> bool:
    return bool(st.session_state.get("admin_actions_unlocked", False))


def render_admin_access() -> None:
    expected_pin = configured_admin_pin()

    with st.expander("🔐 Administrator access", expanded=not admin_is_unlocked()):
        if not expected_pin:
            st.warning(
                "Deletion controls are locked. Add ABAYO_ADMIN_PIN to "
                "your Streamlit secrets."
            )
            return

        if admin_is_unlocked():
            left, right = st.columns([4, 1])
            with left:
                st.success("Administrator controls are unlocked.")
            with right:
                if st.button(
                    "Lock",
                    key="lock_recycle_admin",
                    use_container_width=True,
                ):
                    st.session_state.admin_actions_unlocked = False
                    st.rerun()
            return

        entered_pin = st.text_input(
            "Administrator PIN",
            type="password",
            key="recycle_admin_pin",
        )

        if st.button(
            "Unlock controls",
            key="unlock_recycle_admin",
            use_container_width=True,
        ):
            if hmac.compare_digest(entered_pin, expected_pin):
                st.session_state.admin_actions_unlocked = True
                st.success("Administrator controls unlocked.")
                st.rerun()
            else:
                st.error("Incorrect administrator PIN.")


try:
    supabase = get_supabase_client()
    database_connected = True
except Exception:
    supabase = None
    database_connected = False


recycle_ready = (
    database_connected
    and recycle_bin_is_ready(supabase)
)

if recycle_ready:
    try:
        purge_expired_machines(supabase)
    except Exception:
        # A linked-record foreign key may deliberately block permanent removal.
        pass

try:
    deleted_machines = (
        load_deleted_machines(supabase)
        if recycle_ready
        else []
    )
except Exception:
    deleted_machines = []

local_deleted_records = {
    record_type: load_json_list(settings["file"])
    for record_type, settings in LOCAL_RECYCLE_BINS.items()
}

total_deleted_items = (
    len(deleted_machines)
    + sum(
        len(records)
        for records in local_deleted_records.values()
    )
)


with st.sidebar:
    st.markdown("## 🔷 ABAYO")
    st.caption("AI Operations Assistant")
    st.markdown("---")

    st.page_link(
        "app.py",
        label="Home",
        icon="🏠",
        use_container_width=True,
    )

    st.markdown("#### MACHINES")

    st.page_link(
        "pages/1_fault_diagnosis.py",
        label="Fault Diagnosis",
        icon="🔧",
        use_container_width=True,
    )

    st.page_link(
        "pages/2_recipe_library.py",
        label="Recipe Library",
        icon="📖",
        use_container_width=True,
    )

    st.page_link(
        "pages/3_maintenance_history.py",
        label="Maintenance",
        icon="🛠️",
        use_container_width=True,
    )

    st.page_link(
        "pages/4_smart_toubleshooter.py",
        label="Knowledge Base",
        icon="🧠",
        use_container_width=True,
    )

    st.page_link(
        "pages/5_machine_components.py",
        label="Machine Components",
        icon="⚙️",
        use_container_width=True,
    )

    st.page_link(
        "pages/6_recycle_bin.py",
        label=f"Recycle Bin ({total_deleted_items})",
        icon="🗑️",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("#### ABAYO ASSISTANT")
    st.markdown("🤖 **AI Assistant**")
    st.caption("Coming soon")
    st.markdown("---")

    if database_connected:
        st.success("● Cloud system connected")
    else:
        st.error("● Cloud system disconnected")

    st.caption("System Version 0.6")

if st.button(
    "🏠 ← MAIN MENU",
    key="recycle_bin_main_menu_button",
):
    st.switch_page("app.py")

st.html(
    f"""
    <div class="page-heading">Recycle Bin 🗑️</div>
    <div class="page-subtitle">
        Restore deleted ABAYO records or remove them permanently.
        Items are retained for {RETENTION_DAYS} days.
    </div>
    """
)


if not database_connected:
    st.warning(
        "The cloud database is disconnected. Recycled local records "
        "remain available, but deleted machines cannot be managed."
    )

elif not recycle_ready:
    st.warning(
        "Recycle Bin setup is incomplete. Run "
        "supabase_recycle_bin_setup.sql to manage deleted machines."
    )


st.html(
    f"""
    <div class="recycle-summary">
        <div class="summary-title">
            {total_deleted_items} recycled item(s)
        </div>
        <div class="summary-note">
            Restore an item to return it to its original ABAYO module.
            Permanent deletion cannot be undone.
        </div>
    </div>
    """
)

if "recycle_flash_message" in st.session_state:
    st.success(st.session_state.pop("recycle_flash_message"))

render_admin_access()


if total_deleted_items == 0:
    st.info("The Recycle Bin is empty.")

tab_names = [
    f"🏭 Machines ({len(deleted_machines)})",
    *[
        (
            f"{LOCAL_RECYCLE_BINS[record_type]['icon']} "
            f"{record_type} ({len(records)})"
        )
        for record_type, records in local_deleted_records.items()
    ],
]

recycle_tabs = st.tabs(tab_names)

with recycle_tabs[0]:
    if not recycle_ready:
        st.info(
            "Machine recycling becomes available after the Supabase "
            "Recycle Bin setup is connected."
        )

    elif not deleted_machines:
        st.info("No machines are currently in the Recycle Bin.")

    for machine in deleted_machines:
        machine_id = machine.get("id")
        machine_name = str(
            machine.get("machine_name")
            or f"Machine {machine_id}"
        )
        manufacturer = str(
            machine.get("manufacturer")
            or "Not recorded"
        )
        model = str(machine.get("model") or "Not recorded")
        deleted_at = machine.get("deleted_at")
        days_left = days_until_permanent_deletion(deleted_at)

        with st.container(border=True):
            details, actions = st.columns([3, 2])

            with details:
                st.subheader(f"🏭 {machine_name}")
                st.caption(
                    f"{manufacturer} • {model}  \n"
                    f"Deleted: {format_deleted_at(deleted_at)}  \n"
                    f"Permanent deletion in: {days_left} day(s)"
                )

            with actions:
                restore_column, delete_column = st.columns(2)

                with restore_column:
                    if st.button(
                        "↩️ Restore",
                        key=f"restore_machine_{machine_id}",
                        use_container_width=True,
                        disabled=not admin_is_unlocked(),
                    ):
                        try:
                            restore_machine(supabase, machine_id)
                            st.session_state.selected_machine_id = (
                                machine_id
                            )
                            st.session_state.recycle_flash_message = (
                                f"{machine_name} was restored."
                            )
                            st.rerun()
                        except Exception as error:
                            st.error(
                                f"Unable to restore machine: {error}"
                            )

                with delete_column:
                    if st.button(
                        "🗑️ Delete Forever",
                        key=f"permanent_delete_{machine_id}",
                        use_container_width=True,
                        disabled=not admin_is_unlocked(),
                    ):
                        st.session_state.pending_permanent_delete = (
                            f"machine:{machine_id}"
                        )

            if (
                st.session_state.get("pending_permanent_delete")
                == f"machine:{machine_id}"
            ):
                st.error(
                    f"This will permanently erase {machine_name}. "
                    "This action cannot be undone."
                )

                typed_name = st.text_input(
                    f'Type "{machine_name}" to confirm',
                    key=f"confirm_permanent_name_{machine_id}",
                )

                confirm_column, cancel_column = st.columns(2)

                with confirm_column:
                    if st.button(
                        "Permanently Delete",
                        key=f"confirm_permanent_delete_{machine_id}",
                        type="primary",
                        use_container_width=True,
                        disabled=typed_name.strip() != machine_name,
                    ):
                        try:
                            permanently_delete_machine(
                                supabase,
                                machine_id,
                            )
                            st.session_state.pending_permanent_delete = None
                            st.session_state.recycle_flash_message = (
                                f"{machine_name} was permanently deleted."
                            )
                            st.rerun()
                        except Exception as error:
                            st.error(
                                "Unable to permanently delete this "
                                f"machine. Details: {error}"
                            )

                with cancel_column:
                    if st.button(
                        "Cancel",
                        key=f"cancel_permanent_delete_{machine_id}",
                        use_container_width=True,
                    ):
                        st.session_state.pending_permanent_delete = None
                        st.rerun()


for tab_index, (
    record_type,
    recycled_records,
) in enumerate(
    local_deleted_records.items(),
    start=1,
):
    with recycle_tabs[tab_index]:
        if not recycled_records:
            st.info(
                f"No recycled {record_type.lower()} found."
            )

        recycle_file = LOCAL_RECYCLE_BINS[record_type]["file"]
        icon = LOCAL_RECYCLE_BINS[record_type]["icon"]

        for record_index, record in enumerate(recycled_records):
            record_name = local_record_name(
                record_type,
                record,
                record_index + 1,
            )
            deleted_at = record.get("_deleted_at")
            days_left = days_left_for_local_record(deleted_at)
            item_key = f"{record_type}:{record_index}"

            with st.container(border=True):
                details, menu_column = st.columns([8, 1])

                with details:
                    st.subheader(f"{icon} {record_name}")
                    st.caption(
                        f"Deleted: {deleted_date_text(deleted_at)}  \n"
                        f"Permanent deletion in: {days_left} day(s)"
                    )

                with menu_column:
                    with st.popover(
                        "⋮",
                        help=f"Options for {record_name}",
                        use_container_width=True,
                    ):
                        if st.button(
                            "Open",
                            key=f"open_recycled_{item_key}",
                            use_container_width=True,
                        ):
                            st.session_state.open_recycled_item = item_key
                            st.rerun()

                        if st.button(
                            "↩️ Restore",
                            key=f"restore_recycled_{item_key}",
                            use_container_width=True,
                            disabled=not admin_is_unlocked(),
                        ):
                            try:
                                restore_local_record(
                                    record_type,
                                    record,
                                )
                                refreshed_records = load_json_list(
                                    recycle_file
                                )
                                refreshed_records.pop(record_index)
                                save_json_list(
                                    recycle_file,
                                    refreshed_records,
                                )
                                st.session_state.recycle_flash_message = (
                                    f"{record_name} was restored."
                                )
                                st.rerun()
                            except Exception as error:
                                st.error(
                                    f"Unable to restore item: {error}"
                                )

                        if st.button(
                            "🗑️ Delete Forever",
                            key=f"delete_recycled_{item_key}",
                            use_container_width=True,
                            disabled=not admin_is_unlocked(),
                        ):
                            st.session_state.pending_permanent_delete = (
                                item_key
                            )
                            st.rerun()

                if (
                    st.session_state.get("open_recycled_item")
                    == item_key
                ):
                    display_local_record(record)

                    if st.button(
                        "Close",
                        key=f"close_recycled_{item_key}",
                    ):
                        st.session_state.open_recycled_item = None
                        st.rerun()

                if (
                    st.session_state.get("pending_permanent_delete")
                    == item_key
                ):
                    st.error(
                        f'Permanently delete "{record_name}"? '
                        "This cannot be undone."
                    )

                    confirm_delete = st.checkbox(
                        "Yes, permanently delete this item.",
                        key=f"confirm_recycled_{item_key}",
                    )

                    confirm_column, cancel_column = st.columns(2)

                    with confirm_column:
                        if st.button(
                            "🗑️ Delete Permanently",
                            type="primary",
                            disabled=not confirm_delete,
                            key=f"confirm_delete_recycled_{item_key}",
                            use_container_width=True,
                        ):
                            refreshed_records = load_json_list(
                                recycle_file
                            )

                            if record_index < len(refreshed_records):
                                refreshed_records.pop(record_index)
                                save_json_list(
                                    recycle_file,
                                    refreshed_records,
                                )

                            st.session_state.pending_permanent_delete = None
                            st.session_state.recycle_flash_message = (
                                f"{record_name} was permanently deleted."
                            )
                            st.rerun()

                    with cancel_column:
                        if st.button(
                            "Cancel",
                            key=f"cancel_recycled_{item_key}",
                            use_container_width=True,
                        ):
                            st.session_state.pending_permanent_delete = None
                            st.rerun()


st.html(
    """
    <div class="app-footer">
        ABAYO AI Operations Assistant • System Version 0.6
    </div>
    """
)
