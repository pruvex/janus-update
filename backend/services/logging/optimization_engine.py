"""
Janus Optimization Engine (D13) — Rule-Based System Optimization.

Deterministische Regel-Engine für System-Optimierung basierend auf Insights.
Keine KI im Backend-Core. Nur reine Logik mit Schwellenwerten.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import logging

from backend.services.logging.supabase_client import get_supabase_client

logger = logging.getLogger("janus_backend")


# ─── Problem Classification (D17-PHASE-3) ────────────────────────────────────

TIMEOUT_THRESHOLD_MS = 3000


class ProblemCategory(str, Enum):
    """Classification categories for skill test problems."""
    MODEL_WEAKNESS = "MODEL_WEAKNESS"
    PROMPT_ISSUE = "PROMPT_ISSUE"
    VALIDATION_FAIL = "VALIDATION_FAIL"
    TIMEOUT = "TIMEOUT"
    HEALTHY = "HEALTHY"
    UNKNOWN = "UNKNOWN"


class SkillProblemProfile(BaseModel):
    """Aggregated problem profile for a skill."""
    skill_id: str
    total_runs: int
    dominant_category: ProblemCategory
    category_counts: Dict[str, int]
    category_rates: Dict[str, float]
    confidence: float
    recommendation: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


def classify_test_event(log: Dict[str, Any]) -> ProblemCategory:
    """
    Classify a single skill_test D10 event into a ProblemCategory.
    
    Rules (deterministic — NO AI, based on final_tier, status, attempts_count):
    - TIMEOUT:          status == "passed" AND latency_ms > TIMEOUT_THRESHOLD_MS
    - MODEL_WEAKNESS:   status == "passed" AND final_tier NOT in {primary, ""}
    - PROMPT_ISSUE:     status in {failed, error} AND attempts_count >= 2
    - VALIDATION_FAIL:  status == "failed" AND attempts_count <= 1
    - HEALTHY:          status == "passed" AND final_tier in {primary, ""}
    
    Args:
        log: D10 skill_test event dict
    
    Returns:
        ProblemCategory enum value
    """
    status = log.get("status", "unknown")
    latency_ms = log.get("latency_ms", 0) or 0
    payload = log.get("payload", {}) or {}
    final_tier = payload.get("final_tier", "primary") or "primary"
    attempts_count = payload.get("attempts_count", 1) or 1

    # TIMEOUT: passed but exceeded latency threshold
    if status == "passed" and latency_ms > TIMEOUT_THRESHOLD_MS:
        return ProblemCategory.TIMEOUT

    # MODEL_WEAKNESS: succeeded only after escalating beyond primary
    if status == "passed" and final_tier not in ("primary", "", "none"):
        return ProblemCategory.MODEL_WEAKNESS

    # PROMPT_ISSUE: all tiers tried and still failed
    if status in ("failed", "error") and attempts_count >= 2:
        return ProblemCategory.PROMPT_ISSUE

    # VALIDATION_FAIL: primary executed OK but validation caught a format issue
    if status == "failed" and attempts_count <= 1:
        return ProblemCategory.VALIDATION_FAIL

    # HEALTHY: passed on primary
    if status == "passed":
        return ProblemCategory.HEALTHY

    return ProblemCategory.UNKNOWN


class ProblemClassifier:
    """
    D17 Problem Classifier — Aggregates D10 skill_test events per skill and
    classifies the dominant failure pattern with a confidence score.
    
    Classification is strictly deterministic:
    - Based on: final_tier (payload), status, attempts_count (payload), latency_ms
    - Confidence: category_count / total_runs (frequency-based)
    """

    def __init__(self, hours: int = 24):
        self.hours = hours
        self.supabase = get_supabase_client()

    def fetch_test_events(self) -> List[Dict[str, Any]]:
        """Fetch skill_test events from D10 within the time window."""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=self.hours)
            response = (
                self.supabase
                .table("logs_raw")
                .select("*")
                .eq("event_type", "skill_test")
                .gte("timestamp", cutoff.isoformat())
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"[ProblemClassifier] Error fetching test events: {e}", exc_info=True)
            return []

    def classify_skills(self) -> Dict[str, SkillProblemProfile]:
        """
        Classify all skills based on their D10 test event history.
        
        Returns:
            Dict mapping skill_id -> SkillProblemProfile
        """
        events = self.fetch_test_events()

        if not events:
            return {}

        # Group events by skill_id
        by_skill: Dict[str, List[Dict]] = defaultdict(list)
        for event in events:
            skill_id = event.get("skill") or "unknown"
            by_skill[skill_id].append(event)

        profiles: Dict[str, SkillProblemProfile] = {}

        for skill_id, skill_events in by_skill.items():
            total_runs = len(skill_events)

            # Count each category
            category_counts: Dict[str, int] = defaultdict(int)
            for event in skill_events:
                cat = classify_test_event(event)
                category_counts[cat.value] += 1

            # Calculate rates
            category_rates = {
                cat: round(count / total_runs, 4)
                for cat, count in category_counts.items()
            }

            # Dominant category (most frequent non-HEALTHY, or HEALTHY if all good)
            non_healthy = {
                cat: count for cat, count in category_counts.items()
                if cat != ProblemCategory.HEALTHY.value
            }

            if non_healthy:
                dominant_cat_str = max(non_healthy, key=non_healthy.__getitem__)
                dominant_count = non_healthy[dominant_cat_str]
            else:
                dominant_cat_str = ProblemCategory.HEALTHY.value
                dominant_count = category_counts.get(ProblemCategory.HEALTHY.value, 0)

            dominant_category = ProblemCategory(dominant_cat_str)

            # Confidence = dominant_count / total_runs (frequency-based)
            confidence = round(dominant_count / total_runs, 4) if total_runs > 0 else 0.0

            # Generate recommendation
            recommendation = _build_recommendation(skill_id, dominant_category, category_rates, confidence)

            profiles[skill_id] = SkillProblemProfile(
                skill_id=skill_id,
                total_runs=total_runs,
                dominant_category=dominant_category,
                category_counts=dict(category_counts),
                category_rates=category_rates,
                confidence=confidence,
                recommendation=recommendation
            )

        return profiles


def _build_recommendation(
    skill_id: str,
    category: ProblemCategory,
    rates: Dict[str, float],
    confidence: float
) -> str:
    """Build a [PROVISIONAL] recommendation string for a given problem category."""
    pct = f"{confidence:.0%}"

    if category == ProblemCategory.MODEL_WEAKNESS:
        return (
            f"[PROVISIONAL] PRIMARY MODEL SWAP for {skill_id}. "
            f"Primary model fails {pct} of the time but escalated models succeed. "
            "Consider promoting the fallback model to primary in model_routing.json (manual change required)."
        )
    if category == ProblemCategory.PROMPT_ISSUE:
        return (
            f"[PROVISIONAL] PROMPT/SCHEMA REVIEW for {skill_id}. "
            f"Skill fails across ALL tiers in {pct} of runs. "
            "The tool schema or prompt template is likely malformed. Review the skill JSON and input contract."
        )
    if category == ProblemCategory.VALIDATION_FAIL:
        return (
            f"[PROVISIONAL] VALIDATION RULE REVIEW for {skill_id}. "
            f"Primary model executes but fails validation in {pct} of runs. "
            "The model likely hallucinates the output format. Tighten the prompt or relax the validation regex."
        )
    if category == ProblemCategory.TIMEOUT:
        return (
            f"[PROVISIONAL] LATENCY OPTIMIZATION for {skill_id}. "
            f"Tests pass but exceed {TIMEOUT_THRESHOLD_MS}ms in {pct} of runs. "
            "Consider switching to a faster model tier or enabling response caching."
        )
    if category == ProblemCategory.HEALTHY:
        return f"[PROVISIONAL] CONTINUE MONITORING {skill_id}. System is healthy — no action required."

    return f"[PROVISIONAL] INVESTIGATE {skill_id}. Unknown failure pattern detected."


class ActionPriority(str, Enum):
    """Priority levels for system actions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    """Types of system actions."""
    SCALE_UP = "SCALE_UP"
    SCALE_DOWN = "SCALE_DOWN"
    RETRY_CONFIG = "RETRY_CONFIG"
    TIMEOUT_ADJUST = "TIMEOUT_ADJUST"
    CACHE_ENABLE = "CACHE_ENABLE"
    LOAD_BALANCE = "LOAD_BALANCE"
    MODEL_SWITCH = "MODEL_SWITCH"
    MONITOR = "MONITOR"


