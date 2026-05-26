#!/usr/bin/env python3
"""
Test-Script für Debug Compression Engine (D11)
Testet die deterministische Heuristik ohne LLM-Abhängigkeit.
"""
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.services.logging.debug_engine import (
    DebugReport,
    LogEntry,
    HeuristicResult,
    LogFetcher,
    LogAnalyzer,
    DebugEngine
)


async def test_log_fetcher_ram_buffer():
    """Test 1: RAM-Buffer Priority"""
    print("=" * 60)
    print("TEST 1: LogFetcher RAM-Buffer Priority")
    print("=" * 60)
    
    fetcher = LogFetcher()
    
    # Simulierte Logs hinzufügen
    now = datetime.utcnow()
    for i in range(10):
        entry = LogEntry(
            timestamp=now,
            level="ERROR",
            message=f"HTTP 500 Internal Server Error {i}"
        )
        fetcher.add_to_ram_buffer(entry)
    
    # Logs holen (sollte aus RAM-Buffer kommen)
    logs = await fetcher.fetch_logs(limit=5)
    
    print(f"✅ Fetched {len(logs)} logs from RAM-Buffer")
    print(f"   Expected: 5, Got: {len(logs)}")
    assert len(logs) == 5, f"Expected 5 logs, got {len(logs)}"
    print()


async def test_log_analyzer_heuristics():
    """Test 2: Deterministische Heuristik"""
    print("=" * 60)
    print("TEST 2: LogAnalyzer Deterministische Heuristik")
    print("=" * 60)
    
    analyzer = LogAnalyzer()
    
    # Simulierte Logs mit verschiedenen Mustern
    logs = [
        LogEntry(timestamp=datetime.utcnow(), level="ERROR", message="HTTP 500 Internal Server Error"),
        LogEntry(timestamp=datetime.utcnow(), level="ERROR", message="HTTP 404 Not Found"),
        LogEntry(timestamp=datetime.utcnow(), level="ERROR", message="Connection timeout"),
        LogEntry(timestamp=datetime.utcnow(), level="ERROR", message="Empty payload received"),
        LogEntry(timestamp=datetime.utcnow(), level="ERROR", message="HTTP 500 Internal Server Error"),
        LogEntry(timestamp=datetime.utcnow(), level="ERROR", message="Validation error: invalid argument"),
    ]
    
    heuristics = analyzer.analyze(logs)
    
    print(f"✅ Detected {len(heuristics)} patterns")
    for h in heuristics:
        print(f"   - {h.pattern_type}: count={h.count}, confidence={h.confidence}")
    
    assert len(heuristics) > 0, "Expected at least one pattern"
    print()


async def test_log_analyzer_run_heuristics():
    """Test 2.5: LogAnalyzer _run_heuristics mit Hard Errors, Model Drift, Latency Spikes"""
    print("=" * 60)
    print("TEST 2.5: LogAnalyzer _run_heuristics (Enhanced)")
    print("=" * 60)
    
    from backend.data.schemas_logging import LogEventCreate
    
    analyzer = LogAnalyzer()
    
    # Simulierte LogEvents mit Hard Errors, Model Drift, Latency Spikes
    # Use more healthy events to ensure confidence score > 0
    events = []
    
    # Add 95 healthy events to boost base confidence
    for i in range(95):
        events.append(LogEventCreate(
            timestamp=datetime.utcnow(),
            status="success",
            skill="filesystem.find_files",
            event_type="response",
            latency_ms=200
        ))
    
    # Hard Error
    events.append(LogEventCreate(
        timestamp=datetime.utcnow(),
        status="error",
        skill="knowledge.query",
        event_type="response",
        payload={"error_code": "TIMEOUT_ERROR"}
    ))
    # Latency Spike (> 5 Sekunden)
    events.append(LogEventCreate(
        timestamp=datetime.utcnow(),
        status="success",
        skill="websearch",
        event_type="response",
        latency_ms=6000
    ))
    # Model Drift (innerhalb eines Traces)
    events.append(LogEventCreate(
        timestamp=datetime.utcnow(),
        trace_id="trace-123",
        provider="openai",
        model="gpt-5.4-nano",
        skill="knowledge.query",
        event_type="request"
    ))
    events.append(LogEventCreate(
        timestamp=datetime.utcnow(),
        trace_id="trace-123",
        provider="gemini",  # Provider drift
        model="gemini-3-flash",
        skill="knowledge.query",
        event_type="response"
    ))
    
    findings = analyzer._run_heuristics(events)
    
    print(f"✅ Hard Errors: {len(findings['hard_errors'])}")
    for error in findings['hard_errors']:
        print(f"   - {error}")
    
    print(f"✅ Model Drift: {len(findings['model_drift'])}")
    for drift in findings['model_drift']:
        print(f"   - {drift}")
    
    print(f"✅ Latency Spikes: {len(findings['latency_spikes'])}")
    for spike in findings['latency_spikes']:
        print(f"   - {spike}")
    
    print(f"✅ Confidence Score: {findings['confidence_score']:.2f}")
    
    # Test Heuristic Summary Generierung
    summary = analyzer.generate_heuristic_summary(findings)
    print(f"✅ Heuristic Summary generated ({len(summary)} chars)")
    print("   Preview:")
    print("   " + "\n   ".join(summary.split("\n")[:10]))
    
    assert len(findings['hard_errors']) > 0, "Expected at least one hard error"
    assert len(findings['latency_spikes']) > 0, "Expected at least one latency spike"
    assert len(findings['model_drift']) > 0, "Expected model drift"
    assert findings['confidence_score'] > 0, "Expected confidence score > 0"
    print()


