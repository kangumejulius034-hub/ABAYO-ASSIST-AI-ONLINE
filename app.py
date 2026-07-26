import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="ABAYO ASSIST AI",
    page_icon="🛠️",
    layout="wide",
)


BASE_DIR = Path(__file__).parent
FAULTS_FILE = BASE_DIR / "knowledge" / "faults.json"
RECIPES_FILE = BASE_DIR / "knowledge" / "recipes.json"


def count_records(file_path: Path) -> int:
    """Count records stored in a JSON list safely."""

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return len(data)

        return 0

    except (FileNotFoundError, json.JSONDecodeError):
        return 0


fault_count = count_records(FAULTS_FILE)
recipe_count = count_records(RECIPES_FILE)


st.title("🛠️ ABAYO ASSIST AI")
st.subheader("Industrial Maintenance and Production Assistant")

st.caption("Version 0.4 Alpha — Developed by Kangume Julius")

st.warning(
    "Safety: Stop the machine and isolate electrical, pneumatic and "
    "mechanical energy before carrying out physical inspection."
)

st.divider()

st.write("## ABAYO Dashboard")

st.write(
    "Use the navigation menu on the left to open Fault Diagnosis "
    "or the Recipe Parameter Library."
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("System Version", "0.4")
col2.metric("Fault Records", fault_count)
col3.metric("Recipe Records", recipe_count)
col4.metric("Online AI", "Not connected")

st.divider()

st.write("## Available Modules")

module1, module2 = st.columns(2)

with module1:
    st.write("### 🔧 Fault Diagnosis")
    st.write(
        "Describe a machine problem and ABAYO will search the local "
        "knowledge base for matching faults, possible causes and checks."
    )

with module2:
    st.write("### 📖 Recipe Library")
    st.write(
        "Select a Pakona recipe to retrieve its approved default "
        "parameters, notes and gold-standard status."
    )

st.divider()

st.write("## Current Machine")

st.info(
    "Pakona PFS AG — Premade pouch filling and sealing machine."
)

st.write("## Development Roadmap")

st.write(
    """
    **Version 0.4**
    - Dashboard
    - Fault diagnosis
    - Recipe parameter library
    - Saving and updating recipes

    **Future versions**
    - Recipe comparison
    - Multiple Pakona models
    - Maintenance history
    - PLC read-only monitoring
    - Android application
    - AI image analysis
    """
)