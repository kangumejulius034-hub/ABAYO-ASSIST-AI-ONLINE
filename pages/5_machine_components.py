import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import component_engine

from component_engine import (
    add_component,
    component_summary,
    load_components,
    search_components,
)


st.set_page_config(
    page_title="Machine Components | ABAYO",
    page_icon="⚙️",
    layout="wide",
)

st.html(
    """
    <style>
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important; display: flex !important;
        opacity: 1 !important; position: fixed !important;
        top: .75rem !important; left: .75rem !important;
        z-index: 999999 !important; background: #071426 !important;
        border-radius: 50% !important;
        box-shadow: 0 4px 12px rgba(0,0,0,.22) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"] svg {
        color: white !important; fill: white !important;
        stroke: white !important; opacity: 1 !important;
    }
    </style>
    """
)


STATIONS = [
    "General machine problem",
    "Pouch elevator",
    "Pouch picking station",
    "Pouch opening station",
    "Filling station",
    "Auger and stirrer",
    "Incline screw",
    "Sealing station",
    "Electrical system",
    "Pneumatic system",
]


CATEGORIES = [
    "Mechanical",
    "Electrical",
    "Pneumatic",
    "Sensor",
    "Motor and drive",
    "Heating",
    "Sealing",
    "Vacuum",
    "PLC and control",
    "Other",
]


# =========================================================
# PAKONA PFS — CONFIRMED COMPONENT REFERENCE
# =========================================================
#
# These records are intentionally kept separate from user-created component
# records.  They are based on the machine photographs, operating video and
# observations documented for ABAYO.  Unknown OEM specifications are left as
# "Not recorded" until a nameplate, manual or electrical/pneumatic drawing
# confirms them.

STATION_DISPLAY_NAMES = {
    "Pouch elevator": "Pouch Elevator / Main Pouch Conveyor",
    "Pouch picking station": "Pouch Picking Station",
}


