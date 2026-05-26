"""
D15 Integrity Engine — Reproduction Script for Schema Drift Detection.

Test Scenarios:
A: D12 with forbidden 'recommendation' field → Descriptive-Only Guard violation
B: D13 with invalid 'action_type' → Allowed-Actions Guard violation
C: Recommendation missing [PROVISIONAL] → Decision-Gate violation
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.logging.integrity_engine import IntegrityEngine


async def run_scenarios():
    engine = IntegrityEngine()
    
    print("=" * 80)
    print("D15 INTEGRITY ENGINE — SCHEMA DRIFT REPRODUCTION")
    print("=" * 80)
    
    # Scenario A: D12 with forbidden 'recommendation' field
    print("\n[SCENARIO A] D12 with forbidden 'recommendation' field")
    print("-" * 80)
    d12_violation = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "calls": 100,
            "error_rate": 0.4,
            "avg_latency_ms": 500.0,
            "patterns": ["high_error_rate"],
            "confidence": 0.5,
            "recommendation": "Switch to GPT-4"  # FORBIDDEN in D12
        }
    ]
    report_a = engine.validate_stack_integrity(d12_outputs=d12_violation)
    print(f"Status: {report_a.status}")
    print(f"Integrity Score: {report_a.integrity_score}")
    print(f"Violations: {len(report_a.violations)}")
    if report_a.violations:
        for v in report_a.violations:
            print(f"  - {v.rule}: {v.message}")
            print(f"    Severity: {v.severity}")
            print(f"    Schema Fix: {v.schema_fix}")
    
    # Scenario B: D13 with invalid 'action_type'
    print("\n[SCENARIO B] D13 with invalid 'action_type': DELETE_DATABASE")
    print("-" * 80)
    d13_violation = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "action_type": "DELETE_DATABASE",  # NOT in ALLOWED_ACTIONS
            "priority": "CRITICAL",
            "recommendation": "[PROVISIONAL] Delete the database",
            "current_value": 0.9,
            "threshold": 0.5
        }
    ]
    report_b = engine.validate_stack_integrity(d13_outputs=d13_violation)
    print(f"Status: {report_b.status}")
    print(f"Integrity Score: {report_b.integrity_score}")
    print(f"Violations: {len(report_b.violations)}")
    if report_b.violations:
        for v in report_b.violations:
            print(f"  - {v.rule}: {v.message}")
            print(f"    Severity: {v.severity}")
            print(f"    Schema Fix: {v.schema_fix}")
    
    # Scenario C: Recommendation missing [PROVISIONAL]
    print("\n[SCENARIO C] Recommendation missing [PROVISIONAL] prefix")
    print("-" * 80)
    d13_missing_provisional = [
        {
            "skill_id": "system.websearch",
            "model": "gpt-4o-mini",
            "action_type": "MODEL_SWITCH",
            "priority": "HIGH",
            "recommendation": "Switch to GPT-4 immediately",  # Missing [PROVISIONAL]
            "current_value": 0.6,
            "threshold": 0.5
        }
    ]
    report_c = engine.validate_stack_integrity(d13_outputs=d13_missing_provisional)
    print(f"Status: {report_c.status}")
    print(f"Integrity Score: {report_c.integrity_score}")
    print(f"Violations: {len(report_c.violations)}")
    if report_c.violations:
        for v in report_c.violations:
            print(f"  - {v.rule}: {v.message}")
            print(f"    Severity: {v.severity}")
            print(f"    Schema Fix: {v.schema_fix}")
    
    # Scenario D: Clean stack (baseline)
    print("\n[SCENARIO D] Clean stack (baseline — no violations)")
    print("-" * 80)
    d12_clean = [
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
    d13_clean = [
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
    report_d = engine.validate_stack_integrity(d12_outputs=d12_clean, d13_outputs=d13_clean)
    print(f"Status: {report_d.status}")
    print(f"Integrity Score: {report_d.integrity_score}")
    print(f"Violations: {len(report_d.violations)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Scenario A (D12 forbidden field): {'✅ DETECTED' if report_a.status == 'FAIL' else '❌ MISSED'} (score={report_a.integrity_score})")
    print(f"Scenario B (D13 invalid action): {'✅ DETECTED' if report_b.status == 'FAIL' else '❌ MISSED'} (score={report_b.integrity_score})")
    print(f"Scenario C (Missing PROVISIONAL): {'✅ DETECTED' if report_c.status == 'FAIL' else '❌ MISSED'} (score={report_c.integrity_score})")
    print(f"Scenario D (Clean baseline): {'✅ PASS' if report_d.status == 'PASS' else '❌ FAIL'} (score={report_d.integrity_score})")
    
    all_detected = (report_a.status == "FAIL" and report_b.status == "FAIL" and 
                    report_c.status == "FAIL" and report_d.status == "PASS")
    
    print("\n" + "=" * 80)
    if all_detected:
        print("🎉 DIAMOND HARDENED: All violations detected, clean stack passes")
    else:
        print("❌ NOT HARDENED: Some violations missed or false positives")
    print("=" * 80)
    
    return all_detected


if __name__ == "__main__":
    result = asyncio.run(run_scenarios())
    exit(0 if result else 1)
