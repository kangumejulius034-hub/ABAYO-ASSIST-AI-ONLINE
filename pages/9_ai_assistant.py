from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine import ClaudeGenerationError, configured_anthropic_api_key, configured_anthropic_model, generate_grounded_answer, has_grounding_evidence
from component_engine import search_components
from core.access import require_app_access
from core.machine_context import current_machine, is_pakona_machine, machine_display_name, machine_model_label, selected_machine_id
from knowledge_engine import diagnose_fault
from maintenance_engine import filter_maintenance_records
from recipe_engine import recipes_for_machine
from troubleshooting_engine import search_fault
from ui.sidebar import render_sidebar
from ui.theme import apply_theme

st.set_page_config(page_title="AI Assistant | ABAYO", page_icon="🤖", layout="wide")
apply_theme()
require_app_access()
render_sidebar()

machine = current_machine()
machine_id = selected_machine_id()
if not machine or machine_id in (None, ""):
    st.warning("Select or add a machine first.")
    st.stop()

machine_name = machine_display_name(machine)
machine_model = machine_model_label(machine)
legacy = is_pakona_machine(machine)

st.title("🤖 ABAYO AI Assistant")
st.caption(f"Active machine: {machine_name} • The assistant can only use evidence attached to this machine.")
st.warning("ABAYO does not replace lockout/tagout procedures or qualified electrical/mechanical inspection.")

station = st.text_input("Machine station", placeholder="Optional")
question = st.text_area("Ask about this machine", height=150, placeholder="Example: Why is the infeed sensor missing products intermittently?")


def _tokens(text: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def _recipe_matches(query: str) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    ranked: list[tuple[int, dict[str, Any]]] = []
    for recipe in recipes_for_machine(
        machine_id=machine_id,
        machine_model=machine_model,
        allow_legacy=legacy,
    ):
        text = " ".join(
            str(value)
            for value in (
                recipe.get("recipe_name"),
                recipe.get("status"),
                recipe.get("notes"),
                recipe.get("parameters"),
            )
            if value
        )
        score = len(query_tokens & _tokens(text))
        if score:
            ranked.append((score, recipe))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [recipe for _, recipe in ranked[:5]]


def _local_answer(results: dict[str, Any]) -> str:
    parts: list[str] = []
    troubleshooting = results.get("troubleshooting") or []
    maintenance = results.get("maintenance") or []
    components = results.get("components") or []
    fault_kb = results.get("fault_kb") or {}
    recipes = results.get("recipes") or []

    if troubleshooting:
        top = troubleshooting[0]
        parts.append(
            f"Closest troubleshooting record: **{top.get('fault', 'Unnamed fault')}**. "
            f"Cause: {top.get('cause', 'not recorded')}. Repair: {top.get('repair', 'not recorded')}."
        )
    if maintenance:
        top = maintenance[0]
        parts.append(
            f"Related maintenance: **{top.get('record_number', 'record')}** — "
            f"{top.get('fault', 'fault not recorded')}. Confirmed cause: "
            f"{top.get('confirmed_cause', 'not recorded')}."
        )
    if components:
        top = components[0]
        parts.append(
            f"Related component: **{top.get('component_name', 'Unnamed component')}**. "
            f"Common failures: {top.get('common_failures', 'not recorded')}."
        )
    if isinstance(fault_kb, dict) and fault_kb.get("matched_faults"):
        parts.append(
            "Fault knowledge matches: " + ", ".join(fault_kb.get("matched_faults", [])[:3]) + "."
        )
    if recipes:
        top = recipes[0]
        parts.append(f"Related recipe: **{top.get('recipe_name', 'Unnamed recipe')}**.")

    if not parts:
        return (
            f"I could not find matching evidence for {machine_name}. "
            "Record the observation in Fault Diagnosis, Maintenance, Components or the Troubleshooter, then ask again."
        )
    return "\n\n".join(parts)


if st.button("Ask ABAYO", type="primary", width="stretch"):
    if not question.strip():
        st.error("Enter a question first.")
    else:
        with st.spinner(f"Searching only {machine_name} knowledge..."):
            results = {
                "troubleshooting": search_fault(
                    question,
                    station=station,
                    limit=5,
                    minimum_score=10.0,
                    machine_id=machine_id,
                ),
                "maintenance": filter_maintenance_records(
                    station=station,
                    search_text=question,
                    machine_id=machine_id,
                )[:5],
                "components": search_components(
                    search_text=question,
                    station=station,
                    machine_id=machine_id,
                    allow_legacy=legacy,
                )[:5],
                "fault_kb": diagnose_fault(
                    question,
                    station,
                    machine_id=machine_id,
                    allow_legacy=legacy,
                ),
                "recipes": _recipe_matches(question),
            }

        local_answer = _local_answer(results)
        answer = local_answer

        try:
            api_key = configured_anthropic_api_key(st.secrets)
            model = configured_anthropic_model(st.secrets)
        except Exception:
            api_key = ""
            model = ""

        if api_key and has_grounding_evidence(results):
            try:
                answer = generate_grounded_answer(
                    question,
                    station,
                    results,
                    api_key=api_key,
                    model=model,
                )
            except ClaudeGenerationError:
                answer = local_answer

        st.subheader("Answer")
        st.write(answer)
        st.caption(f"Evidence scope: {machine_name} only • Machine ID: {machine_id}")

        with st.expander("Evidence used"):
            st.json(results)