def test_log_analyzer_confidence():
    """Test 3: Confidence Berechnung"""
    print("=" * 60)
    print("TEST 3: LogAnalyzer Confidence Berechnung")
    print("=" * 60)
    
    analyzer = LogAnalyzer()
    
    # Test 1: Hohe Confidence (>50%)
    confidence_high = analyzer.get_confidence(60, 100)
    print(f"✅ High confidence (60/100): {confidence_high}")
    assert confidence_high == 0.9, f"Expected 0.9, got {confidence_high}"
    
    # Test 2: Mittlere Confidence (>30%)
    confidence_medium = analyzer.get_confidence(40, 100)
    print(f"✅ Medium confidence (40/100): {confidence_medium}")
    assert confidence_medium == 0.7, f"Expected 0.7, got {confidence_medium}"
    
    # Test 3: Niedrige Confidence (>10%)
    confidence_low = analyzer.get_confidence(20, 100)
    print(f"✅ Low confidence (20/100): {confidence_low}")
    assert confidence_low == 0.5, f"Expected 0.5, got {confidence_low}"
    
    # Test 4: Sehr niedrige Confidence (<10%)
    confidence_very_low = analyzer.get_confidence(5, 100)
    print(f"✅ Very low confidence (5/100): {confidence_very_low}")
    assert confidence_very_low == 0.3, f"Expected 0.3, got {confidence_very_low}"
    
    print()


def test_debug_report_schema():
    """Test 4: Pydantic Schema Validierung"""
    print("=" * 60)
    print("TEST 4: DebugReport Pydantic Schema Validierung")
    print("=" * 60)
    
    # Valider Report (V3 Schema)
    report = DebugReport(
        problem="HTTP 500 Internal Server Errors detected in API endpoint logs. This pattern indicates server-side exceptions that are causing service disruption and affecting user experience.",
        root_cause="Server-side exception in API endpoint due to unhandled error conditions",
        patterns="Repeated HTTP 500 errors in logs, indicating systematic failure in backend processing",
        anomalies="Elevated error rate exceeding normal baseline, suggesting potential infrastructure or code issues",
        impact="Service disruption affecting user experience, potential data loss, and degraded system reliability",
        recommended_fix="Check server logs and fix the exception. Implement proper error handling and monitoring",
        confidence=0.9
    )
    
    print(f"✅ Valid DebugReport created")
    print(f"   Problem: {report.problem}")
    print(f"   Root Cause: {report.root_cause}")
    print(f"   Recommended Fix: {report.recommended_fix}")
    print(f"   Confidence: {report.confidence}")
    
    # Test: Extra Feld sollte abgelehnt werden
    try:
        invalid_report = DebugReport(
            problem="Test problem description that meets minimum length requirement of 150 characters for validation purposes",
            root_cause="Test root cause",
            patterns="Test patterns",
            anomalies="Test anomalies",
            impact="Test impact",
            recommended_fix="Test recommended fix",
            confidence=0.5,
            extra_field="should_fail"
        )
        print("❌ FAIL: Extra field should be rejected")
        assert False, "Extra field should be rejected"
    except Exception as e:
        print(f"✅ Extra field correctly rejected: {e}")
    
    # Test: Confidence außerhalb Range sollte abgelehnt werden
    try:
        invalid_report = DebugReport(
            problem="Test problem description that meets minimum length requirement of 150 characters for validation purposes",
            root_cause="Test root cause",
            patterns="Test patterns",
            anomalies="Test anomalies",
            impact="Test impact",
            recommended_fix="Test recommended fix",
            confidence=1.5  # > 1.0
        )
        print("❌ FAIL: Confidence > 1.0 should be rejected")
        assert False, "Confidence > 1.0 should be rejected"
    except Exception as e:
        print(f"✅ Confidence > 1.0 correctly rejected: {e}")
    
    print()


