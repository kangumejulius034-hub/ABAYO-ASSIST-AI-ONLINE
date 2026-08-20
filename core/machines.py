"""Machine-domain operations kept separate from the Streamlit page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from core.constants import DEFAULT_MACHINE_MODULES, MACHINE_STATUSES


class MachineValidationError(ValueError):
    """Raised when machine input cannot be saved safely."""


@dataclass(frozen=True)
class CreateMachineResult:
    machine: dict[str, Any]
    modules_created: bool


def normalize_machine_status(value: Any) -> str:
    requested = str(value or "").strip().lower()
    for status in MACHINE_STATUSES:
        if requested == status.lower():
            return status
    return "Offline"


def machine_label(machine: dict[str, Any]) -> str:
    """Build a stable, readable label without using names as identity."""

    name = str(machine.get("machine_name") or "Unnamed Machine").strip()
    model = str(machine.get("model") or "").strip()
    location = str(machine.get("location") or "").strip()
    suffix = model or location or f"ID {machine.get('id', 'unknown')}"
    return f"{name} — {suffix}"


def machine_options(
    machines: Iterable[dict[str, Any]],
) -> list[tuple[str, Any]]:
    """Return unique display labels paired with true database IDs."""

    options: list[tuple[str, Any]] = []
    seen: dict[str, int] = {}

    for machine in machines:
        base_label = machine_label(machine)
        seen[base_label] = seen.get(base_label, 0) + 1
        label = base_label
        if seen[base_label] > 1:
            label = f"{base_label} ({seen[base_label]})"
        options.append((label, machine.get("id")))

    return options


def create_machine(
    client: Any,
    *,
    machine_name: str,
    manufacturer: str = "",
    model: str = "",
    location: str = "",
    description: str = "",
    status: str = "Online",
) -> CreateMachineResult:
    """Create a machine and its default module configuration."""

    clean_name = machine_name.strip()
    if not clean_name:
        raise MachineValidationError("Machine name is required.")

    response = (
        client.table("machines")
        .insert(
            {
                "machine_name": clean_name,
                "manufacturer": manufacturer.strip(),
                "model": model.strip(),
                "location": location.strip(),
                "description": description.strip(),
                "status": normalize_machine_status(status),
            }
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError("Supabase did not return the created machine.")

    machine = response.data[0]
    machine_id = machine.get("id")
    module_rows = [
        {
            "machine_id": machine_id,
            "module_name": module_name,
            "enabled": True,
        }
        for module_name in DEFAULT_MACHINE_MODULES
    ]

    try:
        client.table("machine_modules").insert(module_rows).execute()
    except Exception:
        return CreateMachineResult(machine=machine, modules_created=False)

    return CreateMachineResult(machine=machine, modules_created=True)