PAKONA_REFERENCE_COMPONENTS = [
    {
        "component_number": "PFS-FEED-001",
        "component_name": "Green pouch conveyor belt / tracks",
        "station": "Pouch elevator",
        "category": "Mechanical",
        "function": (
            "Carries flat pouches forward in an overlapping (shingled) "
            "stream and presents them toward the pickup point. The conveyor "
            "supplies the pouch; it does not perform the vacuum pickup."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Recorded operating problems include under-feeding, over-feeding "
            "and more than one pouch sliding into the pickup area. Belt "
            "tracking, condition and adjustment should be checked before "
            "assigning a mechanical cause."
        ),
        "fault_symptoms": (
            "Next pouch does not reach the pickup point, pouch travels past "
            "the intended presentation point, or multiple pouches crowd the "
            "pickup area."
        ),
        "inspection_procedure": (
            "With hands clear of moving parts, observe pouch overlap and "
            "tracking during controlled operation. When the machine is safely "
            "stopped and isolated, inspect belt condition, alignment and the "
            "pouch path for contamination or obstruction."
        ),
        "replacement_procedure": "Not yet documented — follow the Pakona OEM procedure.",
        "safety_notes": (
            "Never reach into the moving pouch conveyor. Isolate the machine "
            "before touching, cleaning or mechanically adjusting the belt."
        ),
        "related_faults": [
            "Pouch not presented to pickup",
            "Pouch passes presentation point",
            "Multiple pouches at pickup",
        ],
        "verification_status": "Observed on machine",
        "evidence_note": "Project photographs and operating video; 500 g pouch run used as a visual reference.",
    },
    {
        "component_number": "PFS-FEED-002",
        "component_name": "Stainless-steel pouch guide rails",
        "station": "Pouch elevator",
        "category": "Mechanical",
        "function": (
            "Keeps the flat pouches laterally guided as the conveyor carries "
            "them toward the presentation and pickup area."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Possible issues to verify include loose or incorrect guide "
            "adjustment, pouch-edge rubbing and uneven presentation."
        ),
        "fault_symptoms": (
            "Pouches approach the pickup point off-centre, rub against a rail "
            "or no longer form a consistent overlapping stream."
        ),
        "inspection_procedure": (
            "After safe isolation, check that both guides are secure, clear "
            "of product/debris and positioned consistently for the active "
            "pouch size. Compare both sides before changing an adjustment."
        ),
        "replacement_procedure": "Not yet documented — follow the Pakona OEM procedure.",
        "safety_notes": "Stop and isolate the machine before loosening or repositioning guides.",
        "related_faults": [
            "Pouch misaligned at pickup",
            "Multiple pouches at pickup",
        ],
        "verification_status": "Observed on machine",
        "evidence_note": "Clearly visible in the main pouch conveyor operating video.",
    },
    {
        "component_number": "PFS-FEED-003",
        "component_name": "Pouch presentation sensor",
        "station": "Pouch elevator",
        "category": "Sensor",
        "function": (
            "Detects pouch presence/position at the feed presentation area "
            "for the conveyor control sequence. Exact PLC logic still needs "
            "to be confirmed from the electrical/PLC documentation."
        ),
        "manufacturer": "Omron",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "The sensing position has been observed to require readjustment. "
            "Possible checks include bracket movement, sensor alignment, "
            "contamination and sensing-distance setting."
        ),
        "fault_symptoms": (
            "Conveyor stops before the pouch reaches the correct point, "
            "continues feeding past the point, or the sensing distance appears "
            "different from the previously working position."
        ),
        "inspection_procedure": (
            "First note the working position before changing anything. Check "
            "the sensor indicator, mounting security, target alignment and "
            "sensor face. Confirm the PLC/HMI input where available. Only "
            "change sensing distance after the mechanical position is checked."
        ),
        "replacement_procedure": "Model and wiring details must be confirmed before replacement.",
        "safety_notes": (
            "Use authorised electrical isolation for wiring work. Do not "
            "adjust the sensor while reaching into a moving mechanism."
        ),
        "related_faults": [
            "Pouch not presented to pickup",
            "Pouch passes presentation point",
            "Sensor distance appears to drift",
        ],
        "verification_status": "User-confirmed manufacturer",
        "evidence_note": "Omron brand and the recurring presentation/sensing-distance behaviour were documented during operation.",
    },
    {
        "component_number": "PFS-FEED-004",
        "component_name": "Adjustable pouch guides / stops at pickup point",
        "station": "Pouch elevator",
        "category": "Mechanical",
        "function": (
            "Helps keep the leading pouch presented consistently at the end "
            "of the feed path. Exact Pakona names for the individual guide "
            "pieces are not yet recorded."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Incorrect or loose adjustment can change how the leading pouch "
            "is exposed to the pickup mechanism."
        ),
        "fault_symptoms": "Leading pouch is off-centre, over-exposed or inconsistently presented.",
        "inspection_procedure": (
            "After safe isolation, compare guide/stop positions left-to-right, "
            "check fasteners and look for contact marks. Record the original "
            "position before making an adjustment."
        ),
        "replacement_procedure": "Not yet documented — follow the Pakona OEM procedure.",
        "safety_notes": "Isolate the machine before mechanical adjustment.",
        "related_faults": ["Pouch misaligned at pickup"],
        "verification_status": "Observed — OEM name pending",
        "evidence_note": "Adjustable mechanical guides/stops are visible around the presentation/pick area in the operating footage.",
    },
    {
        "component_number": "PFS-PICK-001",
        "component_name": "Vacuum suction cups",
        "station": "Pouch picking station",
        "category": "Vacuum",
        "function": (
            "Contacts the presented pouch, uses vacuum to hold it and carries "
            "it with the pickup mechanism through the transfer movement."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Cup wear, dirt/product contamination, poor contact, vacuum loss "
            "or misalignment can reduce reliable pickup."
        ),
        "fault_symptoms": (
            "Pouch is missed, lifts only partly, is picked inconsistently or "
            "drops during transfer."
        ),
        "inspection_procedure": (
            "With the machine isolated, inspect each cup for cracks, hardening, "
            "contamination and uneven height. Check vacuum connections. During "
            "controlled testing, confirm that cups contact the pouch squarely."
        ),
        "replacement_procedure": "Cup size/material and fitting must be recorded before replacement.",
        "safety_notes": "Isolate pneumatic/vacuum and mechanical energy before touching the pickup assembly.",
        "related_faults": [
            "Pouch not picked",
            "Weak suction",
            "Pouch dropped during transfer",
        ],
        "verification_status": "Observed on machine",
        "evidence_note": "Blue suction cups are clearly visible in the supplied pouch-picking footage and photographs.",
    },
    {
        "component_number": "PFS-PICK-002",
        "component_name": "Spring-loaded suction cup holders",
        "station": "Pouch picking station",
        "category": "Mechanical",
        "function": (
            "Provides compliant movement behind the suction cups so the cup "
            "can follow the pouch surface and make consistent contact during "
            "the pickup stroke."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Possible issues include sticking, unequal spring travel, loose "
            "mounting or height misalignment."
        ),
        "fault_symptoms": (
            "One cup contacts before another, cup contact is weak or the "
            "pickup face does not sit evenly on the pouch."
        ),
        "inspection_procedure": (
            "After isolation, compare holder height and free movement, check "
            "mounting security and inspect for binding or contamination."
        ),
        "replacement_procedure": "Not yet documented — confirm holder and spring specification first.",
        "safety_notes": "Keep hands clear of the pickup stroke and stored spring/mechanical movement.",
        "related_faults": ["Pouch not picked", "Uneven suction-cup contact"],
        "verification_status": "Observed on machine",
        "evidence_note": "Spring-loaded pickup components are visible in the close operating footage.",
    },
    {
        "component_number": "PFS-PICK-003",
        "component_name": "Pouch-picking arm / vacuum pickup assembly",
        "station": "Pouch picking station",
        "category": "Mechanical",
        "function": (
            "Carries the suction cups through the pouch pick, transfer and "
            "return movement. The exact Pakona assembly name and drive details "
            "have not yet been confirmed."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Timing, alignment, looseness or restricted movement should be "
            "checked when pouch pickup position is inconsistent."
        ),
        "fault_symptoms": (
            "Suction cups arrive off-position, pickup occurs late/early or "
            "transfer movement is not repeatable."
        ),
        "inspection_procedure": (
            "Observe the full cycle from outside the guarded movement area. "
            "After isolation, check mounting, alignment and free mechanical "
            "movement. Record timing observations before changing settings."
        ),
        "replacement_procedure": "Not yet documented — assembly drive and timing must be confirmed first.",
        "safety_notes": "This assembly moves rapidly. Stop and isolate all energy before physical inspection.",
        "related_faults": ["Pouch not picked", "Pickup timing incorrect"],
        "verification_status": "Observed — OEM name pending",
        "evidence_note": "The moving vacuum pickup mechanism is visible throughout the operating footage.",
    },
    {
        "component_number": "PFS-PICK-004",
        "component_name": "Red star-shaped wheel",
        "station": "Pouch picking station",
        "category": "Mechanical",
        "function": (
            "Rotates as part of the pouch presentation/picking sequence. During "
            "the documented machine cycle it rotates while the suction pads "
            "are returning to pick. Its exact OEM functional description is "
            "still to be confirmed before ABAYO states a more specific role."
        ),
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Timing, looseness, wear or obstruction are inspection points if "
            "its motion no longer matches the known working cycle."
        ),
        "fault_symptoms": (
            "Wheel does not rotate during the expected return/pick phase, "
            "rotates irregularly or its movement is no longer synchronised "
            "with the pickup cycle."
        ),
        "inspection_procedure": (
            "First compare its timing with a known good cycle without touching "
            "the mechanism. After isolation, inspect the wheel, shaft and "
            "mounting for looseness, obstruction or visible wear."
        ),
        "replacement_procedure": "Not yet documented — confirm OEM name, dimensions and mounting first.",
        "safety_notes": "Keep hands clear during cycling; isolate before touching the wheel or shaft.",
        "related_faults": ["Pickup sequence timing incorrect"],
        "verification_status": "User-observed timing; OEM function pending",
        "evidence_note": "User identified the red star wheel and confirmed its rotation during the suction-pad return-to-pick movement.",
    },
    {
        "component_number": "PFS-PICK-005",
        "component_name": "Star-wheel drive motor",
        "station": "Pouch picking station",
        "category": "Motor and drive",
        "function": "Provides drive to the red star-shaped wheel assembly.",
        "manufacturer": "Not recorded",
        "model_number": "Not recorded",
        "part_number": "Not recorded",
        "common_failures": (
            "Electrical supply, drive command, coupling/shaft condition and "
            "mechanical obstruction are checks when the star wheel does not "
            "move as expected; no specific motor failure has yet been confirmed."
        ),
        "fault_symptoms": "Star wheel does not rotate or its movement is irregular.",
        "inspection_procedure": (
            "Observe commanded motion and check the relevant HMI/PLC indication "
            "where available. Electrical measurements and mechanical drive "
            "inspection must be performed only by authorised personnel after "
            "the correct isolation procedure."
        ),
        "replacement_procedure": "Motor nameplate, rating, gearbox/ratio and wiring must be recorded before replacement.",
        "safety_notes": "Electrical and mechanical isolation is required before motor or shaft work.",
        "related_faults": ["Star wheel not rotating", "Pickup sequence timing incorrect"],
        "verification_status": "Observed on machine; nameplate pending",
        "evidence_note": "The star wheel and its motor/drive arrangement were documented in the supplied machine photographs.",
    },
]


