"""Expanded Janus skill routing matrix for OpenRouter-certified models.

Deterministic (no LLM cost). Complements the live suite.
"""

from __future__ import annotations

import pytest

from backend.services.orchestrator.intent_engine import IntentEngine
from backend.services.skill_selector import SkillSelector

CERTIFIED_MODELS = (
    "anthropic/claude-sonnet-5",
    "z-ai/glm-5.2",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3.7-plus",
)

CASES = (
    {
        "id": "filesystem_list",
        "prompt": (
            r"Nutze nur das Dateisystem. Liste maximal 10 Dateinamen aus dem Ordner "
            r"C:\Users\pruve\Desktop\Janus-OR-Test. Keine Websuche."
        ),
        "primary": "filesystem",
        "must_include": ("filesystem.list_directory", "filesystem.read_file"),
        "must_exclude": ("system.rss_news", "system.websearch", "system.create_pdf", "knowledge.query"),
    },
    {
        "id": "filesystem_read",
        "prompt": (
            r"Welche Version steht in C:\Users\pruve\Desktop\Janus-OR-Test\package.json? "
            r"Nutze die Datei, rate nicht."
        ),
        "primary": "filesystem",
        "must_include": ("filesystem.read_file", "filesystem.list_directory"),
        "must_exclude": ("knowledge.query", "system.websearch", "system.rss_news"),
    },
    {
        "id": "news",
        "prompt": "Zeig mir die Nachrichten von heute",
        "primary": "news",
        "must_include": ("system.rss_news",),
        "must_exclude": ("filesystem.list_directory",),
    },
    {
        "id": "weather",
        "prompt": "Wie ist das Wetter in Berlin heute?",
        "primary": "weather",
        "must_include": ("system.weather",),
        "must_exclude": ("system.create_pdf",),
    },
    {
        "id": "wikipedia",
        "prompt": "Was steht auf Wikipedia zu Albert Einstein?",
        "primary": "wikipedia",
        "must_include": ("system.wikipedia_summary",),
        "must_exclude": ("system.create_pdf",),
    },
    {
        "id": "calendar",
        "prompt": "Was habe ich morgen im Kalender?",
        "primary": "calendar",
        "must_include": ("calendar.list_events",),
        "must_exclude": ("system.create_pdf",),
    },
    {
        "id": "shopping",
        "prompt": "Vergleiche den Preis von AirPods Pro",
        "primary": "shopping",
        "must_include": ("system.price_comparison",),
        "must_exclude": ("system.websearch",),
    },
    {
        "id": "complex_pdf_research",
        "prompt": "Recherchiere den Kurs von Gold und speichere das als PDF-Dokument",
        "primary": "complex_document",
        "must_include": (),
        "must_exclude": (),
        "complex_document": True,
    },
)


@pytest.fixture(scope="module")
def intent_engine():
    return IntentEngine()


@pytest.fixture(scope="module")
def skill_selector():
    return SkillSelector(capability_registry=None)


@pytest.mark.parametrize("model_id", CERTIFIED_MODELS)
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_openrouter_skill_routing_matrix(intent_engine, skill_selector, model_id, case):
    assert model_id in CERTIFIED_MODELS
    prompt = case["prompt"]
    intent = intent_engine.detect_all_intents(prompt)

    if case.get("complex_document"):
        assert intent.is_complex_document_request is True
        assert intent.is_filesystem_intent is False
        return

    assert intent.primary_intent == case["primary"], (
        f"{case['id']}: expected primary={case['primary']}, got {intent.primary_intent}"
    )
    skills = skill_selector.get_relevant_skills(prompt, intent_result=intent, top_k=12)
    for skill in case["must_include"]:
        assert skill in skills, f"{case['id']}/{model_id}: missing {skill} in {skills}"
    for skill in case["must_exclude"]:
        assert skill not in skills, f"{case['id']}/{model_id}: unexpected {skill} in {skills}"
