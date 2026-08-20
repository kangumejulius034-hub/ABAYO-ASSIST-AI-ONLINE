import json

from storage.json_store import load_json, save_json


def test_json_store_round_trip_and_invalid_fallback(tmp_path) -> None:
    path = tmp_path / "data.json"
    payload = [{"name": "Pakona", "weight": 500}]

    save_json(path, payload)

    assert load_json(path, []) == payload
    assert path.read_text(encoding="utf-8").endswith("\n")

    path.write_text("{not valid json", encoding="utf-8")
    assert load_json(path, ["fallback"]) == ["fallback"]


def test_json_store_writes_valid_unicode(tmp_path) -> None:
    path = tmp_path / "unicode.json"
    save_json(path, {"status": "Pouch ✓"})

    assert json.loads(path.read_text(encoding="utf-8")) == {"status": "Pouch ✓"}
