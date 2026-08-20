"""Reusable HTML-safe dashboard presentation components."""

from __future__ import annotations

from html import escape
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


def metric_card(
    *,
    icon: str,
    icon_class: str,
    label: str,
    value: Any,
    note: str,
    value_class: str = "",
) -> None:
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
