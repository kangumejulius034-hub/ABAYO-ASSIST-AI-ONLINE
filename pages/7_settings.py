from __future__ import annotations

from html import escape

import streamlit as st

from supabase_engine import get_supabase_client


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Settings | ABAYO",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DESIGN
# =========================================================

st.html(
    """
    <style>
    :root {
        --navy: #071426;
        --navy-light: #10213c;
        --blue: #2563eb;
        --blue-light: #eff6ff;
        --green: #039855;
        --green-light: #ecfdf3;
        --orange: #f79009;
        --orange-light: #fffaeb;
        --red: #d92d20;
        --red-light: #fef3f2;
        --text: #101828;
        --muted: #667085;
        --border: #e4e7ec;
        --background: #f6f8fc;
    }

    .stApp {
        background: var(--background);
    }

    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(
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

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }

    .settings-heading {
        color: var(--text);
        font-size: 31px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .settings-subtitle {
        color: var(--muted);
        font-size: 15px;
        margin-bottom: 24px;
    }

    .section-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 21px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.045);
    }

    .section-title {
        color: var(--text);
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .section-note {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 14px;
    }

    .profile-preview {
        background: linear-gradient(135deg, #eff6ff, #f8fafc);
        border: 1px solid #dbeafe;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .preview-title {
        color: var(--text);
        font-size: 22px;
        font-weight: 800;
    }

    .preview-subtitle {
        color: var(--muted);
        font-size: 14px;
        margin-top: 5px;
    }

    .security-box {
        background: var(--orange-light);
        border: 1px solid #fedf89;
        border-radius: 12px;
        padding: 16px;
        color: #7a2e0e;
    }

    .system-box {
        background: var(--green-light);
        border: 1px solid #abefc6;
        border-radius: 12px;
        padding: 16px;
        color: #05603a;
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


# =========================================================
# DATABASE
# =========================================================

try:
    supabase = get_supabase_client()
    database_connected = True
except Exception:
    supabase = None
    database_connected = False


DEFAULT_SETTINGS = {
    "id": "global",
    "display_name": "Kangume Julius",
    "job_title": "Administrator",
    "company_name": "",
    "welcome_title": "Welcome back",
    "welcome_subtitle": (
        "Monitor machines, diagnose faults and preserve operational knowledge."
    ),
    "support_email": "",
    "default_machine_location": "",
    "default_machine_status": "Online",
}


def load_settings() -> dict:
    """Load the global ABAYO settings record."""

    if not database_connected:
        return DEFAULT_SETTINGS.copy()

    try:
        response = (
            supabase.table("app_settings")
            .select("*")
            .eq("id", "global")
            .limit(1)
            .execute()
        )

        if response.data:
            saved_settings = response.data[0]

            return {
                **DEFAULT_SETTINGS,
                **saved_settings,
            }

    except Exception:
        pass

    return DEFAULT_SETTINGS.copy()


def save_settings(settings_data: dict) -> None:
    """Create or update the global ABAYO settings record."""

    if not database_connected:
        raise RuntimeError("The cloud database is disconnected.")

    (
        supabase.table("app_settings")
        .upsert(
            settings_data,
            on_conflict="id",
        )
        .execute()
    )


settings = load_settings()


# =========================================================
# SIDEBAR
# =========================================================

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

    st.markdown("#### OPERATIONS")

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

    st.markdown("#### SYSTEM")

    st.page_link(
        "pages/6_recycle_bin.py",
        label="Recycle Bin",
        icon="🗑️",
        use_container_width=True,
    )

    st.page_link(
        "pages/7_settings.py",
        label="Settings",
        icon="⚙️",
        use_container_width=True,
    )

    st.markdown("---")

    if database_connected:
        st.success("● Cloud system connected")
    else:
        st.error("● Cloud system disconnected")

    st.caption("System Version 0.6.2")


# =========================================================
# HEADER
# =========================================================

st.html(
    """
    <div class="settings-heading">Settings</div>
    <div class="settings-subtitle">
        Manage ABAYO profile, display preferences and machine defaults.
    </div>
    """
)


if not database_connected:
    st.error(
        "ABAYO cannot save settings because the Supabase database "
        "is currently disconnected."
    )


# =========================================================
# PROFILE PREVIEW
# =========================================================

preview_name = escape(
    str(settings.get("display_name") or "ABAYO User")
)

preview_title = escape(
    str(settings.get("welcome_title") or "Welcome back")
)

preview_subtitle = escape(
    str(settings.get("welcome_subtitle") or "")
)

st.html(
    f"""
    <div class="profile-preview">
        <div class="preview-title">
            {preview_title}, {preview_name} 👋
        </div>

        <div class="preview-subtitle">
            {preview_subtitle}
        </div>
    </div>
    """
)


# =========================================================
# SETTINGS FORM
# =========================================================

with st.form("abayo_settings_form"):
    st.html(
        """
        <div class="section-title">👤 User Profile</div>
        <div class="section-note">
            These details appear in the ABAYO dashboard header.
        </div>
        """
    )

    profile_left, profile_right = st.columns(2)

    with profile_left:
        display_name = st.text_input(
            "Display Name",
            value=str(settings.get("display_name") or ""),
            help="The name shown in the welcome message.",
        )

        job_title = st.text_input(
            "Job Title",
            value=str(settings.get("job_title") or ""),
            help="Example: Administrator, Technician or Maintenance Engineer.",
        )

    with profile_right:
        company_name = st.text_input(
            "Company Name",
            value=str(settings.get("company_name") or ""),
            help="The company or factory using ABAYO.",
        )

        support_email = st.text_input(
            "Support Email",
            value=str(settings.get("support_email") or ""),
            help="Optional support contact shown in the application.",
        )

    st.divider()

    st.html(
        """
        <div class="section-title">🖥️ Dashboard Display</div>
        <div class="section-note">
            Control the welcome message displayed on the home page.
        </div>
        """
    )

    welcome_title = st.text_input(
        "Welcome Title",
        value=str(settings.get("welcome_title") or "Welcome back"),
        help="Example: Welcome back, Welcome or Good evening.",
    )

    welcome_subtitle = st.text_area(
        "Welcome Subtitle",
        value=str(settings.get("welcome_subtitle") or ""),
        height=100,
        help="The short operational message shown below the welcome title.",
    )

    st.divider()

    st.html(
        """
        <div class="section-title">🏭 Machine Defaults</div>
        <div class="section-note">
            These values can automatically appear when adding new machines.
        </div>
        """
    )

    machine_left, machine_right = st.columns(2)

    with machine_left:
        default_machine_location = st.text_input(
            "Default Machine Location",
            value=str(
                settings.get("default_machine_location") or ""
            ),
            placeholder="Example: Packaging Hall 1",
        )

    with machine_right:
        status_options = [
            "Online",
            "Offline",
            "Maintenance",
        ]

        current_status = str(
            settings.get("default_machine_status") or "Online"
        )

        if current_status not in status_options:
            current_status = "Online"

        default_machine_status = st.selectbox(
            "Default Machine Status",
            options=status_options,
            index=status_options.index(current_status),
        )

    st.divider()

    save_button = st.form_submit_button(
        "Save Settings",
        type="primary",
        use_container_width=True,
        disabled=not database_connected,
    )


if save_button:
    cleaned_display_name = display_name.strip()
    cleaned_welcome_title = welcome_title.strip()
    cleaned_welcome_subtitle = welcome_subtitle.strip()

    if not cleaned_display_name:
        st.error("Display name is required.")

    elif not cleaned_welcome_title:
        st.error("Welcome title is required.")

    elif not cleaned_welcome_subtitle:
        st.error("Welcome subtitle is required.")

    else:
        updated_settings = {
            "id": "global",
            "display_name": cleaned_display_name,
            "job_title": job_title.strip(),
            "company_name": company_name.strip(),
            "welcome_title": cleaned_welcome_title,
            "welcome_subtitle": cleaned_welcome_subtitle,
            "support_email": support_email.strip(),
            "default_machine_location": (
                default_machine_location.strip()
            ),
            "default_machine_status": default_machine_status,
        }

        try:
            save_settings(updated_settings)

            st.session_state.settings_flash_message = (
                "ABAYO settings were saved successfully."
            )

            st.rerun()

        except Exception as error:
            st.error(f"Unable to save settings: {error}")


if "settings_flash_message" in st.session_state:
    st.success(
        st.session_state.pop("settings_flash_message")
    )


# =========================================================
# SECURITY
# =========================================================

st.html('<div class="section-heading">Security</div>')

try:
    admin_pin_configured = bool(
        str(st.secrets.get("ABAYO_ADMIN_PIN", "")).strip()
    )
except Exception:
    admin_pin_configured = False


if admin_pin_configured:
    st.html(
        """
        <div class="system-box">
            <strong>Administrator protection is active.</strong><br>
            The administrator PIN is securely stored in Streamlit Secrets
            and is not displayed inside ABAYO.
        </div>
        """
    )
else:
    st.html(
        """
        <div class="security-box">
            <strong>Administrator PIN is not configured.</strong><br>
            Add ABAYO_ADMIN_PIN to Streamlit Secrets before allowing users
            to delete machines or perform other protected actions.
        </div>
        """
    )


with st.expander("How to update the administrator PIN"):
    st.markdown(
        """
        The administrator PIN should not be stored in the app_settings table.

        Open:

        **Streamlit Cloud → App Settings → Secrets**

        Add:

        ```toml
        ABAYO_ADMIN_PIN = "your-private-pin"
        ```

        Save the secrets and reboot the application.
        """
    )


# =========================================================
# SYSTEM INFORMATION
# =========================================================

st.html('<div class="section-heading">System Information</div>')

system_col_1, system_col_2, system_col_3 = st.columns(3)

with system_col_1:
    st.metric(
        "Application",
        "ABAYO Assist",
    )

with system_col_2:
    st.metric(
        "System Version",
        "0.6.2",
    )

with system_col_3:
    st.metric(
        "Cloud Database",
        "Connected" if database_connected else "Offline",
    )


st.html(
    """
    <div class="app-footer">
        ABAYO AI Operations Assistant • Settings
    </div>
    """
)
