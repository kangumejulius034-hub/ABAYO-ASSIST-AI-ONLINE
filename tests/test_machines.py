from dataclasses import dataclass
from typing import Any

from core.machines import create_machine, machine_options, normalize_machine_status


@dataclass
class FakeResponse:
    data: list[dict[str, Any]]


class FakeQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client = client
        self.table = table
        self.value: Any = None

    def insert(self, value: Any) -> "FakeQuery":
        self.value = value
        return self

    def execute(self) -> FakeResponse:
        self.client.inserts.append((self.table, self.value))
        if self.table == "machine_modules" and self.client.fail_modules:
            raise RuntimeError("module table unavailable")
        if self.table == "machines":
            return FakeResponse([{**self.value, "id": 42}])
        return FakeResponse(self.value)


class FakeClient:
    def __init__(self, *, fail_modules: bool = False) -> None:
        self.fail_modules = fail_modules
        self.inserts: list[tuple[str, Any]] = []

    def table(self, name: str) -> FakeQuery:
        return FakeQuery(self, name)


def test_machine_options_keep_duplicate_names_distinct() -> None:
    machines = [
        {"id": 1, "machine_name": "Pakona", "model": "PFS-1"},
        {"id": 2, "machine_name": "Pakona", "model": "PFS-1"},
    ]

    options = machine_options(machines)

    assert options == [
        ("Pakona — PFS-1", 1),
        ("Pakona — PFS-1 (2)", 2),
    ]


def test_create_machine_reports_partial_module_failure() -> None:
    client = FakeClient(fail_modules=True)

    result = create_machine(
        client,
        machine_name="  Pakona A  ",
        status="unexpected",
    )

    assert result.machine["id"] == 42
    assert result.machine["machine_name"] == "Pakona A"
    assert result.machine["status"] == "Offline"
    assert not result.modules_created
    assert [table for table, _value in client.inserts] == [
        "machines",
        "machine_modules",
    ]


def test_status_normalization_is_case_insensitive() -> None:
    assert normalize_machine_status("maintenance") == "Maintenance"
    assert normalize_machine_status(None) == "Offline"
