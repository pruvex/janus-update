# backend/llm_providers/shared/moa.py
"""
💎 Mixture-of-Agents (MoA) – Skill-Level Model Routing

Löst für einen gegebenen Provider + Tier das optimale Modell auf.
Regeln:
  - Routing ist strikt provider-intern (nie Provider-Mix).
  - Wenn kein Tier gesetzt oder der Provider das Tier nicht kennt → Fallback auf user_base_model.
  - Ollama hat keine Tier-Hierarchie → immer Fallback.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("janus_backend")

# ──────────────────────────────────────────────
# Provider → Tier → konkretes Modell
# ──────────────────────────────────────────────
MOA_MODEL_HIERARCHY: Dict[str, Dict[str, str]] = {
    "openai": {
        "speed": "gpt-5.4-nano",
        "balanced": "gpt-5.4-nano",
        "logic": "gpt-5.4",
        "vision": "gpt-4o",
    },
    "gemini": {
        "speed": "gemini-3-flash-preview",
        "balanced": "gemini-3-flash-preview",
        "logic": "gemini-3.1-pro-preview",
        "vision": "gemini-pro-vision",
    },
    # Ollama: bewusst leer – lokale Modelle haben keine Tier-Hierarchie.
}

_VALID_TIERS = frozenset({"speed", "balanced", "logic", "vision"})


def resolve_moa_model(
    provider: str,
    user_base_model: str,
    allowed_skill_ids: Optional[List[str]],
) -> Tuple[str, bool]:
    """
    Bestimmt das optimale Tool-Execution-Modell per MoA-Routing.

    Returns:
        (tool_execution_model, moa_active)
        - tool_execution_model: Das Modell, das für den Tool-Loop genutzt werden soll.
        - moa_active: True wenn ein MoA-Wechsel stattfand (tool_execution_model != user_base_model).
    """
    if not allowed_skill_ids:
        return user_base_model, False

    # Lokaler Import um Zirkelbezüge zu vermeiden
    from backend.services.tool_manager import tool_manager

    primary_skill = str(allowed_skill_ids[0]).strip()
    if not primary_skill:
        return user_base_model, False

    tier = tool_manager.get_optimal_model_tier(primary_skill, provider)

    if not tier:
        return user_base_model, False

    tier = str(tier).strip().lower()
    if tier not in _VALID_TIERS:
        logger.warning(
            "💎 SKILL-MOA: Unbekannter Tier '%s' für Skill '%s'. Fallback auf User-Basismodell.",
            tier,
            primary_skill,
        )
        return user_base_model, False

    provider_key = str(provider or "").strip().lower()
    provider_tiers = MOA_MODEL_HIERARCHY.get(provider_key)
    if not provider_tiers:
        logger.info(
            "💎 SKILL-MOA: Provider '%s' hat keine Tier-Hierarchie. Fallback auf User-Basismodell.",
            provider_key,
        )
        return user_base_model, False

    resolved_model = provider_tiers.get(tier)
    if not resolved_model:
        logger.warning(
            "💎 SKILL-MOA: Tier '%s' nicht in Hierarchie für Provider '%s'. Fallback auf User-Basismodell.",
            tier,
            provider_key,
        )
        return user_base_model, False

    if resolved_model == user_base_model:
        logger.debug(
            "💎 SKILL-MOA: Aufgelöstes Modell '%s' == User-Basismodell. Kein Wechsel nötig.",
            resolved_model,
        )
        return user_base_model, False

    logger.info(
        "💎 SKILL-MOA AKTIV: Wechsle für Skill '%s' (Tier=%s) von '%s' → '%s' [Provider: %s]",
        primary_skill,
        tier,
        user_base_model,
        resolved_model,
        provider_key,
    )
    return resolved_model, True
