import json

import pytest

from backend.api.routers import system
from backend.services import model_catalog as model_catalog_service
from backend.utils import config_loader


MODEL_ID = "example/vendor-model-2026-07-16"
MODEL_VERSION = "2026-07-16"
BATTERY_VERSION = "test-battery-v1"


def _release_catalog():
    return [
        {"id": "gpt-test", "provider": "openai", "name": "OpenAI Test"},
        {
            "id": MODEL_ID,
            "provider": "openrouter",
            "name": "Release OpenRouter Test",
            "model_version": MODEL_VERSION,
        },
    ]


def _passed_record(model_id=MODEL_ID, model_version=MODEL_VERSION, battery_version=BATTERY_VERSION):
    return {
        "model_id": model_id,
        "model_version": model_version,
        "battery_version": battery_version,
        "status": "passed",
        "mandatory_test_evidence": "passed",
        "audit_evidence": "passed",
    }


def _registry(models=None, *, schema_version=1, battery_version=BATTERY_VERSION):
    return {
        "schema_version": schema_version,
        "battery_version": battery_version,
        "models": [_passed_record()] if models is None else models,
    }


def _bind_sources(
    monkeypatch,
    tmp_path,
    *,
    registry=None,
    registry_text=None,
    user_catalog=None,
    release_catalog=None,
):
    release_path = tmp_path / "release-model-catalog.json"
    registry_path = tmp_path / "release-openrouter-registry.json"
    app_data_dir = tmp_path / "appdata"
    app_data_dir.mkdir()
    release_path.write_text(json.dumps(_release_catalog() if release_catalog is None else release_catalog), encoding="utf-8")
    if registry_text is not None:
        registry_path.write_text(registry_text, encoding="utf-8")
    else:
        registry_path.write_text(json.dumps(_registry() if registry is None else registry), encoding="utf-8")
    if user_catalog is not None:
        (app_data_dir / "model_catalog.json").write_text(json.dumps(user_catalog), encoding="utf-8")

    def fake_resource_path(relative_path):
        normalized = str(relative_path).replace("\\", "/")
        if normalized.endswith("openrouter_certified_models.json"):
            return str(registry_path)
        if normalized.endswith("model_catalog.json"):
            return str(release_path)
        raise AssertionError(f"Unexpected resource path: {relative_path}")

    monkeypatch.setattr(config_loader, "resource_path", fake_resource_path)
    monkeypatch.setattr(config_loader, "get_app_data_dir", lambda: str(app_data_dir))
    return release_path, registry_path, app_data_dir


def _openrouter_models(catalog):
    return [model for model in catalog.values() if model.get("provider") == "openrouter"]


def test_valid_release_binding_is_shared_by_both_loaders_and_api(monkeypatch, tmp_path, test_client):
    user_catalog = [
        {
            "id": MODEL_ID,
            "provider": "openrouter",
            "name": "AppData Must Not Win",
            "model_version": "spoofed-version",
        },
        {
            "id": "user/injected-model",
            "provider": "openrouter",
            "name": "Injected",
            "model_version": MODEL_VERSION,
        },
    ]
    _bind_sources(monkeypatch, tmp_path, user_catalog=user_catalog)

    config_catalog = config_loader.load_model_catalog()
    service_models = model_catalog_service.get_models_by_provider("openrouter")
    response = test_client.get("/api/models/catalog")

    assert response.status_code == 200
    assert _openrouter_models(config_catalog) == [
        {
            "id": MODEL_ID,
            "provider": "openrouter",
            "name": "Release OpenRouter Test",
            "model_version": MODEL_VERSION,
        }
    ]
    assert service_models == _openrouter_models(config_catalog)
    assert [model for model in response.json() if model.get("provider") == "openrouter"] == service_models
    assert config_catalog["gpt-test"]["provider"] == "openai"


@pytest.mark.parametrize(
    "registry",
    [
        {"schema_version": 1, "battery_version": None, "models": []},
        _registry(models=[{"model_id": MODEL_ID}]),
        _registry(models=[{**_passed_record(), "status": "failed"}]),
        _registry(models=[{**_passed_record(), "mandatory_test_evidence": "failed"}]),
        _registry(models=[{**_passed_record(), "audit_evidence": "failed"}]),
        _registry(models=[_passed_record(), _passed_record()]),
        _registry(models=[_passed_record(model_id="example/vendor:latest")]),
        _registry(schema_version=99),
        _registry(models=[_passed_record(battery_version="different-battery")]),
        _registry(models=[_passed_record(model_version="different-version")]),
    ],
)
def test_invalid_or_incomplete_registry_fails_closed(monkeypatch, tmp_path, registry):
    _bind_sources(monkeypatch, tmp_path, registry=registry)

    catalog = config_loader.load_model_catalog()

    assert _openrouter_models(catalog) == []
    assert catalog["gpt-test"]["provider"] == "openai"


def test_malformed_or_missing_registry_fails_closed(monkeypatch, tmp_path):
    _, registry_path, _ = _bind_sources(monkeypatch, tmp_path, registry_text="{not-json")
    assert _openrouter_models(config_loader.load_model_catalog()) == []

    registry_path.unlink()
    assert _openrouter_models(config_loader.load_model_catalog()) == []


def test_latest_model_version_binding_fails_closed(monkeypatch, tmp_path):
    release_catalog = _release_catalog()
    release_catalog[1]["model_version"] = "latest"
    registry = _registry(models=[_passed_record(model_version="latest")])
    _bind_sources(
        monkeypatch,
        tmp_path,
        registry=registry,
        release_catalog=release_catalog,
    )

    assert _openrouter_models(config_loader.load_model_catalog()) == []


def test_appdata_cannot_turn_release_openai_model_into_openrouter(monkeypatch, tmp_path):
    user_catalog = [
        {
            "id": "gpt-test",
            "provider": "openrouter",
            "name": "Provider Override Attempt",
            "model_version": MODEL_VERSION,
        }
    ]
    _bind_sources(monkeypatch, tmp_path, user_catalog=user_catalog)

    catalog = config_loader.load_model_catalog()

    assert catalog["gpt-test"] == {"id": "gpt-test", "provider": "openai", "name": "OpenAI Test"}
    assert _openrouter_models(catalog) == [
        {
            "id": MODEL_ID,
            "provider": "openrouter",
            "name": "Release OpenRouter Test",
            "model_version": MODEL_VERSION,
        }
    ]


def test_catalog_api_cannot_append_openrouter_from_another_lifecycle(monkeypatch, tmp_path, test_client):
    _bind_sources(monkeypatch, tmp_path)

    class FakeLifecycle:
        configured = True

        async def list_models(self):
            return [
                {"id": "runtime/injected", "provider": "openrouter", "model_version": MODEL_VERSION},
                {"id": "chatgpt-test", "provider": "chatgpt", "name": "ChatGPT Test"},
            ]

    monkeypatch.setattr(system, "_get_codex_lifecycle", lambda request: FakeLifecycle())

    response = test_client.get("/api/models/catalog")

    assert response.status_code == 200
    assert {model["id"] for model in response.json() if model.get("provider") == "openrouter"} == {MODEL_ID}
    assert any(model.get("id") == "chatgpt-test" for model in response.json())