class SystemAction(BaseModel):
    """System action generated by the Optimization Engine."""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()), description="Unique action identifier")
    skill_id: str = Field(..., alias="skill", description="Skill identifier (namespace.action format)")
    model: str = Field(..., description="Model name")
    action_type: ActionType = Field(..., description="Type of action")
    priority: ActionPriority = Field(..., description="Priority level")
    reason: str = Field(..., description="Reason for action")
    current_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold that triggered action")
    recommendation: str = Field(..., description="Specific recommendation")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of action generation")
    time_window_hours: int = Field(..., description="Time window used for analysis")


class OptimizationEngine:
    """
    Janus Optimization Engine — Rule-Based System Optimization.
    
    Reads logs_insights and generates SystemAction objects based on thresholds:
    - Error Rate > 0.3 → HIGH PRIORITY: SCALE_UP or MODEL_SWITCH
    - Latency > 3000ms → HIGH PRIORITY: TIMEOUT_ADJUST or MODEL_SWITCH
    - Error Rate > 0.5 → CRITICAL: MODEL_SWITCH
    """
    
    def __init__(self, hours: int = 1):
        """
        Initialize Optimization Engine.
        
        Args:
            hours: Time window in hours for insight analysis (default: 1)
        """
        self.hours = hours
        self.supabase = get_supabase_client()
        
        # Thresholds
        self.ERROR_THRESHOLD_HIGH = 0.3
        self.ERROR_THRESHOLD_CRITICAL = 0.5
        self.LATENCY_THRESHOLD_HIGH = 3000  # milliseconds
        self.LATENCY_THRESHOLD_CRITICAL = 5000  # milliseconds
    
    def fetch_insights(self) -> List[Dict[str, Any]]:
        """
        Fetch insights from logs_insights table.
        
        Returns:
            List of insight records
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=self.hours)
            
            response = (
                self.supabase
                .table("logs_insights")
                .select("*")
                .gte("generated_at", cutoff.isoformat())
                .execute()
            )
            
            insights = response.data if response.data else []
            return insights
        except Exception as e:
            logger.error(f"[OptimizationEngine] Error fetching insights: {e}", exc_info=True)
            return []
    
    def evaluate_insight(self, insight: Dict[str, Any]) -> Optional[SystemAction]:
        """
        Evaluate a single insight and generate action if thresholds are exceeded.
        
        Args:
            insight: Insight record from logs_insights
        
        Returns:
            SystemAction if threshold exceeded, None otherwise
        """
        skill_id = insight.get("skill", "unknown")
        model = insight.get("model", "unknown")
        error_rate = insight.get("error_rate", 0.0)
        avg_latency_ms = insight.get("avg_latency_ms", 0.0)
        
        # Rule 1: Critical Error Rate (> 0.5)
        if error_rate > self.ERROR_THRESHOLD_CRITICAL:
            return SystemAction(
                skill_id=skill_id,
                model=model,
                action_type=ActionType.MODEL_SWITCH,
                priority=ActionPriority.CRITICAL,
                reason=f"Critical error rate detected ({error_rate:.2%})",
                current_value=error_rate,
                threshold=self.ERROR_THRESHOLD_CRITICAL,
                recommendation=f"[PROVISIONAL] Switch model for {skill_id} immediately. Current model {model} has {error_rate:.2%} error rate.",
                time_window_hours=self.hours
            )
        
        # Rule 2: High Error Rate (> 0.3)
        if error_rate > self.ERROR_THRESHOLD_HIGH:
            return SystemAction(
                skill_id=skill_id,
                model=model,
                action_type=ActionType.SCALE_UP,
                priority=ActionPriority.HIGH,
                reason=f"High error rate detected ({error_rate:.2%})",
                current_value=error_rate,
                threshold=self.ERROR_THRESHOLD_HIGH,
                recommendation=f"[PROVISIONAL] Scale up resources for {skill_id} or consider model switch. Error rate is {error_rate:.2%}.",
                time_window_hours=self.hours
            )
        
        # Rule 3: Critical Latency (> 5000ms)
        if avg_latency_ms > self.LATENCY_THRESHOLD_CRITICAL:
            return SystemAction(
                skill_id=skill_id,
                model=model,
                action_type=ActionType.MODEL_SWITCH,
                priority=ActionPriority.HIGH,
                reason=f"Critical latency detected ({avg_latency_ms:.0f}ms)",
                current_value=avg_latency_ms,
                threshold=self.LATENCY_THRESHOLD_CRITICAL,
                recommendation=f"[PROVISIONAL] Switch model for {skill_id}. Current latency is {avg_latency_ms:.0f}ms.",
                time_window_hours=self.hours
            )
        
        # Rule 4: High Latency (> 3000ms)
        if avg_latency_ms > self.LATENCY_THRESHOLD_HIGH:
            return SystemAction(
                skill_id=skill_id,
                model=model,
                action_type=ActionType.TIMEOUT_ADJUST,
                priority=ActionPriority.HIGH,
                reason=f"High latency detected ({avg_latency_ms:.0f}ms)",
                current_value=avg_latency_ms,
                threshold=self.LATENCY_THRESHOLD_HIGH,
                recommendation=f"[PROVISIONAL] Increase timeout for {skill_id} or switch to faster model. Current latency is {avg_latency_ms:.0f}ms.",
                time_window_hours=self.hours
            )
        
        # Rule 5: Stable System (no action needed)
        if error_rate == 0.0 and avg_latency_ms < 1000:
            return SystemAction(
                skill_id=skill_id,
                model=model,
                action_type=ActionType.MONITOR,
                priority=ActionPriority.LOW,
                reason="System operating normally",
                current_value=error_rate,
                threshold=0.0,
                recommendation=f"[PROVISIONAL] Continue monitoring {skill_id}. System is stable.",
                time_window_hours=self.hours
            )
        
        return None
    
    def store_action(self, action: SystemAction) -> bool:
        """
        Store action in logs_actions table.
        
        Args:
            action: SystemAction to store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = (
                self.supabase
                .table("logs_actions")
                .insert(action.model_dump(mode='json', by_alias=True))
                .execute()
            )
            return True
        except Exception as e:
            logger.error(f"[OptimizationEngine] Failed to store action: {e}", exc_info=True)
            return False
    
    def analyze_and_generate_actions(self) -> List[SystemAction]:
        """
        Run full optimization analysis pipeline.
        
        Fetches insights, evaluates each against thresholds,
        generates actions, and stores them.
        
        Returns:
            List of generated SystemAction objects
        """
        insights = self.fetch_insights()
        
        if not insights:
            logger.info("[OptimizationEngine] No insights found for analysis")
            return []
        
        actions = []
        
        for insight in insights:
            action = self.evaluate_insight(insight)
            if action:
                self.store_action(action)
                actions.append(action)
        
        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        priority_order = {
            ActionPriority.CRITICAL: 0,
            ActionPriority.HIGH: 1,
            ActionPriority.MEDIUM: 2,
            ActionPriority.LOW: 3
        }
        
        actions.sort(key=lambda a: priority_order.get(a.priority, 99))
        
        logger.info(f"[OptimizationEngine] Generated {len(actions)} actions from {len(insights)} insights")
        
        return actions
    
    def generate_decision_report(
        self,
        health_matrix: Dict[str, Any],
        problem_profiles: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate D13 Decision Report from Health Matrix + Problem Classifications.
        
        For each degraded skill (< 0.9 pass_rate) emits a full decision block:
        - Health metrics (pass_rate, escalation_rate, latency)
        - Problem classification (MODEL_WEAKNESS / PROMPT_ISSUE / VALIDATION_FAIL / TIMEOUT)
        - Confidence score (frequency-based)
        - [PROVISIONAL] recommendation
        
        Args:
            health_matrix: From insight_engine.generate_health_matrix()
            problem_profiles: Optional dict skill_id -> SkillProblemProfile from ProblemClassifier
        
        Returns:
            Markdown-formatted decision report
        """
        matrix = health_matrix.get("matrix", {})
        generated_at = health_matrix.get("generated_at", datetime.utcnow().isoformat())

        # Filter degraded skills (< 0.9 pass_rate)
        degraded_skills = {
            skill_id: metrics
            for skill_id, metrics in matrix.items()
            if metrics.get("pass_rate", 1.0) < 0.9
        }

        if not degraded_skills:
            return (
                f"# 🎯 D13 Decision Report\n\n"
                f"**Generated:** {generated_at}\n"
                f"**Status:** All skills healthy (pass_rate >= 0.9)\n\n"
                "No degraded skills detected. No action required.\n"
            )

        report_lines = [
            "# 🎯 D13 Decision Report",
            "",
            f"**Generated:** {generated_at}",
            f"**Skills Analyzed:** {len(matrix)}",
            f"**Degraded Skills:** {len(degraded_skills)}",
            ""
        ]

        # Category icons
        _icons = {
            "MODEL_WEAKNESS":  "🔁",
            "PROMPT_ISSUE":    "📋",
            "VALIDATION_FAIL": "🔍",
            "TIMEOUT":         "⏱️",
            "HEALTHY":         "✅",
            "UNKNOWN":         "❓",
        }

        # Generate decision blocks for each degraded skill
        for skill_id, metrics in sorted(degraded_skills.items()):
            pass_rate = metrics.get("pass_rate", 0.0)
            escalation_rate = metrics.get("escalation_rate", 0.0)
            total_runs = metrics.get("total_runs", 0)
            avg_latency = metrics.get("avg_latency_ms", 0.0)
            health_status = metrics.get("health_status", "unknown")

            # Priority from pass_rate
            if pass_rate < 0.5:
                priority = "CRITICAL"
            elif pass_rate < 0.7:
                priority = "HIGH"
            else:
                priority = "MEDIUM"

            # Problem classification block
            profile = (problem_profiles or {}).get(skill_id)
            if profile:
                # Accept both SkillProblemProfile objects and plain dicts
                if hasattr(profile, "dominant_category"):
                    dominant_cat = profile.dominant_category.value if hasattr(profile.dominant_category, "value") else str(profile.dominant_category)
                    confidence = profile.confidence
                    cat_rates = profile.category_rates
                    recommendation = profile.recommendation
                else:
                    dominant_cat = profile.get("dominant_category", "UNKNOWN")
                    confidence = profile.get("confidence", 0.0)
                    cat_rates = profile.get("category_rates", {})
                    recommendation = profile.get("recommendation", "[PROVISIONAL] No recommendation available.")

                icon = _icons.get(dominant_cat, "❓")
                cat_breakdown = "  ".join(
                    f"`{cat}`: {rate:.0%}"
                    for cat, rate in sorted(cat_rates.items(), key=lambda x: x[1], reverse=True)
                )
                classification_section = (
                    f"#### {icon} Problem Classification\n\n"
                    f"| Field | Value |\n"
                    f"|-------|-------|\n"
                    f"| **Dominant Category** | `{dominant_cat}` |\n"
                    f"| **Confidence** | {confidence:.0%} (frequency-based) |\n"
                    f"| **Category Breakdown** | {cat_breakdown} |\n\n"
                    f"**Root-Cause Recommendation:**\n\n"
                    f"> {recommendation}\n"
                )
            else:
                classification_section = (
                    "#### ❓ Problem Classification\n\n"
                    "*No D10 classification data available yet. Run batch tests to populate.*\n"
                )

            report_lines.append(f"## 🚨 [{priority}] {skill_id}\n")
            report_lines.append(
                f"| Metric | Value |\n"
                f"|--------|-------|\n"
                f"| **Health Status** | `{health_status.upper()}` |\n"
                f"| **Pass Rate** | {pass_rate:.2%} |\n"
                f"| **Escalation Rate** | {escalation_rate:.2%} |\n"
                f"| **Total Runs** | {total_runs} |\n"
                f"| **Avg Latency** | {avg_latency:.0f} ms |\n"
            )
            report_lines.append("")
            report_lines.append(classification_section)
            report_lines.append("---\n")

        # Summary
        critical_count = sum(1 for m in degraded_skills.values() if m.get("pass_rate", 1.0) < 0.5)
        high_count = sum(1 for m in degraded_skills.values() if 0.5 <= m.get("pass_rate", 1.0) < 0.7)
        medium_count = sum(1 for m in degraded_skills.values() if 0.7 <= m.get("pass_rate", 1.0) < 0.9)

        # Category summary from profiles
        cat_summary: Dict[str, int] = defaultdict(int)
        for p in (problem_profiles or {}).values():
            if hasattr(p, "dominant_category"):
                cat_summary[p.dominant_category.value if hasattr(p.dominant_category, "value") else str(p.dominant_category)] += 1
            elif isinstance(p, dict):
                cat_summary[p.get("dominant_category", "UNKNOWN")] += 1

        report_lines += [
            "## 📊 Summary",
            "",
            f"- **Total Skills Analyzed:** {len(matrix)}",
            f"- **Healthy Skills:** {len(matrix) - len(degraded_skills)}",
            f"- **Degraded Skills:** {len(degraded_skills)}",
            "",
            "### Priority Breakdown",
            f"- **CRITICAL:** {critical_count}",
            f"- **HIGH:** {high_count}",
            f"- **MEDIUM:** {medium_count}",
            "",
        ]

        if cat_summary:
            report_lines.append("### Problem Category Distribution")
            for cat, count in sorted(cat_summary.items(), key=lambda x: x[1], reverse=True):
                icon = _icons.get(cat, "❓")
                report_lines.append(f"- {icon} **{cat}:** {count} skill(s)")

        return "\n".join(report_lines)
