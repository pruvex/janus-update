"""OpenRouter × Janus filesystem skill suite.

Proves the routing/tool queue that broke live GLM desktop tests:
- list prompts must be filesystem, not news/meta-PDF
- read prompts must expose filesystem.read_file, not knowledge.query
- real list/read tools work against the Desktop Janus-OR-Test folder

The four certified OpenRouter models share the same skill-routing contract;
model ids are parametrized to lock that contract per certified model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.services.filesystem_manager import list_directory, read_file
from backend.services.orchestrator.execution_engine import OrchestratorExecutionEngine
from backend.services.orchestrator.intent_engine import IntentEngine
from backend.services.skill_selector import SkillSelector

TEST_DIR = Path.home() / "Desktop" / "Janus-OR-Test"
README_PATH = TEST_DIR / "README.md"
PACKAGE_PATH = TEST_DIR / "package.json"

LIST_PROMPT = (
    rf"Nutze nur das Dateisystem. Liste maximal 10 Dateinamen aus dem Ordner {TEST_DIR}. "
    r"Keine Websuche."
)
README_PROMPT = rf"Lies {README_PATH} und gib nur den ersten Absatz wieder."
PACKAGE_PROMPT = (
    rf"Welche Version steht in {PACKAGE_PATH}? Nutze die Datei, rate nicht."
)

CERTIFIED_MODELS = (
    "anthropic/claude-sonnet-5",
    "z-ai/glm-5.2",
    "deepseek/deepseek-v4-pro",
    "qwen/qwen3.7-plus",
)


@pytest.fixture(scope="module")
def intent_engine():
    return IntentEngine()


@pytest.fixture(scope="module")
def skill_selector():
    # Fallback policy path (no registry files) — still exercises FS mandatory/forbidden.
    return SkillSelector(capability_registry=None)


def _require_test_folder():
    if not TEST_DIR.is_dir():
        pytest.skip(f"Missing Desktop test folder: {TEST_DIR}")
    if not README_PATH.is_file() or not PACKAGE_PATH.is_file():
        pytest.skip(f"Missing expected files in {TEST_DIR}")


@pytest.mark.parametrize(
    ("prompt",),
    [
        (LIST_PROMPT,),
        (README_PROMPT,),
        (PACKAGE_PROMPT,),
    ],
)
def test_filesystem_prompts_are_not_news_or_meta_pdf(intent_engine, prompt):
    assert intent_engine.detect_filesystem_intent(prompt) is True
    assert intent_engine.detect_news_intent(prompt) is False
    assert intent_engine.detect_complex_document_request(prompt) is False


@pytest.mark.parametrize("model_id", CERTIFIED_MODELS)
@pytest.mark.parametrize(
    ("prompt",),
    [
        (LIST_PROMPT,),
        (README_PROMPT,),
        (PACKAGE_PROMPT,),
    ],
)
def test_certified_openrouter_models_get_filesystem_skill_queue(
    intent_engine, skill_selector, model_id, prompt
):
    """Routing contract is model-agnostic; lock it for each certified OR model."""
    assert model_id in CERTIFIED_MODELS
    intent = intent_engine.detect_all_intents(prompt)
    assert intent.is_filesystem_intent is True
    assert intent.is_news_intent is False
    assert intent.is_complex_document_request is False
    assert intent.is_ambiguous is False
    assert intent.primary_intent == "filesystem"

    skills = skill_selector.get_relevant_skills(
        prompt,
        intent_result=intent,
        top_k=12,
    )
    assert "filesystem.list_directory" in skills
    assert "filesystem.read_file" in skills
    assert "system.rss_news" not in skills
    assert "system.websearch" not in skills
    assert "knowledge.query" not in skills
    assert "system.create_pdf" not in skills


def test_planner_context_requires_filesystem_tools(intent_engine):
    engine = OrchestratorExecutionEngine(
        db=None,
        context_manager=None,
        model_hierarchy=None,
        agent_planner=None,
        agent_runtime=None,
        skill_selector=SkillSelector(capability_registry=None),
        capability_registry=None,
    )
    intent = intent_engine.detect_all_intents(README_PROMPT)
    ctx = engine._build_planner_context(
        user_text=README_PROMPT,
        relevant_skill_ids=[
            "filesystem.list_directory",
            "filesystem.read_file",
            "knowledge.query",
            "system.websearch",
        ],
        intent_result=intent,
    )
    assert "filesystem.read_file" in ctx.required_skill_ids
    assert "filesystem.list_directory" in ctx.required_skill_ids
    assert "knowledge.query" in ctx.forbidden_skill_ids
    assert "system.websearch" in ctx.forbidden_skill_ids
    assert "knowledge.query" not in ctx.allowed_skill_ids
    assert "system.websearch" not in ctx.allowed_skill_ids


def test_real_filesystem_list_and_read_against_desktop_fixture():
    _require_test_folder()
    listed = list_directory(str(TEST_DIR))
    assert listed.status == "ok"
    items = [str(x).lower() for x in (listed.data or {}).get("items", [])]
    joined = "\n".join(items)
    for name in ("readme.md", "package.json", "nota.txt", "notes.md", "data.json"):
        assert name in joined

    readme = read_file(str(README_PATH))
    assert readme.status == "ok"
    readme_blob = f"{readme.message}\n{json.dumps(readme.data or {}, ensure_ascii=False)}"
    assert "OpenRouter" in readme_blob or "openrouter" in readme_blob.lower()

    package = read_file(str(PACKAGE_PATH))
    assert package.status == "ok"
    package_blob = f"{package.message}\n{json.dumps(package.data or {}, ensure_ascii=False)}"
    assert "9.9.9-or-test" in package_blob


def test_websuche_opt_out_does_not_trigger_complex_document(intent_engine):
    # Regression: substring "suche" inside "Websuche" + "datei" inside "Dateinamen"
    assert intent_engine.detect_complex_document_request(LIST_PROMPT) is False
    # Still true for a real research+PDF style ask
    assert (
        intent_engine.detect_complex_document_request(
            "Recherchiere den Kurs von Gold und speichere das als PDF-Dokument"
        )
        is True
    )
