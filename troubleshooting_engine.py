import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent

TROUBLESHOOTING_FILE = (
    BASE_DIR
    / "knowledge"
    / "troubleshooting.json"
)


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
]


def _normalise_text(value: Any) -> str:
    """Convert a value into clean lowercase searchable text."""

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


def _expand_tokens(
    text: str,
) -> set[str]:
    """Add related industrial words to the search tokens."""

    normalised_text = _normalise_text(text)
    tokens = _tokenise(normalised_text)
    expanded = set(tokens)

    for group in SYNONYM_GROUPS:
        group_tokens = set()

        for phrase in group:
            group_tokens.update(
                _tokenise(phrase)
            )

        if tokens & group_tokens:
            expanded.update(group_tokens)

    return expanded


def _record_search_text(
    record: dict[str, Any],
) -> str:
    """Combine all troubleshooting fields into one search string."""

    fields = [
        record.get("fault"),
        record.get("cause"),
        record.get("inspection"),
        record.get("repair"),
        record.get("notes"),
        record.get("station"),
        record.get("keywords"),
        record.get("aliases"),
    ]

    values: list[str] = []

    for field in fields:
        if isinstance(field, list):
            values.extend(
                str(item)
                for item in field
            )

        elif field is not None:
            values.append(
                str(field)
            )

    return _normalise_text(
        " ".join(values)
    )


def _station_score(
    requested_station: str,
    saved_station: str,
) -> float:
    """Calculate a small station relevance bonus."""

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

    requested_tokens = _tokenise(
        requested
    )

    saved_tokens = _tokenise(
        saved
    )

    if requested_tokens & saved_tokens:
        return 5.0

    return -5.0


def calculate_troubleshooting_score(
    search_text: str,
    record: dict[str, Any],
    station: str = "",
) -> float:
    """Calculate a troubleshooting match score from 0 to 100."""

    query = _normalise_text(
        search_text
    )

    record_text = _record_search_text(
        record
    )

    if not query or not record_text:
        return 0.0

    query_tokens = _expand_tokens(
        query
    )

    record_tokens = _expand_tokens(
        record_text
    )

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

    fault_text = _normalise_text(
        record.get(
            "fault",
            "",
        )
    )

    sentence_similarity = SequenceMatcher(
        None,
        query,
        fault_text,
    ).ratio()

    score += sentence_similarity * 10.0

    score += _station_score(
        station,
        str(
            record.get(
                "station",
                "",
            )
        ),
    )

    return round(
        max(
            0.0,
            min(
                score,
                100.0,
            ),
        ),
        1,
    )


def load_troubleshooting() -> list[dict[str, Any]]:
    """Load all troubleshooting knowledge safely."""

    TROUBLESHOOTING_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not TROUBLESHOOTING_FILE.exists():
        save_troubleshooting([])
        return []

    try:
        with TROUBLESHOOTING_FILE.open(
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


def save_troubleshooting(
    records: list[dict[str, Any]],
) -> None:
    """Save all troubleshooting knowledge."""

    TROUBLESHOOTING_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with TROUBLESHOOTING_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False,
        )


def generate_solution_number(
    records: list[dict[str, Any]],
) -> str:
    """Generate the next permanent solution number."""

    highest_number = 0

    for record in records:
        solution_number = str(
            record.get(
                "solution_number",
                "",
            )
        )

        digits = "".join(
            character
            for character in solution_number
            if character.isdigit()
        )

        if digits:
            highest_number = max(
                highest_number,
                int(digits),
            )

    return f"TSH-{highest_number + 1:06d}"


def add_solution(
    fault: str,
    cause: str,
    inspection: str,
    repair: str,
    station: str,
    notes: str = "",
    image_paths: list[str] | None = None,
    keywords: list[str] | None = None,
    aliases: list[str] | None = None,
) -> str:
    """Add a new shared troubleshooting solution."""

    records = load_troubleshooting()

    solution_number = generate_solution_number(
        records
    )

    new_record = {
        "solution_number": solution_number,
        "station": station.strip(),
        "fault": fault.strip(),
        "cause": cause.strip(),
        "inspection": inspection.strip(),
        "repair": repair.strip(),
        "notes": notes.strip(),
        "keywords": keywords or [],
        "aliases": aliases or [],
        "image_paths": image_paths or [],
    }

    records.append(new_record)

    save_troubleshooting(records)

    return solution_number


def search_fault(
    text: str,
    station: str = "",
    limit: int = 10,
    minimum_score: float = 15.0,
) -> list[dict[str, Any]]:
    """
    Search troubleshooting records intelligently.

    This function remains compatible with the existing
    Smart Troubleshooter and Fault Diagnosis pages.
    """

    ranked_results: list[dict[str, Any]] = []

    for record in load_troubleshooting():
        score = calculate_troubleshooting_score(
            search_text=text,
            record=record,
            station=station,
        )

        if score < minimum_score:
            continue

        matched_record = dict(record)

        matched_record[
            "match_score"
        ] = score

        ranked_results.append(
            matched_record
        )

    ranked_results.sort(
        key=lambda item: item.get(
            "match_score",
            0,
        ),
        reverse=True,
    )

    return ranked_results[:limit]


def get_solution(
    solution_number: str,
) -> dict[str, Any] | None:
    """Retrieve one troubleshooting record by number."""

    requested_number = _normalise_text(
        solution_number
    )

    for record in load_troubleshooting():
        saved_number = _normalise_text(
            record.get(
                "solution_number",
                "",
            )
        )

        if saved_number == requested_number:
            return record

    return None