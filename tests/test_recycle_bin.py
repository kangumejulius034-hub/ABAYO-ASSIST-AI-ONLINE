from datetime import datetime, timedelta, timezone

import recycle_bin_engine


def test_timestamp_parsing_accepts_zulu_time() -> None:
    parsed = recycle_bin_engine.parse_timestamp("2026-08-20T10:30:00Z")

    assert parsed == datetime(2026, 8, 20, 10, 30, tzinfo=timezone.utc)


def test_days_remaining_rounds_partial_days_up(monkeypatch) -> None:
    deleted_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        recycle_bin_engine,
        "utc_now",
        lambda: deleted_at + timedelta(days=29, hours=12),
    )

    assert recycle_bin_engine.days_until_permanent_deletion(deleted_at) == 1