def station_display_name(station: str) -> str:
    return STATION_DISPLAY_NAMES.get(station, station)


def search_reference_components(
    search_text: str = "",
    station: str = "",
) -> list[dict]:
    """Search only the built-in Pakona reference records."""

    query = search_text.strip().lower()
    matches: list[dict] = []

    for component in PAKONA_REFERENCE_COMPONENTS:
        if station and component.get("station") != station:
            continue

        searchable_values = [
            component.get("component_number", ""),
            component.get("component_name", ""),
            component.get("station", ""),
            component.get("category", ""),
            component.get("function", ""),
            component.get("manufacturer", ""),
            component.get("common_failures", ""),
            component.get("fault_symptoms", ""),
            " ".join(component.get("related_faults", [])),
        ]

        if query and query not in " ".join(
            str(value).lower() for value in searchable_values
        ):
            continue

        matches.append(component)

    return matches


def display_reference_component(component: dict) -> None:
    """Render one confirmed Pakona reference component."""

    station_name = station_display_name(
        str(component.get("station", "Not recorded"))
    )

    metadata_left, metadata_right = st.columns(2)

    with metadata_left:
        st.write(f"**Station:** {station_name}")
        st.write(f"**Category:** {component.get('category', 'Not recorded')}")
        st.write(f"**Manufacturer:** {component.get('manufacturer', 'Not recorded')}")

    with metadata_right:
        st.write(f"**Model:** {component.get('model_number', 'Not recorded')}")
        st.write(f"**Part number:** {component.get('part_number', 'Not recorded')}")
        st.write(f"**Verification:** {component.get('verification_status', 'Pending')}")

    st.write("#### Function")
    st.write(component.get("function", "Not recorded"))

    st.write("#### Recorded / possible failure behaviour")
    st.write(component.get("common_failures", "Not recorded"))

    st.write("#### Fault symptoms")
    st.write(component.get("fault_symptoms", "Not recorded"))

    st.write("#### Safe inspection guidance")
    st.write(component.get("inspection_procedure", "Not recorded"))

    related_faults = component.get("related_faults", [])
    if related_faults:
        st.write("**Related faults:** " + " • ".join(related_faults))

    evidence_note = component.get("evidence_note")
    if evidence_note:
        st.caption(f"ABAYO evidence note: {evidence_note}")

    safety_notes = component.get("safety_notes")
    if safety_notes:
        st.warning(f"Safety: {safety_notes}")


