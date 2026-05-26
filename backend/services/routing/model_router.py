"""
Model Router for Janus-Skills Quality System.

Loads skill-to-model mappings from config and provides routing configuration.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


def _normalize_provider(provider: str) -> str:
    provider_key = str(provider or "openai").strip().lower()
    if provider_key == "google":
        return "gemini"
    return provider_key


class ModelRouter:
    """Router for model selection based on skill configuration (Provider-Silos)."""
    
    def __init__(self, config_path: str = "backend/config/model_routing.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load routing configuration from JSON file (Provider-Silo structure)."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist (Strict Provider-Silo structure)
            return {
                "default_tiers": {
                    "openai": {
                        "primary": {"model": "gpt-5.4-nano"},
                        "fallback": {"model": "gpt-5.4-mini"},
                        "escalation": {"model": "gpt-5.4"}
                    },
                    "gemini": {
                        "primary": {"model": "gemini-3-flash-preview"},
                        "fallback": {"model": "gemini-3.1-pro-preview"},
                        "escalation": {"model": "gemini-3.1-pro-preview"}
                    }
                },
                "skill_mappings": {}
            }
    
    def get_routing_config(self, skill_id: str, provider: str = "openai") -> Dict[str, Any]:
        """
        Get routing configuration for a specific skill and provider (Provider-Silo).
        
        Args:
            skill_id: Unique skill identifier (e.g., "namespace.action")
            provider: Provider key ("openai" or "gemini")
        
        Returns:
            Dictionary with primary, fallback, and escalation model configs for the provider
        """
        provider = _normalize_provider(provider)
        # Check if skill has specific mapping
        skill_mappings = self.config.get("skill_mappings", {})
        
        if skill_id in skill_mappings:
            provider_mapping = skill_mappings[skill_id].get(provider)
            if provider_mapping:
                return provider_mapping
        
        # Fall back to global defaults for the provider
        default_tiers = self.config.get("default_tiers", {})
        provider_defaults = default_tiers.get(provider)
        if provider_defaults is None:
            provider_defaults = {
                "primary": {"model": "unknown"},
                "fallback": {"model": "unknown"},
                "escalation": {"model": "unknown"},
            }
        
        return provider_defaults
    
    def get_model_for_tier(self, skill_id: str, tier: str, provider: str = "openai") -> Optional[Dict[str, str]]:
        """
        Get model configuration for a specific tier and provider (Provider-Silo).
        
        Args:
            skill_id: Unique skill identifier
            tier: One of "primary", "fallback", "escalation"
            provider: Provider key ("openai" or "gemini")
        
        Returns:
            Model config dict with model, or None if tier invalid
        """
        routing_config = self.get_routing_config(skill_id, provider)
        tier_config = routing_config.get(tier)
        if tier_config and "model" in tier_config:
            return {"provider": provider, "model": tier_config["model"]}
        return None
    
    def add_skill_mapping(self, skill_id: str, provider: str, primary: Dict[str, str], 
                         fallback: Dict[str, str], escalation: Dict[str, str]) -> None:
        """
        Add or update a skill-specific mapping for a provider (Provider-Silo).
        
        Args:
            skill_id: Unique skill identifier
            provider: Provider key ("openai" or "gemini")
            primary: Primary model config (model)
            fallback: Fallback model config (model)
            escalation: Escalation model config (model)
        """
        if "skill_mappings" not in self.config:
            self.config["skill_mappings"] = {}
        if skill_id not in self.config["skill_mappings"]:
            self.config["skill_mappings"][skill_id] = {}
        
        self.config["skill_mappings"][skill_id][provider] = {
            "primary": primary,
            "fallback": fallback,
            "escalation": escalation
        }
        
        # Save to file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)


def get_routing_config(skill_id: str, provider: str = "openai") -> Dict[str, Any]:
    """
    Convenience function to get routing configuration for a skill and provider.
    
    Args:
        skill_id: Unique skill identifier
        provider: Provider key ("openai" or "gemini")
    
    Returns:
        Dictionary with primary, fallback, and escalation model configs for the provider
    """
    router = ModelRouter()
    return router.get_routing_config(skill_id, provider)
