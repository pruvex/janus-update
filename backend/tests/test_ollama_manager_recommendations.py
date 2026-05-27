from datetime import datetime, timedelta

from backend.services.ollama_manager import OllamaManager


def test_ranked_recommendations_prioritize_reasoning_models_on_rolf_node(monkeypatch):
    manager = OllamaManager()
    monkeypatch.setattr(manager, "_fetch_ollama_library_models", lambda: [])

    monkeypatch.setattr(
        manager,
        "_is_reasoning_priority_node",
        lambda active_node, gpu_info: True,
    )

    recommendations = manager._get_ranked_recommendations(
        profile="mid",
        active_node={"id": "rolf", "name": "Rolf GPU", "url": "http://rolf:11434", "active": True},
        gpu_info={"type": "none", "vram_gb": None},
    )

    assert recommendations
    top_three = [str(entry.get("id") or "") for entry in recommendations[:3]]
    assert "mistral-nemo:12b" in top_three
    assert "qwen2.5:14b" in top_three
    assert recommendations[0].get("id") != "llama3.1:8b"


def test_ranked_recommendations_use_latest_ollama_library_when_available(monkeypatch):
    manager = OllamaManager()
    monkeypatch.setattr(
        manager,
        "_fetch_ollama_library_models",
        lambda: [
            {
                "name": "qwen3.5",
                "description": "New model with tools and thinking.",
                "capabilities": ["tools", "thinking"],
                "sizes_b": [8.0, 32.0, 72.0],
            },
            {
                "name": "old-static-model",
                "description": "Older fallback model.",
                "capabilities": [],
                "sizes_b": [7.0],
            },
        ],
    )

    recommendations = manager._get_ranked_recommendations(
        profile="mid",
        active_node={"id": "local", "name": "Local", "url": "http://localhost:11434", "active": True},
        gpu_info={"type": "none", "vram_gb": None},
    )

    assert recommendations[0]["id"] == "qwen3.5:8b"
    assert recommendations[0]["source"] == "ollama_library"
    assert recommendations[0]["tools_supported"] is True
    assert recommendations[0]["description"].startswith("Aktuelles Ollama-Modell")
    assert "New model" not in recommendations[0]["description"]
    assert recommendations[0]["use_case"] == "Agentische Janus-Workflows, Planung und strukturierte Tool-Nutzung im 8B-Profil"
    assert "Ollama Library" not in recommendations[0]["use_case"]

    coding_ids = [entry["id"] for entry in recommendations if entry.get("category") == "coding"]
    assert coding_ids == ["qwen2.5-coder:7b", "deepseek-coder:6.7b"]


def test_get_pull_status_falls_back_to_latest_key_for_same_model_and_node(monkeypatch):
    manager = OllamaManager()

    old_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    old_key = f"llama3.1:8b:localhost:{old_date}"
    manager.active_downloads[old_key] = {
        "status": "running",
        "message": "download in progress",
        "model": old_key,
        "progress": 55,
        "updated_at": 123,
        "error": None,
    }

    monkeypatch.setattr(manager, "list_models", lambda: [])

    payload = manager.get_pull_status("llama3.1:8b@localhost")
    assert payload["status"] == "running"
    assert payload["model"] == old_key
