import re
from difflib import SequenceMatcher
from typing import Any

from component_engine import load_components
from maintenance_engine import filter_maintenance_records
from troubleshooting_engine import search_fault


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "being",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "not",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


SYNONYM_GROUPS = [
    {
        "pouch",
        "pouches",
        "bag",
        "bags",
        "packet",
        "sachet",
    },
    {
        "pick",
        "picked",
        "picking",
        "pickup",
        "collect",
        "grip",
    },
    {
        "open",
        "opened",
        "opening",
        "widen",
        "widening",
        "spread",
    },
    {
        "vacuum",
        "suction",
        "venturi",
        "ejector",
    },
    {
        "dirty",
        "dust",
        "dusty",
        "powder",
        "contaminated",
    },
    {
        "blocked",
        "clogged",
        "obstructed",
        "restricted",
    },
    {
        "loose",
        "leaking",
        "leak",
        "disconnected",
        "slipping",
    },
    {
        "weight",
        "weighing",
        "mass",
        "gram",
        "grams",
    },
    {
        "fluctuating",
        "varying",
        "variation",
        "unstable",
        "inconsistent",
        "different",
    },
    {
        "seal",
        "sealing",
        "sealed",
        "heater",
        "temperature",
    },
    {
        "sensor",
        "sensing",
        "detector",
        "photoelectric",
        "proximity",
    },
    {
        "motor",
        "drive",
        "vfd",
        "rotation",
        "rotating",
    },
    {
        "air",
        "pneumatic",
        "pressure",
        "compressed",
    },
    {
        "auger",
        "screw",
        "dosing",
        "filling",
    },
    {
        "stirrer",
        "agitator",
        "mixer",
        "mixing",
    },
    {
        "cup",
        "cups",
        "suction cup",
        "vacuum cup",
    },
    {
        "hose",
        "pipe",
        "tube",
        "airline",
        "vacuum line",
    },
]


