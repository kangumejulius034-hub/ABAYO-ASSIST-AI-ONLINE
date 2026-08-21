import re
import sys
from pathlib import Path
from typing import Any

import streamlit as st


# ---------------------------------------------------------
# PROJECT PATH SETUP
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# ENGINE IMPORTS
# ---------------------------------------------------------

from core.access import require_app_access
from core.constants import STATIONS as MACHINE_STATIONS

from ai_engine import (
    ClaudeGenerationError,
    configured_anthropic_api_key,
    configured_anthropic_model,
    generate_grounded_answer,
    has_grounding_evidence,
)
from knowledge_engine import diagnose_fault
from maintenance_engine import calculate_summary, filter_maintenance_records
from recipe_engine import load_recipes
from shared_knowledge_engine import (
    get_record_fault,
    get_record_number,
    get_record_recipe,
    search_related_components,
    search_related_maintenance,
)
from troubleshooting_engine import search_fault

from ui.components import page_header, section_heading
from ui.sidebar import render_sidebar
from ui.theme import apply_theme


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="AI Assistant | ABAYO",
    page_icon="🤖",
    layout="wide",
)
apply_theme()
require_app_access()
render_sidebar()


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

STATIONS = ["All stations"] + list(MACHINE_STATIONS)

SCOPE_LABELS = {
    "maintenance": "Maintenance History",
    "troubleshooting": "Shared Troubleshooting",
    "components": "Machine Components",
    "fault_kb": "Fault Knowledge Base",
    "recipes": "Recipe Library",
}

STOP_WORDS = {
    "a", "an", "and", "any", "are", "at", "be", "by", "did", "do", "does",
    "for", "from", "has", "have", "how", "in", "is", "it", "many", "me",
    "of", "on", "or", "our", "show", "tell", "that", "the", "there", "this",
    "to", "us", "was", "we", "were", "what", "when", "which", "who", "why",
    "with", "you",
}

EXAMPLE_QUESTIONS = [
    "Why do pouches fail to get picked at the pouch picking station?",
    "What's the most repeated fault in maintenance history?",
    "How much total downtime have we recorded?",
    "Which station is most affected by faults?",
]

ANALYTIC_KEYWORDS = {
    "total_records": [
        "how many maintenance records",
        "how many records",
        "total records",
        "number of maintenance",
    ],
    "most_repeated_fault": [
        "most common fault",
        "most repeated fault",
        "most frequent fault",
        "recurring fault",
        "top fault",
    ],
    "most_affected_station": [
        "most affected station",
        "worst station",
        "which station",
    ],
    "most_affected_recipe": [
        "most affected recipe",
        "which recipe",
    ],
    "total_downtime": [
        "total downtime",
        "how much downtime",
        "overall downtime",
    ],
    "average_downtime": [
        "average downtime",
        "average time",
    ],
}


# ---------------------------------------------------------
# LOCAL SEARCH HELPERS
# ---------------------------------------------------------

def _tokenise(text: Any) -> set[str]:
    """Convert text into simple lowercase search words."""

    words = re.findall(r"[a-z0-9]+", str(text).lower())
    return {word for word in words if len(word) > 1 and word not in STOP_WORDS}


