from types import SimpleNamespace

import pytest

from ai_engine import (
    ClaudeGenerationError,
    build_grounding_context,
    configured_anthropic_api_key,
    configured_anthropic_model,
    generate_grounded_answer,
    has_grounding_evidence,
)


def test_anthropic_configuration_is_optional() -> None:
    assert configured_anthropic_api_key({}) == ""
    assert configured_anthropic_api_key({"ANTHROPIC_API_KEY": " key "}) == "key"
    assert configured_anthropic_model({}) == "claude-sonnet-5"
    assert configured_anthropic_model({"ANTHROPIC_MODEL": " custom "}) == "custom"


def test_grounding_evidence_ignores_empty_fault_result() -> None:
    assert not has_grounding_evidence({"fault_kb": {"matched_faults": []}})
    assert has_grounding_evidence({"maintenance": [{"record_number": "MNT-1"}]})


def test_context_omits_local_image_paths() -> None:
    context = build_grounding_context(
        "Why did it stop?",
        "Filling",
        {
            "maintenance": [
                {
                    "record_number": "MNT-1",
                    "confirmed_cause": "Loose wire",
                    "recorded_by": "Private employee name",
                    "image_paths": ["/private/machine-photo.jpg"],
                }
            ]
        },
    )

    assert "MNT-1" in context
    assert "Loose wire" in context
    assert "machine-photo.jpg" not in context
    assert "Private employee name" not in context


def test_generate_grounded_answer_uses_retrieved_evidence() -> None:
    captured: dict[str, object] = {}

    class FakeMessages:
        def create(self, **kwargs: object) -> object:
            captured.update(kwargs)
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Check record MNT-1.")],
            )

    class FakeClient:
        def __init__(self) -> None:
            self.messages = FakeMessages()

    def fake_factory(**kwargs: object) -> FakeClient:
        captured["client_options"] = kwargs
        return FakeClient()

    answer = generate_grounded_answer(
        "Why did it stop?",
        "Filling",
        {"maintenance": [{"record_number": "MNT-1", "fault": "Stopped"}]},
        api_key="secret-key",
        client_factory=fake_factory,
    )

    assert answer == "Check record MNT-1."
    assert captured["model"] == "claude-sonnet-5"
    assert "MNT-1" in str(captured["messages"])
    assert "secret-key" not in str(captured["messages"])


def test_generation_requires_key_and_evidence() -> None:
    with pytest.raises(ClaudeGenerationError):
        generate_grounded_answer("Question", "General", {}, api_key="")

    with pytest.raises(ClaudeGenerationError):
        generate_grounded_answer("Question", "General", {}, api_key="key")