IMAGE_ROOT = (
    PROJECT_ROOT
    / "knowledge"
    / "component_images"
)

RECYCLED_COMPONENTS_FILE = (
    PROJECT_ROOT
    / "knowledge"
    / "recycle_bin_components.json"
)


def save_active_components(components: list[dict]) -> None:
    """Save components through the engine or its existing JSON file."""

    for function_name in (
        "save_components",
        "save_all_components",
    ):
        save_function = getattr(
            component_engine,
            function_name,
            None,
        )

        if callable(save_function):
            save_function(components)
            return

    component_file_candidates = (
        PROJECT_ROOT / "knowledge" / "components.json",
        PROJECT_ROOT / "knowledge" / "machine_components.json",
    )

    component_file = next(
        (
            file_path
            for file_path in component_file_candidates
            if file_path.exists()
        ),
        component_file_candidates[0],
    )

    component_file.parent.mkdir(parents=True, exist_ok=True)

    with component_file.open("w", encoding="utf-8") as file:
        json.dump(
            components,
            file,
            indent=4,
            ensure_ascii=False,
        )


def move_component_to_recycle_bin(
    component_number: str,
) -> None:
    """Move one component from the active library to recoverable storage."""

    components = load_components()
    removed_component = None

    for component_index, component in enumerate(components):
        if str(component.get("component_number", "")) == str(
            component_number
        ):
            removed_component = components.pop(component_index)
            break

    if removed_component is None:
        raise ValueError(
            "The selected machine component could not be found."
        )

    removed_component["_deleted_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    removed_component["_deleted_from"] = "components"

    try:
        with RECYCLED_COMPONENTS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            recycled_components = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        recycled_components = []

    if not isinstance(recycled_components, list):
        recycled_components = []

    recycled_components.append(removed_component)
    save_active_components(components)
    RECYCLED_COMPONENTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RECYCLED_COMPONENTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            recycled_components,
            file,
            indent=4,
            ensure_ascii=False,
        )


