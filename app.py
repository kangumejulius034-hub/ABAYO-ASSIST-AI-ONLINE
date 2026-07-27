import streamlit as st
from supabase_engine import get_supabase_client

st.set_page_config(
    page_title="ABAYO",
    page_icon="🏭",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #f6f8fc;
    }

    [data-testid="stSidebar"] {
        background: #101827;
        color: white;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    .title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 2px;
    }

    .subtitle {
        color: #667085;
        margin-bottom: 25px;
    }

    .card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        min-height: 125px;
    }

    .metric-label {
        color: #667085;
        font-size: 14px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 800;
        margin-top: 8px;
    }

    .machine-box {
        background: white;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #dbe3f0;
        margin-bottom: 12px;
    }

    .status-online {
        color: #16a34a;
        font-weight: 700;
    }

    .section-title {
        font-size: 22px;
        font-weight: 800;
        margin-top: 14px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

supabase = get_supabase_client()

if "selected_machine_id" not in st.session_state:
    st.session_state.selected_machine_id = None

# Sidebar
with st.sidebar:
    st.markdown("## 🔷 ABAYO")
    st.caption("AI Operations Assistant")

    st.markdown("---")
    st.page_link("app.py", label="Dashboard", icon="🏠")
    st.markdown("### Machines")

    if st.button("➕ Add Machine", use_container_width=True):
        st.session_state.show_add_machine = True

    st.page_link("pages/1_fault_diagnosis.py", label="Fault Diagnosis", icon="🛠")
    st.page_link("pages/2_recipe_library.py", label="Recipe Library", icon="📖")
    st.page_link("pages/3_maintenance_history.py", label="Maintenance", icon="🔧")
    st.page_link("pages/4_smart_toubleshooter.py", label="🧠 Knowledge Base",)
    st.page_link("pages/5_machine_components.py", label="Components", icon="⚙️")

# Load machines
machines_response = supabase.table("machines").select("*").order("id").execute()
machines = machines_response.data or []

if machines and st.session_state.selected_machine_id is None:
    st.session_state.selected_machine_id = machines[0]["id"]

selected_machine = next(
    (
        machine
        for machine in machines
        if machine["id"] == st.session_state.selected_machine_id
    ),
    machines[0] if machines else None,
)

st.markdown('<div class="title">Welcome back, Kangume Julius 👋</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Here is what is happening with your operations today.</div>',
    unsafe_allow_html=True,
)

# Dashboard counts
online_count = sum(
    1 for machine in machines
    if str(machine.get("status", "")).lower() == "online"
)

faults = supabase.table("faults").select("id").execute().data or []
maintenance = supabase.table("maintenance_history").select("id").execute().data or []

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="card">
            <div class="metric-label">Machines Online</div>
            <div class="metric-value">{online_count}</div>
            <div>of {len(machines)} machines</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="card">
            <div class="metric-label">Active Faults</div>
            <div class="metric-value">{len(faults)}</div>
            <div>Require attention</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="card">
            <div class="metric-label">Maintenance Records</div>
            <div class="metric-value">{len(maintenance)}</div>
            <div>Cloud records</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """
        <div class="card">
            <div class="metric-label">System Status</div>
            <div class="metric-value">Online</div>
            <div>Supabase connected</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-title">Machine Workspace</div>', unsafe_allow_html=True)

if selected_machine:
    st.markdown(
        f"""
        <div class="machine-box">
            <h3>{selected_machine.get("machine_name", "Machine")}</h3>
            <p>{selected_machine.get("description", "")}</p>
            <span class="status-online">
                {selected_machine.get("status", "Online")}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    machine_names = {
        machine["machine_name"]: machine["id"]
        for machine in machines
    }

    selected_name = st.selectbox(
        "Switch Machine",
        options=list(machine_names.keys()),
        index=list(machine_names.values()).index(
            st.session_state.selected_machine_id
        ),
    )

    st.session_state.selected_machine_id = machine_names[selected_name]

else:
    st.info("No machine added yet.")

# Add machine form
if st.session_state.get("show_add_machine"):
    st.markdown('<div class="section-title">Add Machine</div>', unsafe_allow_html=True)

    with st.form("add_machine_form"):
        machine_name = st.text_input("Machine Name")
        manufacturer = st.text_input("Manufacturer")
        model = st.text_input("Model")
        location = st.text_input("Location")
        description = st.text_area("Description")
        status = st.selectbox(
            "Status",
            ["Online", "Offline", "Maintenance"]
        )

        submitted = st.form_submit_button("Save Machine")

        if submitted:
            if not machine_name.strip():
                st.error("Machine name is required.")
            else:
                response = (
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
                        "module_name": module,
                        "enabled": True,
                    }
                    for module in default_modules
                ]

                supabase.table("machine_modules").insert(module_rows).execute()

                st.session_state.selected_machine_id = new_machine["id"]
                st.session_state.show_add_machine = False
                st.success("Machine added successfully.")
                st.rerun()

st.markdown('<div class="section-title">Quick Actions</div>', unsafe_allow_html=True)

q1, q2, q3 = st.columns(3)

with q1:
    st.page_link(
        "pages/1_fault_diagnosis.py",
        label="🛠 Diagnose a Fault",
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

st.markdown(
    '<div class="section-title">Recent Activity</div>',
    unsafe_allow_html=True,
)

activity_response = (
    supabase.table("machine_activity")
    .select("*, machines(machine_name)")
    .order("created_at", desc=True)
    .limit(10)
    .execute()
)

activities = activity_response.data or []

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
    st.info("No recent activity yet.")
