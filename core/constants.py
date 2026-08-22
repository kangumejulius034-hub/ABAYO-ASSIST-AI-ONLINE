"""Shared constants used by the ABAYO application."""

from __future__ import annotations

APP_NAME = "ABAYO"
APP_VERSION = "0.7.1"

MACHINE_STATUSES = ("Online", "Offline", "Maintenance")
SUPPORTED_MACHINE_MODELS = ("Pakona PFS AG",)

DEFAULT_MACHINE_MODULES = (
    "Machine Overview",
    "Fault Diagnosis",
    "Recipe Library",
    "Maintenance History",
    "Smart Troubleshooter",
    "Machine Components",
)

STATIONS = (
    "General machine problem",
    "Pouch elevator",
    "Pouch picking station",
    "Pouch opening station",
    "Filling station",
    "Auger and stirrer",
    "Incline screw",
    "Sealing station",
    "Electrical system",
    "Pneumatic system",
)
