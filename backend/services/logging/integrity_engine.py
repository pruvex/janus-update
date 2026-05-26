"""
Janus Integrity Engine (D15) — Diamond Contract Registry & Stack Validation.

Final control layer over D10-D14. Validates structural truth and prevents schema drift.
No AI interpretation — only strict code validation and Pydantic schema checks.
Fail-Fast: On severe schema violation (drift), output status FAIL with exact schema_fix.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger("janus_backend")

SCHEMA_VERSION = "V0.4.26"


# ─── Contract Registry ────────────────────────────────────────────────────────

class LayerContract(BaseModel):
    """Blueprint for a single Diamond layer's expected schema."""
    layer: str = Field(..., description="Layer identifier (D10, D11, D12, D13, D14)")
    required_fields: List[str] = Field(default_factory=list, description="Fields that MUST be present")
    forbidden_fields: List[str] = Field(default_factory=list, description="Fields that MUST NOT be present")
    allowed_actions: List[str] = Field(default_factory=list, description="Allowed action_type values (empty = no constraint)")
    requires_provisional: bool = Field(default=False, description="Whether recommendation must contain [PROVISIONAL]")
    description: str = Field(default="", description="Human-readable description")


CONTRACT_SPECS: Dict[str, LayerContract] = {
    "D10": LayerContract(
        layer="D10",
        required_fields=["event_type", "timestamp"],
        forbidden_fields=[],
        allowed_actions=[],
        requires_provisional=False,
        description="Resilient Telemetry — raw event ingestion"
    ),
    "D11": LayerContract(
        layer="D11",
        required_fields=[],
        forbidden_fields=[],
        allowed_actions=[],
        requires_provisional=False,
        description="Debug Compression Engine — session-level heuristics"
    ),
    "D12": LayerContract(
        layer="D12",
        required_fields=["skill_id", "model", "calls", "error_rate", "avg_latency_ms", "patterns", "confidence"],
        forbidden_fields=["recommendation", "action_type", "priority"],
        allowed_actions=[],
        requires_provisional=False,
        description="Insight Engine — descriptive metrics only, no recommendations"
    ),
    "D13": LayerContract(
        layer="D13",
        required_fields=["skill_id", "model", "action_type", "priority", "recommendation", "current_value", "threshold"],
        forbidden_fields=[],
        allowed_actions=["MODEL_SWITCH", "SCALE_UP", "SCALE_DOWN", "TIMEOUT_ADJUST", "CACHE_ENABLE", "LOAD_BALANCE", "RETRY_CONFIG", "MONITOR"],
        requires_provisional=True,
        description="Optimization Engine — rule-based actions from D12 aggregates"
    ),
    "D14": LayerContract(
        layer="D14",
        required_fields=["scope", "model", "issue", "trend", "recommendation"],
        forbidden_fields=[],
        allowed_actions=["MODEL_SWITCH", "TIMEOUT_ADJUST", "COST_OPTIMIZE", "MONITOR", "MAINTAIN"],
        requires_provisional=True,
        description="Learning Engine — weekly trend analysis with KPI registry"
    ),
}


# ─── Integrity Report Models ──────────────────────────────────────────────────

class ViolationSeverity(str, Enum):
    """Severity of an integrity violation."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Violation(BaseModel):
    """Single integrity violation."""
    layer: str = Field(..., description="Layer where violation occurred")
    rule: str = Field(..., description="Rule that was violated")
    severity: ViolationSeverity = Field(..., description="Violation severity")
    message: str = Field(..., description="Human-readable violation description")
    schema_fix: str = Field(..., description="Exact fix required to resolve the violation")
    field: Optional[str] = Field(default=None, description="Specific field involved")


class IntegrityReport(BaseModel):
    """Output of a full stack integrity check."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    integrity_score: float = Field(..., description="Integrity score (0.0 = total failure, 1.0 = clean)")
    status: str = Field(..., description="PASS or FAIL")
    layers_checked: int = Field(default=0, description="Number of layers validated")
    violations: List[Violation] = Field(default_factory=list, description="List of violations found")
    schema_version: str = Field(default=SCHEMA_VERSION, description="Contract schema version")


# ─── Integrity Engine ─────────────────────────────────────────────────────────

