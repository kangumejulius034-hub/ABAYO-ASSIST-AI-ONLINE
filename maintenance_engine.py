from pathlib import Path
from typing import Any

from storage.json_store import load_json, save_json

BASE_DIR = Path(__file__).resolve().parent
MAINTENANCE_FILE = BASE_DIR / "knowledge" / "maintenance_history.json"


def _selected_scope(machine_id: Any | None = None) -> tuple[Any | None, bool, str]:
    if machine_id not in (None, ""):
        return machine_id, False, ""
    try:
        from core.machine_context import current_machine, is_pakona_machine, machine_model_label, selected_machine_id
        selected_id = selected_machine_id()
        if selected_id in (None, ""):
            return None, False, ""
        machine = current_machine()
        return selected_id, is_pakona_machine(machine), machine_model_label(machine)
    except Exception:
        return None, False, ""


def load_maintenance_records() -> list[dict[str, Any]]:
    data = load_json(MAINTENANCE_FILE, [])
    if not isinstance(data, list):
        return []
    return [record for record in data if isinstance(record, dict)]


def save_all_maintenance_records(records: list[dict[str, Any]]) -> None:
    save_json(MAINTENANCE_FILE, records)


def record_belongs_to_machine(record: dict[str, Any], machine_id: Any | None, allow_legacy: bool) -> bool:
    saved_id = record.get("machine_id")
    if machine_id in (None, ""):
        return True
    if saved_id not in (None, ""):
        return str(saved_id) == str(machine_id)
    return allow_legacy


def generate_record_number(records: list[dict[str, Any]]) -> str:
    highest = 0
    for record in records:
        digits = "".join(c for c in str(record.get("record_number", "")) if c.isdigit())
        if digits:
            highest = max(highest, int(digits))
    return f"MNT-{highest + 1:06d}"


def add_maintenance_record(
    machine_model: str,
    recipe_name: str,
    station: str,
    fault: str,
    confirmed_cause: str,
    corrective_action: str,
    downtime_minutes: float,
    recorded_by: str,
    production_status: str = "",
    production_shift: str = "",
    batch_number: str = "",
    notes: str = "",
    image_paths: list[str] | None = None,
    *,
    machine_id: Any | None = None,
) -> str:
    selected_id, _, selected_model = _selected_scope(machine_id)
    records = load_maintenance_records()
    number = generate_record_number(records)
    records.append({
        "machine_id": selected_id,
        "machine_model": selected_model or machine_model.strip(),
        "record_number": number,
        "recipe_name": recipe_name.strip(),
        "station": station.strip(),
        "fault": fault.strip(),
        "confirmed_cause": confirmed_cause.strip(),
        "corrective_action": corrective_action.strip(),
        "downtime_minutes": float(downtime_minutes),
        "recorded_by": recorded_by.strip(),
        "production_status": production_status.strip(),
        "production_shift": production_shift.strip(),
        "batch_number": batch_number.strip(),
        "notes": notes.strip(),
        "image_paths": image_paths or [],
    })
    save_all_maintenance_records(records)
    return number


def get_maintenance_record(record_number: str, *, machine_id: Any | None = None) -> dict[str, Any] | None:
    selected_id, allow_legacy, _ = _selected_scope(machine_id)
    requested = record_number.strip().lower()
    for record in load_maintenance_records():
        if not record_belongs_to_machine(record, selected_id, allow_legacy):
            continue
        if str(record.get("record_number", "")).strip().lower() == requested:
            return record
    return None


def list_record_numbers(*, machine_id: Any | None = None) -> list[str]:
    selected_id, allow_legacy, _ = _selected_scope(machine_id)
    numbers = [
        str(record.get("record_number"))
        for record in load_maintenance_records()
        if record.get("record_number") and record_belongs_to_machine(record, selected_id, allow_legacy)
    ]
    return list(reversed(numbers))


def filter_maintenance_records(
    machine_model: str = "",
    recipe_name: str = "",
    station: str = "",
    production_status: str = "",
    search_text: str = "",
    *,
    machine_id: Any | None = None,
) -> list[dict[str, Any]]:
    selected_id, allow_legacy, _ = _selected_scope(machine_id)
    recipe_query = recipe_name.strip().lower()
    station_query = station.strip().lower()
    status_query = production_status.strip().lower()
    text_query = search_text.strip().lower()
    filtered = []

    for record in load_maintenance_records():
        if not record_belongs_to_machine(record, selected_id, allow_legacy):
            continue
        saved_recipe = str(record.get("recipe_name", "")).lower()
        saved_station = str(record.get("station", "")).lower()
        saved_status = str(record.get("production_status", "")).lower()
        searchable = " ".join(str(record.get(key, "")) for key in (
            "record_number", "fault", "confirmed_cause", "corrective_action", "notes", "recorded_by", "batch_number", "machine_model", "recipe_name", "station", "production_status"
        )).lower()
        if recipe_query and saved_recipe != recipe_query:
            continue
        if station_query and saved_station != station_query:
            continue
        if status_query and saved_status != status_query:
            continue
        if text_query and text_query not in searchable:
            continue
        filtered.append(record)
    return list(reversed(filtered))


def calculate_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    total_records = len(records)
    total_downtime = sum(float(record.get("downtime_minutes", 0) or 0) for record in records)
    fault_counts: dict[str, int] = {}
    station_counts: dict[str, int] = {}
    recipe_counts: dict[str, int] = {}
    for record in records:
        fault = str(record.get("fault", "Unknown fault")).strip()
        station = str(record.get("station", "Unknown station")).strip()
        recipe = str(record.get("recipe_name", "")).strip()
        fault_counts[fault] = fault_counts.get(fault, 0) + 1
        station_counts[station] = station_counts.get(station, 0) + 1
        if recipe:
            recipe_counts[recipe] = recipe_counts.get(recipe, 0) + 1
    most_fault = max(fault_counts, key=fault_counts.get) if fault_counts else "None"
    most_station = max(station_counts, key=station_counts.get) if station_counts else "None"
    most_recipe = max(recipe_counts, key=recipe_counts.get) if recipe_counts else "None"
    average = total_downtime / total_records if total_records else 0
    return {
        "total_records": total_records,
        "total_downtime_minutes": round(total_downtime, 2),
        "average_downtime_minutes": round(average, 2),
        "most_repeated_fault": most_fault,
        "most_affected_station": most_station,
        "most_affected_recipe": most_recipe,
    }
