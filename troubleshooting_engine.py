import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from storage.json_store import load_json, save_json

BASE_DIR = Path(__file__).resolve().parent
TROUBLESHOOTING_FILE = BASE_DIR / "knowledge" / "troubleshooting.json"

STOP_WORDS = {"a", "an", "and", "are", "at", "be", "being", "by", "for", "from", "in", "is", "it", "not", "of", "on", "or", "the", "to", "with"}
SYNONYM_GROUPS = [
    {"pouch", "pouches", "bag", "bags", "packet", "sachet"},
    {"pick", "picked", "picking", "pickup", "collect", "grip"},
    {"open", "opened", "opening", "widen", "widening", "spread"},
    {"vacuum", "suction", "venturi", "ejector"},
    {"dirty", "dust", "dusty", "powder", "contaminated"},
    {"blocked", "clogged", "obstructed", "restricted"},
    {"loose", "leaking", "leak", "disconnected", "slipping"},
    {"weight", "weighing", "mass", "gram", "grams"},
    {"fluctuating", "varying", "variation", "unstable", "inconsistent", "different"},
    {"seal", "sealing", "sealed", "heater", "temperature"},
    {"sensor", "sensing", "detector", "photoelectric", "proximity"},
    {"motor", "drive", "vfd", "rotation", "rotating"},
    {"air", "pneumatic", "pressure", "compressed"},
    {"auger", "screw", "dosing", "filling"},
    {"stirrer", "agitator", "mixer", "mixing"},
]


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


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"[^a-z0-9+\- ]+", " ", str(value).lower().strip())
    return re.sub(r"\s+", " ", text).strip()


def _tokenise(value: Any) -> set[str]:
    return {word for word in _normalise_text(value).split() if len(word) > 1 and word not in STOP_WORDS}


def _expand_tokens(text: str) -> set[str]:
    tokens = _tokenise(text)
    expanded = set(tokens)
    for group in SYNONYM_GROUPS:
        group_tokens = set()
        for phrase in group:
            group_tokens.update(_tokenise(phrase))
        if tokens & group_tokens:
            expanded.update(group_tokens)
    return expanded


def _record_search_text(record: dict[str, Any]) -> str:
    values: list[str] = []
    for field in ("fault", "cause", "inspection", "repair", "notes", "station", "keywords", "aliases"):
        value = record.get(field)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value is not None:
            values.append(str(value))
    return _normalise_text(" ".join(values))


def _station_score(requested_station: str, saved_station: str) -> float:
    requested = _normalise_text(requested_station)
    saved = _normalise_text(saved_station)
    if not requested:
        return 0.0
    if requested == saved:
        return 10.0
    if _tokenise(requested) & _tokenise(saved):
        return 5.0
    return -5.0


def calculate_troubleshooting_score(search_text: str, record: dict[str, Any], station: str = "") -> float:
    query = _normalise_text(search_text)
    record_text = _record_search_text(record)
    if not query or not record_text:
        return 0.0
    query_tokens = _expand_tokens(query)
    record_tokens = _expand_tokens(record_text)
    score = 45.0 if query in record_text else 0.0
    if query_tokens:
        score += (len(query_tokens & record_tokens) / len(query_tokens)) * 40.0
    score += SequenceMatcher(None, query, _normalise_text(record.get("fault", ""))).ratio() * 10.0
    score += _station_score(station, str(record.get("station", "")))
    return round(max(0.0, min(score, 100.0)), 1)


def load_troubleshooting() -> list[dict[str, Any]]:
    data = load_json(TROUBLESHOOTING_FILE, [])
    if not isinstance(data, list):
        return []
    return [record for record in data if isinstance(record, dict)]


def save_troubleshooting(records: list[dict[str, Any]]) -> None:
    save_json(TROUBLESHOOTING_FILE, records)


def record_belongs_to_machine(record: dict[str, Any], machine_id: Any | None, allow_legacy: bool) -> bool:
    saved_id = record.get("machine_id")
    if machine_id in (None, ""):
        return True
    if saved_id not in (None, ""):
        return str(saved_id) == str(machine_id)
    return allow_legacy


def generate_solution_number(records: list[dict[str, Any]]) -> str:
    highest = 0
    for record in records:
        digits = "".join(c for c in str(record.get("solution_number", "")) if c.isdigit())
        if digits:
            highest = max(highest, int(digits))
    return f"TSH-{highest + 1:06d}"


def add_solution(fault: str, cause: str, inspection: str, repair: str, station: str, notes: str = "", image_paths: list[str] | None = None, keywords: list[str] | None = None, aliases: list[str] | None = None, *, machine_id: Any | None = None) -> str:
    selected_id, _, model = _selected_scope(machine_id)
    records = load_troubleshooting()
    number = generate_solution_number(records)
    records.append({
        "machine_id": selected_id,
        "machine_model": model,
        "solution_number": number,
        "station": station.strip(),
        "fault": fault.strip(),
        "cause": cause.strip(),
        "inspection": inspection.strip(),
        "repair": repair.strip(),
        "notes": notes.strip(),
        "keywords": keywords or [],
        "aliases": aliases or [],
        "image_paths": image_paths or [],
    })
    save_troubleshooting(records)
    return number


def search_fault(text: str, station: str = "", limit: int = 10, minimum_score: float = 15.0, *, machine_id: Any | None = None) -> list[dict[str, Any]]:
    selected_id, allow_legacy, _ = _selected_scope(machine_id)
    ranked = []
    for record in load_troubleshooting():
        if not record_belongs_to_machine(record, selected_id, allow_legacy):
            continue
        score = calculate_troubleshooting_score(text, record, station)
        if score < minimum_score:
            continue
        matched = dict(record)
        matched["match_score"] = score
        ranked.append(matched)
    ranked.sort(key=lambda item: item.get("match_score", 0), reverse=True)
    return ranked[:limit]


def get_solution(solution_number: str, *, machine_id: Any | None = None) -> dict[str, Any] | None:
    selected_id, allow_legacy, _ = _selected_scope(machine_id)
    requested = _normalise_text(solution_number)
    for record in load_troubleshooting():
        if not record_belongs_to_machine(record, selected_id, allow_legacy):
            continue
        if _normalise_text(record.get("solution_number", "")) == requested:
            return record
    return None
