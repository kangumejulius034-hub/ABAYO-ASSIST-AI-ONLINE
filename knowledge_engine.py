import json
import os
import re
from typing import Any


KNOWLEDGE_PATH = os.path.join("knowledge", "faults.json")

# Words that are too common to help identify a fault.
STOP_WORDS = {
    "the",
    "and",
    "but",
    "for",
    "with",
    "from",
    "this",
    "that",
    "machine",
    "station",
    "problem",
    "fault",
    "does",
    "not",
    "into",
    "when",
    "pouch",
}


def load_faults() -> list[dict[str, Any]]:
    """Load fault records from the local JSON knowledge base."""

    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "faults.json must contain a list of fault records."
        )

    return data


def clean_words(text: str) -> set[str]:
    """
    Convert text into useful lowercase search words.
    Punctuation and common words are removed.
    """

    words = re.findall(r"[a-zA-Z0-9]+", text.lower())

    return {
        word
        for word in words
        if len(word) > 2 and word not in STOP_WORDS
    }


def calculate_match_score(
    problem: str,
    selected_station: str,
    fault_record: dict[str, Any],
) -> int:
    """Calculate how closely one knowledge record matches the report."""

    problem_words = clean_words(problem)

    fault_description = fault_record.get("fault", "")
    fault_words = clean_words(fault_description)

    stored_station = str(
        fault_record.get("station", "")
    ).strip().lower()

    selected_station_text = selected_station.strip().lower()

    matching_words = problem_words.intersection(fault_words)

    # Each matching fault word is valuable.
    score = len(matching_words) * 3

    # Exact phrase match is even stronger.
    if fault_description.lower() in problem.lower():
        score += 5

    # Matching station improves an existing match.
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


def diagnose_fault(problem: str, station: str) -> dict:
    """
    Search the local knowledge base and return the best fault matches.
    """

    try:
        faults = load_faults()

    except FileNotFoundError:
        return {
            "station": station,
            "causes": [
                "The knowledge file could not be found."
            ],
            "checks": [
                "Confirm that knowledge/faults.json exists."
            ],
        }

    except json.JSONDecodeError:
        return {
            "station": station,
            "causes": [
                "The knowledge file contains invalid JSON."
            ],
            "checks": [
                "Check the commas, quotation marks and brackets "
                "inside faults.json."
            ],
        }

    except (OSError, ValueError) as error:
        return {
            "station": station,
            "causes": [
                f"The knowledge base could not be loaded: {error}"
            ],
            "checks": [
                "Check the structure and permissions of faults.json."
            ],
        }

    ranked_matches = []

    for fault in faults:
        score = calculate_match_score(
            problem=problem,
            selected_station=station,
            fault_record=fault,
        )

        # Require more than a station match alone.
        if score >= 3:
            ranked_matches.append(
                {
                    "score": score,
                    "fault": fault,
                }
            )

    ranked_matches.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    # Use the three strongest matching records only.
    best_matches = ranked_matches[:3]

    if not best_matches:
        return {
            "station": station,
            "matched_faults": [],
            "confidence": 0,
            "causes": [
                "No matching fault was found in the local knowledge base."
            ],
            "checks": [
                "State exactly what the machine should do.",
                "State what the machine does instead.",
                "Mention any HMI alarm.",
                "Check the relevant PLC input.",
                "Check the relevant PLC output.",
                "Record the confirmed fault in the knowledge base."
            ],
        }
    matched_faults = []
    matched_causes = []
    matched_checks = []

    highest_score = best_matches[0]["score"]

    confidence = min(
        100,
        max(
            30,
            highest_score * 10,
        ),
    )

    for match in best_matches:
        fault_record = match["fault"]

        matched_faults.append(
            fault_record.get("fault", "Unnamed fault")
        )

        matched_causes.extend(
            fault_record.get("possible_causes", [])
        )

        matched_checks.extend(
            fault_record.get("checks", [])
        )

    return {
    "station": station,
    "matched_faults": list(dict.fromkeys(matched_faults)),
    "causes": list(dict.fromkeys(matched_causes)),
    "checks": list(dict.fromkeys(matched_checks)),
    "confidence": confidence,
}