class IntegrityEngine:
    """
    Diamond Contract Validator (D15).
    
    Validates structural truth across D10-D14 using CONTRACT_SPECS.
    No AI interpretation — strict schema checks only.
    """

    def __init__(self):
        self.contracts = CONTRACT_SPECS
        self.violations: List[Violation] = []

    def _add_violation(
        self,
        layer: str,
        rule: str,
        severity: ViolationSeverity,
        message: str,
        schema_fix: str,
        field: Optional[str] = None
    ) -> None:
        """Register a violation."""
        self.violations.append(Violation(
            layer=layer,
            rule=rule,
            severity=severity,
            message=message,
            schema_fix=schema_fix,
            field=field
        ))

    # ── Rule 1: Descriptive-Only Guard (D12) ──────────────────────────────

    def validate_d12_descriptive_only(self, d12_outputs: List[Dict[str, Any]]) -> None:
        """
        Rule 1: D12 outputs must be purely descriptive.
        Block any D12 output containing forbidden fields (recommendation, action_type, priority).
        """
        contract = self.contracts["D12"]

        for i, output in enumerate(d12_outputs):
            # Check forbidden fields
            for forbidden in contract.forbidden_fields:
                if forbidden in output and output[forbidden] is not None:
                    self._add_violation(
                        layer="D12",
                        rule="DESCRIPTIVE_ONLY_GUARD",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"D12 output[{i}] contains forbidden field '{forbidden}' = '{output[forbidden]}'. D12 must be descriptive-only.",
                        schema_fix=f"Remove field '{forbidden}' from D12 InsightResult. D12 must not emit recommendations or actions.",
                        field=forbidden
                    )

            # Check required fields
            for required in contract.required_fields:
                if required not in output or output[required] is None:
                    self._add_violation(
                        layer="D12",
                        rule="REQUIRED_FIELD_MISSING",
                        severity=ViolationSeverity.HIGH,
                        message=f"D12 output[{i}] missing required field '{required}'.",
                        schema_fix=f"Add field '{required}' to D12 InsightResult output.",
                        field=required
                    )

    # ── Rule 2: Allowed-Actions Guard (D13) ───────────────────────────────

    def validate_d13_allowed_actions(self, d13_outputs: List[Dict[str, Any]]) -> None:
        """
        Rule 2: D13 action_type must come from ALLOWED_ACTIONS list.
        """
        contract = self.contracts["D13"]
        allowed: Set[str] = set(contract.allowed_actions)

        for i, output in enumerate(d13_outputs):
            action_type = output.get("action_type")

            if action_type is None:
                self._add_violation(
                    layer="D13",
                    rule="REQUIRED_FIELD_MISSING",
                    severity=ViolationSeverity.HIGH,
                    message=f"D13 output[{i}] missing required field 'action_type'.",
                    schema_fix="Ensure D13 SystemAction always emits 'action_type'.",
                    field="action_type"
                )
                continue

            if action_type not in allowed:
                self._add_violation(
                    layer="D13",
                    rule="INVALID_ACTION_TYPE",
                    severity=ViolationSeverity.CRITICAL,
                    message=f"D13 output[{i}] has invalid action_type '{action_type}'. Allowed: {sorted(allowed)}.",
                    schema_fix=f"Change action_type from '{action_type}' to one of: {sorted(allowed)}. Or add '{action_type}' to D13 CONTRACT_SPECS.allowed_actions.",
                    field="action_type"
                )

            # Check required fields
            for required in contract.required_fields:
                if required not in output or output[required] is None:
                    self._add_violation(
                        layer="D13",
                        rule="REQUIRED_FIELD_MISSING",
                        severity=ViolationSeverity.HIGH,
                        message=f"D13 output[{i}] missing required field '{required}'.",
                        schema_fix=f"Add field '{required}' to D13 SystemAction output.",
                        field=required
                    )

    # ── Rule 3: KPI-Drift Guard ───────────────────────────────────────────

    def validate_d14_kpi_drift(self, d14_outputs: List[Dict[str, Any]]) -> None:
        """
        Rule 3: Validate D14 outputs have required KPI fields and allowed action_types.
        """
        contract = self.contracts["D14"]
        allowed: Set[str] = set(contract.allowed_actions)

        for i, output in enumerate(d14_outputs):
            # Check required fields
            for required in contract.required_fields:
                if required not in output or output[required] is None:
                    self._add_violation(
                        layer="D14",
                        rule="KPI_DRIFT",
                        severity=ViolationSeverity.HIGH,
                        message=f"D14 output[{i}] missing required KPI field '{required}'.",
                        schema_fix=f"Add field '{required}' to D14 LearningEngine output.",
                        field=required
                    )

            # Validate action_type if present
            action_type = output.get("action_type")
            if action_type and action_type not in allowed:
                self._add_violation(
                    layer="D14",
                    rule="INVALID_ACTION_TYPE",
                    severity=ViolationSeverity.CRITICAL,
                    message=f"D14 output[{i}] has invalid action_type '{action_type}'. Allowed: {sorted(allowed)}.",
                    schema_fix=f"Change action_type from '{action_type}' to one of: {sorted(allowed)}.",
                    field="action_type"
                )

    # ── Rule 4: Decision-Gate Guard ───────────────────────────────────────

    def validate_decision_gate(self, layer: str, outputs: List[Dict[str, Any]]) -> None:
        """
        Rule 4: Validate that [PROVISIONAL] marker is present on all recommendations.
        Applies to D13 and D14 (layers where requires_provisional=True).
        """
        contract = self.contracts.get(layer)
        if not contract or not contract.requires_provisional:
            return

        for i, output in enumerate(outputs):
            recommendation = output.get("recommendation", "")
            if recommendation and "[PROVISIONAL]" not in recommendation:
                self._add_violation(
                    layer=layer,
                    rule="DECISION_GATE_MISSING",
                    severity=ViolationSeverity.CRITICAL,
                    message=f"{layer} output[{i}] recommendation missing [PROVISIONAL] marker: '{recommendation[:80]}...'",
                    schema_fix=f"Prefix recommendation with '[PROVISIONAL]'. AI Studio is the sole validation gatekeeper.",
                    field="recommendation"
                )

    # ── Live Data Fetch ───────────────────────────────────────────────────

    async def fetch_live_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch recent outputs from D12, D13, D14 via Supabase for live validation.
        Returns dict keyed by layer name.
        """
        try:
            from backend.services.logging.supabase_client import get_supabase_client
            supabase = get_supabase_client()
        except Exception as e:
            logger.warning(f"[INTEGRITY-ENGINE] Could not connect to Supabase: {e}")
            return {"D12": [], "D13": [], "D14": []}

        result: Dict[str, List[Dict[str, Any]]] = {"D12": [], "D13": [], "D14": []}

        try:
            # D12: Recent insights (last 24h)
            response = supabase.table("logs_insights").select("*").order("generated_at", desc=True).limit(50).execute()
            result["D12"] = response.data if response.data else []
        except Exception as e:
            logger.warning(f"[INTEGRITY-ENGINE] Failed to fetch D12 data: {e}")

        try:
            # D13: Recent actions (last 24h)
            response = supabase.table("logs_actions").select("*").order("generated_at", desc=True).limit(50).execute()
            result["D13"] = response.data if response.data else []
        except Exception as e:
            logger.warning(f"[INTEGRITY-ENGINE] Failed to fetch D13 data: {e}")

        try:
            # D14: Recent learning reports (last 24h)
            response = supabase.table("logs_learning").select("*").order("generated_at", desc=True).limit(10).execute()
            reports = response.data if response.data else []
            # Extract improvements from report_data
            for report in reports:
                report_data = report.get("report_data", {})
                if isinstance(report_data, dict):
                    improvements = report_data.get("improvements", [])
                    result["D14"].extend(improvements)
        except Exception as e:
            logger.warning(f"[INTEGRITY-ENGINE] Failed to fetch D14 data: {e}")

        return result

    # ── Main Validation ───────────────────────────────────────────────────

    def validate_stack_integrity(
        self,
        d12_outputs: Optional[List[Dict[str, Any]]] = None,
        d13_outputs: Optional[List[Dict[str, Any]]] = None,
        d14_outputs: Optional[List[Dict[str, Any]]] = None,
    ) -> IntegrityReport:
        """
        Run full stack integrity validation against CONTRACT_SPECS.

        Args:
            d12_outputs: D12 InsightResult dicts (optional, fetched live if None)
            d13_outputs: D13 SystemAction dicts (optional, fetched live if None)
            d14_outputs: D14 improvement dicts (optional, fetched live if None)

        Returns:
            IntegrityReport with score, status, and violations
        """
        self.violations = []
        layers_checked = 0

        # D12: Descriptive-Only Guard
        if d12_outputs is not None:
            self.validate_d12_descriptive_only(d12_outputs)
            layers_checked += 1

        # D13: Allowed-Actions Guard + Decision-Gate
        if d13_outputs is not None:
            self.validate_d13_allowed_actions(d13_outputs)
            self.validate_decision_gate("D13", d13_outputs)
            layers_checked += 1

        # D14: KPI-Drift Guard + Decision-Gate
        if d14_outputs is not None:
            self.validate_d14_kpi_drift(d14_outputs)
            self.validate_decision_gate("D14", d14_outputs)
            layers_checked += 1

        # Calculate integrity score
        critical_count = sum(1 for v in self.violations if v.severity == ViolationSeverity.CRITICAL)
        high_count = sum(1 for v in self.violations if v.severity == ViolationSeverity.HIGH)
        medium_count = sum(1 for v in self.violations if v.severity == ViolationSeverity.MEDIUM)

        # Scoring: CRITICAL = -0.3, HIGH = -0.15, MEDIUM = -0.05
        deductions = (critical_count * 0.3) + (high_count * 0.15) + (medium_count * 0.05)
        integrity_score = max(0.0, round(1.0 - deductions, 3))

        # Status: FAIL if any CRITICAL or score < 0.7
        status = "FAIL" if critical_count > 0 or integrity_score < 0.7 else "PASS"

        report = IntegrityReport(
            integrity_score=integrity_score,
            status=status,
            layers_checked=layers_checked,
            violations=self.violations,
            schema_version=SCHEMA_VERSION
        )

        logger.info(
            f"[INTEGRITY-ENGINE] Stack check: {status} "
            f"(score={integrity_score}, violations={len(self.violations)}, layers={layers_checked})"
        )

        return report

    async def run_live_check(self) -> IntegrityReport:
        """
        Fetch live data from Supabase and validate full stack.
        
        Returns:
            IntegrityReport with live validation results
        """
        logger.info("[INTEGRITY-ENGINE] Running live integrity check...")
        data = await self.fetch_live_data()

        report = self.validate_stack_integrity(
            d12_outputs=data.get("D12", []),
            d13_outputs=data.get("D13", []),
            d14_outputs=data.get("D14", []),
        )

        return report