def safe_folder_name(text: str) -> str:
    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text.strip(),
    )

    return cleaned.strip("_") or "unnamed"


def save_component_images(
    uploaded_images,
    folder_name: str,
) -> list[str]:
    saved_paths: list[str] = []

    if not uploaded_images:
        return saved_paths

    destination_folder = (
        IMAGE_ROOT
        / safe_folder_name(folder_name)
    )

    destination_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    for number, uploaded_image in enumerate(
        uploaded_images,
        start=1,
    ):
        suffix = Path(
            uploaded_image.name
        ).suffix.lower()

        if suffix not in {
            ".jpg",
            ".jpeg",
            ".png",
        }:
            suffix = ".jpg"

        destination_path = (
            destination_folder
            / f"component_{number}{suffix}"
        )

        duplicate_number = 1

        while destination_path.exists():
            destination_path = (
                destination_folder
                / (
                    f"component_{number}_"
                    f"{duplicate_number}{suffix}"
                )
            )

            duplicate_number += 1

        with destination_path.open(
            "wb"
        ) as file:
            file.write(
                uploaded_image.getbuffer()
            )

        relative_path = (
            destination_path
            .relative_to(PROJECT_ROOT)
            .as_posix()
        )

        saved_paths.append(relative_path)

    return saved_paths


def display_component_images(
    image_paths: list[str],
) -> None:
    if not image_paths:
        return

    st.write("### Component Photos")

    valid_paths = []

    for image_path in image_paths:
        full_path = PROJECT_ROOT / image_path

        if full_path.exists():
            valid_paths.append(full_path)

    if not valid_paths:
        st.warning(
            "The saved image files could not be found."
        )
        return

    columns = st.columns(
        min(len(valid_paths), 2)
    )

    for number, full_path in enumerate(
        valid_paths
    ):
        with columns[
            number % len(columns)
        ]:
            st.image(
                str(full_path),
                caption=full_path.name,
                use_container_width=True,
            )


def display_component(component: dict) -> None:
    """Display one component as a normal readable app card."""

    top_left, top_right = st.columns(2)

    with top_left:
        st.write(
            f"**Category:** "
            f"{component.get('category', 'Not recorded')}"
        )
        st.write(
            f"**Manufacturer:** "
            f"{component.get('manufacturer') or 'Not recorded'}"
        )
        st.write(
            f"**Model number:** "
            f"{component.get('model_number') or 'Not recorded'}"
        )
        st.write(
            f"**Part number:** "
            f"{component.get('part_number') or 'Not recorded'}"
        )

    with top_right:
        st.write(
            f"**Station:** "
            f"{component.get('station', 'Not recorded')}"
        )
        st.write(
            f"**Spare-part location:** "
            f"{component.get('spare_part_location') or 'Not recorded'}"
        )

        related_faults = component.get("related_faults", [])

        if related_faults:
            st.write(
                "**Related faults:** "
                + ", ".join(str(item) for item in related_faults)
            )

    for heading, field_name in (
        ("Function", "function"),
        ("Common Failures", "common_failures"),
        ("Fault Symptoms", "fault_symptoms"),
        ("Inspection Procedure", "inspection_procedure"),
        ("Replacement Procedure", "replacement_procedure"),
    ):
        st.write(f"### {heading}")
        st.write(component.get(field_name, "Not recorded"))

    safety_notes = component.get("safety_notes")

    if safety_notes:
        st.warning(f"Safety: {safety_notes}")

    display_component_images(
        component.get("image_paths", [])
    )


