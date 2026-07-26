import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent

COMPONENTS_FILE = (
    BASE_DIR
    / "knowledge"
    / "components.json"
)


def load_components() -> list[dict[str, Any]]:
    """Load all machine component records safely."""

    COMPONENTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not COMPONENTS_FILE.exists():
        save_components([])
        return []

    try:
        with COMPONENTS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []


def save_components(
    records: list[dict[str, Any]],
) -> None:
    """Save all machine component records."""

    COMPONENTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with COMPONENTS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False,
        )


def generate_component_number(
    records: list[dict[str, Any]],
) -> str:
    """Generate the next permanent component number."""

    highest_number = 0

    for record in records:
        component_number = str(
            record.get(
                "component_number",
                "",
            )
        )

        digits = "".join(
            character
            for character in component_number
            if character.isdigit()
        )

        if digits:
            highest_number = max(
                highest_number,
                int(digits),
            )

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
) -> str:
    """Save a new machine component."""

    records = load_components()

    component_number = generate_component_number(
        records
    )

    new_record = {
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
) -> list[dict[str, Any]]:
    """Search components by name, station, category or technical details."""

    query = search_text.strip().lower()
    station_query = station.strip().lower()
    category_query = category.strip().lower()

    results: list[dict[str, Any]] = []

    for record in load_components():
        saved_station = str(
            record.get(
                "station",
                "",
            )
        ).lower()

        saved_category = str(
            record.get(
                "category",
                "",
            )
        ).lower()

        related_faults = record.get(
            "related_faults",
            [],
        )

        if not isinstance(
            related_faults,
            list,
        ):
            related_faults = [
                str(related_faults)
            ]

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
                " ".join(
                    str(item)
                    for item in related_faults
                ),
            ]
        ).lower()

        if (
            station_query
            and saved_station != station_query
        ):
            continue

        if (
            category_query
            and saved_category != category_query
        ):
            continue

        if (
            query
            and query not in searchable_text
        ):
            continue

        results.append(record)

    return list(
        reversed(results)
    )


def get_component(
    component_number: str,
) -> dict[str, Any] | None:
    """Retrieve one component by its permanent number."""

    requested_number = (
        component_number
        .strip()
        .lower()
    )

    for record in load_components():
        saved_number = str(
            record.get(
                "component_number",
                "",
            )
        ).strip().lower()

        if saved_number == requested_number:
            return record

    return None


def update_component(
    component_number: str,
    updated_data: dict[str, Any],
) -> bool:
    """Update an existing component record."""

    records = load_components()

    for index, record in enumerate(
        records
    ):
        if (
            record.get("component_number")
            == component_number
        ):
            updated_record = dict(record)

            updated_record.update(
                updated_data
            )

            updated_record[
                "component_number"
            ] = component_number

            records[index] = updated_record

            save_components(records)

            return True

    return False


def delete_component(
    component_number: str,
) -> bool:
    """Delete a component record."""

    records = load_components()

    remaining_records = [
        record
        for record in records
        if record.get(
            "component_number"
        ) != component_number
    ]

    if len(remaining_records) == len(records):
        return False

    save_components(
        remaining_records
    )

    return True


def component_summary() -> dict[str, Any]:
    """Generate basic component-library statistics."""

    records = load_components()

    station_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for record in records:
        station = str(
            record.get(
                "station",
                "Not recorded",
            )
        )

        category = str(
            record.get(
                "category",
                "Not recorded",
            )
        )

        station_counts[station] = (
            station_counts.get(
                station,
                0,
            )
            + 1
        )

        category_counts[category] = (
            category_counts.get(
                category,
                0,
            )
            + 1
        )

    return {
        "total_components": len(records),
        "station_counts": station_counts,
        "category_counts": category_counts,
    }