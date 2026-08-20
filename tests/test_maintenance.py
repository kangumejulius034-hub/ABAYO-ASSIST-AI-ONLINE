from maintenance_engine import calculate_summary


def test_maintenance_summary_uses_all_records() -> None:
    records = [
        {
            "fault": "Pouch not picked",
            "station": "Pouch picking station",
            "recipe_name": "500 g",
            "downtime_minutes": 2,
        },
        {
            "fault": "Pouch not picked",
            "station": "Pouch picking station",
            "recipe_name": "454 g",
            "downtime_minutes": 4,
        },
    ]

    summary = calculate_summary(records)

    assert summary["total_records"] == 2
    assert summary["total_downtime_minutes"] == 6.0
    assert summary["average_downtime_minutes"] == 3.0
    assert summary["most_repeated_fault"] == "Pouch not picked"
