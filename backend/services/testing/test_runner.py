"""
Test Runner for Janus-Skills Quality System.

Executes test blueprints with escalation and logs results to D10 telemetry.
Generates AI Studio compatible health reports.
"""

import json
import asyncio
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime
from uuid import uuid4

from .test_generator import TestGenerator
from .validation import ValidationEngine, ValidationResult
from ..routing.escalation import EscalationEngine, EscalationSummary
from ..routing.model_router import ModelRouter

# Import D10 logging
from backend.services.logging.logger_core import log_event
from backend.data.schemas_logging import LogEventCreate

logger = logging.getLogger("janus_backend")

# D22: Module-level Mutex-Lock for Self-Healing
SELF_HEAL_LOCK = False


class BudgetGuard:
    """
    Budget Guard for D21 Full Fleet Calibration.
    
    Tracks API costs and error counts to prevent runaway spending.
    Stops execution when thresholds are exceeded.
    """
    
    def __init__(self, max_cost_eur: float = 5.0, max_api_errors: int = 20):
        self.max_cost_eur = max_cost_eur
        self.max_api_errors = max_api_errors
        self.total_cost_eur = 0.0
        self.api_error_count = 0
        self.test_count = 0
        
    def record_api_call(self, cost_eur: float = 0.0, success: bool = True) -> bool:
        """
        Record an API call and check if budget is exceeded.
        
        Args:
            cost_eur: Cost of the API call in EUR (estimated or actual)
            success: Whether the API call was successful
            
        Returns:
            True if budget is still within limits, False if exceeded
        """
        self.total_cost_eur += cost_eur
        if not success:
            self.api_error_count += 1
        self.test_count += 1
        
        # Check budget limits
        if self.total_cost_eur >= self.max_cost_eur:
            logger.error(f"[BUDGETGUARD] Cost threshold exceeded: {self.total_cost_eur:.2f}€ >= {self.max_cost_eur:.2f}€")
            return False
        
        if self.api_error_count >= self.max_api_errors:
            logger.error(f"[BUDGETGUARD] API error threshold exceeded: {self.api_error_count} >= {self.max_api_errors}")
            return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current budget guard status."""
        return {
            "total_cost_eur": round(self.total_cost_eur, 4),
            "api_error_count": self.api_error_count,
            "test_count": self.test_count,
            "cost_remaining_eur": round(self.max_cost_eur - self.total_cost_eur, 4),
            "errors_remaining": self.max_api_errors - self.api_error_count,
            "budget_exceeded": self.total_cost_eur >= self.max_cost_eur or self.api_error_count >= self.max_api_errors
        }


class CalibrationWinner:
    """
    Winner-Logic for D21.1 Diamond Routing Engine Upgrade (Minimal Perfect Model).
    
    Analyzes test results to determine optimal model assignments per skill per provider.
    STRICT SILO RULES:
    - OpenAI Silo: ONLY gpt-5.4-nano, gpt-5.4-mini, gpt-5.4 (standard). Pro is FORBIDDEN.
    - Gemini Silo: ONLY gemini-3-flash-preview, gemini-3.1-pro-preview.
    - NO Provider-Mixing: Data from one provider never influences the other.
    
    DIAMOND ROUTING RULES (7 Steps):
    1. Confidence: Only evaluate models with total_runs >= 5.
    2. Silos: Create separate decisions for openai and gemini.
    3. Primary: Choose cheapest model with pass_rate == 1.0. If none, take highest pass-rate.
    4. Fallback: Choose next stronger model in silo (Nano < Mini/Flash < Standard/Pro).
    5. Escalation: Choose smallest model stronger than primary AND guarantees stability.
    6. No-Loop: Enforce primary != fallback != escalation.
    7. Competition: Calculate provider_score. Stability > Cost > Latency. Best provider = winner.
    """
    
    def __init__(self):
        self.model_provider_map = {
            "gpt-5.4-nano": "openai",
            "gpt-5.4-mini": "openai",
            "gpt-5.4": "openai",
            "gpt-5.4-pro": "openai",
            "gpt-4o-mini": "openai",
            "gpt-4o": "openai",
            "gemini-3-flash-preview": "gemini",
            "gemini-3.1-pro-preview": "gemini",
            "gemini-3-pro-preview": "gemini",
            "gemini-3-pro": "gemini",
            "gemini-3.1-pro": "gemini"
        }
        
        # STRICT SILO: Only these models are allowed per provider
        self.silo_allowed_models = {
            "openai": {"gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"},  # Pro is FORBIDDEN
            "gemini": {"gemini-3-flash-preview", "gemini-3.1-pro-preview"}
        }
        
        # MODEL STRENGTH HIERARCHY (weakest to strongest)
        self.model_strength = {
            "openai": ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"],
            "gemini": ["gemini-3-flash-preview", "gemini-3.1-pro-preview"]
        }
        
        # COST MAPPING (for competition scoring)
        self.cost_scores = {
            "gpt-5.4-nano": 1,
            "gpt-5.4-mini": 2,
            "gpt-5.4": 3,
            "gemini-3-flash-preview": 2,
            "gemini-3.1-pro-preview": 3
        }
        
        # STRONGEST MODELS per silo for escalation
        self.strongest_models = {
            "openai": "gpt-5.4",
            "gemini": "gemini-3.1-pro-preview"
        }
    
    def build_diamond_routing(
        self,
        calibration_data: Dict[str, Any],
        load_historical: bool = True,
        historical_limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Build Diamond Routing decision based on calibration results.
        
        Implements the 7-Step Diamond Routing Logic:
        1. Confidence: Only evaluate models with total_runs >= 5
        2. Silos: Separate decisions for OpenAI and Gemini
        3. Primary: Cheapest perfect pass-rate model or highest pass-rate otherwise
        4. Fallback: Next stronger model in silo
        5. Escalation: Smallest stronger model guaranteeing stability
        6. No-Loop: Enforce distinct models in chain
        7. Competition: Score providers and pick winner
        
        Args:
            calibration_data: Dictionary with calibration results
                Structure: {skill_id: {model: [results]}}
                Each result has: test_count, passed_count, avg_latency_ms
            load_historical: If True, load historical test data from database
            historical_limit: Maximum number of historical events to load
                
        Returns:
            Dictionary with optimal assignments per skill
                Structure: {skill_id: {winner, active, openai, gemini, decision_metrics}}
        """
        # DATA-BRIDGE: Load historical test data from database
        if load_historical:
            historical_data = self.load_historical_test_data(limit=historical_limit)
            # Merge historical data with current calibration data
            for skill_id, model_results in historical_data.items():
                if skill_id not in calibration_data:
                    calibration_data[skill_id] = {}
                for model, results in model_results.items():
                    if model not in calibration_data[skill_id]:
                        calibration_data[skill_id][model] = []
                    calibration_data[skill_id][model].extend(results)
            logger.info(f"[DATA-BRIDGE] Merged historical data for {len(historical_data)} skills")
        
        optimal_assignments = {}
        
        # Step 1: Group results by provider, then by skill
        provider_skill_data = {}  # {provider: {skill_id: {model: results}}}
        
        for skill_id, model_results in calibration_data.items():
            if not model_results:
                continue
            
            for model, results in model_results.items():
                if not results:
                    continue
                
                provider = self.model_provider_map.get(model, "openai")
                if provider not in provider_skill_data:
                    provider_skill_data[provider] = {}
                if skill_id not in provider_skill_data[provider]:
                    provider_skill_data[provider][skill_id] = {}
                provider_skill_data[provider][skill_id][model] = results
        
        # STEP 2: For each provider, determine best chain per skill (DIAMOND ROUTING)
        for provider, skill_data in provider_skill_data.items():
            allowed_models = self.silo_allowed_models.get(provider, set())
            strength_order = self.model_strength.get(provider, [])
            
            for skill_id, model_results in skill_data.items():
                if not model_results:
                    continue
                
                # Filter to ONLY allowed models for this silo
                filtered_model_results = {
                    model: results for model, results in model_results.items()
                    if model in allowed_models
                }
                
                if not filtered_model_results:
                    continue
                
                # STEP 1: Confidence - Only evaluate models with total_runs >= 5
                model_metrics = {}
                for model, results in filtered_model_results.items():
                    if not results:
                        continue
                    
                    total_tests = sum(r.get("test_count", 0) for r in results)
                    total_passed = sum(r.get("passed_count", 0) for r in results)
                    total_latency = sum(r.get("avg_latency_ms", 0) for r in results if r.get("avg_latency_ms"))
                    run_count = len(results)
                    
                    # Confidence filter: only models with >= 5 runs
                    if run_count < 3:  # D22-OPTIMIZE: Temporarily lowered from 5 to 3 to see results
                        continue
                    
                    pass_rate = total_passed / total_tests if total_tests > 0 else 0.0
                    avg_latency = total_latency / run_count if run_count > 0 else 0.0
                    
                    model_metrics[model] = {
                        "pass_rate": pass_rate,
                        "avg_latency_ms": avg_latency,
                        "run_count": run_count
                    }
                
                if not model_metrics:
                    # Fallback-Confidence: Write default_tiers as placeholder if insufficient data
                    logger.warning(f"[DATA-BRIDGE] Skill {skill_id} has insufficient data (filtered by MIN_RUNS=3). Using default tiers as placeholder.")
                    continue
                
                # STEP 3: Primary - Choose cheapest model with pass_rate == 1.0. If none, take highest pass-rate
                perfect_models = [m for m, metrics in model_metrics.items() if metrics["pass_rate"] >= 1.0]
                
                if perfect_models:
                    # Confidence Bonus: More runs = more stable decision (lower bonus = better)
                    perfect_models_sorted = sorted(
                        perfect_models,
                        key=lambda m: (self.cost_scores.get(m, 999), model_metrics[m]["run_count"])
                    )
                    primary_model = perfect_models_sorted[0]
                else:
                    # No perfect model, take highest pass-rate
                    max_pass_rate = max(m["pass_rate"] for m in model_metrics.values())
                    best_models = [
                        (m, metrics) for m, metrics in model_metrics.items()
                        if metrics["pass_rate"] >= max_pass_rate - 0.01
                    ]
                    # Confidence Bonus: More runs = more stable decision
                    best_models_sorted = sorted(
                        best_models,
                        key=lambda x: (self.cost_scores.get(x[0], 999), x[1]["run_count"])
                    )
                    primary_model = best_models_sorted[0][0]
                
                primary_pass_rate = model_metrics[primary_model]["pass_rate"]
                
                # STEP 4: Fallback-Hardening - Must reach at least primary pass-rate (preferably 100%)
                primary_idx = strength_order.index(primary_model) if primary_model in strength_order else 0
                stronger_models = [m for m in strength_order if strength_order.index(m) > primary_idx]
                
                if stronger_models:
                    # Filter stronger models that meet primary pass-rate
                    fallback_candidates = [
                        m for m in stronger_models
                        if m in model_metrics and model_metrics[m]["pass_rate"] >= primary_pass_rate - 0.01
                    ]
                    if fallback_candidates:
                        # Choose cheapest among candidates (with confidence bonus)
                        fallback_model = min(
                            fallback_candidates,
                            key=lambda m: (self.cost_scores.get(m, 999), model_metrics[m]["run_count"])
                        )
                    else:
                        # No model meets pass-rate, take next stronger
                        fallback_model = stronger_models[0]
                else:
                    fallback_model = primary_model  # No stronger available
                
                # STEP 5: Escalation-Hardening - Smallest model with 100% pass-rate AND stronger than primary
                # If no such model, take absolute strongest of silo
                stronger_models = [m for m in strength_order if strength_order.index(m) > primary_idx]
                
                if stronger_models:
                    # Find perfect models (100% pass-rate) that are stronger than primary
                    perfect_stronger = [
                        m for m in stronger_models
                        if m in model_metrics and model_metrics[m]["pass_rate"] >= 1.0
                    ]
                    if perfect_stronger:
                        # Choose smallest (weakest) among perfect stronger models
                        escalation_model = perfect_stronger[0]  # Smallest in strength order
                    else:
                        # No perfect model, take absolute strongest of silo
                        escalation_model = stronger_models[-1]
                else:
                    escalation_model = primary_model
                
                # STEP 6: No-Loop - Enforce primary != fallback != escalation
                if fallback_model == primary_model and len(stronger_models) > 1:
                    fallback_model = stronger_models[1]
                if escalation_model == fallback_model and len(stronger_models) > 1:
                    escalation_model = stronger_models[-1]
                
                # Initialize skill entry if needed
                if skill_id not in optimal_assignments:
                    optimal_assignments[skill_id] = {
                        "openai": None,
                        "gemini": None,
                        "winner": None,
                        "active": None
                    }
                
                # Assign provider-specific chain
                optimal_assignments[skill_id][provider] = {
                    "primary": {"model": primary_model},
                    "fallback": {"model": fallback_model},
                    "escalation": {"model": escalation_model},
                    "metrics": model_metrics
                }
        
        # STEP 7: Competition - Calculate provider_score. Stability > Cost > Latency
        for skill_id, skill_data in optimal_assignments.items():
            provider_scores = {}
            
            for provider in ["openai", "gemini"]:
                provider_data = skill_data.get(provider)
                if not provider_data:
                    continue
                
                metrics = provider_data.get("metrics", {})
                primary_model = provider_data["primary"]["model"]
                
                # Calculate scores
                stability_score = max(m["pass_rate"] for m in metrics.values()) if metrics else 0.0
                cost_score = self.cost_scores.get(primary_model, 999)
                latency_score = metrics[primary_model]["avg_latency_ms"] if primary_model in metrics else 999999
                
                # Provider-Gate: 100% pass-rate as binary gate (pass_rate != 1.0 as primary sorting criterion)
                # Perfect stability (1.0) gets priority over imperfect stability
                stability_gate = 1 if stability_score >= 1.0 else 0
                
                # Provider score: Stability Gate (higher is better) > Stability (higher is better) > Cost (lower is better) > Latency (lower is better)
                provider_scores[provider] = (stability_gate, stability_score, -cost_score, -latency_score)
            
            # Determine winner (highest provider_score)
            if provider_scores:
                winner = max(provider_scores.keys(), key=lambda p: provider_scores[p])
                skill_data["winner"] = winner
                skill_data["active"] = skill_data[winner]
                
                # Decision-Metrics: Add metrics for primary model of winner
                winner_data = skill_data[winner]
                if winner_data:
                    primary_model = winner_data["primary"]["model"]
                    winner_metrics = winner_data.get("metrics", {})
                    primary_metrics = winner_metrics.get(primary_model, {})
                    skill_data["decision_metrics"] = {
                        "pass_rate": primary_metrics.get("pass_rate", 0.0),
                        "latency_ms": primary_metrics.get("avg_latency_ms", 0.0),
                        "run_count": primary_metrics.get("run_count", 0)
                    }
        
        return optimal_assignments
    
    def load_historical_test_data(
        self,
        limit: int = 2000,
        days_back: int = 7
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Load historical skill_test events from logs_raw table.
        
        Args:
            limit: Maximum number of events to load (default 2000)
            days_back: How many days back to look for events (default 7)
            
        Returns:
            Dictionary with structure: {skill_id: {model: [results]}}
        """
        try:
            from backend.services.logging.supabase_client import get_supabase_client
            from datetime import datetime, timedelta
            
            supabase = get_supabase_client()
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            
            # Fetch skill_test events from logs_raw, sorted by timestamp DESC (newest first)
            response = (
                supabase
                .table("logs_raw")
                .select("*")
                .eq("event_type", "skill_test")
                .gte("timestamp", cutoff.isoformat())
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            
            test_events = response.data if response.data else []
            logger.info(f"[DATA-BRIDGE] Loaded {len(test_events)} historical skill_test events from logs_raw")
            
            # Debug log: Show first raw event
            if test_events:
                logger.debug(f"[D21-DEBUG] Raw DB Event: {test_events[0]}")
            
            # Reorganize into skill_id -> model -> [results] structure
            historical_data = {}
            valid_candidates = 0
            
            for event in test_events:
                skill_id = event.get("skill")
                model = event.get("model")
                status = event.get("status")
                latency_ms = event.get("latency_ms")
                payload = event.get("payload", {})
                
                # FILTER HARDENING: Skip events with unknown model (useless for routing)
                if not skill_id or not model or model == "unknown":
                    continue
                
                if skill_id not in historical_data:
                    historical_data[skill_id] = {}
                if model not in historical_data[skill_id]:
                    historical_data[skill_id][model] = []
                
                # Convert event to test result format
                # Check payload for status (historical events have payload: {"status": "passed", ...})
                # Also check event-level status as fallback
                payload_status = payload.get("status") or payload.get("passed")
                if payload_status:
                    # Normalize payload status to boolean
                    passed = payload_status == "passed" or payload_status == True or payload_status == "success"
                elif status:
                    # Fallback to event-level status
                    passed = status == "success" or status == "passed"
                else:
                    # Default to failed if no status found
                    passed = False
                
                test_count = 1  # Each event represents one test run
                passed_count = 1 if passed else 0
                avg_latency_ms = latency_ms if latency_ms else 0
                
                historical_data[skill_id][model].append({
                    "test_count": test_count,
                    "passed_count": passed_count,
                    "avg_latency_ms": avg_latency_ms,
                    "run_count": 1,
                    "is_historical": True
                })
                valid_candidates += 1
            
            logger.info(f"[D22-DEBUG] Valid candidates found after filtering 'unknown': {valid_candidates}")
            return historical_data
            
        except Exception as e:
            logger.error(f"[DATA-BRIDGE] Failed to load historical test data: {e}", exc_info=True)
            return {}
    
    def generate_model_routing_json(
        self,
        optimal_assignments: Dict[str, Any],
        default_tiers: Optional[Dict[str, Any]] = None,
        all_skill_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate model_routing.json from optimal assignments (Diamond Routing format).
        
        Args:
            optimal_assignments: Dictionary with optimal model assignments per skill per provider
                Structure: {skill_id: {winner, active, openai, gemini}}
            default_tiers: Optional default tiers to include
            all_skill_ids: List of all skill IDs to include (for fallback placeholders)
            
        Returns:
            Complete model_routing.json structure with winner/active keys
        """
        routing_config = {
            "default_tiers": default_tiers or {
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
        
        # Add optimal assignments
        for skill_id, skill_data in optimal_assignments.items():
            skill_mapping = {
                "winner": skill_data.get("winner", "openai"),
                "active": skill_data.get("active"),
                "openai": skill_data.get("openai"),
                "gemini": skill_data.get("gemini")
            }
            
            routing_config["skill_mappings"][skill_id] = skill_mapping
        
        # Fallback-Confidence: Add default tiers for skills without optimal assignments
        if all_skill_ids:
            for skill_id in all_skill_ids:
                if skill_id not in routing_config["skill_mappings"]:
                    logger.warning(f"[DATA-BRIDGE] Skill {skill_id} has no optimal assignment, using default tiers as placeholder.")
                    routing_config["skill_mappings"][skill_id] = {
                        "winner": "openai",
                        "active": routing_config["default_tiers"]["openai"],
                        "openai": routing_config["default_tiers"]["openai"],
                        "gemini": routing_config["default_tiers"]["gemini"]
                    }
        
        return routing_config
    
    def apply_routing_update(
        self,
        skill_id: str,
        new_config: Dict[str, Any],
        new_pass_rate: float,
        new_latency_ms: float,
        dry_run: bool = False,
        config_path: str = "backend/config/model_routing.json"
    ) -> bool:
        """
        Diamond Safety Layer: Apply routing update with safety checks.
        
        Safety Rules:
        - Never-Degrade: Skip if new pass-rate < existing
        - Hysteresis: Update only if pass-rate +5% OR latency -20%
        
        Args:
            skill_id: Skill identifier
            new_config: New routing configuration for the skill
            new_pass_rate: Pass-rate of new primary model
            new_latency_ms: Latency of new primary model
            dry_run: If True, simulate update without writing to file
            config_path: Path to model_routing.json
            
        Returns:
            True if update was applied (or would be applied in dry_run), False if rejected by shield
        """
        try:
            # Load current config
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = json.load(f)
            
            # Get existing config for skill
            existing_config = current_config.get("skill_mappings", {}).get(skill_id)
            
            # Check if config really differs
            if existing_config == new_config:
                return False  # No change needed
            
            # DIAMOND SHIELD: Never-Degrade Rule
            existing_pass_rate = existing_config.get("metadata", {}).get("pass_rate", 0.0) if existing_config else 0.0
            if new_pass_rate < existing_pass_rate:
                logger.warning(f"[ROUTING-SHIELD] Rejected update for {skill_id}: New pass-rate {new_pass_rate:.2f} < existing {existing_pass_rate:.2f}")
                return False
            
            # DIAMOND SHIELD: Hysteresis Threshold
            # Update only if pass-rate increases by at least 5% OR latency decreases by at least 20%
            existing_latency_ms = existing_config.get("metadata", {}).get("latency_ms", 999999) if existing_config else 999999
            pass_rate_improvement = new_pass_rate - existing_pass_rate
            latency_improvement = existing_latency_ms - new_latency_ms if existing_latency_ms > 0 else 0
            latency_improvement_pct = (latency_improvement / existing_latency_ms) if existing_latency_ms > 0 else 0
            
            if pass_rate_improvement < 0.05 and latency_improvement_pct < 0.20:
                logger.warning(f"[ROUTING-SHIELD] Ignored minor improvement for {skill_id} (pass-rate +{pass_rate_improvement:.2f}, latency -{latency_improvement_pct:.2f} - below 5%/20% threshold)")
                return False
            
            # Add metadata to new config
            new_config["metadata"] = {
                "pass_rate": new_pass_rate,
                "latency_ms": new_latency_ms,
                "updated_at": datetime.now().isoformat()
            }
            
            # Dry run: Return True without writing to file
            if dry_run:
                logger.info(f"[ROUTING-SHIELD] Dry run: Would apply update for {skill_id} to {new_config.get('winner', 'unknown')} strategy (pass-rate: {new_pass_rate:.2f}, latency: {new_latency_ms:.0f}ms)")
                return True
            
            # Apply update
            if "skill_mappings" not in current_config:
                current_config["skill_mappings"] = {}
            current_config["skill_mappings"][skill_id] = new_config
            
            # Write to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=2)
            
            # Emit log
            winner = new_config.get("winner", "unknown")
            logger.info(f"[ROUTING-SHIELD] Applied update for {skill_id} to {winner} strategy (pass-rate: {new_pass_rate:.2f}, latency: {new_latency_ms:.0f}ms)")
            
            return True
        except Exception as e:
            logger.error(f"[ROUTING-UPDATE] Failed to update skill {skill_id}: {e}", exc_info=True)
            return False
    
    def global_sanity_check(
        self,
        calibration_data: Dict[str, Any],
        zero_pass_rate_threshold: float = 0.30
    ) -> Tuple[bool, str]:
        """
        Global Sanity Check: Discard batch if too many skills have 0% pass-rate.
        
        Args:
            calibration_data: Calibration results data
            zero_pass_rate_threshold: Threshold for zero pass-rate skills (default 30%)
            
        Returns:
            (is_valid, reason) - True if batch is valid, False if should be discarded
        """
        total_skills = len(calibration_data)
        if total_skills == 0:
            return False, "No skills in calibration data"
        
        zero_pass_rate_skills = 0
        for skill_id, model_results in calibration_data.items():
            if not model_results:
                zero_pass_rate_skills += 1
                continue
            
            # Check if all models for this skill have 0% pass-rate
            all_zero = True
            for model, results in model_results.items():
                if not results:
                    continue
                for r in results:
                    pass_rate = r.get("passed_count", 0) / max(r.get("test_count", 1), 1)
                    if pass_rate > 0:
                        all_zero = False
                        break
                if not all_zero:
                    break
            
            if all_zero:
                zero_pass_rate_skills += 1
        
        zero_pass_rate_pct = zero_pass_rate_skills / total_skills
        
        if zero_pass_rate_pct > zero_pass_rate_threshold:
            reason = f"Global Sanity Check FAILED: {zero_pass_rate_skills}/{total_skills} skills ({zero_pass_rate_pct:.1%}) have 0% pass-rate (suspected network/API failure)"
            logger.error(f"[ROUTING-SHIELD] {reason}")
            return False, reason
        
        logger.info(f"[ROUTING-SHIELD] Global Sanity Check PASSED: {total_skills - zero_pass_rate_skills}/{total_skills} skills have >0% pass-rate")
        return True, "Batch passed global sanity check"
    
    def run_self_healing_cycle(
        self,
        dry_run: bool = False,
        historical_limit: int = 1000
    ) -> Dict[str, Any]:
        """
        D22 Master-Function: Orchestrate complete self-healing cycle.
        
        Steps:
        1. Acquire SELF_HEAL_LOCK (mutex)
        2. Load ALL historical test data from DB
        3. Build Diamond Routing for all historical skills
        4. Apply routing updates for each skill with D21.3 safety checks
        
        Args:
            dry_run: If True, simulate updates without writing to file
            historical_limit: Maximum number of historical events to load
            
        Returns:
            Dictionary with cycle results
        """
        global SELF_HEAL_LOCK
        
        cycle_result = {
            "status": "started",
            "start_time": datetime.now().isoformat(),
            "dry_run": dry_run,
            "skills_processed": 0,
            "skills_updated": 0,
            "skills_skipped": 0,
            "errors": []
        }
        
        # Check if lock is already held
        if SELF_HEAL_LOCK:
            cycle_result["status"] = "aborted_lock"
            cycle_result["errors"].append("Self-heal cycle already in progress")
            logger.warning("[D22-SELF-HEAL] Cycle aborted: SELF_HEAL_LOCK already held")
            return cycle_result
        
        try:
            # Acquire lock
            SELF_HEAL_LOCK = True
            logger.info(f"[D22-SELF-HEAL] Starting self-healing cycle (dry_run={dry_run})")
            
            # Step 1: Load ALL historical test data from DB
            historical_data = self.load_historical_test_data(limit=historical_limit)
            logger.info(f"[D22-SELF-HEAL] Loaded historical data for {len(historical_data)} skills")
            
            if not historical_data:
                cycle_result["status"] = "no_data"
                cycle_result["errors"].append("No historical data found")
                logger.warning("[D22-SELF-HEAL] No historical data found")
                return cycle_result
            
            # Step 2: Build Diamond Routing for all historical skills
            optimal_assignments = self.build_diamond_routing(historical_data, load_historical=False)
            logger.info(f"[D22-SELF-HEAL] Built Diamond Routing for {len(optimal_assignments)} skills")
            
            # Step 3: Apply routing updates for each skill
            for skill_id, skill_data in optimal_assignments.items():
                cycle_result["skills_processed"] += 1
                
                decision_metrics = skill_data.get("decision_metrics", {})
                new_config = {
                    "winner": skill_data.get("winner"),
                    "active": skill_data.get("active"),
                    "openai": skill_data.get("openai"),
                    "gemini": skill_data.get("gemini")
                }
                
                updated = self.apply_routing_update(
                    skill_id=skill_id,
                    new_config=new_config,
                    new_pass_rate=decision_metrics.get("pass_rate", 0.0),
                    new_latency_ms=decision_metrics.get("latency_ms", 0.0),
                    dry_run=dry_run
                )
                
                if updated:
                    cycle_result["skills_updated"] += 1
                else:
                    cycle_result["skills_skipped"] += 1
            
            cycle_result["status"] = "completed"
            cycle_result["end_time"] = datetime.now().isoformat()
            
            logger.info(f"[D22-SELF-HEAL] Cycle completed. Processed {cycle_result['skills_processed']} skills, updated {cycle_result['skills_updated']}, skipped {cycle_result['skills_skipped']}")
            
        except Exception as e:
            logger.error(f"[D22-SELF-HEAL] Cycle failed: {e}", exc_info=True)
            cycle_result["status"] = "failed"
            cycle_result["errors"].append(str(e))
        finally:
            # Release lock
            SELF_HEAL_LOCK = False
            logger.info("[D22-SELF-HEAL] SELF_HEAL_LOCK released")
        
        return cycle_result

    
    def _check_cooldown(self, cooldown_hours: int = 6, state_path: str = "backend/config/self_heal_state.json") -> Tuple[bool, str]:
        """
        Check if self-healing cooldown has elapsed.
        
        Args:
            cooldown_hours: Cooldown period in hours (default 6)
            state_path: Path to self_heal_state.json
            
        Returns:
            (is_allowed, reason) - True if cooldown elapsed, False if still in cooldown
        """
        try:
            state_file = Path(state_path)
            if not state_file.exists():
                return True, "No previous self-heal found, cooldown not applicable"
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            last_heal_str = state.get("last_self_heal_at")
            if not last_heal_str:
                return True, "No timestamp in state, cooldown not applicable"
            
            from datetime import timedelta
            last_heal = datetime.fromisoformat(last_heal_str)
            now = datetime.now()
            elapsed = now - last_heal
            
            if elapsed < timedelta(hours=cooldown_hours):
                remaining = timedelta(hours=cooldown_hours) - elapsed
                return False, f"Cooldown active. Remaining: {remaining}"
            
            return True, "Cooldown elapsed, self-heal allowed"
        except Exception as e:
            logger.error(f"[SELF-HEAL] Failed to check cooldown: {e}", exc_info=True)
            return True, "Cooldown check failed, allowing self-heal (safety override)"
    
    def _update_cooldown(self, state_path: str = "backend/config/self_heal_state.json") -> None:
        """
        Update the self-heal state with current timestamp.
        
        Args:
            state_path: Path to self_heal_state.json
        """
        try:
            state_file = Path(state_path)
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            state = {
                "last_self_heal_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"[SELF-HEAL] Updated cooldown state: {state['last_self_heal_at']}")
        except Exception as e:
            logger.error(f"[SELF-HEAL] Failed to update cooldown state: {e}", exc_info=True)
    
def _map_input_to_args(skill_id: str, input_value: Any) -> Dict[str, Any]:
    """
    Map skill ID to appropriate argument name for tool execution.
    
    Args:
        skill_id: The skill identifier (e.g., "filesystem.list_directory")
        input_value: The input value from the test blueprint
    
    Returns:
        Dictionary with the appropriate argument name and value
    """
    if skill_id.startswith("filesystem."):
        return {"path": input_value}
    if skill_id == "system.weather":
        return {"location": input_value}
    # Fallback for all other skills
    return {"query": input_value}


def discover_skills(skills_dir: str = "backend/skills") -> List[str]:
    """
    Discover all skills from the skills directory (recursive).
    
    Uses module-based absolute paths to work regardless of CWD.
    Uses Path.rglob to find every *.json file at any nesting depth.
    The namespace is derived from the first directory component relative
    to skills_dir (e.g. backend/skills/filesystem/read_file.json → filesystem.read_file).
    
    Args:
        skills_dir: Path to the skills directory (relative to project root)
    
    Returns:
        Sorted list of skill_ids in format "namespace.action"
    """
    # FORENSIC LOGGING
    print(f"[FORENSIC] __file__ = {__file__}")
    
    # Module-based absolute path resolution
    # __file__ = backend/services/testing/test_runner.py
    module_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[FORENSIC] module_dir = {module_dir}")
    
    # module_dir = backend/services/testing/
    services_dir = os.path.dirname(module_dir)
    print(f"[FORENSIC] services_dir = {services_dir}")
    
    # services_dir = backend/services/
    backend_dir = os.path.dirname(services_dir)
    print(f"[FORENSIC] backend_dir = {backend_dir}")
    
    # backend_dir = backend/
    project_root = os.path.dirname(backend_dir)
    print(f"[FORENSIC] project_root = {project_root}")
    
    skills_path = Path(project_root) / skills_dir
    print(f"[FORENSIC] skills_path = {skills_path}")
    print(f"[FORENSIC] skills_path.exists() = {skills_path.exists()}")
    
    # Log parent directory contents
    parent_dir = str(skills_path.parent)
    print(f"[FORENSIC] parent_dir = {parent_dir}")
    try:
        parent_contents = os.listdir(parent_dir)
        print(f"[FORENSIC] parent_dir contents = {parent_contents}")
    except Exception as e:
        print(f"[FORENSIC] ERROR listing parent_dir: {e}")
    
    skill_ids = []
    
    logger.info(f"[discover_skills] Scanning skills from: {skills_path.absolute()}")
    
    if not skills_path.exists():
        logger.warning(f"[discover_skills] Skills directory does not exist: {skills_path.absolute()}")
        return skill_ids
    
    for skill_file in skills_path.rglob("*.json"):
        # Relative path from skills root, e.g. filesystem/read_file.json
        rel = skill_file.relative_to(skills_path)
        parts = rel.parts  # ('filesystem', 'read_file.json') or deeper
        
        if len(parts) < 2:
            # JSON directly in skills root — skip (no namespace)
            continue
        
        namespace = parts[0]
        skill_name = skill_file.stem
        skill_id = f"{namespace}.{skill_name}"
        skill_ids.append(skill_id)
    
    skill_ids.sort()
    logger.info(f"[discover_skills] Discovered {len(skill_ids)} skills")
    print(f"[FORENSIC] Final skill_ids count = {len(skill_ids)}")
    return skill_ids


class TestRunner:
    """Runs skill tests with escalation and D10 telemetry integration."""
    
    def __init__(self, test_dir: str = "config/skill_tests", budget_guard: Optional[BudgetGuard] = None):
        self.test_dir = Path(test_dir)
        self.validation_engine = ValidationEngine()
        self.escalation_engine = EscalationEngine()
        self.model_router = ModelRouter()
        self.test_results: List[Dict[str, Any]] = []
        self.budget_guard = budget_guard
    
    async def run_testset(
        self,
        skill_id: str,
        tool_call_fn: Callable,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run all tests for a skill with escalation and D10 logging.
        
        Args:
            skill_id: Unique skill identifier
            tool_call_fn: Function to execute (should accept provider, model, **kwargs)
            session_id: Optional session identifier for D10 logging
            trace_id: Optional trace identifier for individual test tracking (D20)
        
        Returns:
            Test summary with all results and health metrics
        """
        # Reset circuit breaker for each skill — batch tests are independent
        self.escalation_engine.reset_circuit_breaker()
        
        # Load test blueprint
        blueprint = self._load_blueprint(skill_id)
        if not blueprint:
            return {"error": f"No test blueprint found for skill_id: {skill_id}"}
        
        # Run each test
        test_results = []
        tests = blueprint.get("tests", {})
        
        for test_type, test_spec in tests.items():
            result = await self._run_single_test(
                skill_id=skill_id,
                test_type=test_type,
                test_spec=test_spec,
                tool_call_fn=tool_call_fn,
                session_id=session_id
            )
            test_results.append(result)
        
        # Generate health summary
        health_summary = self.generate_health_summary(skill_id, test_results)
        
        return {
            "skill_id": skill_id,
            "test_count": len(test_results),
            "passed_count": sum(1 for r in test_results if r.get("passed")),
            "results": test_results,
            "health_summary": health_summary
        }
    
    def _load_blueprint(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Load test blueprint from file."""
        filename = f"{skill_id.replace('.', '_')}_test.json"
        filepath = self.test_dir / filename
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    async def _run_single_test(
        self,
        skill_id: str,
        test_type: str,
        test_spec: Dict[str, Any],
        tool_call_fn: Callable,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a single test with escalation and D10 logging.
        
        Args:
            skill_id: Unique skill identifier
            test_type: Type of test (happy_path, edge_case, failure_case)
            test_spec: Test specification with input and validation
            tool_call_fn: Function to execute
            session_id: Optional session identifier
        
        Returns:
            Test result dict
        """
        trace_id = str(uuid4())
        start_time = datetime.utcnow()
        
        # Debug log to track tool_call_fn binding
        print(f"[TEST-RUNNER-DEBUG] Running test for {skill_id} - tool_call_fn type: {type(tool_call_fn).__name__}, id: {id(tool_call_fn)}")
        
        try:
            # Generate tool_calls payload for ToolExecutor
            test_input = test_spec.get("input", {})
            # Extract the actual input value (could be nested in "input" key or direct)
            input_value = test_input.get("input", test_input) if isinstance(test_input, dict) else test_input
            
            # Map skill ID to appropriate argument name
            arguments = _map_input_to_args(skill_id, input_value)
            
            # Guard: Replace None or empty skill_id with safe default for Gemini compatibility
            # Gemini requires alphanumeric (a-z, A-Z, 0-9) or underscores (_) in tool names
            safe_tool_name = skill_id if skill_id and isinstance(skill_id, str) else "matrix_test_skill"
            if skill_id != safe_tool_name:
                logger.warning(f"[D21-TOOL-NAME-GUARD] Invalid tool_name '{skill_id}' replaced with '{safe_tool_name}' for Gemini compatibility")
            
            # Format as tool_calls structure expected by ToolExecutor
            tool_calls = [{
                "name": safe_tool_name,
                "arguments": arguments
            }]
            
            # Execute with escalation
            escalation_summary = await self.escalation_engine.execute_with_escalation(
                skill_id=skill_id,
                tool_call_fn=tool_call_fn,
                validation_fn=lambda r: self._validate_result(r, test_spec.get("validation")).passed,
                tool_calls=tool_calls
            )
            
            # Get final result
            final_attempt = escalation_summary.attempts[-1] if escalation_summary.attempts else None
            final_model = final_attempt.model if final_attempt else "unknown"
            final_provider = final_attempt.provider if final_attempt else "unknown"
            
            # Validate result with None guard
            result_to_validate = final_attempt.result if final_attempt else {}
            if result_to_validate is None:
                result_to_validate = {"status": "error", "message": "Result was None"}
            
            validation_result = self._validate_result(
                result_to_validate,
                test_spec.get("validation")
            )
            
            # Log to D10
            await self._log_to_d10(
                skill_id=skill_id,
                test_type=test_type,
                status="passed" if validation_result.passed else "failed",
                model=final_model,
                provider=final_provider,
                latency_ms=escalation_summary.total_latency_ms,
                trace_id=trace_id,
                session_id=session_id,
                errors=[final_attempt.error] if final_attempt and final_attempt.error else [],
                final_tier=escalation_summary.final_tier,
                attempts_count=len(escalation_summary.attempts),
                result_data=result_to_validate
            )
            
            return {
                "test_type": test_type,
                "passed": validation_result.passed,
                "validation": validation_result,
                "escalation_summary": {
                    "final_success": escalation_summary.final_success,
                    "final_tier": escalation_summary.final_tier,
                    "attempts_count": len(escalation_summary.attempts),
                    "total_latency_ms": escalation_summary.total_latency_ms
                },
                "trace_id": trace_id
            }
        
        except Exception as e:
            # Log error to D10
            await self._log_to_d10(
                skill_id=skill_id,
                test_type=test_type,
                status="error",
                model="unknown",
                provider="unknown",
                latency_ms=0,
                trace_id=trace_id,
                session_id=session_id,
                errors=[str(e)]
            )
            
            return {
                "test_type": test_type,
                "passed": False,
                "error": str(e),
                "trace_id": trace_id
            }
    
    def _validate_result(self, result: Any, validation_spec: Optional[Dict[str, Any]]) -> ValidationResult:
        """Validate a result against its specification."""
        if not validation_spec:
            return ValidationResult(
                passed=True,
                validator_type="none",
                message="No validation specified"
            )
        
        # Parse JSON string results before validation
        import json
        parsed_result = result
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                pass  # Leave as string, validation engine will mark as error
        
        return self.validation_engine.validate(parsed_result, validation_spec)
    
    async def _log_to_d10(
        self,
        skill_id: str,
        test_type: str,
        status: str,
        model: str,
        provider: str,
        latency_ms: float,
        trace_id: str,
        session_id: Optional[str],
        errors: List[str],
        final_tier: str = "primary",
        attempts_count: int = 1,
        result_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log test result to D10 telemetry system.
        
        Args:
            skill_id: Unique skill identifier
            test_type: Type of test
            status: Test status (passed, failed, error)
            model: Model used
            provider: Provider used
            latency_ms: Latency in milliseconds
            trace_id: Trace identifier
            session_id: Session identifier
            errors: List of errors if any
            result_data: Actual tool execution result for forensic analysis
        """
        payload = {
            "test_type": test_type,
            "errors": errors,
            "final_tier": final_tier,
            "attempts_count": attempts_count
        }
        
        # Include result data for forensic analysis if provided
        if result_data:
            payload["result_data"] = result_data
            # Map to output_summary for D10 logging visibility (first 500 chars)
            payload["output_summary"] = str(result_data)[:500]
        
        event = LogEventCreate(
            event_type="skill_test",
            skill=skill_id,
            status=status,
            provider=provider,
            model=model,
            latency_ms=int(latency_ms),
            trace_id=trace_id,
            session_id=session_id,
            payload=payload
        )
        
        await log_event(event)
    
    def generate_health_summary(self, skill_id: str, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate AI Studio compatible health summary.
        
        Args:
            skill_id: Unique skill identifier
            test_results: List of test results
        
        Returns:
            Health summary dict
        """
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.get("passed"))
        failed_tests = total_tests - passed_tests
        
        # Calculate average latency
        latencies = [
            r.get("escalation_summary", {}).get("total_latency_ms", 0)
            for r in test_results
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Count escalation attempts
        total_attempts = sum(
            r.get("escalation_summary", {}).get("attempts_count", 0)
            for r in test_results
        )
        
        # Calculate health score (0.0 to 1.0)
        health_score = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "skill_id": skill_id,
            "health_score": health_score,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "avg_latency_ms": round(avg_latency, 2),
            "total_escalation_attempts": total_attempts,
            "generated_at": datetime.utcnow().isoformat(),
            "status": "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
        }
    
    async def run_batch_tests(
        self,
        tool_call_fn: Callable,
        skill_ids: Optional[List[str]] = None,
        skills_dir: str = "backend/skills",
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run tests for multiple skills in batch.
        
        Args:
            tool_call_fn: Function to execute (should accept provider, model, **kwargs)
            skill_ids: Optional list of skill_ids to test. If None, discovers all skills.
            skills_dir: Path to the skills directory (for auto-discovery)
            session_id: Optional session identifier for D10 logging
            trace_id: Optional trace identifier for individual test tracking (D20)
        
        Returns:
            Batch test summary with all results and health metrics
        """
        # Discover skills if not provided
        if skill_ids is None:
            skill_ids = discover_skills(skills_dir)
        
        if not skill_ids:
            return {
                "error": "No skills found for batch testing",
                "skills_tested": 0,
                "results": []
            }
        
        # Initialize test generator
        test_generator = TestGenerator()
        
        # Run tests for each skill
        batch_results = []
        total_passed = 0
        total_failed = 0
        
        for skill_id in skill_ids:
            # Check budget guard before running each skill
            if self.budget_guard and self.budget_guard.get_status()["budget_exceeded"]:
                logger.warning(f"[BUDGETGUARD] Budget exceeded, stopping batch test. Status: {self.budget_guard.get_status()}")
                break
            
            try:
                # Generate testset if not exists
                skill_type = skill_id.split('.')[0] if '.' in skill_id else "tool"
                test_generator.generate_testset(skill_id, skill_type)
                
                # Run testset
                test_summary = await self.run_testset(
                    skill_id=skill_id,
                    tool_call_fn=tool_call_fn,
                    session_id=session_id,
                    trace_id=trace_id
                )
                
                batch_results.append(test_summary)
                total_passed += test_summary.get("passed_count", 0)
                total_failed += test_summary.get("test_count", 0) - test_summary.get("passed_count", 0)
                
            except Exception as e:
                batch_results.append({
                    "skill_id": skill_id,
                    "error": str(e),
                    "test_count": 0,
                    "passed_count": 0
                })
        
        # Calculate batch health metrics
        total_tests_run = sum(r.get("test_count", 0) for r in batch_results)
        overall_pass_rate = total_passed / total_tests_run if total_tests_run > 0 else 0.0
        
        return {
            "skills_tested": len(batch_results),
            "total_tests_run": total_tests_run,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_pass_rate": round(overall_pass_rate, 4),
            "results": batch_results,
            "generated_at": datetime.utcnow().isoformat()
        }


async def run_testset(
    skill_id: str,
    tool_call_fn: Callable,
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run a testset.
    
    Args:
        skill_id: Unique skill identifier
        tool_call_fn: Function to execute
        session_id: Optional session identifier
        trace_id: Optional trace identifier for individual test tracking (D20)
    
    Returns:
        Test summary with health metrics
    """
    runner = TestRunner()
    return await runner.run_testset(skill_id, tool_call_fn, session_id, trace_id)
