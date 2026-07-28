from __future__ import annotations

import hmac

import streamlit as st

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
        label=f"Recycle Bin ({len(deleted_machines)})",
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


st.html(
    f"""
    <div class="page-heading">Recycle Bin 🗑️</div>
    <div class="page-subtitle">
        Restore deleted machines or remove them permanently.
        Items are retained for {RETENTION_DAYS} days.
    </div>
    """
)


if not database_connected:
    st.error(
        "The cloud database is disconnected. Reconnect Supabase to use "
        "the Recycle Bin."
    )
    st.stop()

if not recycle_ready:
    st.error(
        "Recycle Bin setup is incomplete. Run "
        "supabase_recycle_bin_setup.sql in the Supabase SQL Editor."
    )
    st.stop()


st.html(
    f"""
    <div class="recycle-summary">
        <div class="summary-title">
            {len(deleted_machines)} deleted machine(s)
        </div>
        <div class="summary-note">
            A restored machine keeps its original ID and linked history.
            Permanent deletion cannot be undone.
        </div>
    </div>
    """
)

if "recycle_flash_message" in st.session_state:
    st.success(st.session_state.pop("recycle_flash_message"))

render_admin_access()


if not deleted_machines:
    st.info("The Recycle Bin is empty.")

for machine in deleted_machines:
    machine_id = machine.get("id")
    machine_name = str(
        machine.get("machine_name")
        or f"Machine {machine_id}"
    )
    manufacturer = str(machine.get("manufacturer") or "Not recorded")
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
                        st.session_state.selected_machine_id = machine_id
                        st.session_state.recycle_flash_message = (
                            f"{machine_name} was restored."
                        )
                        st.rerun()
                    except Exception as error:
                        st.error(f"Unable to restore machine: {error}")

            with delete_column:
                if st.button(
                    "🗑️ Delete Forever",
                    key=f"permanent_delete_{machine_id}",
                    use_container_width=True,
                    disabled=not admin_is_unlocked(),
                ):
                    st.session_state.pending_permanent_delete = machine_id

        if (
            st.session_state.get("pending_permanent_delete")
            == machine_id
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
                            "Unable to permanently delete this machine. "
                            "Linked records may be protected by Supabase. "
                            f"Details: {error}"
                        )

            with cancel_column:
                if st.button(
                    "Cancel",
                    key=f"cancel_permanent_delete_{machine_id}",
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
