"""
Test Cases for Janus Insight Engine (D12).

Validates deterministic aggregation logic with dummy data.
Test Cases:
1. Faulty Skill — High error rate (>0.2)
2. Stable Skill — >50 calls, 0 errors
3. Performance Problem — Latency spike (>2000ms)
"""
import pytest
from datetime import datetime, timedelta
from backend.services.logging.insight_engine import InsightEngine


def test_faulty_skill_high_error_rate():
    """
    Test Case 1: Faulty Skill — High error rate.
    
    Scenario: A skill with 30% error rate should detect "high_error_rate" pattern
    and have reduced confidence due to high error rate.
    """
    # Mock logs for a faulty skill
    logs = [
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 100},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 120},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "error", "latency_ms": 50},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 110},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "error", "latency_ms": 60},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 130},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "error", "latency_ms": 55},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 115},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 105},
        {"skill": "faulty_skill", "model": "gpt-4o-mini", "status": "error", "latency_ms": 65},
    ]
    
    engine = InsightEngine(hours=1)
    
    # Aggregate
    grouped = engine.aggregate_logs(logs)
    metrics_list = engine.calculate_metrics(grouped)
    
    assert len(metrics_list) == 1, "Should have one skill/model combination"
    
    metrics = metrics_list[0]
    assert metrics["skill"] == "faulty_skill"
    assert metrics["model"] == "gpt-4o-mini"
    assert metrics["calls"] == 10
    assert metrics["errors"] == 4
    assert metrics["error_rate"] == 0.4, "Error rate should be 0.4 (40%)"
    
    # Pattern detection
    patterns = engine.detect_patterns(metrics)
    assert "high_error_rate" in patterns, "Should detect high_error_rate pattern"
    assert "stable" not in patterns, "Should not detect stable pattern (has errors)"
    assert "latency_spike" not in patterns, "Should not detect latency spike (avg latency < 2000ms)"
    
    # Confidence calculation
    confidence = engine.calculate_confidence(metrics)
    base_confidence = min(1.0, 10 / 100.0)  # 0.1
    # Error rate > 0.5? No (0.3 < 0.5), so no reduction
    assert confidence == base_confidence, f"Confidence should be {base_confidence}"
    
    print("✅ Test Case 1 PASSED: Faulty Skill — High error rate detected")


def test_stable_skill():
    """
    Test Case 2: Stable Skill — >50 calls, 0 errors.
    
    Scenario: A skill with >50 calls and 0 errors should detect "stable" pattern
    and have high confidence.
    """
    # Mock logs for a stable skill
    logs = []
    for i in range(60):
        logs.append({
            "skill": "stable_skill",
            "model": "gpt-4o-mini",
            "status": "success",
            "latency_ms": 100 + i % 50  # Varying latency but all < 2000ms
        })
    
    engine = InsightEngine(hours=1)
    
    # Aggregate
    grouped = engine.aggregate_logs(logs)
    metrics_list = engine.calculate_metrics(grouped)
    
    assert len(metrics_list) == 1, "Should have one skill/model combination"
    
    metrics = metrics_list[0]
    assert metrics["skill"] == "stable_skill"
    assert metrics["model"] == "gpt-4o-mini"
    assert metrics["calls"] == 60
    assert metrics["errors"] == 0
    assert metrics["error_rate"] == 0.0, "Error rate should be 0.0 (no errors)"
    
    # Pattern detection
    patterns = engine.detect_patterns(metrics)
    assert "stable" in patterns, "Should detect stable pattern (>50 calls, 0 errors)"
    assert "high_error_rate" not in patterns, "Should not detect high_error_rate (no errors)"
    assert "latency_spike" not in patterns, "Should not detect latency spike (avg latency < 2000ms)"
    
    # Confidence calculation
    confidence = engine.calculate_confidence(metrics)
    base_confidence = min(1.0, 60 / 100.0)  # 0.6
    # Error rate > 0.5? No (0.0 < 0.5), so no reduction
    assert confidence == base_confidence, f"Confidence should be {base_confidence}"
    
    print("✅ Test Case 2 PASSED: Stable Skill — Stable pattern detected")


