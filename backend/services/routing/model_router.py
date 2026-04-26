"""
Model Router for Janus-Skills Quality System.

Loads skill-to-model mappings from config and provides routing configuration.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ModelRouter:
    """Router for model selection based on skill configuration."""
    
    def __init__(self, config_path: str = "backend/config/model_routing.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load routing configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file doesn't exist
            return {
                "default_tiers": {
                    "primary": {"provider": "openai", "model": "gpt-4o-mini"},
                    "fallback": {"provider": "openai", "model": "gpt-4o"},
                    "escalation": {"provider": "openai", "model": "gpt-4-turbo"}
                },
                "skill_mappings": {}
            }
    
    def get_routing_config(self, skill_id: str) -> Dict[str, Any]:
        """
        Get routing configuration for a specific skill.
        
        Args:
            skill_id: Unique skill identifier (e.g., "namespace.action")
        
        Returns:
            Dictionary with primary, fallback, and escalation model configs
        """
        # Check if skill has specific mapping
        skill_mappings = self.config.get("skill_mappings", {})
        
        if skill_id in skill_mappings:
            return skill_mappings[skill_id]
        
        # Fall back to global defaults
        return self.config.get("default_tiers", {
            "primary": {"provider": "openai", "model": "gpt-4o-mini"},
            "fallback": {"provider": "openai", "model": "gpt-4o"},
            "escalation": {"provider": "openai", "model": "gpt-4-turbo"}
        })
    
    def get_model_for_tier(self, skill_id: str, tier: str) -> Optional[Dict[str, str]]:
        """
        Get model configuration for a specific tier.
        
        Args:
            skill_id: Unique skill identifier
            tier: One of "primary", "fallback", "escalation"
        
        Returns:
            Model config dict with provider and model, or None if tier invalid
        """
        routing_config = self.get_routing_config(skill_id)
        return routing_config.get(tier)
    
    def add_skill_mapping(self, skill_id: str, primary: Dict[str, str], 
                         fallback: Dict[str, str], escalation: Dict[str, str]) -> None:
        """
        Add or update a skill-specific mapping.
        
        Args:
            skill_id: Unique skill identifier
            primary: Primary model config (provider, model)
            fallback: Fallback model config
            escalation: Escalation model config
        """
        if "skill_mappings" not in self.config:
            self.config["skill_mappings"] = {}
        
        self.config["skill_mappings"][skill_id] = {
            "primary": primary,
            "fallback": fallback,
            "escalation": escalation
        }
        
        # Save to file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)


def get_routing_config(skill_id: str) -> Dict[str, Any]:
    """
    Convenience function to get routing configuration for a skill.
    
    Args:
        skill_id: Unique skill identifier
    
    Returns:
        Dictionary with primary, fallback, and escalation model configs
    """
    router = ModelRouter()
    return router.get_routing_config(skill_id)
