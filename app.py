from html import escape

import streamlit as st

from supabase_engine import get_supabase_client


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="ABAYO",
    page_icon="🏠",
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
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
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

    /* Hide Streamlit decoration */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }

    /* Typography */
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

    .section-heading {
        font-size: 21px;
        font-weight: 800;
        color: var(--text);
        margin-top: 26px;
        margin-bottom: 12px;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 19px;
        min-height: 148px;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.045);
    }

    .metric-icon {
        width: 42px;
        height: 42px;
        border-radius: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        margin-bottom: 12px;
    }

    .green-icon {
        background: var(--green-light);
    }

    .red-icon {
        background: var(--red-light);
    }

    .orange-icon {
        background: var(--orange-light);
    }

    .blue-icon {
        background: var(--blue-light);
    }

    .metric-label {
        color: #344054;
        font-size: 14px;
        font-weight: 700;
    }

    .metric-value {
        color: var(--text);
        font-size: 29px;
        font-weight: 800;
        margin-top: 4px;
    }

    .metric-value.connected {
        color: var(--green);
        font-size: 23px;
        margin-top: 10px;
    }

    .metric-note {
        color: var(--muted);
        font-size: 13px;
        margin-top: 4px;
    }

    /* Machine card */
    .machine-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 22px;
        box-shadow: 0 4px 16px rgba(16, 24, 40, 0.045);
    }

    .machine-header {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .machine-icon {
        width: 58px;
        height: 58px;
        border-radius: 50%;
        background: var(--green-light);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 29px;
        flex-shrink: 0;
    }

    .machine-name {
        color: var(--text);
        font-size: 23px;
        font-weight: 800;
    }

    .machine-description {
        color: var(--muted);
        font-size: 14px;
        margin-top: 4px;
    }

    .machine-details {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        margin-top: 22px;
        border-top: 1px solid #f0f2f5;
        padding-top: 18px;
    }

    .machine-detail {
        padding-right: 20px;
    }

    .machine-detail + .machine-detail {
        border-left: 1px solid #f0f2f5;
        padding-left: 20px;
    }

    .detail-label {
        color: var(--muted);
        font-size: 12px;
        margin-bottom: 5px;
    }

    .detail-value {
        color: var(--text);
        font-size: 15px;
        font-weight: 750;
    }

    .machine-status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        border-radius: 20px;
        padding: 7px 13px;
        margin-top: 20px;
        font-size: 14px;
        font-weight: 700;
    }

    .machine-status.online {
        background: var(--green-light);
        color: var(--green);
    }

    .machine-status.offline {
        background: var(--red-light);
        color: var(--red);
    }

    .machine-status.maintenance {
        background: var(--orange-light);
        color: #b54708;
    }

    /* Quick action cards */
    .action-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px;
        min-height: 135px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.035);
        margin-bottom: 7px;
    }

    .action-icon {
        font-size: 24px;
        margin-bottom: 10px;
    }

    .action-title {
        color: var(--text);
        font-size: 15px;
        font-weight: 800;
    }

    .action-note {
        color: var(--muted);
        font-size: 13px;
        margin-top: 5px;
        line-height: 1.45;
    }

    /* Footer */
    .app-footer {
        color: #98a2b3;
        text-align: center;
        margin-top: 35px;
        font-size: 12px;
    }

    @media (max-width: 800px) {
        .machine-details {
            grid-template-columns: 1fr;
        }

        .machine-detail {
            padding: 10px 0;
        }

        .machine-detail + .machine-detail {
            border-left: none;
            border-top: 1px solid #f0f2f5;
            padding-left: 0;
        }

        .page-heading {
            font-size: 25px;
        }
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


def load_table(table_name: str) -> list:
    if not database_connected:
        return []

    try:
        result = supabase.table(table_name).select("*").execute()
        return result.data or []
    except Exception:
        return []


machines = load_table("machines")
faults = load_table("faults")
maintenance_records = load_table("maintenance_history")


# =========================================================
# SESSION STATE
# =========================================================

if "selected_machine_id" not in st.session_state:
    st.session_state.selected_machine_id = (
        machines[0].get("id") if machines else None
    )

if "show_add_machine" not in st.session_state:
    st.session_state.show_add_machine = False


# =========================================================
# CUSTOM SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🔷 ABAYO")
    st.caption("AI Operations Assistant")

    st.markdown("---")

    # This replaces the random “app” wording.
    st.page_link(
        "app.py",
        label="Home",
        icon="🏠",
        use_container_width=True,
    )

    st.markdown("#### MACHINES")

    if st.button("＋  Add Machine", use_container_width=True):
        st.session_state.show_add_machine = True

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

    st.markdown("---")
    st.markdown("#### ABAYO ASSISTANT")
    st.markdown("🤖 **AI Assistant**")
    st.caption("Coming soon")

    st.markdown("---")

    if database_connected:
        st.success("● Cloud system connected")
    else:
        st.error("● Cloud system disconnected")

    st.caption("System Version 0.5")


# =========================================================
# HEADER
# =========================================================

st.html(
    """
    <div class="page-heading">
        Welcome back, Kangume Julius 👋
    </div>
    <div class="page-subtitle">
        Monitor machines, diagnose faults and preserve operational knowledge.
    </div>
    """
)


# =========================================================
# DASHBOARD METRICS
# =========================================================

online_count = sum(
    1
    for machine in machines
    if str(machine.get("status", "")).lower() == "online"
)

total_machines = len(machines)
fault_count = len(faults)
maintenance_count = len(maintenance_records)

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-icon green-icon">📡</div>
            <div class="metric-label">Machines Online</div>
            <div class="metric-value">{online_count}</div>
            <div class="metric-note">
                of {total_machines} registered machines
            </div>
        </div>
        """
    )

with metric_2:
    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-icon red-icon">⚠️</div>
            <div class="metric-label">Fault Records</div>
            <div class="metric-value">{fault_count}</div>
            <div class="metric-note">Saved fault knowledge</div>
        </div>
        """
    )