def test_performance_problem():
    """
    Test Case 3: Performance Problem — Latency spike (>2000ms).
    
    Scenario: A skill with average latency >2000ms should detect "latency_spike" pattern.
    """
    # Mock logs for a skill with latency spikes
    logs = [
        {"skill": "slow_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 2500},
        {"skill": "slow_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 2800},
        {"skill": "slow_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 2200},
        {"skill": "slow_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 3000},
        {"skill": "slow_skill", "model": "gpt-4o-mini", "status": "success", "latency_ms": 2600},
    ]
    
    engine = InsightEngine(hours=1)
    
    # Aggregate
    grouped = engine.aggregate_logs(logs)
    metrics_list = engine.calculate_metrics(grouped)
    
    assert len(metrics_list) == 1, "Should have one skill/model combination"
    
    metrics = metrics_list[0]
    assert metrics["skill"] == "slow_skill"
    assert metrics["model"] == "gpt-4o-mini"
    assert metrics["calls"] == 5
    assert metrics["errors"] == 0
    assert metrics["error_rate"] == 0.0, "Error rate should be 0.0 (no errors)"
    assert metrics["avg_latency_ms"] > 2000, "Average latency should be >2000ms"
    
    # Pattern detection
    patterns = engine.detect_patterns(metrics)
    assert "latency_spike" in patterns, "Should detect latency_spike pattern (avg latency >2000ms)"
    assert "high_error_rate" not in patterns, "Should not detect high_error_rate (no errors)"
    assert "stable" not in patterns, "Should not detect stable pattern (<50 calls)"
    
    # Confidence calculation
    confidence = engine.calculate_confidence(metrics)
    base_confidence = min(1.0, 5 / 100.0)  # 0.05
    # Error rate > 0.5? No (0.0 < 0.5), so no reduction
    assert confidence == base_confidence, f"Confidence should be {base_confidence}"
    
    print("✅ Test Case 3 PASSED: Performance Problem — Latency spike detected")


def test_multiple_skills_and_models():
    """
    Test Case 4: Multiple skills and models.
    
    Scenario: Aggregates logs from multiple skills and models correctly.
    """
    logs = [
        {"skill": "skill_a", "model": "gpt-4o-mini", "status": "success", "latency_ms": 100},
        {"skill": "skill_a", "model": "gpt-4o-mini", "status": "success", "latency_ms": 120},
        {"skill": "skill_a", "model": "gpt-4o-mini", "status": "error", "latency_ms": 50},
        {"skill": "skill_a", "model": "gpt-4", "status": "success", "latency_ms": 200},
        {"skill": "skill_a", "model": "gpt-4", "status": "success", "latency_ms": 220},
        {"skill": "skill_b", "model": "gpt-4o-mini", "status": "success", "latency_ms": 150},
        {"skill": "skill_b", "model": "gpt-4o-mini", "status": "success", "latency_ms": 160},
    ]
    
    engine = InsightEngine(hours=1)
    
    # Aggregate
    grouped = engine.aggregate_logs(logs)
    metrics_list = engine.calculate_metrics(grouped)
    
    assert len(metrics_list) == 3, "Should have three skill/model combinations"
    
    # Verify skill_a/gpt-4o-mini
    skill_a_mini = next(m for m in metrics_list if m["skill"] == "skill_a" and m["model"] == "gpt-4o-mini")
    assert skill_a_mini["calls"] == 3
    assert skill_a_mini["errors"] == 1
    assert skill_a_mini["error_rate"] == pytest.approx(0.333, rel=0.01)
    
    # Verify skill_a/gpt-4
    skill_a_4 = next(m for m in metrics_list if m["skill"] == "skill_a" and m["model"] == "gpt-4")
    assert skill_a_4["calls"] == 2
    assert skill_a_4["errors"] == 0
    
    # Verify skill_b/gpt-4o-mini
    skill_b = next(m for m in metrics_list if m["skill"] == "skill_b" and m["model"] == "gpt-4o-mini")
    assert skill_b["calls"] == 2
    assert skill_b["errors"] == 0
    
    print("✅ Test Case 4 PASSED: Multiple skills and models — Aggregation correct")


if __name__ == "__main__":
    test_faulty_skill_high_error_rate()
    test_stable_skill()
    test_performance_problem()
    test_multiple_skills_and_models()
    print("\n🎉 ALL TESTS PASSED")
