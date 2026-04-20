# backend/tests/test_moa_routing.py
"""
💎 Regression-Tests für das Mixture-of-Agents (MoA) Skill-Level Model Routing.
"""
from unittest.mock import patch

from backend.llm_providers.shared.moa import (
    resolve_moa_model,
    MOA_MODEL_HIERARCHY,
    _VALID_TIERS,
)
from backend.data.schemas import SkillMetadata

_TM_PATCH = "backend.services.tool_manager.ToolManager.get_skill_metadata"


# ---------------------------------------------------------------------------
# 1. Basis-Auflösung: Tier vorhanden + Provider kennt Tier → Wechsel
# ---------------------------------------------------------------------------

class TestResolveMoaModel:

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="speed"))
    def test_speed_tier_openai_resolves_to_nano(self, _mock):
        model, active = resolve_moa_model("openai", "gpt-5.4", ["system.websearch"])
        assert model == "gpt-5.4-nano"
        assert active is True

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="speed"))
    def test_speed_tier_gemini_resolves_to_flash(self, _mock):
        model, active = resolve_moa_model("gemini", "gemini-3-pro-preview", ["system.websearch"])
        assert model == "gemini-3-flash-preview"
        assert active is True

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="logic"))
    def test_logic_tier_openai_resolves_to_standard(self, _mock):
        model, active = resolve_moa_model("openai", "gpt-5.4-nano", ["system.create_pdf"])
        assert model == "gpt-5.4"
        assert active is True

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="vision"))
    def test_vision_tier_gemini_resolves_to_pro_vision(self, _mock):
        model, active = resolve_moa_model("gemini", "gemini-3-flash-preview", ["system.analyze_image"])
        assert model == "gemini-pro-vision"
        assert active is True


    # ---------------------------------------------------------------------------
    # 2. Fallback-Pfade: kein Tier, unbekannter Tier, Ollama
    # ---------------------------------------------------------------------------

    @patch(_TM_PATCH, return_value=SkillMetadata())
    def test_no_tier_falls_back_to_base_model(self, _mock):
        """Skill ohne optimal_model_tier → Kein Wechsel."""
        model, active = resolve_moa_model("openai", "gpt-5.4", ["system.local_business"])
        assert model == "gpt-5.4"
        assert active is False

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="quantum"))
    def test_unknown_tier_falls_back_to_base_model(self, _mock):
        """Unbekannter Tier-Wert → sicherer Fallback."""
        model, active = resolve_moa_model("openai", "gpt-5.4", ["system.websearch"])
        assert model == "gpt-5.4"
        assert active is False

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="speed"))
    def test_ollama_always_falls_back(self, _mock):
        """Ollama hat keine Tier-Hierarchie → immer Fallback."""
        model, active = resolve_moa_model("ollama", "qwen2.5:14b", ["system.websearch"])
        assert model == "qwen2.5:14b"
        assert active is False

    def test_no_allowed_skills_falls_back(self):
        """Keine allowed_skill_ids → Kein MoA."""
        model, active = resolve_moa_model("openai", "gpt-5.4", None)
        assert model == "gpt-5.4"
        assert active is False

    def test_empty_allowed_skills_falls_back(self):
        """Leere allowed_skill_ids → Kein MoA."""
        model, active = resolve_moa_model("openai", "gpt-5.4", [])
        assert model == "gpt-5.4"
        assert active is False

    @patch(_TM_PATCH, return_value=SkillMetadata(optimal_model_tier="speed"))
    def test_resolved_model_equals_base_no_switch(self, _mock):
        """Wenn das aufgelöste Modell == User-Basismodell ist, kein MoA-Wechsel."""
        # User nutzt bereits das Speed-Modell
        model, active = resolve_moa_model("openai", "gpt-5.4-nano", ["system.websearch"])
        assert model == "gpt-5.4-nano"
        assert active is False


    # ---------------------------------------------------------------------------
    # 3. Strukturelle Validierung
    # ---------------------------------------------------------------------------

    def test_hierarchy_keys_match_valid_tiers(self):
        """Alle Tiers in der Hierarchie müssen in _VALID_TIERS sein."""
        for provider, tiers in MOA_MODEL_HIERARCHY.items():
            for tier in tiers:
                assert tier in _VALID_TIERS, f"Tier '{tier}' für Provider '{provider}' nicht in _VALID_TIERS"

    def test_hierarchy_has_openai_and_gemini(self):
        """Mindestens OpenAI und Gemini müssen Einträge haben."""
        assert "openai" in MOA_MODEL_HIERARCHY
        assert "gemini" in MOA_MODEL_HIERARCHY

    def test_skill_metadata_accepts_optimal_model_tier(self):
        """SkillMetadata akzeptiert optimal_model_tier korrekt."""
        meta = SkillMetadata(optimal_model_tier="speed")
        assert meta.optimal_model_tier == "speed"

        meta_none = SkillMetadata()
        assert meta_none.optimal_model_tier is None
