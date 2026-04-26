"""
Test Cases for Janus Integrity Engine (D15).

Validates Diamond Contract Registry and Cross-Layer Consistency.
Test Cases:
1. Clean D12 output → PASS
2. D12 with forbidden 'recommendation' field → FAIL (Descriptive-Only Guard)
3. D13 with invalid action_type → FAIL (Allowed-Actions Guard)
4. D13 missing [PROVISIONAL] → FAIL (Decision-Gate Guard)
5. D14 missing required KPI fields → FAIL (KPI-Drift Guard)
6. Full clean stack → PASS (integrity_score = 1.0)
7. Mixed violations → FAIL with correct score
"""
import pytest
from backend.services.logging.integrity_engine import (
    IntegrityEngine,
    IntegrityReport,
    CONTRACT_SPECS,
    ViolationSeverity,
    SCHEMA_VERSION
)


def test_clean_d12_output_passes():
    """
    Test Case 1: Clean D12 output with all required fields → PASS.
    """
    engine = IntegrityEngine()

    d12_outputs = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "calls": 100,
            "error_rate": 0.05,
            "avg_latency_ms": 500.0,
            "patterns": ["stable"],
            "confidence": 0.8
        }
    ]

    report = engine.validate_stack_integrity(d12_outputs=d12_outputs)

    assert report.status == "PASS"
    assert report.integrity_score == 1.0
    assert len(report.violations) == 0
    assert report.layers_checked == 1

    print("✅ Test Case 1 PASSED: Clean D12 output → PASS")


def test_d12_with_forbidden_recommendation_fails():
    """
    Test Case 2: D12 output containing 'recommendation' → FAIL.
    Descriptive-Only Guard blocks recommendations in D12.
    """
    engine = IntegrityEngine()

    d12_outputs = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "calls": 100,
            "error_rate": 0.4,
            "avg_latency_ms": 500.0,
            "patterns": ["high_error_rate"],
            "confidence": 0.5,
            "recommendation": "Switch to gpt-4o"  # FORBIDDEN in D12
        }
    ]

    report = engine.validate_stack_integrity(d12_outputs=d12_outputs)

    assert report.status == "FAIL"
    assert report.integrity_score < 1.0
    assert len(report.violations) == 1
    assert report.violations[0].rule == "DESCRIPTIVE_ONLY_GUARD"
    assert report.violations[0].severity == ViolationSeverity.CRITICAL
    assert report.violations[0].field == "recommendation"

    print("✅ Test Case 2 PASSED: D12 with forbidden 'recommendation' → FAIL")


def test_d13_invalid_action_type_fails():
    """
    Test Case 3: D13 output with unregistered action_type → FAIL.
    """
    engine = IntegrityEngine()

    d13_outputs = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "action_type": "REBOOT_SERVER",  # NOT in ALLOWED_ACTIONS
            "priority": "CRITICAL",
            "recommendation": "[PROVISIONAL] Reboot the server",
            "current_value": 0.9,
            "threshold": 0.5
        }
    ]

    report = engine.validate_stack_integrity(d13_outputs=d13_outputs)

    assert report.status == "FAIL"
    assert len(report.violations) == 1
    assert report.violations[0].rule == "INVALID_ACTION_TYPE"
    assert report.violations[0].severity == ViolationSeverity.CRITICAL
    assert "REBOOT_SERVER" in report.violations[0].message

    print("✅ Test Case 3 PASSED: D13 invalid action_type → FAIL")


def test_d13_missing_provisional_fails():
    """
    Test Case 4: D13 output missing [PROVISIONAL] marker → FAIL.
    """
    engine = IntegrityEngine()

    d13_outputs = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "action_type": "MODEL_SWITCH",
            "priority": "HIGH",
            "recommendation": "Switch to gpt-4o immediately",  # Missing [PROVISIONAL]
            "current_value": 0.6,
            "threshold": 0.5
        }
    ]

    report = engine.validate_stack_integrity(d13_outputs=d13_outputs)

    assert report.status == "FAIL"
    violations_gate = [v for v in report.violations if v.rule == "DECISION_GATE_MISSING"]
    assert len(violations_gate) == 1
    assert violations_gate[0].severity == ViolationSeverity.CRITICAL

    print("✅ Test Case 4 PASSED: D13 missing [PROVISIONAL] → FAIL")