with metric_3:
    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-icon orange-icon">🗓️</div>
            <div class="metric-label">Maintenance Records</div>
            <div class="metric-value">{maintenance_count}</div>
            <div class="metric-note">Recorded service history</div>
        </div>
        """
    )

with metric_4:
    cloud_status = "Connected" if database_connected else "Offline"

    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-icon blue-icon">☁️</div>
            <div class="metric-label">Cloud Status</div>
            <div class="metric-value connected">{cloud_status}</div>
            <div class="metric-note">Supabase database</div>
        </div>
        """
    )


# =========================================================
# MACHINE WORKSPACE
# =========================================================

st.html('<div class="section-heading">Machine Workspace</div>')

if machines:
    machine_choices = {
        machine.get("machine_name", f"Machine {machine.get('id')}"):
        machine.get("id")
        for machine in machines
    }

    current_machine_name = next(
        (
            name
            for name, machine_id in machine_choices.items()
            if machine_id == st.session_state.selected_machine_id
        ),
        list(machine_choices.keys())[0],
    )

    switch_column, add_column = st.columns([4, 1])

    with switch_column:
        chosen_name = st.selectbox(
            "Select Machine",
            options=list(machine_choices.keys()),
            index=list(machine_choices.keys()).index(
                current_machine_name
            ),
            label_visibility="collapsed",
        )

        chosen_id = machine_choices[chosen_name]

        if chosen_id != st.session_state.selected_machine_id:
            st.session_state.selected_machine_id = chosen_id
            st.rerun()

    with add_column:
        if st.button(
            "＋ Add Machine",
            key="workspace_add_machine",
            use_container_width=True,
        ):
            st.session_state.show_add_machine = True
            st.rerun()

    selected_machine = next(
        (
            machine
            for machine in machines
            if machine.get("id")
            == st.session_state.selected_machine_id
        ),
        machines[0],
    )

    machine_name = escape(
        str(selected_machine.get("machine_name") or "Unnamed Machine")
    )

    description = escape(
        str(
            selected_machine.get("description")
            or "Industrial production machine"
        )
    )

    manufacturer = escape(
        str(
            selected_machine.get("manufacturer")
            or "Not recorded"
        )
    )

    model = escape(
        str(selected_machine.get("model") or "Not recorded")
    )

    location = escape(
        str(selected_machine.get("location") or "Not recorded")
    )

    status = escape(
        str(selected_machine.get("status") or "Unknown")
    )

    status_lower = status.lower()

    if status_lower == "online":
        status_class = "online"
    elif status_lower == "maintenance":
        status_class = "maintenance"
    else:
        status_class = "offline"

    # st.html prevents the HTML tags from appearing as random words.
    st.html(
        f"""
        <div class="machine-card">
            <div class="machine-header">
                <div class="machine-icon">🏭</div>

                <div>
                    <div class="machine-name">{machine_name}</div>
                    <div class="machine-description">
                        {description}
                    </div>
                </div>
            </div>

            <div class="machine-details">
                <div class="machine-detail">
                    <div class="detail-label">Manufacturer</div>
                    <div class="detail-value">{manufacturer}</div>
                </div>

                <div class="machine-detail">
                    <div class="detail-label">Model</div>
                    <div class="detail-value">{model}</div>
                </div>

                <div class="machine-detail">
                    <div class="detail-label">Location</div>
                    <div class="detail-value">{location}</div>
                </div>
            </div>

            <div class="machine-status {status_class}">
                ● {status}
            </div>
        </div>
        """
    )

