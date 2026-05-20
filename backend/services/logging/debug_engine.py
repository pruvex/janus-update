"""
Debug Compression Engine (D11) — Production-Safe Design
Deterministische Heuristik + Lightweight LLM Integration für Debug-Report Generierung.
Provider-Agnostic (BYOK-kompatibel) — Nutzt das konfigurierte Speed-Tier Modell des Users.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import re
from backend.utils.redaction import redact_sensitive_text, redact_sensitive_value

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions (Provider-Agnostic)
# ============================================================================

def get_speed_tier_model() -> tuple[str, str]:
    """
    Gibt das Speed-Tier Modell für den aktuell konfigurierten Provider zurück.
    
    Returns:
        tuple: (provider, model) - Provider und Speed-Tier Modell
               Falls nicht konfiguriert: ("openai", "gpt-5.4-nano") als Fallback
    """
    try:
        from backend.utils.config_loader import load_config_data
        config = load_config_data()
        
        # Provider aus Config lesen
        provider = str(config.get("last_used_provider", "openai")).strip().lower()
        
        # Speed-Tier Modell aus MOA_MODEL_HIERARCHY holen
        from backend.llm_providers.shared.moa import MOA_MODEL_HIERARCHY
        
        provider_tiers = MOA_MODEL_HIERARCHY.get(provider)
        if provider_tiers:
            model = provider_tiers.get("speed")
            if model:
                logger.info(f"DebugEngine: Using speed-tier model '{model}' for provider '{provider}'")
                return provider, model
        
        # Fallback: Default Speed-Tier Modell
        logger.warning(f"DebugEngine: No speed-tier model found for provider '{provider}', using fallback")
        return "openai", "gpt-5.4-nano"
        
    except Exception as e:
        logger.error(f"DebugEngine: Failed to get speed-tier model: {e}")
        return "openai", "gpt-5.4-nano"


# ============================================================================
# Pydantic Schemas (Strict Data Integrity)
# ============================================================================

class DebugReport(BaseModel):
    """
    Strukturierter Debug-Report mit strikter Schema-Validierung (V3).
    Production-Safe Design: Alle Felder sind required und haben klare Typen.
    Enhanced with detailed sections for comprehensive analysis.
    """
    problem: str = Field(..., description="Präzise Benennung des Problems (minimum 150 chars)")
    root_cause: str = Field(..., description="Technische Ursache des Problems")
    patterns: str = Field(..., description="Erkannte Patterns in den Logs")
    anomalies: str = Field(..., description="Ungewöhnliches Verhalten oder Ausreißer")
    impact: str = Field(..., description="Business- oder System-Impact Assessment")
    recommended_fix: str = Field(..., description="Konkrete Handlungsempfehlung zur Lösung")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Sicherheit der Diagnose (0.0 - 1.0)")
    
    class Config:
        extra = "forbid"  # Striktes Schema: Keine zusätzlichen Felder erlaubt


class LogEntry(BaseModel):
    """
    Ein einzelner Log-Eintrag für die Analyse.
    Minimalistisches Schema für effiziente Verarbeitung.
    """
    timestamp: datetime
    level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None


class HeuristicResult(BaseModel):
    """
    Ergebnis der deterministischen Heuristik-Analyse.
    Wird als Input für die LLM-Übersetzung verwendet.
    """
    pattern_type: str
    pattern_match: str
    count: int
    sample_messages: List[str]
    confidence: float


# ============================================================================
# Data Fetching (RAM-Buffer -> Supabase Fallback)
# ============================================================================

class LogFetcher:
    """
    Log-Fetcher mit Kaskade: RAM-Buffer (logger_core) -> Supabase Fallback.
    Production-Safe: RAM-Buffer hat Priorität für Performance, Supabase als Fallback.
    """
    
    def __init__(self):
        self.ram_buffer: List[LogEntry] = []
        self.max_ram_entries = 1000
        
    def add_to_ram_buffer(self, entry: LogEntry) -> None:
        """Fügt einen Log-Eintrag zum RAM-Buffer hinzu."""
        self.ram_buffer.append(entry)
        if len(self.ram_buffer) > self.max_ram_entries:
            self.ram_buffer.pop(0)  # Drop-Oldest
        
    async def fetch_logs(self, limit: int = 100) -> List[LogEntry]:
        """
        Holt Logs mit Kaskade: RAM-Buffer -> Supabase Fallback -> Log-File Fallback.
        
        Args:
            limit: Maximale Anzahl der zurückzugebenden Logs.
            
        Returns:
            List[LogEntry]: Liste der Log-Einträge.
        """
        # 1. Versuch: RAM-Buffer (schnell, keine DB-Abfrage)
        if len(self.ram_buffer) >= limit:
            logger.debug(f"LogFetcher: Returned {limit} entries from RAM-Buffer")
            return self.ram_buffer[-limit:]
        
        # 2. Fallback: Supabase (letzte 10 Minuten)
        try:
            from backend.services.logging.supabase_client import get_supabase_client
            client = get_supabase_client()
            
            # Letzte 10 Minuten
            cutoff = datetime.utcnow() - timedelta(minutes=10)
            
            response = (
                client.table("logs_raw")
                .select("created_at, level, message, metadata")
                .gte("created_at", cutoff.isoformat())
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            logs = []
            for row in response.data:
                logs.append(LogEntry(
                    timestamp=datetime.fromisoformat(row["created_at"]),
                    level=row.get("level", "INFO"),
                    message=redact_sensitive_text(row.get("message", "")),
                    metadata=redact_sensitive_value(row.get("metadata"))
                ))
            
            logger.info(f"LogFetcher: Returned {len(logs)} entries from Supabase")
            return logs
            
        except Exception as e:
            logger.warning(f"LogFetcher: Supabase fallback failed: {e}")
            
        # 3. Fallback: Log-File (janus_backend.log)
        try:
            from backend.utils.paths import get_app_data_dir
            import os
            
            log_dir = os.path.join(get_app_data_dir(), "logs")
            log_file = os.path.join(log_dir, "janus_backend.log")
            
            if os.path.exists(log_file):
                # Letzte 1000 Zeilen lesen
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                # Nur die letzten limit Zeilen nehmen
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                logs = []
                for line in recent_lines:
                    # Einfache Log-Parser-Logik
                    # Format: TIMESTAMP - LEVEL - MESSAGE
                    try:
                        # Extrahiere Timestamp und Level aus der Zeile
                        parts = line.split(" - ")
                        if len(parts) >= 3:
                            timestamp_str = parts[0]
                            level = parts[1].split(" - ")[0] if " - " in parts[1] else "INFO"
                            message = " - ".join(parts[2:])
                            
                            # Timestamp parsen
                            try:
                                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            except:
                                timestamp = datetime.utcnow()
                            
                            logs.append(LogEntry(
                                timestamp=timestamp,
                                level=level,
                                message=redact_sensitive_text(message.strip()),
                                metadata=None
                            ))
                    except:
                        continue
                
                logger.info(f"LogFetcher: Returned {len(logs)} entries from log file")
                return logs
            else:
                logger.warning(f"LogFetcher: Log file not found: {log_file}")
                
        except Exception as e:
            logger.warning(f"LogFetcher: Log file fallback failed: {e}")
        
        # 4. Ultimate Fallback: Leere Liste
        logger.warning("LogFetcher: All fallbacks failed, returning empty list")
        return []


# ============================================================================
# Deterministische Heuristik
# ============================================================================

class LogAnalyzer:
    """
    Deterministische Heuristik für Log-Analyse.
    Production-Safe: Keine LLM-Abhängigkeit, nur regelbasierte Muster-Erkennung.
    Erweitert um Trace-basierte Analyse und Heuristic Summary Generierung.
    """
    
    # Hartkodierte Fehler-Muster (Production-Safe)
    PATTERNS = {
        "http_4xx": re.compile(r"4\d{2}"),
        "http_5xx": re.compile(r"5\d{2}"),
        "timeout": re.compile(r"timeout|timed out|deadline exceeded", re.IGNORECASE),
        "empty_payload": re.compile(r"empty payload|no data|null payload", re.IGNORECASE),
        "connection_error": re.compile(r"connection refused|connection error|network error", re.IGNORECASE),
        "validation_error": re.compile(r"validation error|invalid argument|bad request", re.IGNORECASE),
        "permission_error": re.compile(r"permission denied|access denied|unauthorized", re.IGNORECASE),
    }
    
    def __init__(self):
        self.pattern_counts: Dict[str, int] = {}
        self.pattern_samples: Dict[str, List[str]] = {}
        
    def analyze(self, logs: List[LogEntry]) -> List[HeuristicResult]:
        """
        Analysiert Logs mit deterministischen Heuristiken (Legacy-Methode).
        
        Args:
            logs: Liste der zu analysierenden Log-Einträge.
            
        Returns:
            List[HeuristicResult]: Liste der erkannten Muster.
        """
        results = []
        
        # Reset Counts
        self.pattern_counts = {key: 0 for key in self.PATTERNS.keys()}
        self.pattern_samples = {key: [] for key in self.PATTERNS.keys()}
        
        # Pattern Matching
        for log in logs:
            for pattern_name, pattern in self.PATTERNS.items():
                if pattern.search(log.message):
                    self.pattern_counts[pattern_name] += 1
                    if len(self.pattern_samples[pattern_name]) < 3:
                        self.pattern_samples[pattern_name].append(log.message)
        
        # Ergebnisse generieren
        for pattern_name, count in self.pattern_counts.items():
            if count > 0:
                confidence = self.get_confidence(count, len(logs))
                results.append(HeuristicResult(
                    pattern_type=pattern_name,
                    pattern_match=self.PATTERNS[pattern_name].pattern,
                    count=count,
                    sample_messages=self.pattern_samples[pattern_name],
                    confidence=confidence
                ))
        
        # Sortieren nach Häufigkeit
        results.sort(key=lambda x: x.count, reverse=True)
        
        logger.info(f"LogAnalyzer: Found {len(results)} patterns in {len(logs)} logs")
        return results
    
    def _run_heuristics(self, events: List[Any]) -> Dict[str, Any]:
        """
        Erweiterte Heuristik-Analyse mit Trace-basierten Erkennungen.
        
        Args:
            events: Liste der LogEvent-Objekte.
            
        Returns:
            Dict[str, Any]: Heuristic Summary mit allen Funden.
        """
        findings = {
            "hard_errors": [],
            "model_drift": [],
            "latency_spikes": [],
            "confidence_score": 0.0
        }
        
        # 1. Hard Errors: Filter Events mit status='error'
        for event in events:
            if event.status == 'error':
                findings["hard_errors"].append({
                    "timestamp": str(event.timestamp),
                    "skill": event.skill,
                    "error_code": (event.payload or {}).get("error_code") if event.payload else None
                })
        
        # 2. Model Drift: Prüfe Provider/Model Wechsel innerhalb eines Traces
        trace_groups: Dict[str, List[Any]] = {}
        for event in events:
            trace_id = event.trace_id
            if trace_id:
                if trace_id not in trace_groups:
                    trace_groups[trace_id] = []
                trace_groups[trace_id].append(event)
        
        for trace_id, trace_events in trace_groups.items():
            providers = set(e.provider for e in trace_events if e.provider)
            models = set(e.model for e in trace_events if e.model)
            
            if len(providers) > 1:
                findings["model_drift"].append({
                    "trace_id": trace_id,
                    "type": "provider_drift",
                    "providers": list(providers)
                })
            
            if len(models) > 1:
                findings["model_drift"].append({
                    "trace_id": trace_id,
                    "type": "model_drift",
                    "models": list(models)
                })
        
        # 3. Latency Spikes: Markiere Events > 5 Sekunden
        for event in events:
            if event.latency_ms and event.latency_ms > 5000:
                findings["latency_spikes"].append({
                    "timestamp": str(event.timestamp),
                    "skill": event.skill,
                    "latency_ms": event.latency_ms
                })
        
        # 4. Confidence Score basierend auf Log-Count und Fehler-Präsenz
        # Healthy logs (no errors) MUST produce high confidence
        if not events:
            findings["confidence_score"] = 0.0
        else:
            # Base confidence from log count (positive signal)
            log_count = len(events)
            base_confidence = min(log_count / 100.0, 1.0) * 0.9  # Max 0.9 for healthy logs
            
            # Penalty for errors (negative signal)
            error_penalty = 0.0
            error_penalty += len(findings["hard_errors"]) * 0.3  # Hard Errors: -0.3 each
            error_penalty += len(findings["model_drift"]) * 0.2   # Model Drift: -0.2 each
            error_penalty += len(findings["latency_spikes"]) * 0.1  # Latency Spikes: -0.1 each
            
            # Final confidence: base - penalty, bounded to [0.0, 1.0]
            findings["confidence_score"] = max(0.0, min(base_confidence - error_penalty, 1.0))
        
        logger.info(f"LogAnalyzer._run_heuristics: {len(findings['hard_errors'])} errors, {len(findings['model_drift'])} drift, {len(findings['latency_spikes'])} spikes, confidence={findings['confidence_score']:.2f}")
        return findings
    
    def generate_heuristic_summary(self, findings: Dict[str, Any]) -> str:
        """
        Generiert ein vor-strukturiertes Text-Paket ('Heuristic Summary') für das LLM.
        
        Args:
            findings: Ergebnisse aus _run_heuristics().
            
        Returns:
            str: Strukturierter Text für LLM-Input.
        """
        summary_parts = []
        
        summary_parts.append("=== HEURISTIC SUMMARY ===")
        summary_parts.append(f"Confidence Score: {findings['confidence_score']:.2f}")
        summary_parts.append("")
        
        # Hard Errors
        if findings["hard_errors"]:
            summary_parts.append(f"Hard Errors ({len(findings['hard_errors'])}):")
            for error in findings["hard_errors"][:5]:  # Max 5 Beispiele
                summary_parts.append(f"  - {error['timestamp']} | Skill: {error['skill']} | Error: {error['error_code']}")
            if len(findings["hard_errors"]) > 5:
                summary_parts.append(f"  ... and {len(findings['hard_errors']) - 5} more")
        else:
            summary_parts.append("Hard Errors: None")
        
        summary_parts.append("")
        
        # Model Drift
        if findings["model_drift"]:
            summary_parts.append(f"Model Drift ({len(findings['model_drift'])}):")
            for drift in findings["model_drift"][:5]:
                if drift["type"] == "provider_drift":
                    summary_parts.append(f"  - Trace {drift['trace_id']}: Provider drift: {drift['providers']}")
                else:
                    summary_parts.append(f"  - Trace {drift['trace_id']}: Model drift: {drift['models']}")
            if len(findings["model_drift"]) > 5:
                summary_parts.append(f"  ... and {len(findings['model_drift']) - 5} more")
        else:
            summary_parts.append("Model Drift: None")
        
        summary_parts.append("")
        
        # Latency Spikes
        if findings["latency_spikes"]:
            summary_parts.append(f"Latency Spikes ({len(findings['latency_spikes'])}):")
            for spike in findings["latency_spikes"][:5]:
                summary_parts.append(f"  - {spike['timestamp']} | Skill: {spike['skill']} | Latency: {spike['latency_ms']}ms")
            if len(findings["latency_spikes"]) > 5:
                summary_parts.append(f"  ... and {len(findings['latency_spikes']) - 5} more")
        else:
            summary_parts.append("Latency Spikes: None")
        
        summary_parts.append("")
        summary_parts.append("=== END HEURISTIC SUMMARY ===")
        
        return "\n".join(summary_parts)
    
    def get_confidence(self, count: int, total_logs: int) -> float:
        """
        Berechnet die Sicherheit der Diagnose (Legacy-Methode).
        
        Args:
            count: Anzahl der Matches für das Pattern.
            total_logs: Gesamtzahl der analysierten Logs.
            
        Returns:
            float: Confidence-Wert (0.0 - 1.0).
        """
        if total_logs == 0:
            return 0.0
        
        # Simple Heuristik: Relative Häufigkeit
        relative_freq = count / total_logs
        
        # Confidence basierend auf Häufigkeit
        if relative_freq > 0.5:
            return 0.9
        elif relative_freq > 0.3:
            return 0.7
        elif relative_freq > 0.1:
            return 0.5
        else:
            return 0.3


# ============================================================================
# LLM Integration (Lightweight)
# ============================================================================

class DebugReportGenerator:
    """
    LLM-basierte Übersetzung von Heuristik-Daten in DebugReport.
    Production-Safe: LLM wird nur am Ende aufgerufen, deterministische Daten fließen zuerst.
    Provider-Agnostic: Nutzt llm_gateway und das konfigurierte Speed-Tier Modell des Users.
    """
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Args:
            provider: Optional Provider-Override. Falls None, wird aus Config gelesen.
            model: Optional Modell-Override. Falls None, wird Speed-Tier Modell verwendet.
        """
        self.provider_override = provider
        self.model_override = model
        
    async def generate_report(self, heuristics: List[HeuristicResult]) -> DebugReport:
        """
        Generiert einen Debug-Report aus Heuristik-Daten mittels LLM.
        
        Args:
            heuristics: Liste der Heuristik-Ergebnisse.
            
        Returns:
            DebugReport: Strukturierter Debug-Report.
        """
        if not heuristics:
            # Fallback: Leerer Report
            return DebugReport(
                problem="No patterns detected",
                cause="No error patterns found in the logs",
                fix="Review logs manually for potential issues",
                confidence=0.0
            )
        
        # Provider und Modell bestimmen (Provider-Agnostic)
        if self.provider_override and self.model_override:
            provider = self.provider_override
            model = self.model_override
        else:
            provider, model = get_speed_tier_model()
        
        # Heuristik-Daten in Prompt formatieren
        heuristics_text = "\n".join([
            f"- Pattern: {h.pattern_type}, Count: {h.count}, Confidence: {h.confidence}, Sample: {h.sample_messages[0][:100] if h.sample_messages else 'N/A'}"
            for h in heuristics
        ])
        
        # Provider-agnostischer System-Prompt (V3 - Enhanced with Sections)
        prompt = f"""Analyze the following log pattern heuristics and generate a structured debug report.

Heuristics:
{heuristics_text}

CRITICAL: For CRITICAL signals (e.g., 500 errors, hard failures), DO NOT reduce information aggressively. Preserve all relevant details.

Generate a JSON response with the following structure:
{{
  "problem": "Precise problem name (minimum 150 chars for full description)",
  "root_cause": "Technical root cause analysis",
  "patterns": "Detected patterns in the logs",
  "anomalies": "Unusual behavior or outliers",
  "impact": "Business or system impact assessment",
  "recommended_fix": "Concrete action recommendation",
  "confidence": 0.0 to 1.0
}}

Required sections: ROOT CAUSE, PATTERNS, ANOMALIES, IMPACT, RECOMMENDED FIX.
Minimum total length: 150 characters.
For CRITICAL signals: Preserve full error details, stack traces, and context.
Focus on the most frequent pattern but ensure comprehensive coverage."""
        
        try:
            # LLM-Aufruf via llm_gateway (Provider-Agnostic)
            from backend.services.llm_gateway import llm_gateway
            from keyring import get_password
            
            # API Key holen
            api_key = get_password("Janus-Projekt", provider)
            if not api_key:
                raise ValueError(f"API key for provider '{provider}' not found")
            
            # Chat-Message für llm_gateway formatieren
            messages = [{"role": "user", "content": prompt}]
            
            # llm_gateway Aufruf (Provider-Agnostic)
            response = await llm_gateway.chat_completion(
                provider=provider,
                model=model,
                api_key=api_key,
                messages=messages,
                temperature=0.3  # Low temperature für deterministische Ergebnisse
            )
            
            report = self._parse_response(response)
            
            # Validierung: Wenn Confidence zu niedrig oder Felder leer, Fallback
            if self._is_incomplete_report(report):
                logger.warning(f"DebugReportGenerator: {model} result incomplete, using heuristics fallback")
                return self._generate_fallback_from_heuristics(heuristics)
            
            logger.info(f"DebugReportGenerator: Successfully generated report using {provider}/{model}")
            return report
            
        except Exception as e:
            logger.error(f"DebugReportGenerator: LLM call failed: {e}")
            # Ultimate Fallback: Aus Heuristik direkt generieren
            return self._generate_fallback_from_heuristics(heuristics)
    
    def _parse_response(self, response: dict) -> DebugReport:
        """Parst die LLM-Antwort in ein DebugReport Schema."""
        content = response.get("text", "")
        if not content:
            raise ValueError("Empty response from LLM")
        
        # JSON aus Response extrahieren
        import json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        report_data = json.loads(content)
        return DebugReport(**report_data)
    
    def _is_incomplete_report(self, report: DebugReport) -> bool:
        """Prüft, ob der Report vollständig ist (V3)."""
        # Confidence zu niedrig
        if report.confidence < 0.3:
            return True
        # Felder zu kurz oder leer (V3: Alle Felder prüfen)
        if len(report.problem) < 150:
            return True
        if len(report.root_cause) < 10 or len(report.patterns) < 10 or len(report.anomalies) < 10:
            return True
        if len(report.impact) < 10 or len(report.recommended_fix) < 10:
            return True
        return False
    
    def _generate_fallback_from_heuristics(self, heuristics: List[HeuristicResult]) -> DebugReport:
        """Generiert einen Fallback-Report direkt aus Heuristik-Daten (V3)."""
        top_pattern = heuristics[0]
        problem_desc = f"Detected {top_pattern.pattern_type} pattern in logs. This pattern occurred {top_pattern.count} times with confidence {top_pattern.confidence}. Sample messages: {', '.join(top_pattern.sample_messages[:3])}"
        return DebugReport(
            problem=problem_desc,
            root_cause=f"Logs contain {top_pattern.count} occurrences of {top_pattern.pattern_type}. Pattern detected: {top_pattern.pattern_match}",
            patterns=f"Primary pattern: {top_pattern.pattern_type} (count: {top_pattern.count}). Confidence: {top_pattern.confidence}",
            anomalies="No specific anomalies detected in heuristic analysis",
            impact=f"System performance or reliability may be affected by {top_pattern.pattern_type} pattern",
            recommended_fix=f"Investigate {top_pattern.pattern_type} in the application logs. Review sample messages: {', '.join(top_pattern.sample_messages[:2])}",
            confidence=top_pattern.confidence
        )


