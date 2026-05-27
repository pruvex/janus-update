from datetime import datetime, timedelta
import json
import subprocess

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


def test_windows_gpu_detection_uses_powershell_cim_for_amd_radeon(monkeypatch):
    manager = OllamaManager()
    payload = [
        {
            "Name": "AMD Radeon RX 7700 XT",
            "AdapterRAM": 4293918720,
            "PNPDeviceID": "PCI\\VEN_1002&DEV_747E",
        }
    ]

    def fake_run(command, **kwargs):
        if command[0] == "powershell":
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("backend.services.ollama_manager.platform.system", lambda: "Windows")
    monkeypatch.setattr("backend.services.ollama_manager.subprocess.run", fake_run)

    gpu = manager._detect_generic_gpu()

    assert gpu == {
        "type": "amd",
        "name": "AMD Radeon RX 7700 XT",
        "vram_gb": 12.0,
        "detection_source": "cim",
        "vram_source": "gpu_name_heuristic",
        "vram_confidence": "medium",
    }
    assert manager._is_reasoning_priority_node({"id": "local"}, gpu) is True


def test_windows_gpu_detection_parses_wmic_csv_by_header(monkeypatch):
    manager = OllamaManager()
    wmic_output = "\n".join(
        [
            "Node,AdapterRAM,Name",
            "TEST-PC,12884901888,AMD Radeon RX 7700 XT",
        ]
    )

    def fake_run(command, **kwargs):
        if command[0] == "powershell":
            raise FileNotFoundError("powershell unavailable")
        if command[0] == "wmic" and "/format:csv" in command:
            return subprocess.CompletedProcess(command, 0, stdout=wmic_output, stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("backend.services.ollama_manager.platform.system", lambda: "Windows")
    monkeypatch.setattr("backend.services.ollama_manager.subprocess.run", fake_run)

    gpu = manager._detect_generic_gpu()

    assert gpu == {
        "type": "amd",
        "name": "AMD Radeon RX 7700 XT",
        "vram_gb": 12.0,
        "detection_source": "wmic",
        "vram_source": "wmic_adapter_ram",
        "vram_confidence": "medium",
    }


def test_windows_gpu_detection_uses_registry_when_cim_and_wmic_only_report_remote_adapters(monkeypatch):
    manager = OllamaManager()
    calls = []
    registry_payload = {
        "Name": "NVIDIA GeForce RTX 4070 SUPER",
        "MemorySize": 12884901888,
    }

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == "powershell" and "Get-CimInstance" in command[-1]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({"Name": "Microsoft Remote Display Adapter", "AdapterRAM": None}),
                stderr="",
            )
        if command[0] == "wmic" and "/format:csv" in command:
            return subprocess.CompletedProcess(command, 0, stdout="Node,AdapterRAM,Name\nTEST,,Microsoft Remote Display Adapter", stderr="")
        if command[0] == "wmic" and command[-1] == "name":
            return subprocess.CompletedProcess(command, 0, stdout="Name\nMicrosoft Remote Display Adapter", stderr="")
        if command[0] == "powershell" and "CurrentControlSet" in command[-1]:
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(registry_payload), stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("backend.services.ollama_manager.platform.system", lambda: "Windows")
    monkeypatch.setattr("backend.services.ollama_manager.subprocess.run", fake_run)

    gpu = manager._detect_generic_gpu()

    assert gpu == {
        "type": "nvidia",
        "name": "NVIDIA GeForce RTX 4070 SUPER",
        "vram_gb": 12.0,
        "detection_source": "registry",
        "vram_source": "registry_memory_size",
        "vram_confidence": "medium",
    }


def test_dxdiag_parser_extracts_gpu_and_memory():
    text = """
---------------
Display Devices
---------------
          Card name: Intel(R) Arc(TM) A770 Graphics
       Display Memory: 16322 MB
    Dedicated Memory: 16305 MB
"""

    controllers = OllamaManager._parse_dxdiag_video_controllers(text)

    assert controllers == [
        {
            "name": "Intel(R) Arc(TM) A770 Graphics",
            "vram_gb": 15.9,
            "detection_source": "dxdiag",
            "vram_source": "dxdiag_memory",
            "vram_confidence": "medium",
        }
    ]


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