def search_recipes(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Keyword search across the recipe library."""

    query_tokens = _tokenise(query)

    if not query_tokens:
        return []

    ranked: list[tuple[int, dict[str, Any]]] = []

    for recipe in load_recipes():
        parameters = recipe.get("parameters") or {}

        if isinstance(parameters, dict):
            parameter_text = " ".join(
                f"{key} {value}" for key, value in parameters.items()
            )
        else:
            parameter_text = str(parameters)

        record_text = " ".join(
            str(value)
            for value in [
                recipe.get("recipe_name"),
                recipe.get("machine_model"),
                recipe.get("status"),
                recipe.get("notes"),
                parameter_text,
            ]
            if value
        )

        shared_tokens = query_tokens & _tokenise(record_text)

        if not shared_tokens:
            continue

        ranked.append((len(shared_tokens), recipe))

    ranked.sort(key=lambda item: item[0], reverse=True)

    return [recipe for _, recipe in ranked[:limit]]


def detect_analytics_intent(question: str) -> set[str]:
    """Detect whether the question is asking for a maintenance statistic."""

    lowered = question.lower()
    matched: set[str] = set()

    for key, phrases in ANALYTIC_KEYWORDS.items():
        if any(phrase in lowered for phrase in phrases):
            matched.add(key)

    return matched


def build_analytics_answer(
    matched_keys: set[str],
    station_filter: str,
) -> tuple[str, dict[str, Any]]:
    """Answer a statistics question straight from maintenance history."""

    station = "" if station_filter == "All stations" else station_filter
    records = filter_maintenance_records(station=station)
    summary = calculate_summary(records)

    lines: list[str] = []

    scope_note = f" for **{station_filter}**" if station else ""

    if "total_records" in matched_keys:
        lines.append(
            f"There are **{summary['total_records']}** maintenance "
            f"records{scope_note} in local history."
        )

    if "most_repeated_fault" in matched_keys:
        lines.append(
            f"The most repeated fault{scope_note} is "
            f"**{summary['most_repeated_fault']}**."
        )

    if "most_affected_station" in matched_keys:
        lines.append(
            f"The most affected station is "
            f"**{summary['most_affected_station']}**."
        )

    if "most_affected_recipe" in matched_keys:
        lines.append(
            f"The most affected recipe{scope_note} is "
            f"**{summary['most_affected_recipe']}**."
        )

    if "total_downtime" in matched_keys:
        lines.append(
            f"Total recorded downtime{scope_note} is "
            f"**{summary['total_downtime_minutes']} minutes**."
        )

    if "average_downtime" in matched_keys:
        lines.append(
            f"Average downtime per record{scope_note} is "
            f"**{summary['average_downtime_minutes']} minutes**."
        )

    if not lines:
        lines.append("I couldn't compute that statistic yet.")

    return " ".join(lines), summary


def run_knowledge_search(
    question: str,
    station_filter: str,
    scopes: list[str],
) -> dict[str, Any]:
    """Search every local knowledge source ABAYO currently has."""

    station = "" if station_filter == "All stations" else station_filter
    results: dict[str, Any] = {}

    if "troubleshooting" in scopes:
        results["troubleshooting"] = search_fault(
            text=question,
            station=station,
            limit=5,
            minimum_score=12.0,
        )

    if "maintenance" in scopes:
        results["maintenance"] = search_related_maintenance(
            fault_text=question,
            station=station,
            limit=5,
            minimum_score=12.0,
        )

    if "components" in scopes:
        results["components"] = search_related_components(
            fault_text=question,
            station=station,
            limit=5,
            minimum_score=12.0,
        )

    if "fault_kb" in scopes:
        results["fault_kb"] = diagnose_fault(
            problem=question,
            station=station,
        )

    if "recipes" in scopes:
        results["recipes"] = search_recipes(question, limit=5)

    return results


def synthesize_answer(results: dict[str, Any]) -> str:
    """Turn raw search results into one readable answer."""

    parts: list[str] = []

    troubleshooting = results.get("troubleshooting") or []
    maintenance = results.get("maintenance") or []
    components = results.get("components") or []
    fault_kb = results.get("fault_kb") or {}
    recipes = results.get("recipes") or []

    if troubleshooting:
        top = troubleshooting[0]
        score = top.get("match_score")
        score_text = f" ({score}% match)" if score is not None else ""

        parts.append(
            f"The closest shared troubleshooting match is "
            f"**{top.get('fault', 'Unnamed fault')}**{score_text}. "
            f"Likely cause: {top.get('cause', 'not recorded')}. "
            f"Fix: {top.get('repair', 'not recorded')}."
        )

    if maintenance:
        top = maintenance[0]

        parts.append(
            f"This has happened before — record "
            f"**{get_record_number(top)}** on "
            f"{top.get('machine_model', 'an unrecorded machine')} "
            f"({top.get('station', 'unrecorded station')}): "
            f"{get_record_fault(top)}. Confirmed cause: "
            f"{top.get('confirmed_cause', 'not recorded')}. "
            f"Corrective action: "
            f"{top.get('corrective_action', 'not recorded')} "
            f"({top.get('downtime_minutes', 0)} min downtime)."
        )

    if components:
        top = components[0]

        parts.append(
            f"Related component: "
            f"**{top.get('component_name', 'Unnamed component')}** "
            f"({top.get('station', 'unrecorded station')}). "
            f"Common failures: "
            f"{top.get('common_failures', 'not recorded')}."
        )

    matched_faults = (
        fault_kb.get("matched_faults") if isinstance(fault_kb, dict) else None
    )

    if matched_faults:
        causes = fault_kb.get("causes", [])
        parts.append(
            "The static fault knowledge base also lists "
            + ", ".join(matched_faults[:2])
            + ". Possible causes: "
            + (", ".join(causes[:3]) if causes else "not recorded")
            + "."
        )

    if recipes:
        top = recipes[0]
        note = str(top.get("notes") or "").strip()

        parts.append(
            f"Related recipe: **{top.get('recipe_name', 'Unknown')}** "
            f"on {top.get('machine_model', 'an unrecorded machine')}."
            + (f" {note}" if note else "")
        )

    if not parts:
        return (
            "I couldn't find anything matching in the local knowledge base "
            "yet. Try describing the fault a little differently, narrow "
            "the station, or save it in Smart Troubleshooter or "
            "Maintenance History so ABAYO can find it next time."
        )

    return "\n\n".join(parts)


# ---------------------------------------------------------
# RESULT CARD RENDERERS
# ---------------------------------------------------------

def display_match_score(record: dict[str, Any]) -> None:
    match_score = record.get("match_score")

    if match_score is None:
        return

    try:
        score_value = float(match_score)
    except (TypeError, ValueError):
        return

    st.progress(
        min(max(score_value / 100, 0.0), 1.0),
        text=f"{score_value:.1f}% match",
    )


def render_troubleshooting_source(record: dict[str, Any]) -> None:
    solution_number = record.get("solution_number", "Troubleshooting solution")
    fault_name = record.get("fault", "Unnamed fault")
    score = record.get("match_score")

    title = f"{solution_number} — {fault_name}"
    if score is not None:
        title += f" ({score}% match)"

    with st.expander(title):
        display_match_score(record)
        st.write(f"**Station:** {record.get('station', 'Not recorded')}")
        st.write(f"**Possible cause:** {record.get('cause', 'Not recorded')}")
        st.write(f"**Inspection:** {record.get('inspection', 'Not recorded')}")
        st.write(f"**Repair:** {record.get('repair', 'Not recorded')}")

        notes = record.get("notes")
        if notes:
            st.write(f"**Shared notes:** {notes}")


def render_maintenance_source(record: dict[str, Any]) -> None:
    number = get_record_number(record)
    fault = get_record_fault(record)
    score = record.get("match_score")

    title = f"{number} — {fault}"
    if score is not None:
        title += f" ({score}% match)"

    with st.expander(title):
        display_match_score(record)
        st.write(f"**Machine:** {record.get('machine_model', 'Not recorded')}")
        st.write(f"**Station:** {record.get('station', 'Not recorded')}")
        st.write(f"**Recipe:** {get_record_recipe(record)}")
        st.write(
            f"**Confirmed cause:** "
            f"{record.get('confirmed_cause', 'Not recorded')}"
        )
        st.write(
            f"**Corrective action:** "
            f"{record.get('corrective_action', 'Not recorded')}"
        )
        st.write(f"**Downtime:** {record.get('downtime_minutes', 0)} minutes")

        recorded_by = record.get("recorded_by")
        if recorded_by:
            st.write(f"**Recorded by:** {recorded_by}")

        notes = record.get("notes")
        if notes:
            st.write(f"**Notes:** {notes}")


def render_component_source(record: dict[str, Any]) -> None:
    number = record.get("component_number", "Component")
    name = record.get("component_name", "Unnamed component")
    score = record.get("match_score")

    title = f"{number} — {name}"
    if score is not None:
        title += f" ({score}% match)"

    with st.expander(title):
        display_match_score(record)
        st.write(f"**Station:** {record.get('station', 'Not recorded')}")
        st.write(f"**Category:** {record.get('category', 'Not recorded')}")
        st.write(
            f"**Common failures:** "
            f"{record.get('common_failures', 'Not recorded')}"
        )
        st.write(
            f"**Fault symptoms:** "
            f"{record.get('fault_symptoms', 'Not recorded')}"
        )

        related_faults = record.get("related_faults") or []
        if related_faults:
            st.write("**Related faults:** " + ", ".join(str(item) for item in related_faults))


def render_recipe_source(record: dict[str, Any]) -> None:
    title = f"{record.get('recipe_name', 'Recipe')} — {record.get('machine_model', '')}"

    with st.expander(title):
        st.write(f"**Status:** {record.get('status', 'Not recorded')}")

        parameters = record.get("parameters") or {}
        if isinstance(parameters, dict) and parameters:
            for key, value in parameters.items():
                st.write(f"**{key}:** {value}")

        notes = record.get("notes")
        if notes:
            st.write(f"**Notes:** {notes}")


def render_fault_kb_source(fault_kb: dict[str, Any]) -> None:
    matched_faults = fault_kb.get("matched_faults") or []

    if not matched_faults:
        return

    with st.expander(
        f"Fault knowledge base — {matched_faults[0]} "
        f"({fault_kb.get('confidence', 0)}% confidence)"
    ):
        st.write("**Matched faults:** " + ", ".join(matched_faults))

        causes = fault_kb.get("causes") or []
        if causes:
            st.write("**Possible causes:**")
            for cause in causes:
                st.write(f"- {cause}")

        checks = fault_kb.get("checks") or []
        if checks:
            st.write("**Suggested checks:**")
            for check in checks:
                st.write(f"- {check}")


def render_sources(results: dict[str, Any]) -> None:
    """Render every matching record grouped by knowledge source."""

    troubleshooting = results.get("troubleshooting") or []
    maintenance = results.get("maintenance") or []
    components = results.get("components") or []
    fault_kb = results.get("fault_kb") or {}
    recipes = results.get("recipes") or []

    has_any = (
        troubleshooting
        or maintenance
        or components
        or (isinstance(fault_kb, dict) and fault_kb.get("matched_faults"))
        or recipes
    )

    if not has_any:
        return

    with st.container(border=True):
        st.caption("Sources ABAYO checked")

        if maintenance:
            st.write("**🛠️ Maintenance History**")
            for record in maintenance:
                render_maintenance_source(record)

        if troubleshooting:
            st.write("**🧠 Shared Troubleshooting**")
            for record in troubleshooting:
                render_troubleshooting_source(record)

        if components:
            st.write("**⚙️ Machine Components**")
            for record in components:
                render_component_source(record)

        if isinstance(fault_kb, dict) and fault_kb.get("matched_faults"):
            st.write("**📘 Fault Knowledge Base**")
            render_fault_kb_source(fault_kb)

        if recipes:
            st.write("**📖 Recipe Library**")
            for record in recipes:
                render_recipe_source(record)


# ---------------------------------------------------------
# QUESTION PROCESSING
# ---------------------------------------------------------

def process_question(
    question: str,
    station_filter: str,
    scopes: list[str],
    *,
    use_claude: bool,
    anthropic_api_key: str,
    anthropic_model: str,
) -> None:
    """Answer one question and store it in the chat history."""

    question = question.strip()

    if not question:
        return

    analytic_keys = detect_analytics_intent(question)
    generation_mode = "local"
    generation_notice = ""

    if analytic_keys:
        answer_text, _summary = build_analytics_answer(analytic_keys, station_filter)
        results: dict[str, Any] = {}
        generation_mode = "calculated"
    else:
        with st.spinner("ABAYO is searching the local knowledge base..."):
            results = run_knowledge_search(question, station_filter, scopes)

        local_answer = synthesize_answer(results)
        answer_text = local_answer

        if use_claude and anthropic_api_key and has_grounding_evidence(results):
            with st.spinner("Claude is writing a grounded answer from ABAYO records..."):
                try:
                    answer_text = generate_grounded_answer(
                        question,
                        station_filter,
                        results,
                        api_key=anthropic_api_key,
                        model=anthropic_model,
                    )
                    generation_mode = "claude"
                except ClaudeGenerationError:
                    generation_notice = (
                        "Claude was unavailable, so ABAYO returned its local "
                        "evidence-based answer instead."
                    )

    st.session_state.ai_assistant_history.append(
        {
            "question": question,
            "station": station_filter,
            "answer": answer_text,
            "results": results,
            "generation_mode": generation_mode,
            "generation_notice": generation_notice,
        }
    )


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------

if st.button("🏠 ← MAIN MENU", key="ai_assistant_main_menu_button"):
    st.switch_page("app.py")

page_header(
    "🤖 AI Assistant",
    "Ask about anything stored in ABAYO's local knowledge — "
    "maintenance history, troubleshooting, components, recipes and faults.",
)

st.info(
    "ABAYO always searches its own maintenance, troubleshooting, component, "
    "fault and recipe records first. When Claude is enabled, only the matched "
    "evidence and your question are sent to Anthropic to produce a clearer "
    "grounded answer. Exact maintenance statistics are calculated locally."
)

try:
    anthropic_api_key = configured_anthropic_api_key(st.secrets)
    anthropic_model = configured_anthropic_model(st.secrets)
except Exception:
    anthropic_api_key = ""
    anthropic_model = configured_anthropic_model({})

if anthropic_api_key:
    use_claude = st.toggle(
        "Use Claude for grounded answers",
        value=True,
        key="ai_assistant_use_claude",
        help=(
            "Matched ABAYO records and your question will be sent to the "
            "Anthropic API. Turn this off to keep processing entirely local."
        ),
    )
    st.caption(f"Claude model: {anthropic_model} · Local fallback stays active")
else:
    use_claude = False
    st.caption(
        "Claude is not configured. ABAYO is using the local evidence-based "
        "answer generator."
    )


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "ai_assistant_history" not in st.session_state:
    st.session_state.ai_assistant_history = []

if "ai_assistant_pending_question" not in st.session_state:
    st.session_state.ai_assistant_pending_question = ""


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

filter_column, scope_column, clear_column = st.columns([2, 3, 1])

with filter_column:
    station_filter = st.selectbox(
        "Machine station",
        STATIONS,
        key="ai_assistant_station",
    )

with scope_column:
    selected_scope_labels = st.multiselect(
        "Search in",
        list(SCOPE_LABELS.values()),
        default=list(SCOPE_LABELS.values()),
        key="ai_assistant_scope",
    )

    label_to_key = {label: key for key, label in SCOPE_LABELS.items()}
    selected_scopes = [label_to_key[label] for label in selected_scope_labels]

with clear_column:
    st.write("")
    st.write("")
    if st.button("Clear chat", key="ai_assistant_clear", width="stretch"):
        st.session_state.ai_assistant_history = []
        st.rerun()


# ---------------------------------------------------------
# EXAMPLE QUESTIONS
# ---------------------------------------------------------

if not st.session_state.ai_assistant_history:
    section_heading("Try asking")

    example_columns = st.columns(2)

    for index, example in enumerate(EXAMPLE_QUESTIONS):
        with example_columns[index % 2]:
            if st.button(example, key=f"ai_assistant_example_{index}", width="stretch"):
                st.session_state.ai_assistant_pending_question = example
                st.rerun()


# ---------------------------------------------------------
# HANDLE PENDING EXAMPLE QUESTION
# ---------------------------------------------------------

if st.session_state.ai_assistant_pending_question:
    pending_question = st.session_state.ai_assistant_pending_question
    st.session_state.ai_assistant_pending_question = ""
    process_question(
        pending_question,
        station_filter,
        selected_scopes,
        use_claude=use_claude,
        anthropic_api_key=anthropic_api_key,
        anthropic_model=anthropic_model,
    )


# ---------------------------------------------------------
# CHAT HISTORY
# ---------------------------------------------------------

for turn in st.session_state.ai_assistant_history:
    with st.chat_message("user"):
        st.write(turn["question"])

    with st.chat_message("assistant", avatar="🤖"):
        st.write(turn["answer"])

        generation_mode = turn.get("generation_mode", "local")
        if generation_mode == "claude":
            st.caption("Answer generated by Claude from the matched ABAYO records")
        elif generation_mode == "calculated":
            st.caption("Calculated directly from ABAYO maintenance history")
        else:
            st.caption("Answer generated locally from the matched ABAYO records")

        generation_notice = turn.get("generation_notice")
        if generation_notice:
            st.warning(generation_notice)

        render_sources(turn.get("results") or {})


# ---------------------------------------------------------
# CHAT INPUT
# ---------------------------------------------------------

new_question = st.chat_input(
    "Ask about a fault, machine, recipe, component or maintenance record..."
)

if new_question:
    process_question(
        new_question,
        station_filter,
        selected_scopes,
        use_claude=use_claude,
        anthropic_api_key=anthropic_api_key,
        anthropic_model=anthropic_model,
    )
    st.rerun()


st.divider()

st.caption(
    "Safety: Stop the machine and isolate electrical, pneumatic and "
    "mechanical energy before physical inspection."
)
