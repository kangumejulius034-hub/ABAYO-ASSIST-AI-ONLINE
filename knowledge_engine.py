import re
from pathlib import Path
from typing import Any

from storage.json_store import load_json

KNOWLEDGE_PATH = Path(__file__).resolve().parent / "knowledge" / "faults.json"
STOP_WORDS = {
    "the", "and", "but", "for", "with", "from", "this", "that", "machine",
    "station", "problem", "fault", "does", "not", "into", "when", "pouch",
}


def _selected_scope(machine_id: Any | None, allow_legacy: bool) -> tuple[Any | None, bool]:
    if machine_id not in (None, ""):
        return machine_id, allow_legacy
    try:
        from core.machine_context import current_machine, is_pakona_machine, selected_machine_id
        selected_id = selected_machine_id()
        if selected_id in (None, ""):
            return machine_id, allow_legacy
        return selected_id, is_pakona_machine(current_machine())
    except Exception:
        return machine_id, allow_legacy


def load_faults() -> list[dict[str, Any]]:
    data = load_json(KNOWLEDGE_PATH, [])
    if not isinstance(data, list):
        raise ValueError("faults.json must contain a list of fault records.")
    return [record for record in data if isinstance(record, dict)]


def fault_belongs_to_machine(fault: dict[str, Any], *, machine_id=None, allow_legacy=False) -> bool:
    machine_id, allow_legacy = _selected_scope(machine_id, allow_legacy)
    saved_id = fault.get("machine_id")
    if machine_id in (None, ""):
        return True
    if saved_id not in (None, ""):
        return str(saved_id) == str(machine_id)
    return allow_legacy


def faults_for_machine(*, machine_id=None, allow_legacy=False) -> list[dict[str, Any]]:
    machine_id, allow_legacy = _selected_scope(machine_id, allow_legacy)
    return [fault for fault in load_faults() if fault_belongs_to_machine(fault, machine_id=machine_id, allow_legacy=allow_legacy)]


def clean_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def calculate_match_score(problem: str, selected_station: str, fault_record: dict[str, Any]) -> int:
    problem_words = clean_words(problem)
    description = str(fault_record.get("fault", ""))
    matching = problem_words.intersection(clean_words(description))
    score = len(matching) * 3
    if description and description.lower() in problem.lower():
        score += 5
    stored_station = str(fault_record.get("station", "")).strip().lower()
    selected = selected_station.strip().lower()
    if stored_station and selected and (stored_station == selected or stored_station in selected or selected in stored_station):
        score += 2
    return score


def diagnose_fault(problem: str, station: str, *, machine_id=None, allow_legacy=False) -> dict:
    machine_id, allow_legacy = _selected_scope(machine_id, allow_legacy)
    try:
        faults = faults_for_machine(machine_id=machine_id, allow_legacy=allow_legacy)
    except (OSError, ValueError) as error:
        return {"station": station, "causes": [f"The knowledge base could not be loaded: {error}"], "checks": ["Check the structure and permissions of faults.json."]}

    ranked = []
    for fault in faults:
        score = calculate_match_score(problem, station, fault)
        if score >= 3:
            ranked.append({"score": score, "fault": fault})
    ranked.sort(key=lambda item: item["score"], reverse=True)
    best = ranked[:3]
    if not best:
        return {
            "station": station,
            "matched_faults": [],
            "confidence": 0,
            "causes": ["No matching fault was found for the selected machine."],
            "checks": [
                "State exactly what the machine should do.",
                "State what the machine does instead.",
                "Mention any HMI alarm.",
                "Check the relevant PLC input.",
                "Check the relevant PLC output.",
                "Record the confirmed fault for this machine in the knowledge base.",
            ],
        }

    matched_faults = []
    causes = []
    checks = []
    confidence = min(100, max(30, best[0]["score"] * 10))
    for match in best:
        record = match["fault"]
        matched_faults.append(record.get("fault", "Unnamed fault"))
        causes.extend(record.get("possible_causes", []))
        checks.extend(record.get("checks", []))
    return {
        "station": station,
        "matched_faults": list(dict.fromkeys(matched_faults)),
        "causes": list(dict.fromkeys(causes)),
        "checks": list(dict.fromkeys(checks)),
        "confidence": confidence,
    }