def parse_related_faults(
    text: str,
) -> list[str]:
    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]

if st.button(
    "🏠 ← MAIN MENU",
    key="components_main_menu_button",
):
    st.switch_page("app.py")

st.title("⚙️ Machine Components Library")

st.caption(
    "ABAYO Assist AI — Component identification, "
    "failure symptoms, inspection and replacement knowledge"
)

st.info(
    "Store important machine parts together with their photos, "
    "functions, common failures and maintenance procedures."
)


reference_tab, view_tab, add_tab, summary_tab = st.tabs(
    [
        "🧭 Pakona PFS Reference",
        "🔍 View Components",
        "➕ Add Component",
        "📊 Component Summary",
    ]
)


with reference_tab:
    st.write("## Pakona PFS — Component Reference")

    st.info(
        "Stage 1 covers the two assemblies documented in detail so far. "
        "The Pouch Elevator / Main Pouch Conveyor presents the next pouch; "
        "the Pouch Picking Station performs the vacuum pickup. They are kept "
        "separate so operators do not confuse their components or functions."
    )

    reference_search_column, reference_station_column = st.columns([2, 1])

    with reference_search_column:
        reference_search_text = st.text_input(
            "Search Pakona reference",
            placeholder="Example: Omron sensor, suction cup, star wheel or guide rail",
            key="pakona_reference_search",
        )

    with reference_station_column:
        reference_station_label = st.selectbox(
            "Assembly",
            [
                "All documented assemblies",
                "Pouch Elevator / Main Pouch Conveyor",
                "Pouch Picking Station",
            ],
            key="pakona_reference_station",
        )

    reference_station_map = {
        "All documented assemblies": "",
        "Pouch Elevator / Main Pouch Conveyor": "Pouch elevator",
        "Pouch Picking Station": "Pouch picking station",
    }

    reference_results = search_reference_components(
        search_text=reference_search_text,
        station=reference_station_map[reference_station_label],
    )

    feed_count = sum(
        component.get("station") == "Pouch elevator"
        for component in PAKONA_REFERENCE_COMPONENTS
    )
    pick_count = sum(
        component.get("station") == "Pouch picking station"
        for component in PAKONA_REFERENCE_COMPONENTS
    )

    count_one, count_two, count_three = st.columns(3)
    count_one.metric("Documented Parts", len(PAKONA_REFERENCE_COMPONENTS))
    count_two.metric("Main Conveyor", feed_count)
    count_three.metric("Picking Station", pick_count)

    st.caption(
        "Unknown Pakona model numbers, part numbers and exact OEM names remain "
        "Not recorded until we confirm them from a nameplate, manual or drawing."
    )

    if not reference_results:
        st.info("No documented Pakona components match this search.")
    else:
        current_station = None

        for reference_component in reference_results:
            station_name = station_display_name(
                str(reference_component.get("station", "Not recorded"))
            )

            if station_name != current_station:
                st.write(f"### {station_name}")
                current_station = station_name

            component_number = reference_component.get(
                "component_number",
                "Reference",
            )
            component_name = reference_component.get(
                "component_name",
                "Unnamed component",
            )

            with st.expander(
                f"{component_number} — {component_name}",
                expanded=False,
            ):
                display_reference_component(reference_component)


