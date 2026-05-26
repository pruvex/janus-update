import asyncio
import json
from pathlib import Path

from backend.llm_providers.shared.moa import MOA_MODEL_HIERARCHY, resolve_moa_model
from backend.services.routing.escalation import EscalationEngine
from backend.services.routing.model_router import ModelRouter


REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "backend" / "config" / "model_catalog.json"
ROUTING_PATH = REPO_ROOT / "backend" / "config" / "model_routing.json"


def _catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _catalog_by_id():
    return {entry["id"]: entry for entry in _catalog()}


def _provider_for(model_id: str) -> str:
    return str(_catalog_by_id()[model_id]["provider"]).lower()


def _routing():
    return json.loads(ROUTING_PATH.read_text(encoding="utf-8"))


def _models_in_config(node):
    if isinstance(node, dict):
        if isinstance(node.get("model"), str):
            yield node["model"]
        for value in node.values():
            yield from _models_in_config(value)
    elif isinstance(node, list):
        for value in node:
            yield from _models_in_config(value)


def test_default_smallest_viable_models_exist_and_match_provider_silos():
    routing = _routing()
    defaults = routing["default_tiers"]

    assert defaults["openai"]["primary"]["model"] == "gpt-5.4-nano"
    assert defaults["gemini"]["primary"]["model"] == "gemini-3-flash-preview"

    for provider, tiers in defaults.items():
        for tier in ("primary", "fallback", "escalation"):
            model_id = tiers[tier]["model"]
            assert model_id in _catalog_by_id()
            assert _provider_for(model_id) == provider


def test_every_configured_routing_model_exists_in_catalog_and_stays_in_provider_silo():
    routing = _routing()
    catalog = _catalog_by_id()

    for model_id in _models_in_config(routing):
        assert model_id in catalog

    router = ModelRouter(str(ROUTING_PATH))
    for provider in ("openai", "gemini"):
        for skill_id in ("system.weather", "filesystem.list_directory", "unknown.synthetic_skill"):
            config = router.get_routing_config(skill_id, provider)
            for tier in ("primary", "fallback", "escalation"):
                model_id = config[tier]["model"]
                assert model_id in catalog
                assert _provider_for(model_id) == provider


def test_weather_policy_uses_optimized_openai_mini_but_gemini_default_flash_silo():
    router = ModelRouter(str(ROUTING_PATH))

    openai_weather = router.get_routing_config("system.weather", "openai")
    gemini_weather = router.get_routing_config("system.weather", "gemini")

    assert openai_weather["primary"]["model"] == "gpt-5.4-mini"
    assert _provider_for(openai_weather["primary"]["model"]) == "openai"
    assert gemini_weather["primary"]["model"] == "gemini-3-flash-preview"
    assert _provider_for(gemini_weather["primary"]["model"]) == "gemini"


def test_google_alias_routes_to_gemini_silo_not_openai_fallback():
    router = ModelRouter(str(ROUTING_PATH))

    config = router.get_routing_config("unknown.synthetic_skill", "google")

    assert config["primary"]["model"] == "gemini-3-flash-preview"
    assert _provider_for(config["primary"]["model"]) == "gemini"


def test_moa_hierarchy_models_exist_and_never_cross_provider_silos():
    catalog = _catalog_by_id()

    for provider, tiers in MOA_MODEL_HIERARCHY.items():
        for tier, model_id in tiers.items():
            assert tier in {"speed", "balanced", "logic", "vision"}
            assert model_id in catalog
            assert _provider_for(model_id) == provider


def test_moa_uses_provider_specific_logic_model(monkeypatch):
    from backend.services import tool_manager as tool_manager_module

    monkeypatch.setattr(
        tool_manager_module.tool_manager,
        "get_optimal_model_tier",
        lambda skill_id, provider: "logic",
    )

    openai_model, openai_active = resolve_moa_model("openai", "gpt-5.4-nano", ["system.websearch"])
    gemini_model, gemini_active = resolve_moa_model("gemini", "gemini-3-flash-preview", ["system.websearch"])

    assert openai_active is True
    assert openai_model == "gpt-5.4"
    assert _provider_for(openai_model) == "openai"
    assert gemini_active is True
    assert gemini_model == "gemini-3.1-pro-preview"
    assert _provider_for(gemini_model) == "gemini"


def test_escalation_engine_attempts_remain_inside_requested_provider_silo():
    async def run():
        seen = []

        async def tool_call_fn(provider, model, **kwargs):
            seen.append((provider, model))
            return {"status": "error" if len(seen) == 1 else "ok"}

        engine = EscalationEngine(router=ModelRouter(str(ROUTING_PATH)))
        summary = await engine.execute_with_escalation(
            "unknown.synthetic_skill",
            tool_call_fn=tool_call_fn,
            provider="gemini",
        )

        assert summary.final_success is True
        assert len(summary.attempts) == 2
        assert seen == [
            ("gemini", "gemini-3-flash-preview"),
            ("gemini", "gemini-3.1-pro-preview"),
        ]

    asyncio.run(run())
