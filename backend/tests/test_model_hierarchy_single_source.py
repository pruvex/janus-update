import ast
from pathlib import Path

from backend.llm_providers.shared.moa import MOA_MODEL_HIERARCHY, _VALID_TIERS


def test_shared_hierarchy_matches_approved_phase_a_mapping():
    assert MOA_MODEL_HIERARCHY == {
        "openai": {
            "vision": "gpt-4o",
            "logic": "gpt-5.4",
            "speed": "gpt-5.4-nano",
            "balanced": "gpt-5.4-mini",
        },
        "gemini": {
            "vision": "gemini-3-flash-preview",
            "logic": "gemini-3-pro-preview",
            "speed": "gemini-3-flash-preview",
            "balanced": "gemini-3-flash-preview",
        },
        "ollama": {
            "vision": "llava",
            "logic": "llama3.1:8b",
            "speed": "llama3.1:8b",
            "fast": "llama3.1:8b",
            "balanced": "qwen2.5:14b",
        },
    }
    assert "fast" in _VALID_TIERS


def test_chat_orchestrator_has_no_runtime_model_hierarchy_definition():
    source_path = Path("backend/services/chat_orchestrator.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    orchestrator = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ChatOrchestrator"
    )

    for node in orchestrator.body:
        if not isinstance(node, ast.Assign):
            continue
        assert not any(
            isinstance(target, ast.Name) and target.id == "MODEL_HIERARCHY"
            for target in node.targets
        )


def test_gemini_gateway_reads_shared_hierarchy_without_orchestrator_import():
    source = Path("backend/llm_providers/gemini/gateway.py").read_text(encoding="utf-8")
    assert "from ..shared.moa import MOA_MODEL_HIERARCHY" in source
    assert "ChatOrchestrator.MODEL_HIERARCHY" not in source