def test_d14_missing_required_fields_fails():
    """
    Test Case 5: D14 output missing required KPI fields → FAIL.
    """
    engine = IntegrityEngine()

    d14_outputs = [
        {
            "scope": "skill:websearch",
            "model": "gpt-4o-mini",
            # Missing: issue, trend, recommendation
        }
    ]

    report = engine.validate_stack_integrity(d14_outputs=d14_outputs)

    assert report.status == "FAIL"
    missing_fields = [v.field for v in report.violations if v.rule == "KPI_DRIFT"]
    assert "issue" in missing_fields
    assert "trend" in missing_fields
    assert "recommendation" in missing_fields

    print("✅ Test Case 5 PASSED: D14 missing required fields → FAIL")


def test_full_clean_stack_passes():
    """
    Test Case 6: Full clean stack with all layers → PASS, score = 1.0.
    """
    engine = IntegrityEngine()

    d12 = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "calls": 100,
            "error_rate": 0.05,
            "avg_latency_ms": 500.0,
            "patterns": ["stable"],
            "confidence": 0.8
        }
    ]
    d13 = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "action_type": "MONITOR",
            "priority": "LOW",
            "recommendation": "[PROVISIONAL] System operating normally. Continue monitoring.",
            "current_value": 0.0,
            "threshold": 0.0
        }
    ]
    d14 = [
        {
            "scope": "skill:system.websearch",
            "model": "gpt-4o-mini",
            "issue": "System improving (error rate: 0.02, latency: 450ms)",
            "trend": "improving",
            "recommendation": "[PROVISIONAL] MAINTAIN: Current configuration working well.",
            "action_type": "MAINTAIN"
        }
    ]

    report = engine.validate_stack_integrity(
        d12_outputs=d12,
        d13_outputs=d13,
        d14_outputs=d14
    )

    assert report.status == "PASS"
    assert report.integrity_score == 1.0
    assert report.layers_checked == 3
    assert len(report.violations) == 0
    assert report.schema_version == SCHEMA_VERSION

    print("✅ Test Case 6 PASSED: Full clean stack → PASS (score=1.0)")


def test_mixed_violations_correct_score():
    """
    Test Case 7: Multiple violations across layers → FAIL with correct scoring.
    1 CRITICAL (-0.3) + 1 HIGH (-0.15) = score 0.55
    """
    engine = IntegrityEngine()

    d12 = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "calls": 100,
            "error_rate": 0.4,
            "avg_latency_ms": 500.0,
            "patterns": ["high_error_rate"],
            "confidence": 0.5,
            "action_type": "MODEL_SWITCH"  # FORBIDDEN → CRITICAL
        }
    ]
    d14 = [
        {
            "scope": "skill:websearch",
            "model": "gpt-4o-mini",
            # missing 'issue' → HIGH
            "trend": "worsening",
            "recommendation": "[PROVISIONAL] MODEL_SWITCH needed"
        }
    ]

    report = engine.validate_stack_integrity(d12_outputs=d12, d14_outputs=d14)

    assert report.status == "FAIL"
    assert report.integrity_score == 0.55
    assert len(report.violations) == 2
    critical_count = sum(1 for v in report.violations if v.severity == ViolationSeverity.CRITICAL)
    high_count = sum(1 for v in report.violations if v.severity == ViolationSeverity.HIGH)
    assert critical_count == 1
    assert high_count == 1

    print("✅ Test Case 7 PASSED: Mixed violations → FAIL (score=0.55)")


def test_contract_specs_completeness():
    """
    Test Case 8: Verify CONTRACT_SPECS covers all 5 layers.
    """
    assert "D10" in CONTRACT_SPECS
    assert "D11" in CONTRACT_SPECS
    assert "D12" in CONTRACT_SPECS
    assert "D13" in CONTRACT_SPECS
    assert "D14" in CONTRACT_SPECS
    assert len(CONTRACT_SPECS) == 5

    # D12 must have forbidden fields
    assert "recommendation" in CONTRACT_SPECS["D12"].forbidden_fields
    assert "action_type" in CONTRACT_SPECS["D12"].forbidden_fields

    # D13 must require provisional
    assert CONTRACT_SPECS["D13"].requires_provisional is True

    # D14 must require provisional
    assert CONTRACT_SPECS["D14"].requires_provisional is True

    print("✅ Test Case 8 PASSED: CONTRACT_SPECS covers all 5 layers")


if __name__ == "__main__":
    test_clean_d12_output_passes()
    test_d12_with_forbidden_recommendation_fails()
    test_d13_invalid_action_type_fails()
    test_d13_missing_provisional_fails()
    test_d14_missing_required_fields_fails()
    test_full_clean_stack_passes()
    test_mixed_violations_correct_score()
    test_contract_specs_completeness()
    print("\n🎉 ALL TESTS PASSED")
