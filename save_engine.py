import json
from pathlib import Path
from typing import Any

from supabase_engine import get_supabase_client


PROJECT_ROOT = Path(__file__).resolve().parent
FAULTS_JSON_PATH = PROJECT_ROOT / "knowledge" / "faults.json"


def _convert_to_text(value: Any) -> str:
    """Convert lists or other values into text suitable for Supabase."""

    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())

    return str(value).strip()


def _save_local_backup(record: dict) -> None:
    """Keep a temporary JSON backup for compatibility with the existing app."""

    FAULTS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        with FAULTS_JSON_PATH.open("r", encoding="utf-8") as file:
            faults = json.load(file)

        if not isinstance(faults, list):
            faults = []

    except (FileNotFoundError, json.JSONDecodeError):
        faults = []

    faults.append(record)

    with FAULTS_JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(faults, file, indent=4, ensure_ascii=False)


def save_fault(station, fault, causes, checks) -> bool:
    """
    Save a fault permanently to Supabase.

    A local JSON copy is also created as a temporary backup.
    """

    record = {
        "station": _convert_to_text(station),
        "fault": _convert_to_text(fault),
        "possible_causes": _convert_to_text(causes),
        "recommended_checks": _convert_to_text(checks),
    }

    try:
        supabase = get_supabase_client()

        (
            supabase.table("faults")
            .insert(record)
            .execute()
        )

        cloud_saved = True

    except Exception as error:
        print(f"Supabase fault save failed: {error}")
        cloud_saved = False

    try:
        local_record = {
            "station": record["station"],
            "fault": record["fault"],
            "possible_causes": causes,
            "checks": checks,
        }

        _save_local_backup(local_record)

    except Exception as error:
        print(f"Local JSON backup failed: {error}")

    return cloud_saved
