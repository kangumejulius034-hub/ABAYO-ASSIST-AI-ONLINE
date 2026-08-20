import logging
from pathlib import Path
from typing import Any

from supabase_engine import get_supabase_client
from storage.json_store import load_json, save_json


PROJECT_ROOT = Path(__file__).resolve().parent
FAULTS_JSON_PATH = PROJECT_ROOT / "knowledge" / "faults.json"
LOGGER = logging.getLogger(__name__)


def _convert_to_text(value: Any) -> str:
    """Convert lists or other values into text suitable for Supabase."""

    if value is None:
        return ""

    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())

    return str(value).strip()


def _save_local_backup(record: dict) -> bool:
    """Keep a temporary JSON backup for compatibility with the existing app."""

    faults = load_json(FAULTS_JSON_PATH, [])
    if not isinstance(faults, list):
        faults = []

    fingerprint = (
        str(record.get("station", "")).strip().lower(),
        str(record.get("fault", "")).strip().lower(),
    )
    already_saved = any(
        (
            str(item.get("station", "")).strip().lower(),
            str(item.get("fault", "")).strip().lower(),
        )
        == fingerprint
        for item in faults
        if isinstance(item, dict)
    )

    if not already_saved:
        faults.append(record)
        return save_json(FAULTS_JSON_PATH, faults)

    return False


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

    document_saved = False
    try:
        supabase = get_supabase_client()

        (
            supabase.table("faults")
            .insert(record)
            .execute()
        )

        cloud_saved = True

    except Exception as error:
        LOGGER.warning("Supabase fault save failed: %s", error)
        cloud_saved = False

    try:
        local_record = {
            "station": record["station"],
            "fault": record["fault"],
            "possible_causes": causes,
            "checks": checks,
        }

        document_saved = _save_local_backup(local_record)

    except Exception as error:
        LOGGER.warning("Local JSON backup failed: %s", error)

    return cloud_saved or document_saved