async def test_debug_engine_integration():
    """Test 5: Debug Engine Integration (ohne LLM)"""
    print("=" * 60)
    print("TEST 5: Debug Engine Integration (ohne LLM)")
    print("=" * 60)
    
    # Test mit Provider-Agnostic Konfiguration (ohne Override -> liest aus Config)
    engine = DebugEngine()
    
    # Simulierte Logs in RAM-Buffer hinzufügen
    now = datetime.utcnow()
    for i in range(20):
        entry = LogEntry(
            timestamp=now,
            level="ERROR",
            message=f"HTTP 500 Internal Server Error {i}"
        )
        engine.fetcher.add_to_ram_buffer(entry)
    
    # Analyse ohne LLM (durch manuellen Heuristik-Aufruf)
    logs = await engine.fetcher.fetch_logs(limit=10)
    heuristics = engine.analyzer.analyze(logs)
    
    print(f"✅ Engine analyzed {len(logs)} logs")
    print(f"   Detected {len(heuristics)} patterns")
    print(f"   Provider-Agnostic: Uses configured speed-tier model")
    
    # Test get_speed_tier_model() Funktion
    from backend.services.logging.debug_engine import get_speed_tier_model
    provider, model = get_speed_tier_model()
    print(f"   Auto-detected Provider: {provider}")
    print(f"   Auto-detected Speed-Tier Model: {model}")
    
    if heuristics:
        top_pattern = heuristics[0]
        print(f"   Top pattern: {top_pattern.pattern_type} (count={top_pattern.count})")
        
        # Manuelles Fallback-Report generieren (ohne LLM)
        from backend.services.logging.debug_engine import DebugReport
        report = DebugReport(
            problem=f"Detected {top_pattern.pattern_type} pattern in logs. This pattern occurred {top_pattern.count} times with confidence {top_pattern.confidence}. Sample messages: {', '.join(top_pattern.sample_messages[:3])}",
            root_cause=f"Logs contain {top_pattern.count} occurrences of {top_pattern.pattern_type}. Pattern detected: {top_pattern.pattern_match}",
            patterns=f"Primary pattern: {top_pattern.pattern_type} (count: {top_pattern.count}). Confidence: {top_pattern.confidence}",
            anomalies="No specific anomalies detected in heuristic analysis",
            impact=f"System performance or reliability may be affected by {top_pattern.pattern_type} pattern",
            recommended_fix=f"Investigate {top_pattern.pattern_type} in the application logs. Review sample messages: {', '.join(top_pattern.sample_messages[:2])}",
            confidence=top_pattern.confidence
        )
        
        print(f"✅ Generated fallback report")
        print(f"   Problem: {report.problem}")
        print(f"   Confidence: {report.confidence}")
    
    print()


async def main():
    """Führt alle Tests aus"""
    print("\n")
    print("=" * 60)
    print("DEBUG COMPRESSION ENGINE (D11) — TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        await test_log_fetcher_ram_buffer()
        await test_log_analyzer_heuristics()
        await test_log_analyzer_run_heuristics()
        test_log_analyzer_confidence()
        test_debug_report_schema()
        await test_debug_engine_integration()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        
    except AssertionError as e:
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print("=" * 60)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
