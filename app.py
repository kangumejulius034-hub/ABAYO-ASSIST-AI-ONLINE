import streamlit as st
from supabase_engine import get_supabase_client

st.set_page_config(
    page_title="ABAYO AI Operations Assistant",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------
# DESIGN
# -------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a, #111c33);
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #667085;
        margin-bottom: 24px;
    }

    .metric-card {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 15px;
        padding: 20px;
        min-height: 135px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
    }

    .metric-icon {
        font-size: 25px;
    }

    .metric-label {
        color: #667085;
        font-size: 14px;
        font-weight: 600;
        margin-top: 8px;
    }

    .metric-number {
        color: #101828;
        font-size: 30px;
        font-weight: 800;
    }

    .metric-note {
        color: #98a2b3;
        font-size: 13px;
    }

    .workspace {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 3px 12px rgba(16, 24, 40, 0.04);
        margin-top: 20px;
    }

    .machine-card {
        background: #f8fbff;
        border: 1px solid #84adff;
        border-radius: 13px;
        padding: 18px;
        margin-top: 12px;
    }

    .machine-name {
        color: #175cd3;
        font-size: 21px;
        font-weight: 800;
    }

    .online {
        color: #039855;
        font-weight: 700;
    }

    .offline {
        color: #d92d20;
        font-weight: 700;
    }

    .section-title {
        font-size: 22px;
        font-weight: 800;
        color: #101828;
        margin-top: 24px;
        margin-bottom: 12px;
    }

    .proposal-box {
        background: #eff8ff;
        border-left: 5px solid #1570ef;
        padding: 17px;
        border-radius: 10px;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# DATABASE
# -------------------------------------------------

try:
    supabase = get_supabase_client()
    database_connected = True
except Exception:
    supabase = None
    database_connected = False


def load_table(table_name, columns="*"):
    if not database_connected:
        return []

    try:
        response = supabase.table(table_name).select(columns).execute()
        return response.data or []
    except Exception:
        return []


machines = load_table("machines")
faults = load_table("faults")
maintenance_records = load_table("maintenance_history")
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

# -------------------------------------------------
# SESSION
# -------------------------------------------------

if "selected_machine_id" not in st.session_state:
    st.session_state.selected_machine_id = (
        machines[0]["id"] if machines else None
    )

if "show_add_machine" not in st.session_state:
    st.session_state.show_add_machine = False

selected_machine = next(
    (
        machine
        for machine in machines
        if machine.get("id") == st.session_state.selected_machine_id
    ),
    machines[0] if machines else None,
)

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:
    st.markdown("## 🔷 ABAYO")
    st.caption("AI Operations Assistant")

    st.markdown("---")

    st.page_link("app.py", label="Dashboard", icon="🏠")

    st.markdown("### 🏭 Machines")

    if st.button("＋ Add Machine", use_container_width=True):
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

    # The existing filename is intentionally spelled "toubleshooter"
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

    st.markdown("### 🤖 ABAYO AI Assistant")
    st.caption(
        "Diagnose faults, retrieve recipes and access machine knowledge."
    )

    st.button(
        "Open Assistant — Coming Soon",
        use_container_width=True,
        disabled=True,
    )

    st.markdown("---")

    if database_connected:
        st.success("All systems operational")
    else:
        st.error("Cloud database disconnected")

    st.caption("Proposal Pilot • Version 0.5")

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown(
    '<div class="main-title">Welcome back, Kangume Julius 👋</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Monitor machines, diagnose faults and preserve maintenance knowledge.
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# METRICS
# -------------------------------------------------

online_count = sum(
    1
    for machine in machines
    if str(machine.get("status", "")).lower() == "online"
)

total_machines = len(machines)
active_faults = len(faults)
maintenance_count = len(maintenance_records)

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">📶</div>
            <div class="metric-label">Machines Online</div>
            <div class="metric-number">{online_count}</div>
            <div class="metric-note">of {total_machines} registered machines</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">⚠️</div>
            <div class="metric-label">Fault Records</div>
            <div class="metric-number">{active_faults}</div>
            <div class="metric-note">Stored in the cloud</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">🗓️</div>
            <div class="metric-label">Maintenance Records</div>
            <div class="metric-number">{maintenance_count}</div>
            <div class="metric-note">Machine service history</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with m4:
    connection_text = "Connected" if database_connected else "Offline"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">☁️</div>
            <div class="metric-label">Cloud Status</div>
            <div class="metric-number">{connection_text}</div>
            <div class="metric-note">Supabase backend</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------
# MACHINE WORKSPACE
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Machine Workspace</div>',
    unsafe_allow_html=True,
)

if machines:
    machine_options = {
        machine.get("machine_name", f"Machine {machine.get('id')}"):
        machine.get("id")
        for machine in machines
    }

    current_name = next(
        (
            name
            for name, machine_id in machine_options.items()
            if machine_id == st.session_state.selected_machine_id
        ),
        list(machine_options.keys())[0],
    )

    switch_col, add_col = st.columns([4, 1])

    with switch_col:
        chosen_machine = st.selectbox(
            "Switch Machine",
            options=list(machine_options.keys()),
            index=list(machine_options.keys()).index(current_name),
        )

        chosen_id = machine_options[chosen_machine]

        if chosen_id != st.session_state.selected_machine_id:
            st.session_state.selected_machine_id = chosen_id
            st.rerun()

    with add_col:
        st.write("")
        st.write("")

        if st.button("＋ Add Machine", use_container_width=True):
            st.session_state.show_add_machine = True
            st.rerun()

    selected_machine = next(
        (
            machine
            for machine in machines
            if machine.get("id") == st.session_state.selected_machine_id
        ),
        machines[0],
    )

    status = selected_machine.get("status", "Unknown")
    status_class = (
        "online"
        if str(status).lower() == "online"
        else "offline"
    )

   machine_name = selected_machine.get("machine_name", "Unnamed Machine")
description = (
    selected_machine.get("description")
    or "Industrial production machine"
)
manufacturer = (
    selected_machine.get("manufacturer")
    or "Not recorded"
)
model = selected_machine.get("model") or "Not recorded"
location = selected_machine.get("location") or "Not recorded"
status = selected_machine.get("status", "Unknown")

status_color = "#039855" if status.lower() == "online" else "#d92d20"

machine_html = f"""
<div class="machine-card">
    <div class="machine-name">🏭 {machine_name}</div>
    <div style="color:#667085; margin-top:6px;">
        {description}
    </div>

    <div style="
        display:grid;
        grid-template-columns:repeat(3, 1fr);
        gap:16px;
        margin-top:18px;
    ">
        <div>
            <div style="color:#98a2b3; font-size:13px;">Manufacturer</div>
            <div style="font-weight:700;">{manufacturer}</div>
        </div>

        <div>
            <div style="color:#98a2b3; font-size:13px;">Model</div>
            <div style="font-weight:700;">{model}</div>
        </div>

        <div>
            <div style="color:#98a2b3; font-size:13px;">Location</div>
            <div style="font-weight:700;">{location}</div>
        </div>
    </div>

    <div style="
        margin-top:18px;
        display:inline-block;
        padding:6px 12px;
        border-radius:20px;
        background:#ecfdf3;
        color:{status_color};
        font-weight:700;
    ">
        ● {status}
    </div>
</div>
"""

st.markdown(machine_html, unsafe_allow_html=True)

else:
    st.warning("No machines have been added.")

# -------------------------------------------------
# ADD MACHINE
# -------------------------------------------------

if st.session_state.show_add_machine:
    st.markdown(
        '<div class="section-title">Add New Machine</div>',
        unsafe_allow_html=True,
    )

    with st.form("add_machine_form"):
        c1, c2 = st.columns(2)

        with c1:
            machine_name = st.text_input("Machine Name *")
            manufacturer = st.text_input("Manufacturer")
            model = st.text_input("Model")

        with c2:
            location = st.text_input("Location")
            status = st.selectbox(
                "Status",
                ["Online", "Offline", "Maintenance"],
            )
            description = st.text_area("Description")

        save_machine = st.form_submit_button(
            "Save Machine",
            use_container_width=True,
        )

        if save_machine:
            if not machine_name.strip():
                st.error("Machine name is required.")

            elif not database_connected:
                st.error("Supabase is not connected.")

            else:
                try:
                    result = (
                        supabase.table("machines")
                        .insert(
                            {
                                "machine_name": machine_name.strip(),
                                "manufacturer": manufacturer.strip(),
                                "model": model.strip(),
                                "location": location.strip(),
                                "description": description.strip(),
                                "status": status,
                            }
                        )
                        .execute()
                    )

                    new_machine = result.data[0]

                    default_modules = [
                        "Machine Overview",
                        "Fault Diagnosis",
                        "Recipe Library",
                        "Maintenance History",
                        "Smart Troubleshooter",
                        "Machine Components",
                        "Documents",
                        "Reports & Analytics",
                    ]

                    module_rows = [
                        {
                            "machine_id": new_machine["id"],
                            "module_name": module,
                            "enabled": True,
                        }
                        for module in default_modules
                    ]

                    supabase.table("machine_modules").insert(
                        module_rows
                    ).execute()

                    st.session_state.selected_machine_id = new_machine["id"]
                    st.session_state.show_add_machine = False

                    st.success("Machine added successfully.")
                    st.rerun()

                except Exception as error:
                    st.error(f"Machine could not be saved: {error}")

# -------------------------------------------------
# QUICK ACTIONS
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Quick Actions</div>',
    unsafe_allow_html=True,
)

