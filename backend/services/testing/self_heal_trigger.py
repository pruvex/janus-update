"""
D24: Self-Heal Trigger Layer

Observes system health and automatically triggers run_self_healing_cycle
when health gates require intervention.

Gates:
1. Min Threshold: At least 1 degraded or critical skill
2. Cooldown: Uses D22 cooldown logic from CalibrationWinner
3. Sanity: Uses global_sanity_check from CalibrationWinner

STRICT GUARDRAILS:
- No model selection logic (delegates entirely to D22)
- No direct writes to model_routing.json
- Read-only on config files except for cooldown state
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

logger = logging.getLogger("janus_backend")

# Config paths relative to project root
ROUTING_CONFIG_PATH = "backend/config/model_routing.json"
SELF_HEAL_STATE_PATH = "backend/config/self_heal_state.json"

# Health thresholds (must match D23 get_system_health logic)
HEALTHY_THRESHOLD = 0.95
DEGRADED_THRESHOLD = 0.70


def _read_routing_config() -> Dict[str, Any]:
    """Read model_routing.json. Returns empty dict if unavailable."""
    try:
        routing_file = Path(ROUTING_CONFIG_PATH)
        if not routing_file.exists():
            logger.warning("[D24-TRIGGER] model_routing.json not found, skipping health check")
            return {}
        with open(routing_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[D24-TRIGGER] Failed to read routing config: {e}", exc_info=True)
        return {}


def _classify_skills(routing_config: Dict[str, Any]) -> Tuple[int, int, int]:
    """
    Classify skills by health status from metadata.pass_rate.
    Returns (healthy, degraded, critical) counts.
    """
    skill_mappings = routing_config.get("skill_mappings", {})
    healthy = degraded = critical = 0

    for skill_data in skill_mappings.values():
        pass_rate = skill_data.get("metadata", {}).get("pass_rate", 0.0)
        if pass_rate >= HEALTHY_THRESHOLD:
            healthy += 1
        elif pass_rate >= DEGRADED_THRESHOLD:
            degraded += 1
        else:
            critical += 1

    return healthy, degraded, critical


def auto_trigger_self_heal(dry_run: bool = False) -> Dict[str, Any]:
    """
    D24 Core Function: Observe system health and trigger self-heal if needed.

    Args:
        dry_run: If True, passes dry_run=True to the D22 cycle (no file writes)

    Returns:
        Dictionary with trigger result:
        - status: "triggered", "skipped_no_issues", "skipped_cooldown",
                  "skipped_sanity", "skipped_no_data", "failed"
        - details: Human-readable reason
    """
    result = {
        "status": None,
        "dry_run": dry_run,
        "gates": {
            "threshold": None,
            "cooldown": None,
            "sanity": None
        },
        "details": None
    }

    try:
        from backend.services.testing.test_runner import CalibrationWinner

        # ── READ: Health state from model_routing.json ──────────────────────
        routing_config = _read_routing_config()
        if not routing_config:
            result["status"] = "skipped_no_data"
            result["details"] = "model_routing.json unavailable or empty"
            logger.warning("[D24-TRIGGER] Skipped: no routing data available")
            return result

        # ── GATE 1: Min Threshold ────────────────────────────────────────────
        healthy, degraded, critical = _classify_skills(routing_config)
        unhealthy_count = degraded + critical

        logger.info(
            f"[D24-TRIGGER] Health snapshot: healthy={healthy}, "
            f"degraded={degraded}, critical={critical}"
        )

        if unhealthy_count < 1:
            result["status"] = "skipped_no_issues"
            result["gates"]["threshold"] = "pass"
            result["details"] = f"All {healthy} skills are healthy. No trigger needed."
            logger.info("[D24-TRIGGER] Gate 1 PASS: All skills healthy, no trigger needed")
            return result

        result["gates"]["threshold"] = "triggered"
        logger.info(
            f"[D24-TRIGGER] Gate 1 FAIL: {unhealthy_count} unhealthy skill(s) "
            f"(degraded={degraded}, critical={critical}) — evaluating further gates"
        )

        # ── GATE 2: Cooldown ─────────────────────────────────────────────────
        winner = CalibrationWinner()
        cooldown_allowed, cooldown_reason = winner._check_cooldown()

        if not cooldown_allowed:
            result["status"] = "skipped_cooldown"
            result["gates"]["cooldown"] = "blocked"
            result["details"] = cooldown_reason
            logger.info(f"[D24-TRIGGER] Gate 2 BLOCKED: {cooldown_reason}")
            return result

        result["gates"]["cooldown"] = "pass"
        logger.info(f"[D24-TRIGGER] Gate 2 PASS: Cooldown clear — {cooldown_reason}")

        # ── GATE 3: Sanity Check ─────────────────────────────────────────────
        # Load historical data to run sanity check on
        historical_data = winner.load_historical_test_data()

        if not historical_data:
            result["status"] = "skipped_no_data"
            result["gates"]["sanity"] = "no_data"
            result["details"] = "No historical data available for sanity check"
            logger.warning("[D24-TRIGGER] Gate 3: No historical data for sanity check, aborting")
            return result

        sanity_ok, sanity_reason = winner.global_sanity_check(historical_data)

        if not sanity_ok:
            result["status"] = "skipped_sanity"
            result["gates"]["sanity"] = "blocked"
            result["details"] = sanity_reason
            logger.warning(f"[D24-TRIGGER] Gate 3 BLOCKED: {sanity_reason}")
            return result

        result["gates"]["sanity"] = "pass"
        logger.info(f"[D24-TRIGGER] Gate 3 PASS: {sanity_reason}")

        # ── EXECUTION: All gates green — trigger D22 ─────────────────────────
        logger.info(
            f"[D24-TRIGGER] All gates GREEN. Launching D22 self-heal cycle "
            f"(dry_run={dry_run})..."
        )

        cycle_result = winner.run_self_healing_cycle(dry_run=dry_run)

        result["status"] = "triggered"
        result["details"] = (
            f"Self-heal cycle executed. "
            f"Status={cycle_result.get('status')}, "
            f"Updated={cycle_result.get('skills_updated', 0)}, "
            f"Skipped={cycle_result.get('skills_skipped', 0)}"
        )
        result["cycle_result"] = cycle_result

        logger.info(f"[D24-TRIGGER] Trigger complete: {result['details']}")
        return result

    except Exception as e:
        logger.error(f"[D24-TRIGGER] Unexpected error: {e}", exc_info=True)
        result["status"] = "failed"
        result["details"] = str(e)
        return result