def _normalise_text(value: Any) -> str:
    """Convert a value into clean searchable text."""

    if value is None:
        return ""

    text = str(value).lower().strip()

    text = re.sub(
        r"[^a-z0-9+\- ]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _tokenise(value: Any) -> set[str]:
    """Convert text into useful search words."""

    text = _normalise_text(value)

    return {
        word
        for word in text.split()
        if len(word) > 1
        and word not in STOP_WORDS
    }


def _expand_tokens(value: Any) -> set[str]:
    """Add related industrial words to search tokens."""

    tokens = _tokenise(value)
    expanded = set(tokens)

    for group in SYNONYM_GROUPS:
        group_tokens: set[str] = set()

        for phrase in group:
            group_tokens.update(
                _tokenise(phrase)
            )

        if tokens & group_tokens:
            expanded.update(group_tokens)

    return expanded


def _station_bonus(
    requested_station: str,
    saved_station: str,
) -> float:
    """Calculate relevance from the selected machine station."""

    requested = _normalise_text(
        requested_station
    )

    saved = _normalise_text(
        saved_station
    )

    if not requested:
        return 0.0

    if requested == saved:
        return 10.0

    if (
        _tokenise(requested)
        & _tokenise(saved)
    ):
        return 5.0

    return -5.0


# ---------------------------------------------------------
# MAINTENANCE SEARCH
# ---------------------------------------------------------

def _maintenance_record_text(
    record: dict[str, Any],
) -> str:
    """Combine maintenance fields into searchable text."""

    fields = [
        record.get("fault"),
        record.get("fault_description"),
        record.get("confirmed_cause"),
        record.get("corrective_action"),
        record.get("notes"),
        record.get("station"),
        record.get("recipe"),
        record.get("recipe_name"),
        record.get("production_status"),
        record.get("batch_number"),
    ]

    return _normalise_text(
        " ".join(
            str(value)
            for value in fields
            if value is not None
        )
    )


def _maintenance_match_score(
    search_text: str,
    record: dict[str, Any],
    station: str = "",
) -> float:
    """Calculate maintenance relevance from 0 to 100."""

    query = _normalise_text(search_text)
    record_text = _maintenance_record_text(record)

    if not query or not record_text:
        return 0.0

    query_tokens = _expand_tokens(query)
    record_tokens = _expand_tokens(record_text)

    score = 0.0

    if query in record_text:
        score += 45.0

    if query_tokens:
        shared_tokens = (
            query_tokens
            & record_tokens
        )

        coverage = (
            len(shared_tokens)
            / len(query_tokens)
        )

        score += coverage * 40.0

    record_fault = _normalise_text(
        record.get("fault")
        or record.get("fault_description")
        or ""
    )

    similarity = SequenceMatcher(
        None,
        query,
        record_fault,
    ).ratio()

    score += similarity * 10.0

    score += _station_bonus(
        station,
        str(record.get("station", "")),
    )

    return round(
        max(
            0.0,
            min(score, 100.0),
        ),
        1,
    )


def _load_maintenance_records(
    station: str = "",
) -> list[dict[str, Any]]:
    """Load maintenance records safely."""

    attempts = [
        {
            "station": station,
            "search_text": "",
        },
        {
            "station": station,
        },
        {},
    ]

    for arguments in attempts:
        try:
            records = filter_maintenance_records(
                **arguments
            )

            if isinstance(records, list):
                return records

        except TypeError:
            continue

        except Exception:
            return []

    return []


def search_related_maintenance(
    fault_text: str,
    station: str = "",
    limit: int = 5,
    minimum_score: float = 15.0,
) -> list[dict[str, Any]]:
    """Search and rank previous maintenance records."""

    records = _load_maintenance_records(
        station=station
    )

    ranked_records: list[dict[str, Any]] = []

    for record in records:
        score = _maintenance_match_score(
            search_text=fault_text,
            record=record,
            station=station,
        )

        if score < minimum_score:
            continue

        matched_record = dict(record)
        matched_record["match_score"] = score

        ranked_records.append(
            matched_record
        )

    ranked_records.sort(
        key=lambda item: item.get(
            "match_score",
            0,
        ),
        reverse=True,
    )

    return ranked_records[:limit]


# ---------------------------------------------------------
# COMPONENT SEARCH
# ---------------------------------------------------------

def _component_record_text(
    record: dict[str, Any],
) -> str:
    """Combine component information into searchable text."""

    related_faults = record.get(
        "related_faults",
        [],
    )

    if isinstance(related_faults, list):
        related_fault_text = " ".join(
            str(item)
            for item in related_faults
        )
    else:
        related_fault_text = str(
            related_faults
        )

    fields = [
        record.get("component_number"),
        record.get("component_name"),
        record.get("station"),
        record.get("category"),
        record.get("manufacturer"),
        record.get("model_number"),
        record.get("part_number"),
        record.get("function"),
        record.get("common_failures"),
        record.get("fault_symptoms"),
        record.get("inspection_procedure"),
        record.get("replacement_procedure"),
        record.get("safety_notes"),
        related_fault_text,
    ]

    return _normalise_text(
        " ".join(
            str(value)
            for value in fields
            if value is not None
        )
    )


def _component_match_score(
    search_text: str,
    record: dict[str, Any],
    station: str = "",
) -> float:
    """Calculate component relevance from 0 to 100."""

    query = _normalise_text(
        search_text
    )

    component_text = _component_record_text(
        record
    )

    if not query or not component_text:
        return 0.0

    query_tokens = _expand_tokens(
        query
    )

    component_tokens = _expand_tokens(
        component_text
    )

    score = 0.0

    if query in component_text:
        score += 40.0

    if query_tokens:
        shared_tokens = (
            query_tokens
            & component_tokens
        )

        coverage = (
            len(shared_tokens)
            / len(query_tokens)
        )

        score += coverage * 40.0

    component_name = _normalise_text(
        record.get(
            "component_name",
            "",
        )
    )

    name_similarity = SequenceMatcher(
        None,
        query,
        component_name,
    ).ratio()

    score += name_similarity * 10.0

    related_faults = record.get(
        "related_faults",
        [],
    )

    if isinstance(related_faults, list):
        related_fault_text = _normalise_text(
            " ".join(
                str(item)
                for item in related_faults
            )
        )
    else:
        related_fault_text = _normalise_text(
            related_faults
        )

    if query in related_fault_text:
        score += 10.0

    score += _station_bonus(
        station,
        str(record.get("station", "")),
    )

    return round(
        max(
            0.0,
            min(score, 100.0),
        ),
        1,
    )


def search_related_components(
    fault_text: str,
    station: str = "",
    limit: int = 5,
    minimum_score: float = 15.0,
) -> list[dict[str, Any]]:
    """Search and rank machine components related to a fault."""

    try:
        records = load_components()
    except Exception:
        records = []

    if not isinstance(records, list):
        records = []

    ranked_components: list[dict[str, Any]] = []

    for record in records:
        score = _component_match_score(
            search_text=fault_text,
            record=record,
            station=station,
        )

        if score < minimum_score:
            continue

        matched_component = dict(record)
        matched_component["match_score"] = score

        ranked_components.append(
            matched_component
        )

    ranked_components.sort(
        key=lambda item: item.get(
            "match_score",
            0,
        ),
        reverse=True,
    )

    return ranked_components[:limit]


# ---------------------------------------------------------
# SHARED SEARCH
# ---------------------------------------------------------

def search_all_knowledge(
    fault_text: str,
    station: str = "",
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """
    Search troubleshooting knowledge, maintenance history
    and machine components together.
    """

    troubleshooting_results = search_fault(
        text=fault_text,
        station=station,
        limit=limit,
        minimum_score=15.0,
    )

    maintenance_results = search_related_maintenance(
        fault_text=fault_text,
        station=station,
        limit=limit,
        minimum_score=15.0,
    )

    component_results = search_related_components(
        fault_text=fault_text,
        station=station,
        limit=limit,
        minimum_score=15.0,
    )

    return {
        "troubleshooting": troubleshooting_results,
        "maintenance": maintenance_results,
        "components": component_results,
    }


# ---------------------------------------------------------
# RECORD HELPERS
# ---------------------------------------------------------

def get_record_fault(
    record: dict[str, Any],
) -> str:
    """Return the saved fault description."""

    return str(
        record.get("fault")
        or record.get("fault_description")
        or "Unnamed fault"
    )


def get_record_number(
    record: dict[str, Any],
) -> str:
    """Return a saved record number."""

    return str(
        record.get("record_number")
        or record.get("maintenance_number")
        or record.get("solution_number")
        or record.get("component_number")
        or record.get("id")
        or "Record"
    )


def get_record_recipe(
    record: dict[str, Any],
) -> str:
    """Return the affected recipe."""

    return str(
        record.get("recipe_name")
        or record.get("recipe")
        or "Not recipe-related"
    )


def get_record_images(
    record: dict[str, Any],
) -> list[str]:
    """Return saved image paths."""

    image_paths = (
        record.get("image_paths")
        or record.get("images")
        or record.get("photo_paths")
        or []
    )

    if isinstance(image_paths, list):
        return image_paths

    if (
        isinstance(image_paths, str)
        and image_paths.strip()
    ):
        return [image_paths]

    return []