q1, q2, q3, q4 = st.columns(4)

with q1:
    st.page_link(
        "pages/1_fault_diagnosis.py",
        label="🛠️ Diagnose a Fault",
        use_container_width=True,
    )

with q2:
    st.page_link(
        "pages/2_recipe_library.py",
        label="📖 Browse Recipes",
        use_container_width=True,
    )

with q3:
    st.page_link(
        "pages/3_maintenance_history.py",
        label="🔧 Maintenance History",
        use_container_width=True,
    )

with q4:
    st.page_link(
        "pages/5_machine_components.py",
        label="⚙️ Machine Components",
        use_container_width=True,
    )

# -------------------------------------------------
# PROPOSAL ROADMAP
# -------------------------------------------------

left, right = st.columns(2)

with left:
    st.markdown(
        '<div class="section-title">Pilot Capabilities</div>',
        unsafe_allow_html=True,
    )

    st.success("✅ Multi-machine architecture")
    st.success("✅ Cloud database connection")
    st.success("✅ Fault diagnosis")
    st.success("✅ Recipe library")
    st.success("✅ Maintenance history")
    st.success("✅ Troubleshooting knowledge")
    st.success("✅ Machine component register")

with right:
    st.markdown(
        '<div class="section-title">Development Roadmap</div>',
        unsafe_allow_html=True,
    )

    st.info("🔄 Version 0.5 — Cloud module integration")
    st.info("📅 Version 0.6 — Maintenance planning")
    st.info("📊 Version 0.7 — Analytics, MTTR, MTBF and OEE")
    st.info("🤖 Version 0.8 — AI assistant")
    st.info("📷 Version 0.9 — AI vision diagnosis")
    st.info("📱 Version 1.0 — Installable mobile application")

# -------------------------------------------------
# RECENT ACTIVITY
# -------------------------------------------------

st.markdown(
    '<div class="section-title">Recent Activity</div>',
    unsafe_allow_html=True,
)

if activities:
    activity_rows = []

    for activity in activities:
        machine_data = activity.get("machines") or {}

        activity_rows.append(
            {
                "Machine": machine_data.get(
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
    st.info(
        "Recent actions will appear here as faults, recipes and "
        "maintenance records are added."
    )

# -------------------------------------------------
# PROPOSAL MESSAGE
# -------------------------------------------------

st.markdown(
    """
    <div class="proposal-box">
        <strong>ABAYO Pilot Proposal</strong><br>
        Begin with the Pakona PFS AG as the pilot machine.
        Validate fault diagnosis, recipe control and maintenance
        knowledge capture, then progressively connect additional
        factory machines.
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "ABAYO AI Operations Assistant • Pilot Proposal Version 0.5"
)