with view_tab:
    st.write("## Search Machine Components")

    search_column, station_column, category_column = st.columns(3)

    with search_column:
        search_text = st.text_input(
            "Search",
            placeholder=(
                "Example: suction cup, Omron sensor, "
                "Venturi ejector or auger motor"
            ),
            key="component_search_text",
        )

    with station_column:
        selected_station = st.selectbox(
            "Station filter",
            ["All stations"] + STATIONS,
            key="component_station_filter",
        )

    with category_column:
        selected_category = st.selectbox(
            "Category filter",
            ["All categories"] + CATEGORIES,
            key="component_category_filter",
        )

    station_filter = (
        ""
        if selected_station == "All stations"
        else selected_station
    )

    category_filter = (
        ""
        if selected_category == "All categories"
        else selected_category
    )

    results = search_components(
        search_text=search_text,
        station=station_filter,
        category=category_filter,
    )

    st.write(
        f"### Components Found: {len(results)}"
    )

    if results:
        for component_index, component in enumerate(results):
            component_number = str(
                component.get("component_number")
                or f"Component {component_index + 1}"
            )
            component_name = str(
                component.get("component_name")
                or "Unnamed component"
            )
            station = str(
                component.get("station")
                or "Not recorded"
            )

            item_column, menu_column = st.columns([8, 1])

            with item_column:
                st.markdown(
                    f"**{component_number} — {component_name}**"
                )
                st.caption(station)

            with menu_column:
                with st.popover(
                    "⋮",
                    help=f"Options for {component_name}",
                    use_container_width=True,
                ):
                    if st.button(
                        "Open",
                        key=f"open_component_{component_index}",
                        use_container_width=True,
                    ):
                        st.session_state.open_component_number = (
                            component_number
                        )
                        st.session_state.pending_component_delete = None
                        st.rerun()

                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_component_{component_index}",
                        use_container_width=True,
                    ):
                        st.session_state.pending_component_delete = (
                            component_number
                        )
                        st.session_state.open_component_number = None
                        st.rerun()

            if (
                st.session_state.get("open_component_number")
                == component_number
            ):
                with st.container(border=True):
                    st.subheader(
                        f"{component_number} — {component_name}"
                    )
                    display_component(component)

                    if st.button(
                        "Close",
                        key=f"close_component_{component_index}",
                    ):
                        st.session_state.open_component_number = None
                        st.rerun()

            if (
                st.session_state.get("pending_component_delete")
                == component_number
            ):
                with st.container(border=True):
                    st.warning(
                        f'Move "{component_name}" to the Recycle Bin?'
                    )

                    confirm_delete = st.checkbox(
                        "Yes, move this component to the Recycle Bin.",
                        key=f"confirm_component_{component_index}",
                    )

                    confirm_column, cancel_column = st.columns(2)

                    with confirm_column:
                        if st.button(
                            "🗑️ Move to Recycle Bin",
                            type="primary",
                            disabled=not confirm_delete,
                            key=f"confirm_move_component_{component_index}",
                            use_container_width=True,
                        ):
                            try:
                                move_component_to_recycle_bin(
                                    component_number
                                )
                                st.session_state.pending_component_delete = (
                                    None
                                )
                                st.success(
                                    f"{component_name} was moved to "
                                    "the Recycle Bin."
                                )
                                st.rerun()
                            except Exception as error:
                                st.error(
                                    "Unable to move component: "
                                    f"{error}"
                                )

                    with cancel_column:
                        if st.button(
                            "Cancel",
                            key=f"cancel_component_{component_index}",
                            use_container_width=True,
                        ):
                            st.session_state.pending_component_delete = None
                            st.rerun()

            st.divider()

    else:
        st.info(
            "No machine components matched the selected filters."
        )


