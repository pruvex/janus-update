"""
Test Cases for Janus Optimization Engine (D13).

Validates rule-based action generation with dummy data.
Test Cases:
1. High Error Rate (> 0.3) → HIGH PRIORITY Action
2. Critical Error Rate (> 0.5) → CRITICAL PRIORITY Action
3. High Latency (> 3000ms) → HIGH PRIORITY Action
4. Critical Latency (> 5000ms) → HIGH PRIORITY Action
5. Stable System (error_rate = 0, latency < 1000) → LOW PRIORITY MONITOR Action
"""
import pytest
from datetime import datetime
from backend.services.logging.optimization_engine import (
    OptimizationEngine,
    SystemAction,
    ActionPriority,
    ActionType
)


def test_high_error_rate_generates_high_priority_action():
    """
    Test Case 1: High Error Rate (> 0.3) → HIGH PRIORITY Action.
    
    Scenario: A skill with 40% error rate should trigger a HIGH PRIORITY SCALE_UP action.
    """
    engine = OptimizationEngine(hours=1)
    
    insight = {
        "skill": "knowledge.query",
        "model": "gpt-4o-mini",
        "error_rate": 0.4,
        "avg_latency_ms": 500,
        "calls": 100,
        "patterns": ["high_error_rate"],
        "confidence": 0.5
    }
    
    action = engine.evaluate_insight(insight)
    
    assert action is not None, "Action should be generated for high error rate"
    assert action.skill == "knowledge.query"
    assert action.model == "gpt-4o-mini"
    assert action.priority == ActionPriority.HIGH, f"Expected HIGH priority, got {action.priority}"
    assert action.action_type == ActionType.SCALE_UP, f"Expected SCALE_UP action, got {action.action_type}"
    assert "High error rate" in action.reason
    assert action.current_value == 0.4
    assert action.threshold == engine.ERROR_THRESHOLD_HIGH
    
    print("✅ Test Case 1 PASSED: High Error Rate → HIGH PRIORITY Action")


def test_critical_error_rate_generates_critical_priority_action():
    """
    Test Case 2: Critical Error Rate (> 0.5) → CRITICAL PRIORITY Action.
    
    Scenario: A skill with 60% error rate should trigger a CRITICAL PRIORITY MODEL_SWITCH action.
    """
    engine = OptimizationEngine(hours=1)
    
    insight = {
        "skill": "websearch",
        "model": "gpt-4o-mini",
        "error_rate": 0.6,
        "avg_latency_ms": 500,
        "calls": 100,
        "patterns": ["high_error_rate"],
        "confidence": 0.5
    }
    
    action = engine.evaluate_insight(insight)
    
    assert action is not None, "Action should be generated for critical error rate"
    assert action.skill == "websearch"
    assert action.model == "gpt-4o-mini"
    assert action.priority == ActionPriority.CRITICAL, f"Expected CRITICAL priority, got {action.priority}"
    assert action.action_type == ActionType.MODEL_SWITCH, f"Expected MODEL_SWITCH action, got {action.action_type}"
    assert "Critical error rate" in action.reason
    assert action.current_value == 0.6
    assert action.threshold == engine.ERROR_THRESHOLD_CRITICAL
    
    print("✅ Test Case 2 PASSED: Critical Error Rate → CRITICAL PRIORITY Action")


def test_high_latency_generates_high_priority_action():
    """
    Test Case 3: High Latency (> 3000ms) → HIGH PRIORITY Action.
    
    Scenario: A skill with 3500ms latency should trigger a HIGH PRIORITY TIMEOUT_ADJUST action.
    """
    engine = OptimizationEngine(hours=1)
    
    insight = {
        "skill": "filesystem.find_files",
        "model": "gpt-4o-mini",
        "error_rate": 0.1,
        "avg_latency_ms": 3500,
        "calls": 100,
        "patterns": ["latency_spike"],
        "confidence": 0.5
    }
    
    action = engine.evaluate_insight(insight)
    
    assert action is not None, "Action should be generated for high latency"
    assert action.skill == "filesystem.find_files"
    assert action.model == "gpt-4o-mini"
    assert action.priority == ActionPriority.HIGH, f"Expected HIGH priority, got {action.priority}"
    assert action.action_type == ActionType.TIMEOUT_ADJUST, f"Expected TIMEOUT_ADJUST action, got {action.action_type}"
    assert "High latency" in action.reason
    assert action.current_value == 3500
    assert action.threshold == engine.LATENCY_THRESHOLD_HIGH
    
    print("✅ Test Case 3 PASSED: High Latency → HIGH PRIORITY Action")


