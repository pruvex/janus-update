"""
Feature flags and bounded config for the auxiliary intent classifier.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() == "true"


INTENT_BENCHMARK_MODE = _env_flag("INTENT_BENCHMARK_MODE")
INTENT_AUX_CLASSIFIER_ENABLED = _env_flag("INTENT_AUX_CLASSIFIER_ENABLED")
INTENT_CONFIDENCE_ROUTING_ENABLED = _env_flag("INTENT_CONFIDENCE_ROUTING_ENABLED")
INTENT_REGEX_FREEZE = _env_flag("INTENT_REGEX_FREEZE")
INTENT_ENTITY_FIRST_ENABLED = _env_flag("INTENT_ENTITY_FIRST_ENABLED")
INTENT_SKIP_DETECT_ENABLED = _env_flag("INTENT_SKIP_DETECT_ENABLED", "true")


@dataclass(frozen=True)
class IntentAuxClassifierConfig:
    """Bounded runtime config for the auxiliary classifier slice."""

    enabled: bool = INTENT_AUX_CLASSIFIER_ENABLED
    provider: str = os.getenv("INTENT_AUX_PROVIDER", "openai")
    model_id: str = os.getenv("INTENT_AUX_MODEL_ID", "gpt-5.4-nano")
    high_confidence_threshold: float = 0.80
    medium_confidence_threshold: float = 0.55
    circuit_failure_threshold: int = 3
    circuit_recovery_timeout_seconds: int = 120
    max_output_tokens: int = 20


_DEFAULT_AUX_CONFIG = IntentAuxClassifierConfig()


def get_intent_aux_classifier_config() -> IntentAuxClassifierConfig:
    return _DEFAULT_AUX_CONFIG


def is_aux_classifier_enabled() -> bool:
    return get_intent_aux_classifier_config().enabled