# ============================================================================
# Main Engine
# ============================================================================

class DebugEngine:
    """
    Debug Compression Engine (D11) — Production-Safe Design.
    Kombiniert deterministische Heuristik mit Lightweight LLM Integration.
    Provider-Agnostic: Nutzt das konfigurierte Speed-Tier Modell des Users (via llm_gateway).
    """
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Args:
            provider: Optional Provider-Override. Falls None, wird aus Config gelesen.
            model: Optional Modell-Override. Falls None, wird Speed-Tier Modell verwendet.
        """
        self.fetcher = LogFetcher()
        self.analyzer = LogAnalyzer()
        self.report_generator = DebugReportGenerator(provider=provider, model=model)
        
    async def analyze_logs(self, limit: int = 100) -> DebugReport:
        """
        Analysiert Logs und generiert einen Debug-Report.
        
        Args:
            limit: Maximale Anzahl der zu analysierenden Logs.
            
        Returns:
            DebugReport: Strukturierter Debug-Report.
        """
        # 1. Logs holen (RAM-Buffer -> Supabase Fallback)
        logs = await self.fetcher.fetch_logs(limit)
        
        if not logs:
            logger.warning("DebugEngine: No logs available for analysis")
            return DebugReport(
                problem="No logs available for analysis. The system could not retrieve any log entries from the RAM-Buffer, Supabase, or local log file. This indicates a potential issue with the logging pipeline or that no logs have been generated yet.",
                root_cause="No logs found in RAM-Buffer, Supabase, or local log file (janus_backend.log). The log fetching cascade returned empty results.",
                patterns="No patterns detected - no log data available",
                anomalies="No anomalies detected - no log data available",
                impact="Debug analysis cannot be performed without log data. System monitoring and troubleshooting capabilities are unavailable.",
                recommended_fix="Check logging pipeline configuration, ensure logs are being generated, verify Supabase connection, and check local log file permissions.",
                confidence=0.0
            )
        
        # 2. Deterministische Heuristik (Production-Safe)
        heuristics = self.analyzer.analyze(logs)
        
        if not heuristics:
            logger.info("DebugEngine: No patterns detected in logs")
            return DebugReport(
                problem="No patterns detected",
                cause="No error patterns found in the logs",
                fix="Review logs manually for potential issues",
                confidence=0.0
            )
        
        # 3. LLM Integration (Lightweight, nur am Ende)
        report = await self.report_generator.generate_report(heuristics)
        
        logger.info(f"DebugEngine: Generated report with confidence {report.confidence}")
        return report
