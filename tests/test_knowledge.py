import knowledge_engine
from storage.json_store import save_json


def test_diagnosis_returns_ranked_fault(monkeypatch, tmp_path) -> None:
    fault_file = tmp_path / "faults.json"
    save_json(
        fault_file,
        [
            {
                "station": "Pouch picking station",
                "fault": "Suction cups do not pick pouch",
                "possible_causes": ["Low vacuum pressure"],
                "checks": ["Inspect venturi pressure"],
            }
        ],
    )
    monkeypatch.setattr(knowledge_engine, "KNOWLEDGE_PATH", fault_file)

    result = knowledge_engine.diagnose_fault(
        "suction cups do not pick the pouch",
        "Pouch picking station",
    )

    assert result["matched_faults"] == ["Suction cups do not pick pouch"]
    assert result["causes"] == ["Low vacuum pressure"]
    assert result["confidence"] > 0
