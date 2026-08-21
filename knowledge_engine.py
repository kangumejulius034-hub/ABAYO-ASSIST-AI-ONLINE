import re
from pathlib import Path
from typing import Any

from storage.json_store import load_json


KNOWLEDGE_PATH = Path(__file__).resolve().parent / "knowledge" / "faults.json"

STOP_WORDS = {
    "the", "and", "but", "for", "with", "from", "this", "that", "machine",
    "station", "problem", "fault", "does", "not", "into", "when", "pouch",
}


def load_faults() -> list[dict[str, Any]]:
    data = load_json(KNOWLEDGE_PATH, [])
    if not isinstance(data, list):
        raise ValueError("faults.json must contain a list of fault records.")
    return [record for record in data if isinstance(record, dict)]


def fault_belongs_to_machine(
    fault: dict[str, Any],
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> bool:
    saved_id = fault.get("machine_id")
    if machine_id in (None, ""):
        return True
    if saved_id not in (None, ""):
        return str(saved_id) == str(machine_id)
    return allow_legacy


def faults_for_machine(
    *, machine_id: Any | None, allow_legacy: bool = False
) -> list[dict[str, Any]]:
    return [
        fault
        for fault in load_faults()
        if fault_belongs_to_machine(
            fault, machine_id=machine_id, allow_legacy=allow_legacy
        )
    ]


def clean_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def calculate_match_score(
    problem: str,
    selected_station: str,
    fault_record: dict[str, Any],
) -> int:
    problem_words = clean_words(problem)
    fault_description = str(fault_record.get("fault", ""))
    fault_words = clean_words(fault_description)
    stored_station = str(fault_record.get("station", "")).strip().lower()
    selected_station_text = selected_station.strip().lower()
    matching_words = problem_words.intersection(fault_words)
    score = len(matching_words) * 3

    if fault_description and fault_description.lower() in problem.lower():
        score += 5

    if (
        stored_station
        and selected_station_text
        and (
            stored_station == selected_station_text
            or stored_station in selected_station_text
            or selected_station_text in stored_station
        )
    ):
        score += 2
    return score


def diagnose_fault(
    problem: str,
    station: str,
    *,
    machine_id: Any | None = None,
    allow_legacy: bool = False,
) -> dict:
    """Search only fault knowledge belonging to the selected machine."""

    try:
        faults = faults_for_machine(
            machine_id=machine_id,
            allow_legacy=allow_legacy,
        )
    except (OSError, ValueError) as error:
        return {
            "station": station,
            "causes": [f"The knowledge base could not be loaded: {error}"],
            "checks": ["Check the structure and permissions of faults.json."],
        }

    ranked_matches = []
    for fault in faults:
        score = calculate_match_score(problem, station, fault)
        if score >= 3:
            ranked_matches.append({"score": score, "fault": fault})

    ranked_matches.sort(key=lambda item: item["score"], reverse=True)
    best_matches = ranked_matches[:3]

    if not best_matches:
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

    matched_faults: list[str] = []
    matched_causes: list[str] = []
    matched_checks: list[str] = []
    highest_score = best_matches[0]["score"]
    confidence = min(100, max(30, highest_score * 10))

    for match in best_matches:
        fault_record = match["fault"]
        matched_faults.append(fault_record.get("fault", "Unnamed fault"))
        matched_causes.extend(fault_record.get("possible_causes", []))
        matched_checks.extend(fault_record.get("checks", []))

    return {
        "station": station,
        "matched_faults": list(dict.fromkeys(matched_faults)),
        "causes": list(dict.fromkeys(matched_causes)),
        "checks": list(dict.fromkeys(matched_checks)),
        "confidence": confidence,
    }
