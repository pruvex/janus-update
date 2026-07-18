from unittest.mock import patch

import pytest

from backend.data.schemas import OpenRouterKeyPublicState, OpenRouterKeyValidationState


def _public_state(*, present: bool, state: OpenRouterKeyValidationState):
    return OpenRouterKeyPublicState(
        present=present,
        masked="********" if present else None,
        state=state,
    )


def _catalog(*model_ids: str):
    return {
        model_id: {
            "id": model_id,
            "name": model_id,
            "provider": "openrouter",
            "model_version": model_id.rsplit("/", 1)[-1],
        }
        for model_id in model_ids
    }


@pytest.mark.parametrize(
    ("present", "state", "expected_reason"),
    [
        (False, OpenRouterKeyValidationState.UNVERIFIED, "key_missing"),
        (True, OpenRouterKeyValidationState.UNVERIFIED, "key_unverified"),
        (True, OpenRouterKeyValidationState.INVALID, "key_invalid"),
    ],
)
def test_openrouter_selection_fails_closed_for_non_valid_key(
    test_client,
    present,
    state,
    expected_reason,
):
    with patch(
        "backend.api.routers.system._openrouter_public_state",
        return_value=_public_state(present=present, state=state),
    ), patch(
        "backend.api.routers.system.load_model_catalog",
        return_value=_catalog("anthropic/claude-3.7-sonnet-20250219"),
    ):
        response = test_client.get("/api/models/openrouter/eligibility")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "openrouter",
        "key_present": present,
        "key_state": state.value,
        "eligible": False,
        "reason": expected_reason,
        "models": ["anthropic/claude-3.7-sonnet-20250219"],
    }


def test_openrouter_selection_requires_at_least_one_filtered_certified_model(test_client):
    with patch(
        "backend.api.routers.system._openrouter_public_state",
        return_value=_public_state(
            present=True,
            state=OpenRouterKeyValidationState.VALID,
        ),
    ), patch("backend.api.routers.system.load_model_catalog", return_value={}):
        response = test_client.get("/api/models/openrouter/eligibility")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "openrouter",
        "key_present": True,
        "key_state": "VALID",
        "eligible": False,
        "reason": "no_certified_models",
        "models": [],
    }


def test_openrouter_selection_returns_only_filtered_exact_openrouter_ids(test_client):
    catalog = _catalog(
        "anthropic/claude-3.7-sonnet-20250219",
        "qwen/qwen3-235b-a22b-2507",
    )
    catalog["openai/gpt-5.4"] = {
        "id": "openai/gpt-5.4",
        "provider": "openai",
    }
    catalog["blank"] = {"id": "", "provider": "openrouter"}

    with patch(
        "backend.api.routers.system._openrouter_public_state",
        return_value=_public_state(
            present=True,
            state=OpenRouterKeyValidationState.VALID,
        ),
    ), patch("backend.api.routers.system.load_model_catalog", return_value=catalog):
        response = test_client.get("/api/models/openrouter/eligibility")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "provider": "openrouter",
        "key_present": True,
        "key_state": "VALID",
        "eligible": True,
        "reason": "eligible",
        "models": [
            "anthropic/claude-3.7-sonnet-20250219",
            "qwen/qwen3-235b-a22b-2507",
        ],
    }
    serialized = response.text.lower()
    assert "api_key" not in serialized
    assert "fingerprint" not in serialized
    assert "binding" not in serialized


def test_openrouter_model_selection_save_keeps_only_certified_ids(test_client, monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("backend.api.routers.system.CONFIG_FILE", str(config_path))
    monkeypatch.setattr(
        "backend.api.routers.system.load_config",
        lambda: {"model_selection": {}},
    )
    saved = {}

    def _save(config):
        saved.update(config)

    monkeypatch.setattr("backend.api.routers.system.save_config", _save)
    with patch(
        "backend.api.routers.system.load_model_catalog",
        return_value=_catalog("anthropic/claude-sonnet-5", "z-ai/glm-5.2"),
    ):
        response = test_client.post(
            "/api/models/selection",
            json={
                "provider": "openrouter",
                "models": [
                    "anthropic/claude-sonnet-5",
                    "not-certified/model",
                    "z-ai/glm-5.2",
                ],
            },
        )

    assert response.status_code == 200
    assert saved["model_selection"]["openrouter"] == [
        "anthropic/claude-sonnet-5",
        "z-ai/glm-5.2",
    ]
