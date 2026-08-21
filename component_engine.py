from pathlib import Path
from typing import Any

from storage.json_store import load_json, save_json


BASE_DIR = Path(__file__).resolve().parent
COMPONENTS_FILE = BASE_DIR / "knowledge" / "components.json"


def load_components() -> list[dict[str, Any]]:
    data = load_json(COMPONENTS_FILE, [])
    if not isinstance(data, list):
        return []
    return [record for record in data if isinstance(record, dict)]


def save_components(records: list[dict[str, Any]]) -> None:
    save_json(COMPONENTS_FILE, records)


def component_belongs_to_machine(
    record: dict[str, Any],
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> bool:
    saved_id = record.get("machine_id")
    if machine_id in (None, ""):
        return True
    if saved_id not in (None, ""):
        return str(saved_id) == str(machine_id)
    return allow_legacy


def components_for_machine(
    *, machine_id: Any | None, allow_legacy: bool = False
) -> list[dict[str, Any]]:
    return [
        record
        for record in load_components()
        if component_belongs_to_machine(
            record, machine_id=machine_id, allow_legacy=allow_legacy
        )
    ]


def generate_component_number(records: list[dict[str, Any]]) -> str:
    highest_number = 0
    for record in records:
        digits = "".join(
            character
            for character in str(record.get("component_number", ""))
            if character.isdigit()
        )
        if digits:
            highest_number = max(highest_number, int(digits))
    return f"CMP-{highest_number + 1:06d}"


def add_component(
    component_name: str,
    station: str,
    category: str,
    function: str,
    common_failures: str,
    fault_symptoms: str,
    inspection_procedure: str,
    replacement_procedure: str,
    safety_notes: str = "",
    manufacturer: str = "",
    model_number: str = "",
    part_number: str = "",
    spare_part_location: str = "",
    related_faults: list[str] | None = None,
    image_paths: list[str] | None = None,
    *,
    machine_id: Any | None = None,
    machine_model: str = "",
) -> str:
    records = load_components()
    component_number = generate_component_number(records)
    new_record = {
        "machine_id": machine_id,
        "machine_model": machine_model.strip(),
        "component_number": component_number,
        "component_name": component_name.strip(),
        "station": station.strip(),
        "category": category.strip(),
        "manufacturer": manufacturer.strip(),
        "model_number": model_number.strip(),
        "part_number": part_number.strip(),
        "function": function.strip(),
        "common_failures": common_failures.strip(),
        "fault_symptoms": fault_symptoms.strip(),
        "inspection_procedure": inspection_procedure.strip(),
        "replacement_procedure": replacement_procedure.strip(),
        "safety_notes": safety_notes.strip(),
        "spare_part_location": spare_part_location.strip(),
        "related_faults": related_faults or [],
        "image_paths": image_paths or [],
    }
    records.append(new_record)
    save_components(records)
    return component_number


def search_components(
    search_text: str = "",
    station: str = "",
    category: str = "",
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> list[dict[str, Any]]:
    query = search_text.strip().lower()
    station_query = station.strip().lower()
    category_query = category.strip().lower()
    results: list[dict[str, Any]] = []

    for record in components_for_machine(
        machine_id=machine_id, allow_legacy=allow_legacy
    ):
        saved_station = str(record.get("station", "")).lower()
        saved_category = str(record.get("category", "")).lower()
        related_faults = record.get("related_faults", [])
        if not isinstance(related_faults, list):
            related_faults = [str(related_faults)]

        searchable_text = " ".join(
            [
                str(record.get("component_number", "")),
                str(record.get("component_name", "")),
                str(record.get("station", "")),
                str(record.get("category", "")),
                str(record.get("manufacturer", "")),
                str(record.get("model_number", "")),
                str(record.get("part_number", "")),
                str(record.get("function", "")),
                str(record.get("common_failures", "")),
                str(record.get("fault_symptoms", "")),
                str(record.get("inspection_procedure", "")),
                str(record.get("replacement_procedure", "")),
                str(record.get("safety_notes", "")),
                str(record.get("spare_part_location", "")),
                " ".join(str(item) for item in related_faults),
            ]
        ).lower()

        if station_query and saved_station != station_query:
            continue
        if category_query and saved_category != category_query:
            continue
        if query and query not in searchable_text:
            continue
        results.append(record)

    return list(reversed(results))


def get_component(
    component_number: str,
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> dict[str, Any] | None:
    requested_number = component_number.strip().lower()
    for record in components_for_machine(
        machine_id=machine_id, allow_legacy=allow_legacy
    ):
        if str(record.get("component_number", "")).strip().lower() == requested_number:
            return record
    return None


def update_component(
    component_number: str,
    updated_data: dict[str, Any],
    *,
    machine_id: Any | None = None,
) -> bool:
    records = load_components()
    for index, record in enumerate(records):
        if record.get("component_number") != component_number:
            continue
        if machine_id not in (None, "") and str(record.get("machine_id")) != str(machine_id):
            continue
        updated_record = dict(record)
        updated_record.update(updated_data)
        updated_record["component_number"] = component_number
        if machine_id not in (None, ""):
            updated_record["machine_id"] = machine_id
        records[index] = updated_record
        save_components(records)
        return True
    return False
