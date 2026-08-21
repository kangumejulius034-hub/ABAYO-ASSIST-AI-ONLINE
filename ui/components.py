"""Reusable HTML-safe dashboard presentation components."""

from __future__ import annotations

from html import escape
import re
from typing import Any

import streamlit as st


def _text(value: Any, fallback: str = "") -> str:
    return escape(str(value if value not in (None, "") else fallback))


def page_header(title: str, subtitle: str = "") -> None:
    st.html(
        f'<div class="page-heading">{_text(title)}</div>'
        f'<div class="page-subtitle">{_text(subtitle)}</div>'
    )


def section_heading(title: str) -> None:
    st.html(f'<div class="section-heading">{_text(title)}</div>')


def _operational_metric(
    label: str,
    value: Any,
    note: str,
    value_class: str,
) -> tuple[str, Any, str, str]:
    """Translate raw dashboard counters into operator-friendly states.

    The Home page should communicate whether the factory needs attention rather
    than exposing database record totals. Detailed counts remain available in
    the individual feature pages and later analytics/reporting views.
    """

    if label == "Machines Online":
        try:
            online_count = int(value)
        except (TypeError, ValueError):
            online_count = 0

        total_match = re.search(r"of\s+(\d+)\s+registered", str(note), re.I)
        total_count = int(total_match.group(1)) if total_match else 0

        if total_count == 0:
            return (
                "Fleet Health",
                "No Machines",
                "Add a machine to begin monitoring operations",
                "",
            )

        if online_count == total_count:
            return (
                "Fleet Health",
                "All Online",
                "All registered machines are operational",
                "connected",
            )

        if online_count == 0:
            return (
                "Fleet Health",
                "Attention",
                "No registered machine is currently marked online",
                "offline",
            )

        return (
            "Fleet Health",
            "Attention",
            "One or more machines need status review",
            "offline",
        )

    if label == "Fault Records":
        try:
            has_fault_knowledge = int(value) > 0
        except (TypeError, ValueError):
            has_fault_knowledge = bool(value)

        if has_fault_knowledge:
            return (
                "Fault Intelligence",
                "Available",
                "Verified fault knowledge is available for diagnosis",
                "connected",
            )

        return (
            "Fault Intelligence",
            "Building",
            "Add verified fault knowledge as issues are confirmed",
            "",
        )

    if label == "Maintenance Records":
        try:
            has_history = int(value) > 0
        except (TypeError, ValueError):
            has_history = bool(value)

        if has_history:
            return (
                "Maintenance",
                "History Available",
                "Recorded service history is available",
                "connected",
            )

        return (
            "Maintenance",
            "No History Yet",
            "Maintenance activity will appear after it is recorded",
            "",
        )

    return label, value, note, value_class


def metric_card(
    *,
    icon: str,
    icon_class: str,
    label: str,
    value: Any,
    note: str,
    value_class: str = "",
) -> None:
    label, value, note, value_class = _operational_metric(
        label,
        value,
        note,
        value_class,
    )

    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-icon {_text(icon_class)}">{_text(icon)}</div>
            <div class="metric-label">{_text(label)}</div>
            <div class="metric-value {_text(value_class)}">{_text(value)}</div>
            <div class="metric-note">{_text(note)}</div>
        </div>
        """
    )


def machine_card(machine: dict[str, Any]) -> None:
    status = str(machine.get("status") or "Unknown")
    status_key = status.lower()
    status_class = (
        status_key if status_key in {"online", "offline", "maintenance"} else "offline"
    )

    st.html(
        f"""
        <div class="machine-card">
            <div class="machine-header">
                <div class="machine-icon">🏭</div>
                <div>
                    <div class="machine-name">{_text(machine.get('machine_name'), 'Unnamed Machine')}</div>
                    <div class="machine-description">{_text(machine.get('description'), 'Industrial production machine')}</div>
                </div>
            </div>
            <div class="machine-details">
                <div class="machine-detail">
                    <div class="detail-label">Manufacturer</div>
                    <div class="detail-value">{_text(machine.get('manufacturer'), 'Not recorded')}</div>
                </div>
                <div class="machine-detail">
                    <div class="detail-label">Model</div>
                    <div class="detail-value">{_text(machine.get('model'), 'Not recorded')}</div>
                </div>
                <div class="machine-detail">
                    <div class="detail-label">Location</div>
                    <div class="detail-value">{_text(machine.get('location'), 'Not recorded')}</div>
                </div>
                <div class="machine-detail">
                    <div class="detail-label">Knowledge Scope</div>
                    <div class="detail-value">This machine only</div>
                </div>
            </div>
            <div class="machine-status {_text(status_class)}">● {_text(status)}</div>
        </div>
        """
    )


def action_card(*, icon: str, title: str, note: str) -> None:
    st.html(
        f"""
        <div class="action-card">
            <div class="action-icon">{_text(icon)}</div>
            <div class="action-title">{_text(title)}</div>
            <div class="action-note">{_text(note)}</div>
        </div>
        """
    )
