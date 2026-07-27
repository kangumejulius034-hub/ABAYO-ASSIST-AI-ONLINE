import streamlit as st
from supabase_engine import get_supabase_client


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="ABAYO AI Operations Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DESIGN
# =========================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1729 0%, #111f38 100%);
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    [data-testid="stSidebar"] .stButton button {
        background-color: #175cd3;
        color: white;
        border: none;
        border-radius: 9px;
    }

    .abayo-title {
        font-size: 34px;
        font-weight: 800;
        color: #101828;
        margin-bottom: 3px;
    }

    .abayo-subtitle {
        font-size: 15px;
        color: #667085;
        margin-bottom: 22px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 800;
        color: #101828;
        margin-top: 25px;
        margin-bottom: 12px;
    }

    .metric-card {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 15px;
        padding: 20px;
        min-height: 145px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .metric-icon {
        font-size: 25px;
        margin-bottom: 8px;
    }

    .metric-label {
        color: #667085;
        font-size: 14px;
        font-weight: 600;
    }

    .metric-value {
        color: #101828;
        font-size: 29px;
        font-weight: 800;
        margin-top: 5px;
    }

    .metric-note {
        color: #98a2b3;
        font-size: 13px;
        margin-top: 3px;
    }

    .machine-card {
        background: white;
        border: 1px solid #84adff;
        border-radius: 15px;
        padding: 22px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .machine-title {
        color: #175cd3;
        font-size: 23px;
        font-weight: 800;
    }

    .machine-description {
        color: #667085;
        margin-top: 5px;
        margin-bottom: 18px;
    }

    .machine-details {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
    }

    .detail-label {
        color: #98a2b3;
        font-size: 12px;
        margin-bottom: 2px;
    }

    .detail-value {
        color: #344054;
        font-size: 15px;
        font-weight: 700;
    }

    .status-online {
        display: inline-block;
        margin-top: 18px;
        padding: 6px 12px;
        border-radius: 20px;
        background: #ecfdf3;
        color: #027a48;
        font-weight: 700;
    }

    .status-offline {
        display: inline-block;
        margin-top: 18px;
        padding: 6px 12px;
        border-radius: 20px;
        background: #fef3f2;
        color: #b42318;
        font-weight: 700;
    }

    .status-maintenance {
        display: inline-block;
        margin-top: 18px;
        padding: 6px 12px;
        border-radius: 20px;
        background: #fffaeb;
        color: #b54708;
        font-weight: 700;
    }

    .system-footer {
        text-align: center;
        color: #98a2b3;
        margin-top: 35px;
        font-size: 13px;
    }

    @media (max-width: 800px) {
        .machine-details {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SUPABASE CONNECTION
# =========================================================

try:
    supabase = get_supabase_client()
    database_connected = True
except Exception:
    supabase = None
    database_connected = False


def load_table(table_name, columns="*"):
    """Safely load records from Supabase."""

    if not database_connected:
        return []

    try:
        response = (
            supabase.table(table_name)
            .select(columns)
            .execute()
        )
        return response.data or []

    except Exception:
        return []


machines = load_table("machines")
faults = load_table("faults")
maintenance_records = load_table("maintenance_history")


# =========================================================
# SESSION STATE
# =========================================================

if "selected_machine_id" not in st.session_state:
    if machines:
        st.session_state.selected_machine_id = machines[0].get("id")
    else:
        st.session_state.selected_machine_id = None


if "show_add_machine" not in st.session_state:
    st.session_state.show_add_machine = False


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
    )

    st.markdown("### Machines")

    if st.button(
        "＋ Add Machine",
        use_container_width=True,
    ):
        st.session_state.show_add_machine = True

    st.page_link(
        "pages/1_fault_diagnosis.py",
        label="Fault Diagnosis",
        icon="🛠️",
    )

    st.page_link(
        "pages/2_recipe_library.py",
        label="Recipe Library",
        icon="📖",
    )

    st.page_link(
        "pages/3_maintenance_history.py",
        label="Maintenance",
        icon="🔧",
    )

    # The real filename currently uses "toubleshooter"
    st.page_link(
        "pages/4_smart_toubleshooter.py",
        label="Knowledge Base",
        icon="🧠",
    )

    st.page_link(
        "pages/5_machine_components.py",
        label="Machine Components",
        icon="⚙️",
    )

    st.markdown("---")

    st.markdown("### 🤖 ABAYO Assistant")
    st.caption(
        "Machine knowledge, guided fault diagnosis and operational support."
    )

    st.button(
        "AI Assistant — Coming Soon",
        disabled=True,
        use_container_width=True,
    )

    st.markdown("---")

    if database_connected:
        st.success("Cloud system connected")
    else:
        st.error("Cloud system disconnected")

    st.caption("System Version 0.5")


# =========================================================
# PAGE HEADER
# =========================================================

st.markdown(
    '<div class="abayo-title">Welcome back, Kangume Julius 👋</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="abayo-subtitle">
        Monitor machines, diagnose faults and preserve operational knowledge.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# METRIC CARDS
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

    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-icon">📶</div>
    <div class="metric-label">Machines Online</div>
    <div class="metric-value">{online_count}</div>
    <div class="metric-note">of {total_machines} registered machines</div>
</div>
        """,
        unsafe_allow_html=True,
    )


with metric_2:

    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-icon">⚠️</div>
    <div class="metric-label">Fault Records</div>
    <div class="metric-value">{fault_count}</div>
    <div class="metric-note">Saved fault knowledge</div>
</div>
        """,
        unsafe_allow_html=True,
    )


with metric_3:

    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-icon">🗓️</div>
    <div class="metric-label">Maintenance Records</div>
    <div class="metric-value">{maintenance_count}</div>
    <div class="metric-note">Recorded service history</div>
</div>
        """,
        unsafe_allow_html=True,
    )


with metric_4:

    connection_status = (
        "Connected"
        if database_connected
        else "Offline"
    )

    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-icon">☁️</div>
    <div class="metric-label">Cloud Status</div>
    <div class="metric-value">{connection_status}</div>
    <div class="metric-note">Supabase database</div>
</div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# MACHINE WORKSPACE
# =========================================================

st.markdown(
    '<div class="section-title">Machine Workspace</div>',
    unsafe_allow_html=True,
)


if machines:

    machine_options = {
        machine.get(
            "machine_name",
            f"Machine {machine.get('id')}",
        ): machine.get("id")
        for machine in machines
    }

    selected_machine_name = next(
        (
            name
            for name, machine_id in machine_options.items()
            if machine_id == st.session_state.selected_machine_id
        ),
        list(machine_options.keys())[0],
    )

    switch_column, add_column = st.columns([4, 1])

    with switch_column:

        selected_name = st.selectbox(
            "Select Machine",
            options=list(machine_options.keys()),
            index=list(machine_options.keys()).index(
                selected_machine_name
            ),
        )

        selected_id = machine_options[selected_name]

        if selected_id != st.session_state.selected_machine_id:
            st.session_state.selected_machine_id = selected_id
            st.rerun()


    with add_column:

        st.write("")
        st.write("")

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

    machine_name = selected_machine.get(
        "machine_name",
        "Unnamed Machine",
    )

    description = (
        selected_machine.get("description")
        or "Industrial production machine"
    )

    manufacturer = (
        selected_machine.get("manufacturer")
        or "Not recorded"
    )

    model = (
        selected_machine.get("model")
        or "Not recorded"
    )

    location = (
        selected_machine.get("location")
        or "Not recorded"
    )

    status = (
        selected_machine.get("status")
        or "Unknown"
    )

    status_lower = str(status).lower()

    if status_lower == "online":
        status_class = "status-online"

    elif status_lower == "maintenance":
        status_class = "status-maintenance"

    else:
        status_class = "status-offline"


    machine_html = f"""
<div class="machine-card">
    <div class="machine-title">🏭 {machine_name}</div>

    <div class="machine-description">
        {description}
    </div>

    <div class="machine-details">
        <div>
            <div class="detail-label">Manufacturer</div>
            <div class="detail-value">{manufacturer}</div>
        </div>

        <div>
            <div class="detail-label">Model</div>
            <div class="detail-value">{model}</div>
        </div>

        <div>
            <div class="detail-label">Location</div>
            <div class="detail-value">{location}</div>
        </div>
    </div>

    <div class="{status_class}">
        ● {status}
    </div>
</div>
"""

    st.markdown(
        machine_html,
        unsafe_allow_html=True,
    )


else:

    st.info(
        "No machine has been registered. "
        "Use Add Machine to create the first machine."
    )


# =========================================================
# ADD MACHINE FORM
# =========================================================

if st.session_state.show_add_machine:

    st.markdown(
        '<div class="section-title">Add New Machine</div>',
        unsafe_allow_html=True,
    )

    with st.form("add_machine_form"):

        left_column, right_column = st.columns(2)

        with left_column:

            new_machine_name = st.text_input(
                "Machine Name *"
            )

            new_manufacturer = st.text_input(
                "Manufacturer"
            )

            new_model = st.text_input(
                "Model"
            )


        with right_column:

            new_location = st.text_input(
                "Location"
            )

            new_status = st.selectbox(
                "Status",
                [
                    "Online",
                    "Offline",
                    "Maintenance",
                ],
            )

            new_description = st.text_area(
                "Description"
            )


        save_machine = st.form_submit_button(
            "Save Machine",
            use_container_width=True,
        )


        if save_machine:

            if not new_machine_name.strip():

                st.error(
                    "Machine name is required."
                )

            elif not database_connected:

                st.error(
                    "Supabase database is not connected."
                )

            else:

                try:

                    machine_result = (
                        supabase.table("machines")
                        .insert(
                            {
                                "machine_name":
                                    new_machine_name.strip(),

                                "manufacturer":
                                    new_manufacturer.strip(),

                                "model":
                                    new_model.strip(),

                                "location":
                                    new_location.strip(),

                                "description":
                                    new_description.strip(),

                                "status":
                                    new_status,
                            }
                        )
                        .execute()
                    )

                    new_machine = machine_result.data[0]

                    default_modules = [
                        "Machine Overview",
                        "Fault Diagnosis",
                        "Recipe Library",
                        "Maintenance History",
                        "Smart Troubleshooter",
                        "Machine Components",
                        "Documents",
                        "Reports and Analytics",
                    ]

                    module_rows = [
                        {
                            "machine_id":
                                new_machine["id"],

                            "module_name":
                                module_name,

                            "enabled":
                                True,
                        }
                        for module_name in default_modules
                    ]

                    try:

                        supabase.table(
                            "machine_modules"
                        ).insert(
                            module_rows
                        ).execute()

                    except Exception:
                        pass

                    st.session_state.selected_machine_id = (
                        new_machine["id"]
                    )

                    st.session_state.show_add_machine = False

                    st.success(
                        "Machine added successfully."
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Machine could not be saved: {error}"
                    )


# =========================================================
# QUICK ACTIONS
# =========================================================

st.markdown(
    '<div class="section-title">Quick Actions</div>',
    unsafe_allow_html=True,
)

action_1, action_2, action_3, action_4 = st.columns(4)


with action_1:

    st.page_link(
        "pages/1_fault_diagnosis.py",
        label="🛠️ Diagnose a Fault",
        use_container_width=True,
    )


with action_2:

    st.page_link(
        "pages/2_recipe_library.py",
        label="📖 Browse Recipes",
        use_container_width=True,
    )


with action_3:

    st.page_link(
        "pages/3_maintenance_history.py",
        label="🔧 Maintenance History",
        use_container_width=True,
    )


with action_4:

    st.page_link(
        "pages/5_machine_components.py",
        label="⚙️ Machine Components",
        use_container_width=True,
    )


# =========================================================
# RECENT ACTIVITY
# =========================================================

st.markdown(
    '<div class="section-title">Recent Activity</div>',
    unsafe_allow_html=True,
)

activities = []

if database_connected:

    try:

        activities = (
            supabase.table("machine_activity")
            .select(
                "*, machines(machine_name)"
            )
            .order(
                "created_at",
                desc=True,
            )
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

        machine_information = (
            activity.get("machines")
            or {}
        )

        activity_rows.append(
            {
                "Machine":
                    machine_information.get(
                        "machine_name",
                        "Unknown Machine",
                    ),

                "Activity":
                    activity.get(
                        "description",
                        "",
                    ),

                "Type":
                    activity.get(
                        "activity_type",
                        "",
                    ),

                "Status":
                    activity.get(
                        "status",
                        "",
                    ),

                "Time":
                    activity.get(
                        "created_at",
                        "",
                    ),
            }
        )

    st.dataframe(
        activity_rows,
        use_container_width=True,
        hide_index=True,
    )


else:

    st.info(
        "Recent operational activities will appear here."
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="system-footer">
        ABAYO AI Operations Assistant • System Version 0.5
    </div>
    """,
    unsafe_allow_html=True,
)
