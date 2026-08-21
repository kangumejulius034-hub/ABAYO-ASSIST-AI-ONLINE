from pathlib import Path
from typing import Any

from storage.json_store import load_json, save_json

BASE_DIR = Path(__file__).resolve().parent
COMPONENTS_FILE = BASE_DIR / "knowledge" / "components.json"


def _selected_scope(machine_id: Any | None, allow_legacy: bool) -> tuple[Any | None, bool, str]:
    if machine_id not in (None, ""):
        return machine_id, allow_legacy, ""
    try:
        from core.machine_context import current_machine, is_pakona_machine, machine_model_label, selected_machine_id
        selected_id = selected_machine_id()
        if selected_id in (None, ""):
            return machine_id, allow_legacy, ""
        machine = current_machine()
        return selected_id, is_pakona_machine(machine), machine_model_label(machine)
    except Exception:
        return machine_id, allow_legacy, ""


def load_components() -> list[dict[str, Any]]:
    data = load_json(COMPONENTS_FILE, [])
    if not isinstance(data, list):
        return []
    return [record for record in data if isinstance(record, dict)]


def save_components(records: list[dict[str, Any]]) -> None:
    save_json(COMPONENTS_FILE, records)


def component_belongs_to_machine(record: dict[str, Any], *, machine_id=None, allow_legacy=False) -> bool:
    machine_id, allow_legacy, _ = _selected_scope(machine_id, allow_legacy)
    saved_id = record.get("machine_id")
    if machine_id in (None, ""):
        return True
    if saved_id not in (None, ""):
        return str(saved_id) == str(machine_id)
    return allow_legacy


def components_for_machine(*, machine_id=None, allow_legacy=False) -> list[dict[str, Any]]:
    machine_id, allow_legacy, _ = _selected_scope(machine_id, allow_legacy)
    return [record for record in load_components() if component_belongs_to_machine(record, machine_id=machine_id, allow_legacy=allow_legacy)]


def generate_component_number(records: list[dict[str, Any]]) -> str:
    highest = 0
    for record in records:
        digits = "".join(c for c in str(record.get("component_number", "")) if c.isdigit())
        if digits:
            highest = max(highest, int(digits))
    return f"CMP-{highest + 1:06d}"


def add_component(component_name: str, station: str, category: str, function: str, common_failures: str, fault_symptoms: str, inspection_procedure: str, replacement_procedure: str, safety_notes: str = "", manufacturer: str = "", model_number: str = "", part_number: str = "", spare_part_location: str = "", related_faults: list[str] | None = None, image_paths: list[str] | None = None, *, machine_id=None, machine_model: str = "") -> str:
    machine_id, _, selected_model = _selected_scope(machine_id, False)
    machine_model = selected_model or machine_model
    records = load_components()
    number = generate_component_number(records)
    records.append({
        "machine_id": machine_id,
        "machine_model": machine_model.strip(),
        "component_number": number,
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
    })
    save_components(records)
    return number


def search_components(search_text: str = "", station: str = "", category: str = "", *, machine_id=None, allow_legacy=False) -> list[dict[str, Any]]:
    machine_id, allow_legacy, _ = _selected_scope(machine_id, allow_legacy)
    query = search_text.strip().lower()
    station_query = station.strip().lower()
    category_query = category.strip().lower()
    results = []
    for record in components_for_machine(machine_id=machine_id, allow_legacy=allow_legacy):
        if station_query and str(record.get("station", "")).lower() != station_query:
            continue
        if category_query and str(record.get("category", "")).lower() != category_query:
            continue
        related = record.get("related_faults", [])
        if not isinstance(related, list):
            related = [str(related)]
        searchable = " ".join(str(record.get(key, "")) for key in (
            "component_number", "component_name", "station", "category", "manufacturer", "model_number", "part_number", "function", "common_failures", "fault_symptoms", "inspection_procedure", "replacement_procedure", "safety_notes", "spare_part_location"
        )) + " " + " ".join(str(item) for item in related)
        if query and query not in searchable.lower():
            continue
        results.append(record)
    return list(reversed(results))


def get_component(component_number: str, *, machine_id=None, allow_legacy=False) -> dict[str, Any] | None:
    requested = component_number.strip().lower()
    for record in components_for_machine(machine_id=machine_id, allow_legacy=allow_legacy):
        if str(record.get("component_number", "")).strip().lower() == requested:
            return record
    return None


def update_component(component_number: str, updated_data: dict[str, Any], *, machine_id=None) -> bool:
    machine_id, _, _ = _selected_scope(machine_id, False)
    records = load_components()
    for index, record in enumerate(records):
        if record.get("component_number") != component_number:
            continue
        if machine_id not in (None, "") and str(record.get("machine_id")) != str(machine_id):
            continue
        updated = dict(record)
        updated.update(updated_data)
        updated["component_number"] = component_number
        if machine_id not in (None, ""):
            updated["machine_id"] = machine_id
        records[index] = updated
        save_components(records)
        return True
    return False