else:
    st.info("No machine registered. Select Add Machine to begin.")


# =========================================================
# ADD MACHINE FORM
# =========================================================

if st.session_state.show_add_machine:
    st.html('<div class="section-heading">Add New Machine</div>')

    with st.form("add_machine_form"):
        left, right = st.columns(2)

        with left:
            new_machine_name = st.text_input("Machine Name *")
            new_manufacturer = st.text_input("Manufacturer")
            new_model = st.text_input("Model")

        with right:
            new_location = st.text_input("Location")
            new_status = st.selectbox(
                "Status",
                ["Online", "Offline", "Maintenance"],
            )
            new_description = st.text_area("Description")

        save_machine = st.form_submit_button(
            "Save Machine",
            use_container_width=True,
        )

        if save_machine:
            if not new_machine_name.strip():
                st.error("Machine name is required.")

            elif not database_connected:
                st.error("Cloud database is disconnected.")

            else:
                try:
                    response = (
                        supabase.table("machines")
                        .insert(
                            {
                                "machine_name": new_machine_name.strip(),
                                "manufacturer": new_manufacturer.strip(),
                                "model": new_model.strip(),
                                "location": new_location.strip(),
                                "description": new_description.strip(),
                                "status": new_status,
                            }
                        )
                        .execute()
                    )

                    new_machine = response.data[0]

                    default_modules = [
                        "Machine Overview",
                        "Fault Diagnosis",
                        "Recipe Library",
                        "Maintenance History",
                        "Smart Troubleshooter",
                        "Machine Components",
                    ]

                    module_rows = [
                        {
                            "machine_id": new_machine["id"],
                            "module_name": module_name,
                            "enabled": True,
                        }
                        for module_name in default_modules
                    ]

                    try:
                        (
                            supabase.table("machine_modules")
                            .insert(module_rows)
                            .execute()
                        )
                    except Exception:
                        pass

                    st.session_state.selected_machine_id = (
                        new_machine["id"]
                    )
                    st.session_state.show_add_machine = False

                    st.success("Machine added successfully.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Unable to save machine: {error}")


# =========================================================
# QUICK ACTIONS
# =========================================================

st.html('<div class="section-heading">Quick Actions</div>')

action_1, action_2, action_3, action_4 = st.columns(4)

with action_1:
    st.html(
        """
        <div class="action-card">
            <div class="action-icon">🔧</div>
            <div class="action-title">Diagnose a Fault</div>
            <div class="action-note">
                Find possible causes and recommended checks.
            </div>
        </div>
        """
    )

    st.page_link(
        "pages/1_fault_diagnosis.py",
        label="Open Fault Diagnosis",
        use_container_width=True,
    )

with action_2:
    st.html(
        """
        <div class="action-card">
            <div class="action-icon">📖</div>
            <div class="action-title">Browse Recipes</div>
            <div class="action-note">
                Search and review machine recipe parameters.
            </div>
        </div>
        """
    )

    st.page_link(
        "pages/2_recipe_library.py",
        label="Open Recipe Library",
        use_container_width=True,
    )

with action_3:
    st.html(
        """
        <div class="action-card">
            <div class="action-icon">📋</div>
            <div class="action-title">Maintenance History</div>
            <div class="action-note">
                View servicing and maintenance records.
            </div>
        </div>
        """
    )

    st.page_link(
        "pages/3_maintenance_history.py",
        label="Open Maintenance",
        use_container_width=True,
    )

with action_4:
    st.html(
        """
        <div class="action-card">
            <div class="action-icon">⚙️</div>
            <div class="action-title">Machine Components</div>
            <div class="action-note">
                Explore machine parts and components.
            </div>
        </div>
        """
    )

    st.page_link(
        "pages/5_machine_components.py",
        label="Open Components",
        use_container_width=True,
    )


# =========================================================
# RECENT ACTIVITY
# =========================================================

st.html('<div class="section-heading">Recent Activity</div>')

activities = []

if database_connected:
    try:
        activities = (
            supabase.table("machine_activity")
            .select("*, machines(machine_name)")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
            .data
            or []
        )
    except Exception:
        activities = []

if activities:
    activity_rows = []

    for activity in activities:
        machine_details = activity.get("machines") or {}

        activity_rows.append(
            {
                "Machine": machine_details.get(
                    "machine_name",
                    "Unknown Machine",
                ),
                "Activity": activity.get("description", ""),
                "Type": activity.get("activity_type", ""),
                "Status": activity.get("status", ""),
                "Time": activity.get("created_at", ""),
            }
        )

    st.dataframe(
        activity_rows,
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("Recent operational activities will appear here.")


# =========================================================
# FOOTER
# =========================================================

st.html(
    """
    <div class="app-footer">
        ABAYO AI Operations Assistant • System Version 0.5
    </div>
    """
)