def test_critical_latency_generates_high_priority_action():
    """
    Test Case 4: Critical Latency (> 5000ms) → HIGH PRIORITY Action.
    
    Scenario: A skill with 6000ms latency should trigger a HIGH PRIORITY MODEL_SWITCH action.
    """
    engine = OptimizationEngine(hours=1)
    
    insight = {
        "skill": "video.understand",
        "model": "gpt-4o",
        "error_rate": 0.1,
        "avg_latency_ms": 6000,
        "calls": 50,
        "patterns": ["latency_spike"],
        "confidence": 0.3
    }
    
    action = engine.evaluate_insight(insight)
    
    assert action is not None, "Action should be generated for critical latency"
    assert action.skill == "video.understand"
    assert action.model == "gpt-4o"
    assert action.priority == ActionPriority.HIGH, f"Expected HIGH priority, got {action.priority}"
    assert action.action_type == ActionType.MODEL_SWITCH, f"Expected MODEL_SWITCH action, got {action.action_type}"
    assert "Critical latency" in action.reason
    assert action.current_value == 6000
    assert action.threshold == engine.LATENCY_THRESHOLD_CRITICAL
    
    print("✅ Test Case 4 PASSED: Critical Latency → HIGH PRIORITY Action")


def test_stable_system_generates_low_priority_monitor_action():
    """
    Test Case 5: Stable System (error_rate = 0, latency < 1000) → LOW PRIORITY MONITOR Action.
    
    Scenario: A skill with 0 error rate and low latency should trigger a LOW PRIORITY MONITOR action.
    """
    engine = OptimizationEngine(hours=1)
    
    insight = {
        "skill": "system.websearch",
        "model": "gpt-4o-mini",
        "error_rate": 0.0,
        "avg_latency_ms": 500,
        "calls": 100,
        "patterns": ["stable"],
        "confidence": 1.0
    }
    
    action = engine.evaluate_insight(insight)
    
    assert action is not None, "Action should be generated for stable system"
    assert action.skill == "system.websearch"
    assert action.model == "gpt-4o-mini"
    assert action.priority == ActionPriority.LOW, f"Expected LOW priority, got {action.priority}"
    assert action.action_type == ActionType.MONITOR, f"Expected MONITOR action, got {action.action_type}"
    assert "operating normally" in action.reason
    assert action.current_value == 0.0
    assert action.threshold == 0.0
    
    print("✅ Test Case 5 PASSED: Stable System → LOW PRIORITY MONITOR Action")


def test_no_action_for_moderate_metrics():
    """
    Test Case 6: Moderate metrics (error_rate < 0.3, latency < 3000) → No action.
    
    Scenario: A skill with moderate metrics should not trigger any action.
    """
    engine = OptimizationEngine(hours=1)
    
    insight = {
        "skill": "knowledge.query",
        "model": "gpt-4o-mini",
        "error_rate": 0.2,
        "avg_latency_ms": 1500,
        "calls": 100,
        "patterns": [],
        "confidence": 0.5
    }
    
    action = engine.evaluate_insight(insight)
    
    assert action is None, "No action should be generated for moderate metrics"
    
    print("✅ Test Case 6 PASSED: Moderate metrics → No action")


def test_action_serialization():
    """
    Test Case 7: Action serialization for JSON storage.
    
    Scenario: Verify that SystemAction can be serialized with model_dump(mode='json').
    """
    action = SystemAction(
        skill="test.skill",
        model="test-model",
        action_type=ActionType.SCALE_UP,
        priority=ActionPriority.HIGH,
        reason="Test reason",
        current_value=0.4,
        threshold=0.3,
        recommendation="Test recommendation",
        time_window_hours=1
    )
    
    # Test serialization
    action_dict = action.model_dump(mode='json')
    
    assert action_dict["skill"] == "test.skill"
    assert action_dict["model"] == "test-model"
    assert action_dict["action_type"] == "SCALE_UP"
    assert action_dict["priority"] == "HIGH"
    assert "generated_at" in action_dict
    assert isinstance(action_dict["generated_at"], str), "generated_at should be serialized as string"
    
    print("✅ Test Case 7 PASSED: Action serialization")


if __name__ == "__main__":
    test_high_error_rate_generates_high_priority_action()
    test_critical_error_rate_generates_critical_priority_action()
    test_high_latency_generates_high_priority_action()
    test_critical_latency_generates_high_priority_action()
    test_stable_system_generates_low_priority_monitor_action()
    test_no_action_for_moderate_metrics()
    test_action_serialization()
    print("\n🎉 ALL TESTS PASSED")
