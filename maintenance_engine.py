import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent

MAINTENANCE_FILE = (
    BASE_DIR
    / "knowledge"
    / "maintenance_history.json"
)


def load_maintenance_records() -> list[dict[str, Any]]:
    """Load all maintenance records safely."""

    try:
        with MAINTENANCE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except FileNotFoundError:
        MAINTENANCE_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        save_all_maintenance_records([])
        return []

    except json.JSONDecodeError:
        return []


def save_all_maintenance_records(
    records: list[dict[str, Any]],
) -> None:
    """Save all maintenance records."""

    MAINTENANCE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MAINTENANCE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False,
        )


def generate_record_number(
    records: list[dict[str, Any]],
) -> str:
    """
    Generate a permanent sequential record number.

    Examples:
    MNT-000001
    MNT-000002
    """

    highest_number = 0

    for record in records:
        record_number = str(
            record.get(
                "record_number",
                "",
            )
        )

        number_text = "".join(
            character
            for character in record_number
            if character.isdigit()
        )

        if number_text:
            highest_number = max(
                highest_number,
                int(number_text),
            )

    next_number = highest_number + 1

    return f"MNT-{next_number:06d}"


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
) -> str:
    """
    Save one maintenance event.

    Returns the generated permanent record number.
    """

    records = load_maintenance_records()

    record_number = generate_record_number(
        records
    )

    new_record = {
        "record_number": record_number,
        "machine_model": machine_model.strip(),
        "recipe_name": recipe_name.strip(),
        "station": station.strip(),
        "fault": fault.strip(),
        "confirmed_cause": confirmed_cause.strip(),
        "corrective_action": corrective_action.strip(),
        "downtime_minutes": float(
            downtime_minutes
        ),
        "recorded_by": recorded_by.strip(),
        "production_status": (
            production_status.strip()
        ),
        "production_shift": (
            production_shift.strip()
        ),
        "batch_number": batch_number.strip(),
        "notes": notes.strip(),
        "image_paths": image_paths or [],
    }

    records.append(new_record)

    save_all_maintenance_records(records)

    return record_number


def get_maintenance_record(
    record_number: str,
) -> dict[str, Any] | None:
    """Find one record using its permanent number."""

    requested_number = (
        record_number.strip().lower()
    )

    records = load_maintenance_records()

    for record in records:
        saved_number = str(
            record.get(
                "record_number",
                "",
            )
        ).strip().lower()

        if saved_number == requested_number:
            return record

    return None


def list_record_numbers() -> list[str]:
    """Return record numbers with newest first."""

    records = load_maintenance_records()

    numbers = [
        str(
            record.get(
                "record_number",
                "",
            )
        )
        for record in records
        if record.get("record_number")
    ]

    return list(reversed(numbers))


def filter_maintenance_records(
    machine_model: str = "",
    recipe_name: str = "",
    station: str = "",
    production_status: str = "",
    search_text: str = "",
) -> list[dict[str, Any]]:
    """Search and filter the maintenance history."""

    records = load_maintenance_records()

    machine_query = machine_model.strip().lower()
    recipe_query = recipe_name.strip().lower()
    station_query = station.strip().lower()

    status_query = (
        production_status.strip().lower()
    )

    text_query = search_text.strip().lower()

    filtered_records: list[dict[str, Any]] = []

    for record in records:
        saved_machine = str(
            record.get(
                "machine_model",
                "",
            )
        ).lower()

        saved_recipe = str(
            record.get(
                "recipe_name",
                "",
            )
        ).lower()

        saved_station = str(
            record.get(
                "station",
                "",
            )
        ).lower()

        saved_status = str(
            record.get(
                "production_status",
                "",
            )
        ).lower()

        searchable_text = " ".join(
            [
                str(
                    record.get(
                        "record_number",
                        "",
                    )
                ),
                str(record.get("fault", "")),
                str(
                    record.get(
                        "confirmed_cause",
                        "",
                    )
                ),
                str(
                    record.get(
                        "corrective_action",
                        "",
                    )
                ),
                str(record.get("notes", "")),
                str(
                    record.get(
                        "recorded_by",
                        "",
                    )
                ),
                str(
                    record.get(
                        "batch_number",
                        "",
                    )
                ),
                saved_machine,
                saved_recipe,
                saved_station,
                saved_status,
            ]
        ).lower()

        if (
            machine_query
            and saved_machine != machine_query
        ):
            continue

        if (
            recipe_query
            and saved_recipe != recipe_query
        ):
            continue

        if (
            station_query
            and saved_station != station_query
        ):
            continue

        if (
            status_query
            and saved_status != status_query
        ):
            continue

        if (
            text_query
            and text_query not in searchable_text
        ):
            continue

        filtered_records.append(record)

    return list(
        reversed(filtered_records)
    )


def calculate_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate maintenance performance statistics."""

    total_records = len(records)

    total_downtime = sum(
        float(
            record.get(
                "downtime_minutes",
                0,
            )
            or 0
        )
        for record in records
    )

    fault_counts: dict[str, int] = {}
    station_counts: dict[str, int] = {}
    recipe_counts: dict[str, int] = {}

    for record in records:
        fault = str(
            record.get(
                "fault",
                "Unknown fault",
            )
        ).strip()

        station = str(
            record.get(
                "station",
                "Unknown station",
            )
        ).strip()

        recipe = str(
            record.get(
                "recipe_name",
                "",
            )
        ).strip()

        fault_counts[fault] = (
            fault_counts.get(fault, 0) + 1
        )

        station_counts[station] = (
            station_counts.get(station, 0) + 1
        )

        if recipe:
            recipe_counts[recipe] = (
                recipe_counts.get(recipe, 0) + 1
            )

    most_repeated_fault = "None"

    if fault_counts:
        most_repeated_fault = max(
            fault_counts,
            key=fault_counts.get,
        )

    most_affected_station = "None"

    if station_counts:
        most_affected_station = max(
            station_counts,
            key=station_counts.get,
        )

    most_affected_recipe = "None"

    if recipe_counts:
        most_affected_recipe = max(
            recipe_counts,
            key=recipe_counts.get,
        )

    average_downtime = 0

    if total_records:
        average_downtime = (
            total_downtime / total_records
        )

    return {
        "total_records": total_records,
        "total_downtime_minutes": round(
            total_downtime,
            2,
        ),
        "average_downtime_minutes": round(
            average_downtime,
            2,
        ),
        "most_repeated_fault": (
            most_repeated_fault
        ),
        "most_affected_station": (
            most_affected_station
        ),
        "most_affected_recipe": (
            most_affected_recipe
        ),
    }