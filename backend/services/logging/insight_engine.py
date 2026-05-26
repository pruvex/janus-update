"""
Janus Insight Engine (D12) — Globale Log-Aggregation für System-Health Monitoring.

Deterministische Aggregation von Logs nach Skill und Model.
Keine Physics-Engine, keine Reality-Scores. Nur harte, deterministische Berechnungen.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from pydantic import BaseModel, Field
import statistics
import logging

from backend.services.logging.supabase_client import get_supabase_client

logger = logging.getLogger("janus_backend")


class InsightResult(BaseModel):
    """Ergebnis der Insight-Analyse für einen Skill/Model-Kombination."""
    skill_id: str = Field(..., description="Skill identifier (namespace.action format)")
    model: str = Field(..., description="Model name")
    calls: int = Field(..., description="Total number of calls")
    error_rate: float = Field(..., description="Error rate (0.0 to 1.0)")
    avg_latency_ms: float = Field(..., description="Average latency in milliseconds")
    patterns: List[str] = Field(default_factory=list, description="Detected patterns")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of analysis")


class InsightEngine:
    """
    Janus Insight Engine — Globale Log-Aggregation.
    
    Aggregiert Logs aus Supabase nach Skill und Model,
    berechnet Metriken (calls, error_rate, avg_latency),
    detektiert Patterns und berechnet Confidence-Scores.
    """
    
    def __init__(self, hours: int = 1):
        """
        Initialize Insight Engine.
        
        Args:
            hours: Time window in hours for log fetching (default: 1)
        """
        self.hours = hours
        self.supabase = get_supabase_client()
    
    def fetch_logs(self) -> List[Dict[str, Any]]:
        """
        Fetch logs from Supabase for the specified time window.
        
        Returns:
            List of log entries from logs_raw table
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=self.hours)
            
            response = (
                self.supabase
                .table("logs_raw")
                .select("*")
                .gte("timestamp", cutoff.isoformat())
                .execute()
            )
            
            logs = response.data if response.data else []
            return logs
        except Exception as e:
            logger.error(f"[InsightEngine] Error fetching logs: {e}", exc_info=True)
            return []
    
    def aggregate_logs(self, logs: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Aggregate logs by skill and model.
        
        Groups logs by (skill, model) and calculates:
        - calls: Total number of calls
        - errors: Number of errors (status='error')
        - total_latency: Sum of latency_ms
        - latency_count: Number of logs with latency_ms
        
        Args:
            logs: List of log entries
        
        Returns:
            Dictionary mapping (skill, model) -> aggregated metrics
        """
        grouped = defaultdict(lambda: {
            "calls": 0,
            "errors": 0,
            "total_latency": 0,
            "latency_count": 0
        })
        
        for log in logs:
            skill_id = log.get("skill") or "unknown"
            model = log.get("model") or "unknown"
            key = (skill_id, model)
            
            grouped[key]["calls"] += 1
            
            if log.get("status") == "error":
                grouped[key]["errors"] += 1
            
            latency = log.get("latency_ms")
            if latency is not None and latency > 0:
                grouped[key]["total_latency"] += latency
                grouped[key]["latency_count"] += 1
        
        return grouped
    
    def calculate_metrics(self, grouped: Dict[Tuple[str, str], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate metrics for each skill/model combination.
        
        Computes:
        - error_rate: errors / calls
        - avg_latency_ms: total_latency / latency_count
        
        Args:
            grouped: Aggregated logs from aggregate_logs()
        
        Returns:
            List of metric dictionaries
        """
        metrics = []
        
        for (skill_id, model), data in grouped.items():
            calls = data["calls"]
            errors = data["errors"]
            total_latency = data["total_latency"]
            latency_count = data["latency_count"]
            
            error_rate = errors / calls if calls > 0 else 0.0
            avg_latency = total_latency / latency_count if latency_count > 0 else 0.0
            
            metrics.append({
                "skill_id": skill_id,
                "model": model,
                "calls": calls,
                "errors": errors,
                "error_rate": error_rate,
                "avg_latency_ms": avg_latency
            })
        
        return metrics
    
    def detect_patterns(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Detect patterns based on metrics.
        
        Pattern rules:
        - error_rate > 0.2 -> "high_error_rate"
        - avg_latency_ms > 2000 -> "latency_spike"
        - calls > 50 and error_rate == 0 -> "stable"
        
        Args:
            metrics: Dictionary with calls, error_rate, avg_latency_ms
        
        Returns:
            List of detected pattern strings
        """
        patterns = []
        
        calls = metrics.get("calls", 0)
        error_rate = metrics.get("error_rate", 0.0)
        avg_latency = metrics.get("avg_latency_ms", 0.0)
        
        if error_rate > 0.2:
            patterns.append("high_error_rate")
        
        if avg_latency > 2000:
            patterns.append("latency_spike")
        
        if calls > 50 and error_rate == 0.0:
            patterns.append("stable")
        
        return patterns
    
    def calculate_confidence(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on metrics.
        
        Confidence formula:
        - Base: min(1.0, calls / 100)
        - Reduction: -20% if error_rate > 0.5
        
        Args:
            metrics: Dictionary with calls, error_rate
        
        Returns:
            Confidence score (0.0 to 1.0)
        """
        calls = metrics.get("calls", 0)
        error_rate = metrics.get("error_rate", 0.0)
        
        base_confidence = min(1.0, calls / 100.0)
        
        if error_rate > 0.5:
            base_confidence *= 0.8
        
        return base_confidence
    
    def analyze(self) -> List[InsightResult]:
        """
        Run full insight analysis pipeline.
        
        Fetches logs, aggregates by skill/model, calculates metrics,
        detects patterns, and computes confidence scores.
        
        Returns:
            List of InsightResult objects
        """
        logs = self.fetch_logs()
        
        if not logs:
            print(f"[InsightEngine] No logs found in last {self.hours} hour(s)")
            return []
        
        grouped = self.aggregate_logs(logs)
        metrics_list = self.calculate_metrics(grouped)
        
        results = []
        for metrics in metrics_list:
            patterns = self.detect_patterns(metrics)
            confidence = self.calculate_confidence(metrics)
            
            result = InsightResult(
                skill_id=metrics["skill_id"],
                model=metrics["model"],
                calls=metrics["calls"],
                error_rate=metrics["error_rate"],
                avg_latency_ms=metrics["avg_latency_ms"],
                patterns=patterns,
                confidence=confidence
            )
            results.append(result)
        
        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)
        
        return results
    
    def generate_health_matrix(self) -> Dict[str, Any]:
        """
        Generate Skill Health Matrix from D10 skill_test events.
        
        Aggregates skill_test events and calculates:
        - pass_rate = passed / total_runs
        - escalation_rate = escalation_attempts / total_runs
        
        Returns:
            Health Matrix dict with skill-level metrics
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=self.hours)
            
            # Fetch skill_test events from logs_raw
            response = (
                self.supabase
                .table("logs_raw")
                .select("*")
                .eq("event_type", "skill_test")
                .gte("timestamp", cutoff.isoformat())
                .execute()
            )
            
            test_logs = response.data if response.data else []
            
            if not test_logs:
                return {
                    "skills_analyzed": 0,
                    "matrix": {},
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            # Aggregate by skill_id
            skill_metrics = defaultdict(lambda: {
                "total_runs": 0,
                "passed": 0,
                "failed": 0,
                "error": 0,
                "total_escalation_attempts": 0,
                "total_latency_ms": 0
            })
            
            for log in test_logs:
                skill_id = log.get("skill") or "unknown"
                status = log.get("status") or "unknown"
                payload = log.get("payload", {}) or {}
                latency_ms = log.get("latency_ms", 0) or 0
                
                metrics = skill_metrics[skill_id]
                metrics["total_runs"] += 1
                
                if status == "passed":
                    metrics["passed"] += 1
                elif status == "failed":
                    metrics["failed"] += 1
                elif status == "error":
                    metrics["error"] += 1
                
                # Extract escalation attempts from test results if available
                # For now, we use a simple heuristic: if latency > 200ms, count as potential escalation
                if latency_ms > 200:
                    metrics["total_escalation_attempts"] += 1
                
                metrics["total_latency_ms"] += latency_ms
            
            # Calculate health matrix
            matrix = {}
            for skill_id, metrics in skill_metrics.items():
                total_runs = metrics["total_runs"]
                passed = metrics["passed"]
                escalation_attempts = metrics["total_escalation_attempts"]
                total_latency = metrics["total_latency_ms"]
                
                pass_rate = passed / total_runs if total_runs > 0 else 0.0
                escalation_rate = escalation_attempts / total_runs if total_runs > 0 else 0.0
                avg_latency = total_latency / total_runs if total_runs > 0 else 0.0
                
                # Determine health status
                if pass_rate >= 0.9:
                    health_status = "healthy"
                elif pass_rate >= 0.7:
                    health_status = "degraded"
                else:
                    health_status = "unhealthy"
                
                matrix[skill_id] = {
                    "pass_rate": round(pass_rate, 4),
                    "escalation_rate": round(escalation_rate, 4),
                    "total_runs": total_runs,
                    "passed": passed,
                    "failed": metrics["failed"],
                    "error": metrics["error"],
                    "avg_latency_ms": round(avg_latency, 2),
                    "health_status": health_status
                }
            
            return {
                "skills_analyzed": len(matrix),
                "matrix": matrix,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[InsightEngine] Error generating health matrix: {e}", exc_info=True)
            return {
                "error": str(e),
                "skills_analyzed": 0,
                "matrix": {},
                "generated_at": datetime.utcnow().isoformat()
            }