with add_tab:
    st.write("## Add a Machine Component")

    component_name = st.text_input(
        "Component name",
        placeholder=(
            "Example: Pouch-picking suction cup"
        ),
        key="add_component_name",
    )

    first_column, second_column = st.columns(2)

    with first_column:
        station = st.selectbox(
            "Machine station",
            STATIONS,
            key="add_component_station",
        )

        category = st.selectbox(
            "Component category",
            CATEGORIES,
            key="add_component_category",
        )

        manufacturer = st.text_input(
            "Manufacturer",
            placeholder="Example: Omron",
            key="add_component_manufacturer",
        )

    with second_column:
        model_number = st.text_input(
            "Model number",
            key="add_component_model",
        )

        part_number = st.text_input(
            "Part number",
            key="add_component_part",
        )

        spare_part_location = st.text_input(
            "Spare-part storage location",
            placeholder=(
                "Example: Engineering store, shelf B2"
            ),
            key="add_component_location",
        )

    component_function = st.text_area(
        "Component function",
        placeholder=(
            "Explain what the component does "
            "during normal machine operation."
        ),
        height=110,
        key="add_component_function",
    )

    common_failures = st.text_area(
        "Common failures",
        placeholder=(
            "Example: Wear, dust contamination, "
            "vacuum leakage and misalignment."
        ),
        height=120,
        key="add_component_failures",
    )

    fault_symptoms = st.text_area(
        "Fault symptoms",
        placeholder=(
            "Example: Pouches are missed, picked late "
            "or dropped during transfer."
        ),
        height=120,
        key="add_component_symptoms",
    )

    inspection_procedure = st.text_area(
        "Inspection procedure",
        placeholder=(
            "Write the safe inspection steps "
            "in the correct order."
        ),
        height=140,
        key="add_component_inspection",
    )

    replacement_procedure = st.text_area(
        "Replacement procedure",
        placeholder=(
            "Write the safe replacement or adjustment steps."
        ),
        height=140,
        key="add_component_replacement",
    )

    safety_notes = st.text_area(
        "Safety notes",
        placeholder=(
            "Example: Isolate electrical and pneumatic energy "
            "before removing the component."
        ),
        height=100,
        key="add_component_safety",
    )

    related_fault_text = st.text_area(
        "Related faults",
        placeholder=(
            "Separate faults with commas. Example: "
            "pouch not picked, weak suction, pouch dropped"
        ),
        height=100,
        key="add_component_faults",
    )

    uploaded_images = st.file_uploader(
        "Upload component photographs",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        accept_multiple_files=True,
        key="add_component_images",
    )

    if uploaded_images:
        st.write("### Image Preview")

        preview_columns = st.columns(
            min(len(uploaded_images), 2)
        )

        for number, uploaded_image in enumerate(
            uploaded_images
        ):
            with preview_columns[
                number % len(preview_columns)
            ]:
                st.image(
                    uploaded_image,
                    caption=uploaded_image.name,
                    use_container_width=True,
                )

    confirmation = st.checkbox(
        "I confirm that the component information is accurate.",
        key="add_component_confirmation",
    )

    if st.button(
        "Save Machine Component",
        type="primary",
        use_container_width=True,
        key="save_component_button",
    ):
        if not component_name.strip():
            st.error(
                "Enter the component name."
            )

        elif not component_function.strip():
            st.error(
                "Enter the component function."
            )

        elif not common_failures.strip():
            st.error(
                "Enter at least one common failure."
            )

        elif not fault_symptoms.strip():
            st.error(
                "Enter the fault symptoms."
            )

        elif not inspection_procedure.strip():
            st.error(
                "Enter the inspection procedure."
            )

        elif not replacement_procedure.strip():
            st.error(
                "Enter the replacement procedure."
            )

        elif not confirmation:
            st.error(
                "Confirm that the information is accurate."
            )

        else:
            temporary_folder = "pending_component"

            image_paths = save_component_images(
                uploaded_images,
                temporary_folder,
            )

            component_number = add_component(
                component_name=component_name,
                station=station,
                category=category,
                function=component_function,
                common_failures=common_failures,
                fault_symptoms=fault_symptoms,
                inspection_procedure=inspection_procedure,
                replacement_procedure=replacement_procedure,
                safety_notes=safety_notes,
                manufacturer=manufacturer,
                model_number=model_number,
                part_number=part_number,
                spare_part_location=spare_part_location,
                related_faults=parse_related_faults(
                    related_fault_text
                ),
                image_paths=image_paths,
            )

            st.success(
                "Machine component saved successfully."
            )

            st.metric(
                "Component Number",
                component_number,
            )

            st.info(
                "This component is now available "
                "in the Machine Components Library."
            )


with summary_tab:
    st.write("## Component Library Summary")

    summary = component_summary()

    total_components = summary.get(
        "total_components",
        0,
    )

    summary_reference_column, summary_saved_column = st.columns(2)

    summary_reference_column.metric(
        "Pakona Reference Components",
        len(PAKONA_REFERENCE_COMPONENTS),
    )

    summary_saved_column.metric(
        "Saved Components",
        total_components,
    )

    station_counts = summary.get(
        "station_counts",
        {},
    )

    category_counts = summary.get(
        "category_counts",
        {},
    )

    left_column, right_column = st.columns(2)

    with left_column:
        st.write("### Components by Station")

        if station_counts:
            for station_name, count in sorted(
                station_counts.items()
            ):
                st.write(
                    f"**{station_name}:** {count}"
                )
        else:
            st.info(
                "No station statistics are available yet."
            )

    with right_column:
        st.write("### Components by Category")

        if category_counts:
            for category_name, count in sorted(
                category_counts.items()
            ):
                st.write(
                    f"**{category_name}:** {count}"
                )
        else:
            st.info(
                "No category statistics are available yet."
            )


st.divider()

st.caption(
    "Safety: Stop the machine and isolate electrical, "
    "pneumatic and mechanical energy before inspection "
    "or component replacement."
)
