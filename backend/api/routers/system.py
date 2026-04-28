import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import keyring
from backend.data import crud
from backend.services.telemetry_service import submit_feedback_async
from backend.utils.config_loader import initialize_file_from_template, load_model_catalog
from backend.utils.paths import get_app_data_dir, resource_path
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.data.database import get_db

router = APIRouter()
logger = logging.getLogger("janus_backend")


class RoutingCalibrationRequest(BaseModel):
    """D20: Routing Calibration Matrix Run Request"""
    skill_ids: List[str] = Field(default_factory=list, description="List of skill IDs to test")
    models: List[str] = Field(default=["gpt-5.4-mini"], description="List of models to test (e.g., gpt-5.4-mini, gpt-5.4, gemini-3-flash, gemini-3-pro)")
    runs_per_model: int = Field(default=1, ge=1, le=10, description="Number of runs per model")
    real_run: bool = Field(default=False, description="If True, makes actual API calls")

# --- Config Helpers (lokal in diesem Modul genutzt) ---
DATA_DIR = get_app_data_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
TEMPLATE_CONFIG_FILE = resource_path("backend/config/config.json")


def load_config():
    initialize_file_from_template(TEMPLATE_CONFIG_FILE, CONFIG_FILE)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# --- Models ---
class ApiKey(BaseModel):
    provider: str
    api_key: str


class ModelSelection(BaseModel):
    provider: str
    models: list[str]


class WorkspaceAdd(BaseModel):
    path: str


class WorkspaceRemove(BaseModel):
    path: str


class WorkspaceUpdate(BaseModel):
    workspaces: list[str]


class BudgetUpdate(BaseModel):
    budget: float


class FeedbackRequest(BaseModel):
    """Schema for beta feedback submission."""
    type: str  # bug, feature, feedback, crash
    description: str
    include_logs: bool = False


# --- Endpoints ---


@router.get("/keys")
async def get_api_keys():
    providers = ["openai", "gemini", "anthropic", "cohere"]
    retrieved_keys = {}
    for p in providers:
        if keyring.get_password("Janus-Projekt", p):
            retrieved_keys[p] = "********"
    return {"api_keys": retrieved_keys}


@router.post("/keys")
async def add_api_key(key: ApiKey):
    try:
        keyring.set_password("Janus-Projekt", key.provider.lower(), key.api_key)
        return {"message": "API Key saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save API key.")


@router.get("/costs/summary-by-model")
async def get_costs_summary_by_model(db: Session = Depends(get_db)):
    today = datetime.now()
    summary = crud.get_monthly_cost_summary_by_model(db, today.year, today.month)
    return summary


@router.get("/costs/dashboard")
async def get_costs_dashboard(db: Session = Depends(get_db)):
    today = datetime.now()
    cost = crud.get_costs_for_month(db, today.year, today.month)  # Updated to use crud with db parameter
    config = load_config()
    budget = config.get("monthly_budget", 10.00)
    return {"current_month_cost": cost, "monthly_budget": budget}


@router.post("/budget")
async def save_budget(data: BudgetUpdate):
    config = load_config()
    config["monthly_budget"] = data.budget
    save_config(config)
    return {"message": "Budget saved", "monthly_budget": data.budget}


@router.get("/orchestrator/kpis")
async def get_orchestrator_kpis_dashboard(db: Session = Depends(get_db)):
    today = datetime.now()
    return crud.get_orchestrator_kpi_dashboard(db, today.year, today.month)


@router.get("/models/catalog")
async def get_model_catalog():
    return list(load_model_catalog().values())


@router.get("/models/selection/{provider}")
async def get_model_selection(provider: str):
    config = load_config()
    return {"selected_models": config.get("model_selection", {}).get(provider, [])}


@router.post("/models/selection")
async def save_model_selection(selection: ModelSelection):
    config = load_config()
    if "model_selection" not in config:
        config["model_selection"] = {}
    config["model_selection"][selection.provider] = selection.models
    save_config(config)
    return {"message": "Model selection saved successfully"}


@router.get("/workspaces")
async def get_workspaces():
    config = load_config()
    return {"workspaces": config.get("filesystem_workspaces", [])}


@router.post("/workspaces/add")
async def add_workspace(addition: WorkspaceAdd):
    config = load_config()
    if "filesystem_workspaces" not in config:
        config["filesystem_workspaces"] = []
    if addition.path not in config["filesystem_workspaces"]:
        config["filesystem_workspaces"].append(addition.path)
        save_config(config)
        return {"message": "Workspace added successfully"}
    return {"message": "Workspace already exists"}


@router.post("/workspaces/remove")
async def remove_workspace(removal: WorkspaceRemove):
    config = load_config()
    if "filesystem_workspaces" in config and removal.path in config["filesystem_workspaces"]:
        config["filesystem_workspaces"].remove(removal.path)
        save_config(config)
        return {"message": "Workspace removed successfully"}
    raise HTTPException(status_code=404, detail="Workspace not found")


@router.post("/feedback")
async def submit_feedback_endpoint(request: FeedbackRequest):
    """Submit beta feedback/bug reports to Discord webhook.

    The submission happens asynchronously (fire-and-forget) to avoid
    blocking the API response. Success/failure is logged internally.
    """
    try:
        # Fire-and-forget submission (non-blocking)
        submit_feedback_async(
            feedback_type=request.type,
            description=request.description,
            include_logs=request.include_logs,
        )

        logger.info("[FEEDBACK-API] Feedback submission queued: type=%s, logs=%s",
                    request.type, request.include_logs)

        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "type": request.type,
        }
    except Exception as e:
        logger.error("[FEEDBACK-API] Failed to queue feedback: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {e}")


# P7: RAG V2 Health Check Endpoint


@router.get("/rag-status")
async def get_rag_status():
    """
    P7: Health check endpoint for RAG systems.

    Returns status of both Chroma instances (legacy V1 and V2),
    number of indexed files in V2, and FTS5 status.
    """
    try:
        from backend.services.rag.api_adapter import get_v2_status
        from backend.utils.paths import get_app_data_dir
        import os

        # Legacy ChromaDB (V1) status
        legacy_chroma_path = os.path.join(get_app_data_dir(), "rag_chroma_db")
        legacy_chroma_exists = os.path.exists(legacy_chroma_path)

        # V2 status
        v2_status = get_v2_status()

        return {
            "legacy": {
                "chroma_path": legacy_chroma_path,
                "chroma_exists": legacy_chroma_exists,
                "status": "available" if legacy_chroma_exists else "unavailable",
            },
            "v2": v2_status,
        }
    except Exception as e:
        logger.error("[RAG-STATUS] Failed to get RAG status: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get RAG status: {e}")


# D11: Debug Compression Engine Endpoint


@router.get("/debug-summary")
async def get_debug_summary():
    """
    D11: Debug Compression Engine — Returns compressed debug diagnosis as Markdown.
    
    Analyzes recent logs using the LogAnalyzer (heuristics + LLM summary)
    and returns a clean Markdown summary for AI Studio debugging.
    
    Returns:
        str: Markdown-formatted debug summary with:
            - Heuristic findings (hard errors, model drift, latency spikes)
            - AI-generated diagnosis (if available)
            - Confidence score
    """
    try:
        import asyncio
        from backend.services.logging.debug_engine import DebugEngine, get_speed_tier_model
        from backend.data.schemas_logging import LogEventCreate
        from datetime import datetime
        
        # Empty-State-Check: Prüfe zuerst, ob überhaupt Logs vorhanden sind
        # Dies verhindert unnötige DB-Abfragen bei leerem RAM-Buffer
        from backend.services.logging.debug_engine import LogFetcher
        temp_fetcher = LogFetcher()
        
        # Schneller Check: RAM-Buffer leer?
        if len(temp_fetcher.ram_buffer) == 0:
            return "# Debug Summary\n\nKeine relevanten Logs für eine Analyse vorhanden."
        
        # Get provider and model for LLM
        provider, model = get_speed_tier_model()
        logger.info(f"[DEBUG-SUMMARY] Using {provider}/{model} for LLM summary")
        
        # Initialize Debug Engine
        engine = DebugEngine(provider=provider, model=model)
        
        # Timeout-Guard: Fetch logs mit 5 Sekunden Timeout
        try:
            logs = await asyncio.wait_for(
                engine.fetcher.fetch_logs(limit=100),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("[DEBUG-SUMMARY] Timeout bei Log-Fetch")
            return "# Debug Summary\n\nTimeout bei Log-Analyse (5s exceeded)."
        
        if not logs:
            return "# Debug Summary\n\nKeine relevanten Logs für eine Analyse vorhanden."
        
        # Convert LogEntry to LogEvent for _run_heuristics
        events = []
        for log in logs:
            event = LogEventCreate(
                timestamp=log.timestamp,
                level=log.level,
                message=log.message,
                event_type="log"
            )
            events.append(event)
        
        # Timeout-Guard: Heuristik mit 5 Sekunden Timeout (non-blocking via run_in_executor)
        try:
            findings = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    engine.analyzer._run_heuristics,
                    events
                ),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning("[DEBUG-SUMMARY] Timeout bei Heuristik-Analyse")
            return "# Debug Summary\n\nTimeout bei Heuristik-Analyse (5s exceeded)."
        
        # Generate heuristic summary
        heuristic_summary = engine.analyzer.generate_heuristic_summary(findings)
        
        # Build Markdown response
        markdown_parts = []
        markdown_parts.append("# 🐛 Debug Summary")
        markdown_parts.append(f"\n**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        markdown_parts.append(f"**Logs Analyzed:** {len(logs)}")
        markdown_parts.append(f"**Confidence Score:** {findings['confidence_score']:.2f}")
        markdown_parts.append("")
        
        # Heuristic Findings
        markdown_parts.append("## 🔍 Heuristic Findings")
        markdown_parts.append("")
        markdown_parts.append("```")
        markdown_parts.append(heuristic_summary)
        markdown_parts.append("```")
        markdown_parts.append("")
        
        # AI Diagnosis (if available - optional, can be added later)
        # For now, we return just the heuristic summary
        
        # Add copy-friendly summary
        markdown_parts.append("## 📋 Quick Summary")
        markdown_parts.append("")
        if findings['hard_errors']:
            markdown_parts.append(f"- **Hard Errors:** {len(findings['hard_errors'])}")
        if findings['model_drift']:
            markdown_parts.append(f"- **Model Drift:** {len(findings['model_drift'])}")
        if findings['latency_spikes']:
            markdown_parts.append(f"- **Latency Spikes:** {len(findings['latency_spikes'])}")
        if not any([findings['hard_errors'], findings['model_drift'], findings['latency_spikes']]):
            markdown_parts.append("- No critical issues detected")
        
        markdown_parts.append("")
        markdown_parts.append("---")
        markdown_parts.append("")
        markdown_parts.append("*Generated by D11 Debug Compression Engine*")
        
        return "\n".join(markdown_parts)
        
    except Exception as e:
        logger.error("[DEBUG-SUMMARY] Failed to generate debug summary: %s", e, exc_info=True)
        return f"# Debug Summary\n\nFehler bei der Log-Analyse: {str(e)}"


# D11: Debug-Log Skill Endpoint (Final Production Wrapper)


class DebugLogRequest(BaseModel):
    """Request schema for /api/skills/debug-log endpoint."""
    trace_id: Optional[str] = None
    mode: str = "fast"  # "fast" or "full"


@router.post("/skills/debug-log")
async def debug_log_skill(request: DebugLogRequest):
    """
    D11: Debug-Log Skill — Final Production Wrapper for AI-Studio.
    
    Accepts trace_id and mode parameters, runs D11 analysis, and returns
    formatted debug report with standard sections for AI-Studio integration.
    
    CRITICAL: All blocking I/O operations run in executor to prevent server freeze.
    Hard timeout of 3.0s on entire operation to prevent deadlocks.
    
    Args:
        request: DebugLogRequest with optional trace_id and mode (fast|full)
    
    Returns:
        str: Formatted markdown report with sections:
            - SUMMARY
            - ROOT CAUSE
            - FINDINGS
            - CONFIDENCE
            - RECOMMENDED ACTION
    """
    try:
        import asyncio
        from backend.services.logging.debug_engine import DebugEngine, get_speed_tier_model, LogFetcher
        from backend.services.logging.debug_formatter import format_debug_report
        from backend.data.schemas_logging import LogEventCreate
        from datetime import datetime
        from fastapi import HTTPException
        
        # Get provider and model for LLM (if needed)
        provider, model = get_speed_tier_model()
        logger.info(f"[DEBUG-LOG-SKILL] Using {provider}/{model}, mode={request.mode}, trace_id={request.trace_id}")
        
        # Initialize Debug Engine
        engine = DebugEngine(provider=provider, model=model)
        
        # Timeout-Guard: Fetch logs mit 3.0 Sekunden Hard Timeout
        # engine.fetcher.fetch_logs is already async - call directly with await
        try:
            logs = await asyncio.wait_for(
                engine.fetcher.fetch_logs(limit=100 if request.mode == "fast" else 500),
                timeout=3.0
            )
        except asyncio.TimeoutError:
            logger.warning("[DEBUG-LOG-SKILL] CRITICAL TIMEOUT: Log-Fetch exceeded 3.0s")
            raise HTTPException(status_code=504, detail="Debug analysis timeout: Log fetch exceeded 3.0 seconds")
        
        if not logs:
            return "# Debug Report\n\nKeine relevanten Logs für eine Analyse vorhanden."
        
        # Convert LogEntry to objects with attributes expected by _run_heuristics
        # _run_heuristics expects: status, skill, latency_ms, trace_id
        events = []
        for log in logs:
            # Create simple object with required attributes
            event = type('Event', (), {
                'timestamp': log.timestamp,
                'status': log.metadata.get('status') if log.metadata else None,
                'skill': log.metadata.get('skill') if log.metadata else None,
                'latency_ms': log.metadata.get('latency_ms') if log.metadata else None,
                'trace_id': log.metadata.get('trace_id') if log.metadata else None,
                'payload': log.metadata.get('payload') if log.metadata else None
            })()
            events.append(event)
        
        # Filter by trace_id if provided (non-blocking, in-memory)
        if request.trace_id:
            events = [e for e in events if hasattr(e, 'trace_id') and e.trace_id == request.trace_id]
            if not events:
                return f"# Debug Report\n\nKeine Logs für trace_id '{request.trace_id}' gefunden."
        
        # Timeout-Guard: Heuristik mit 3.0 Sekunden Hard Timeout (already in executor)
        try:
            findings = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    engine.analyzer._run_heuristics,
                    events
                ),
                timeout=3.0
            )
        except asyncio.TimeoutError:
            logger.warning("[DEBUG-LOG-SKILL] CRITICAL TIMEOUT: Heuristik exceeded 3.0s")
            raise HTTPException(status_code=504, detail="Debug analysis timeout: Heuristic analysis exceeded 3.0 seconds")
        
        # Build summary data for formatter (non-blocking, in-memory)
        summary_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "logs_analyzed": len(events),
            "confidence_score": findings['confidence_score'],
            "hard_errors": findings['hard_errors'],
            "model_drift": findings['model_drift'],
            "latency_spikes": findings['latency_spikes']
        }
        
        # Calculate suggest_d13 flag: True if hard_errors > 2 or latency_spikes > 1 or model_drift == True
        suggest_d13 = (
            len(findings['hard_errors']) > 2 or
            len(findings['latency_spikes']) > 1 or
            len(findings['model_drift']) > 0
        )
        
        # Format using debug_formatter (non-blocking, in-memory)
        formatted_report = format_debug_report(summary_data)
        
        # Return JSON response with d11_debug_report spec
        json_response = {
            "d11_debug_report": {
                "generated_at": summary_data["generated_at"],
                "logs_analyzed": summary_data["logs_analyzed"],
                "confidence_score": summary_data["confidence_score"],
                "hard_errors": summary_data["hard_errors"],
                "model_drift": summary_data["model_drift"],
                "latency_spikes": summary_data["latency_spikes"],
                "suggest_d13": suggest_d13,
                "markdown_report": formatted_report
            }
        }
        
        logger.info(f"[DEBUG-LOG-SKILL] Generated report for {len(events)} logs, confidence={findings['confidence_score']:.2f}, suggest_d13={suggest_d13}")
        return json_response
        
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        logger.error("[DEBUG-LOG-SKILL] Failed to generate debug report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug analysis failed: {str(e)}")


class InsightRequest(BaseModel):
    """Request model for insights endpoint."""
    hours: int = Field(default=1, description="Time window in hours (default: 1)")


@router.post("/system/insights")
async def generate_insights(request: InsightRequest):
    """
    D12: Janus Insight Engine — Globale Log-Aggregation für System-Health Monitoring.
    
    Aggregiert Logs aus Supabase nach Skill und Model,
    berechnet Metriken (calls, error_rate, avg_latency),
    detektiert Patterns und speichert Ergebnisse in logs_insights Tabelle.
    """
    try:
        from backend.services.logging.insight_engine import InsightEngine
        from backend.services.logging.supabase_client import get_supabase_client
        from backend.data.schemas_logging import InsightCreate
        
        logger.info(f"[INSIGHT-ENGINE] Generating insights for last {request.hours} hour(s)")
        
        engine = InsightEngine(hours=request.hours)
        results = engine.analyze()
        
        if not results:
            return {"message": "No logs found for the specified time window", "insights": []}
        
        # Store insights in Supabase
        supabase = get_supabase_client()
        stored_insights = []
        
        for result in results:
            insight_data = InsightCreate(
                skill_id=result.skill_id,
                model=result.model,
                calls=result.calls,
                error_rate=result.error_rate,
                avg_latency_ms=result.avg_latency_ms,
                patterns=result.patterns,
                confidence=result.confidence,
                generated_at=result.generated_at,
                time_window_hours=request.hours
            )
            
            try:
                response = (
                    supabase
                    .table("logs_insights")
                    .insert(insight_data.model_dump(mode='json', by_alias=True))
                ).execute()
                stored_insights.append(insight_data.model_dump(mode='json', by_alias=True))
            except Exception as e:
                logger.error(f"[INSIGHT-ENGINE] Failed to store insight for {result.skill_id}/{result.model}: {e}")
        
        logger.info(f"[INSIGHT-ENGINE] Generated and stored {len(stored_insights)} insights")
        
        return {
            "message": f"Generated {len(stored_insights)} insights",
            "insights": stored_insights
        }
        
    except Exception as e:
        logger.error("[INSIGHT-ENGINE] Failed to generate insights: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@router.get("/system/optimization-report")
async def get_optimization_report(skill_id: Optional[str] = None):
    """
    D13: Janus Optimization Engine — Rule-Based System Optimization Report.
    
    Loads latest actions from logs_actions table and formats as Markdown report
    for AI Studio integration.
    
    Args:
        skill: Optional skill name to filter the report on a specific tool
    """
    try:
        from backend.services.logging.supabase_client import get_supabase_client
        
        logger.info(f"[OPTIMIZATION-ENGINE] Generating optimization report (skill_id filter: {skill_id})")
        
        supabase = get_supabase_client()
        
        # Fetch latest actions (last 24 hours, sorted by priority)
        query = (
            supabase
            .table("logs_actions")
            .select("*")
            .gte("generated_at", (datetime.utcnow() - timedelta(hours=24)).isoformat())
        )
        
        # Apply skill filter if provided
        if skill_id:
            query = query.eq("skill", skill_id)
        
        response = query.order("priority", desc=True).execute()
        
        actions = response.data if response.data else []
        
        if not actions:
            if skill_id:
                return f"# Optimization Report\n\nNo actions generated for skill_id '{skill_id}' in the last 24 hours. System is operating normally."
            return "# Optimization Report\n\nNo actions generated in the last 24 hours. System is operating normally."
        
        # Format as Markdown
        report = format_optimization_report(actions)
        
        logger.info(f"[OPTIMIZATION-ENGINE] Generated report with {len(actions)} actions")
        return report
        
    except Exception as e:
        logger.error("[OPTIMIZATION-ENGINE] Failed to generate report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/system/learning-report")
async def get_learning_report(days: int = 14, format: str = "json"):
    """
    D14: Weekly Learning Engine — System Performance Trend Analysis.
    
    Analyzes historical insights to identify trends and generate
    system improvement recommendations.
    
    Args:
        days: Number of days to analyze (default: 14 for 2-week comparison)
        format: Response format - "json" or "markdown" (default: "json")
    """
    try:
        from backend.services.logging.learning_engine import LearningEngine
        
        logger.info(f"[LEARNING-ENGINE] Generating learning report for last {days} days, format={format}")
        
        engine = LearningEngine()
        report = await engine.generate_weekly_report(days=days)
        
        # Return markdown if requested
        if format == "markdown":
            markdown_report = engine.format_report_to_markdown(report)
            logger.info(f"[LEARNING-ENGINE] Generated markdown report with {len(report.get('improvements', []))} improvements")
            return markdown_report
        
        logger.info(f"[LEARNING-ENGINE] Generated JSON report with {len(report.get('improvements', []))} improvements")
        return report
        
    except Exception as e:
        logger.error("[LEARNING-ENGINE] Failed to generate learning report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Learning report generation failed: {str(e)}")


@router.post("/system/learning-trigger")
async def trigger_learning_report(days: int = 14, persist: bool = True):
    """
    D14: Manual trigger for weekly learning report generation.
    
    Allows immediate execution of the learning job without waiting
    for the 7-day cycle. Useful for testing and manual audits.
    
    Args:
        days: Number of days to analyze (default: 14)
        persist: Whether to persist the report to database (default: True)
    """
    try:
        from backend.services.logging.learning_engine import LearningEngine
        
        logger.info(f"[LEARNING-ENGINE] Manual trigger: generating learning report for last {days} days, persist={persist}")
        
        engine = LearningEngine()
        report = await engine.generate_weekly_report(days=days, persist=persist)
        
        logger.info(f"[LEARNING-ENGINE] Manual trigger completed with {len(report.get('improvements', []))} improvements")
        
        return {
            "status": "success",
            "message": "Learning report generated successfully",
            "report": report
        }
        
    except Exception as e:
        logger.error("[LEARNING-ENGINE] Manual trigger failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Learning report trigger failed: {str(e)}")


@router.get("/system/integrity-check")
async def get_integrity_check():
    """
    D15: Integrity Engine — Diamond Contract Registry & Stack Validation.
    
    Fetches recent D12, D13, D14 outputs from Supabase and validates
    them against CONTRACT_SPECS. Returns IntegrityReport with score,
    status, and violations.
    """
    try:
        from backend.services.logging.integrity_engine import IntegrityEngine
        
        logger.info("[INTEGRITY-ENGINE] Running integrity check via API")
        
        engine = IntegrityEngine()
        report = await engine.run_live_check()
        
        logger.info(f"[INTEGRITY-ENGINE] Check complete: {report.status} (score={report.integrity_score})")
        return report.model_dump(mode='json')
        
    except Exception as e:
        logger.error("[INTEGRITY-ENGINE] Failed to run integrity check: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Integrity check failed: {str(e)}")


@router.post("/system/run-batch-tests")
async def run_batch_tests(
    request: RoutingCalibrationRequest,
    background_tasks: BackgroundTasks
):
    """
    D20: Routing Calibration Matrix Run — Test multiple models against skills.
    
    Accepts POST with JSON body containing:
    - skill_ids: list of skill IDs to test
    - models: list of models to test (e.g., gpt-5.4-mini, gpt-5.4, gemini-3-flash, gemini-3-pro)
    - runs_per_model: number of runs per model
    - real_run: if True, makes actual API calls
    
    Returns immediately with status. Tests run in background with rate limiting.
    
    Args:
        request: RoutingCalibrationRequest with skill_ids, models, runs_per_model, real_run
        background_tasks: FastAPI BackgroundTasks for async execution
    
    Returns:
        {"status": "started", "total_tests": <count>, "config": {...}}
    """
    try:
        import asyncio
        import uuid
        from backend.services.testing.test_runner import TestRunner, discover_skills, BudgetGuard, CalibrationWinner
        from backend.services.tool_executor import ToolExecutor
        import keyring
        
        # Use provided skill_ids, or discover all if empty
        skill_ids_to_test = request.skill_ids if request.skill_ids else discover_skills()
        models_to_test = request.models if request.models else ["gpt-5.4-mini"]
        runs_per_model = request.runs_per_model
        real_run = request.real_run
        
        total_tests = len(skill_ids_to_test) * len(models_to_test) * runs_per_model
        logger.info(f"[D20-MATRIX-RUN] Starting matrix run: {len(skill_ids_to_test)} skills × {len(models_to_test)} models × {runs_per_model} runs = {total_tests} total tests")
        
        # Background task function
        async def run_matrix_background():
            try:
                logger.info(f"[D20-MATRIX-RUN] Starting background matrix run (real_run={real_run})")
                
                # Initialize BudgetGuard for D21
                budget_guard = BudgetGuard(max_cost_eur=5.0, max_api_errors=20) if real_run else None
                test_runner = TestRunner(budget_guard=budget_guard)
                
                # Calibration data collection: skill_id -> model -> [results]
                calibration_data = {}
                
                # Tool call function based on real_run flag
                if real_run:
                    logger.warning("[D20-MATRIX-RUN] REAL RUN ACTIVE - API calls will be made")
                    
                    from backend.data.database import SessionLocal
                    db = SessionLocal()
                    
                    api_key = keyring.get_password("janus", "api_key")
                    
                    tool_executor = ToolExecutor(
                        db=db,
                        api_key=api_key,
                        provider="openai",
                        model="gpt-4o-mini"
                    )
                    
                    # Helper function to derive provider from model name
                    def get_provider_from_model(model_name: str) -> str:
                        """Derive provider from model name prefix."""
                        if model_name.startswith("gpt-"):
                            return "openai"
                        elif model_name.startswith("gemini-"):
                            return "gemini"
                        elif model_name.startswith("claude-"):
                            return "anthropic"
                        else:
                            # Default fallback
                            return "openai"
                    
                    async def real_tool_call_fn(provider: str, model: str, **kwargs):
                        print(f"[REAL-TOOL-CALL-FN] CALLED! provider={provider}, model={model}, kwargs keys={list(kwargs.keys())}")
                        from backend.services import llm_gateway
                        
                        # Derive correct provider from model name (override escalation engine if needed)
                        derived_provider = get_provider_from_model(model)
                        print(f"[D21-PROVIDER-FIX] Derived provider from model '{model}': {derived_provider} (was: {provider})")
                        provider = derived_provider
                        
                        tool_calls = kwargs.get("tool_calls", [])
                        print(f"[REAL-TOOL-CALL-FN] tool_calls={len(tool_calls)} items")
                        if not tool_calls:
                            print(f"[REAL-TOOL-CALL-FN] ERROR: No tool_calls provided")
                            return {"status": "error", "message": "No tool_calls provided"}
                        
                        first_call = tool_calls[0]
                        tool_name = first_call.get("name", "")
                        tool_args = first_call.get("arguments", {})
                        input_value = list(tool_args.values())[0] if tool_args else ""
                        
                        print(f"[LLM-AUDIT] Starting real call for {tool_name}...")
                        
                        import os
                        from pathlib import Path
                        
                        api_key = keyring.get_password("Janus-Projekt", provider)
                        key_source = "keyring"
                        
                        if not api_key:
                            api_key = os.environ.get(f"{provider.upper()}_API_KEY")
                            key_source = "environment"
                        
                        if not api_key:
                            env_file = Path(__file__).parent.parent / ".env"
                            if env_file.exists():
                                from dotenv import load_dotenv
                                load_dotenv(env_file)
                                api_key = os.environ.get(f"{provider.upper()}_API_KEY")
                                key_source = "backend/.env"
                        
                        print(f"🔑 AUTH-CHECK: Key found for {provider}: {'Yes' if api_key else 'No'} (source: {key_source if api_key else 'none'})")
                        
                        if not api_key:
                            print(f"⚠️ CRITICAL: No API Key found for {provider}")
                            return {"status": "error", "message": f"No API key found for provider {provider}"}
                        
                        messages = [{"role": "user", "content": str(input_value)}]
                        
                        from backend.services.tool_manager import tool_manager
                        skill_tools = tool_manager.get_tool_definitions(allowed_skill_ids=[tool_name])
                        
                        # Guard: Abort if tool_definitions is empty
                        if not skill_tools:
                            logger.error(f"[D21-GUARD] No tool_definitions found for skill_id: {tool_name}. Aborting LLM call to prevent loop.")
                            return {"status": "error", "message": f"No tool_definitions found for skill_id: {tool_name}. Check tool_manager registry."}
                        
                        llm_response = await llm_gateway.call_llm(
                            provider=provider,
                            model_id=model,
                            api_key=api_key,
                            messages=messages,
                            tools=skill_tools if skill_tools else None,
                            tool_choice="required" if provider == "openai" else None
                        )
                        
                        llm_tool_calls = llm_response.get("tool_calls", [])
                        if llm_tool_calls:
                            results = await tool_executor.execute_tool_calls(llm_tool_calls)
                            
                            if isinstance(results, list) and len(results) > 0:
                                result = results[0]
                            else:
                                result = results
                            
                            import json
                            if isinstance(result, str):
                                try:
                                    result = json.loads(result)
                                except json.JSONDecodeError:
                                    result = {"status": "error", "message": "Unparseable string", "data": result}
                            
                            if isinstance(result, dict):
                                if "status" not in result:
                                    result = {
                                        "status": "ok",
                                        "data": result,
                                        "message": "Tool executed successfully",
                                        "error": None
                                    }
                            
                            print(f"[ORCH-BRIDGE-DEBUG] LLM called tool, returning: {result}")
                            return result
                        else:
                            return {"status": "error", "message": "LLM did not call the tool", "llm_response": llm_response}
                else:
                    db = None
                    logger.info("[D20-MATRIX-RUN] MOCK MODE - no API calls")
                    async def mock_tool_call_fn(provider: str, model: str, **kwargs):
                        return {"status": "mock_success", "provider": provider, "model": model}
                
                tool_call_fn = real_tool_call_fn if real_run else mock_tool_call_fn
                
                try:
                    # Matrix run: loop over models and runs
                    for model_idx, model in enumerate(models_to_test):
                        logger.info(f"[D20-MATRIX-RUN] Starting model {model_idx + 1}/{len(models_to_test)}: {model}")
                        
                        # Initialize calibration data for this model
                        calibration_data[model] = []
                        
                        for run_idx in range(runs_per_model):
                            logger.info(f"[D20-MATRIX-RUN] Run {run_idx + 1}/{runs_per_model} for model {model}")
                            
                            # Check budget guard before each run
                            if budget_guard and budget_guard.get_status()["budget_exceeded"]:
                                logger.warning(f"[D21-BUDGETGUARD] Budget exceeded, stopping matrix run. Status: {budget_guard.get_status()}")
                                break
                            
                            # Generate unique trace_id for this run
                            trace_id = str(uuid.uuid4())
                            
                            # Capture the current loop model to override escalation engine's model selection
                            _forced_model = model
                            
                            batch_summary = await test_runner.run_batch_tests(
                                tool_call_fn=lambda provider, model=None, _fn=tool_call_fn, _m=_forced_model, **kwargs: _fn(provider=provider, model=_m, **kwargs),
                                skill_ids=skill_ids_to_test,
                                trace_id=trace_id
                            )
                            
                            # Collect calibration data for this run
                            calibration_data[model].append(batch_summary)
                            
                            logger.info(f"[D20-MATRIX-RUN] Run {run_idx + 1}/{runs_per_model} complete for model {model}: {batch_summary.get('skills_tested', 0)} skills tested")
                            
                            # Rate limiting between runs
                            if run_idx < runs_per_model - 1:
                                await asyncio.sleep(0.5)
                        
                        # Rate limiting between models
                        if model_idx < len(models_to_test) - 1:
                            await asyncio.sleep(0.5)
                    
                    logger.info(f"[D20-MATRIX-RUN] Matrix run complete: {total_tests} total tests executed")
                    
                    # Generate model_routing.json if real_run and calibration data available
                    if calibration_data:
                        logger.info("[D21-CALIBRATION] Analyzing calibration results and generating model_routing.json")
                        
                        # Reorganize calibration data for CalibrationWinner: skill_id -> model -> [results]
                        skill_calibration_data = {}
                        for model, run_results in calibration_data.items():
                            for batch_summary in run_results:
                                for skill_result in batch_summary.get("results", []):
                                    skill_id = skill_result.get("skill_id")
                                    if skill_id:
                                        if skill_id not in skill_calibration_data:
                                            skill_calibration_data[skill_id] = {}
                                        if model not in skill_calibration_data[skill_id]:
                                            skill_calibration_data[skill_id][model] = []
                                        skill_calibration_data[skill_id][model].append(skill_result)
                        
                        # Analyze calibration results
                        winner = CalibrationWinner()
                        optimal_assignments = winner.build_diamond_routing(skill_calibration_data)
                        
                        # Generate model_routing.json
                        routing_config = winner.generate_model_routing_json(optimal_assignments)
                        
                        # Write to file
                        from pathlib import Path
                        routing_file = Path(__file__).parent.parent.parent / "config/model_routing.json"
                        import json
                        with open(routing_file, 'w', encoding='utf-8') as f:
                            json.dump(routing_config, f, indent=2)
                        
                        logger.info(f"[D21-CALIBRATION] model_routing.json generated at {routing_file}")
                        logger.info(f"[D21-CALIBRATION] Budget guard final status: {budget_guard.get_status() if budget_guard else 'N/A'}")
                finally:
                    if db is not None:
                        db.close()
                        logger.info("[D20-MATRIX-RUN] DB session closed after matrix run")
                
            except Exception as e:
                logger.error(f"[D20-MATRIX-RUN] Matrix run failed: {e}", exc_info=True)
        
        # Add background task
        background_tasks.add_task(run_matrix_background)
        
        # Return immediately
        return {
            "status": "started",
            "total_tests": total_tests,
            "config": {
                "skills": len(skill_ids_to_test),
                "models": len(models_to_test),
                "runs_per_model": runs_per_model,
                "real_run": real_run
            },
            "message": "Matrix run started in background. Check logs for progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[D20-MATRIX-RUN] Failed to start matrix run: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Matrix run start failed: {str(e)}")


@router.post("/system/self-heal")
async def trigger_self_heal(
    request: RoutingCalibrationRequest,
    background_tasks: BackgroundTasks
):
    """
    D22: Self-Healing Loop — Autonomous model routing optimization.
    
    Orchestrates complete self-healing flow from batch-start to shielded-update.
    Includes 6-hour cooldown guard, Diamond Safety Layer, and autonomous routing updates.
    
    Accepts POST with JSON body containing:
    - skill_ids: list of skill IDs to test (optional, None = all skills)
    - models: list of models to test (optional, None = all models in silo)
    - runs_per_model: number of runs per model (default 10)
    - real_run: if True, makes actual API calls (default False)
    
    Returns immediately with status. Self-heal cycle runs in background.
    
    Args:
        request: RoutingCalibrationRequest with skill_ids, models, runs_per_model, real_run
        background_tasks: FastAPI BackgroundTasks for async execution
    
    Returns:
        {"status": "started", "cooldown_check": {...}, "message": "..."}
    """
    try:
        from backend.services.testing.test_runner import CalibrationWinner
        
        logger.info("[D22-SELF-HEAL] Self-heal cycle requested")
        
        # Background task function
        async def run_self_heal_background():
            try:
                logger.info("[D22-SELF-HEAL] Starting background self-heal cycle")
                
                # Initialize CalibrationWinner with self-healing capabilities
                winner = CalibrationWinner()
                
                # Run self-healing cycle
                cycle_result = await winner.run_self_healing_cycle(
                    real_run=request.real_run,
                    skill_ids=request.skill_ids if request.skill_ids else None,
                    models_to_test=request.models if request.models else None,
                    runs_per_model=request.runs_per_model if request.runs_per_model else 10,
                    cooldown_hours=6
                )
                
                logger.info(f"[D22-SELF-HEAL] Self-heal cycle completed: {cycle_result['status']}")
                
            except Exception as e:
                logger.error(f"[D22-SELF-HEAL] Self-heal cycle failed: {e}", exc_info=True)
        
        # Add background task
        background_tasks.add_task(run_self_heal_background)
        
        # Return immediately with cooldown check result
        winner = CalibrationWinner()
        is_allowed, cooldown_reason = winner._check_cooldown()
        
        return {
            "status": "started",
            "cooldown_check": {"allowed": is_allowed, "reason": cooldown_reason},
            "message": "Self-heal cycle started in background. Check logs for progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[D22-SELF-HEAL] Failed to start self-heal cycle: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Self-heal cycle start failed: {str(e)}")


@router.get("/system/run-skill-tests/{skill_id}")
async def run_skill_tests(skill_id: str, skill_type: str = "tool"):
    """
    D16: Skill Stability System — Run automated tests for a skill.
    
    Generates test blueprints (if not exists), executes tests with escalation
    chain (Primary -> Fallback -> Escalation), and returns health summary.
    
    Args:
        skill_id: Unique skill identifier (e.g., "system.weather")
        skill_type: Type of skill (default: "tool", options: "tool", "agent", "renderer")
    
    Returns:
        Health summary with test results and metrics
    """
    try:
        from backend.services.testing.test_generator import TestGenerator
        from backend.services.testing.test_runner import TestRunner
        from backend.services.routing.escalation import EscalationEngine
        from backend.services.routing.model_router import ModelRouter
        from backend.services.tool_executor import ToolExecutor
        from backend.data.database import get_db
        import keyring
        
        logger.info(f"[D16-SKILL-TEST] Starting test run for skill_id={skill_id}, skill_type={skill_type}")
        
        # Initialize components
        test_generator = TestGenerator()
        test_runner = TestRunner()
        escalation_engine = EscalationEngine()
        model_router = ModelRouter()
        
        # Generate testset if not exists
        try:
            blueprint = test_generator.generate_testset(skill_id, skill_type)
            logger.info(f"[D16-SKILL-TEST] Generated test blueprint for {skill_id}")
        except Exception as e:
            logger.error(f"[D16-SKILL-TEST] Failed to generate test blueprint: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate test blueprint: {str(e)}")
        
        # Create mock tool_call_fn for testing
        # In production, this would use actual ToolExecutor
        async def mock_tool_call_fn(provider: str, model: str, **kwargs) -> Dict[str, Any]:
            """
            Mock tool execution for testing purposes.
            
            In production, this would instantiate ToolExecutor and execute
            the actual skill/tool call with the given provider and model.
            """
            logger.info(f"[D16-SKILL-TEST] Mock execution: provider={provider}, model={model}, kwargs={kwargs}")
            
            # Simulate successful execution
            return {
                "status": "success",
                "provider": provider,
                "model": model,
                "result": f"Mock result for {skill_id}",
                "latency_ms": 100
            }
        
        # Run testset with mock function
        # Note: session_id is None for manual API triggers
        test_summary = await test_runner.run_testset(
            skill_id=skill_id,
            tool_call_fn=mock_tool_call_fn,
            session_id=None
        )
        
        logger.info(f"[D16-SKILL-TEST] Test run complete: {test_summary['passed_count']}/{test_summary['test_count']} passed")
        
        return {
            "skill_id": skill_id,
            "skill_type": skill_type,
            "test_summary": test_summary,
            "health_summary": test_summary.get("health_summary", {}),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[D16-SKILL-TEST] Failed to run skill tests: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Skill test execution failed: {str(e)}")


@router.get("/system/health-matrix")
async def get_health_matrix(hours: int = 1):
    """
    D17: Skill Health Matrix — Get health metrics for all skills.
    
    Aggregates skill_test events from D10 telemetry and calculates:
    - pass_rate = passed / total_runs
    - escalation_rate = escalation_attempts / total_runs
    
    Args:
        hours: Time window in hours for analysis (default: 1)
    
    Returns:
        Health Matrix dict with skill-level metrics
    """
    try:
        from backend.services.logging.insight_engine import InsightEngine
        
        logger.info(f"[D17-HEALTH-MATRIX] Generating health matrix for last {hours} hour(s)")
        
        insight_engine = InsightEngine(hours=hours)
        health_matrix = insight_engine.generate_health_matrix()
        
        logger.info(f"[D17-HEALTH-MATRIX] Generated matrix for {health_matrix.get('skills_analyzed', 0)} skills")
        
        return health_matrix
        
    except Exception as e:
        logger.error("[D17-HEALTH-MATRIX] Failed to generate health matrix: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Health matrix generation failed: {str(e)}")


@router.get("/system/decision-report")
async def get_decision_report(hours: int = 1, classification_hours: int = 24):
    """
    D17: Decision Report — D13 decision recommendations with problem classification.
    
    Combines Health Matrix (pass_rate, escalation_rate) with Problem Classification
    (MODEL_WEAKNESS / PROMPT_ISSUE / VALIDATION_FAIL / TIMEOUT) and confidence scores.
    
    Args:
        hours: Time window for health matrix aggregation (default: 1)
        classification_hours: Time window for problem classification from D10 history (default: 24)
    
    Returns:
        Markdown report + health_matrix + problem_profiles
    """
    try:
        from backend.services.logging.insight_engine import InsightEngine
        from backend.services.logging.optimization_engine import OptimizationEngine, ProblemClassifier
        
        logger.info(
            f"[D17-DECISION-REPORT] Generating report — matrix_hours={hours}, classify_hours={classification_hours}"
        )
        
        # 1. Health Matrix
        insight_engine = InsightEngine(hours=hours)
        health_matrix = insight_engine.generate_health_matrix()
        
        # 2. Problem Classification from D10 history
        classifier = ProblemClassifier(hours=classification_hours)
        problem_profiles_raw = classifier.classify_skills()
        
        # Serialize profiles to plain dicts for JSON response
        problem_profiles_serialized = {
            skill_id: profile.model_dump(mode="json")
            for skill_id, profile in problem_profiles_raw.items()
        }
        
        # 3. Generate enriched decision report
        optimization_engine = OptimizationEngine(hours=hours)
        decision_report = optimization_engine.generate_decision_report(
            health_matrix,
            problem_profiles=problem_profiles_raw
        )
        
        logger.info(
            f"[D17-DECISION-REPORT] Report generated — "
            f"{health_matrix.get('skills_analyzed', 0)} skills in matrix, "
            f"{len(problem_profiles_raw)} classified"
        )
        
        return {
            "report": decision_report,
            "health_matrix": health_matrix,
            "problem_profiles": problem_profiles_serialized,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("[D17-DECISION-REPORT] Failed to generate decision report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Decision report generation failed: {str(e)}")


def format_optimization_report(actions: List[Dict[str, Any]]) -> str:
    """
    Format actions as Markdown report for AI Studio.
    
    Args:
        actions: List of action records
    
    Returns:
        Formatted Markdown report
    """
    report_lines = [
        "# 🚀 Optimization Report",
        "",
        f"**Generated:** {datetime.utcnow().isoformat()}",
        f"**Actions:** {len(actions)}",
        ""
    ]
    
    # Group by priority
    priority_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    grouped = {}
    for action in actions:
        priority = action.get("priority", "LOW")
        if priority not in grouped:
            grouped[priority] = []
        grouped[priority].append(action)
    
    # Output by priority
    for priority in priority_order:
        if priority not in grouped:
            continue
        
        report_lines.append(f"## {priority} PRIORITY")
        report_lines.append("")
        
        for action in grouped[priority]:
            report_lines.append(f"### {action.get('skill', 'unknown')} / {action.get('model', 'unknown')}")
            report_lines.append("")
            report_lines.append(f"**Action:** {action.get('action_type', 'UNKNOWN')}")
            report_lines.append(f"**Reason:** {action.get('reason', 'N/A')}")
            report_lines.append(f"**Current Value:** {action.get('current_value', 0):.2f}")
            report_lines.append(f"**Threshold:** {action.get('threshold', 0):.2f}")
            report_lines.append("")
            report_lines.append("**Recommendation:**")
            report_lines.append(f"> {action.get('recommendation', 'N/A')}")
            report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Generated by D13 Janus Optimization Engine*")
    
    return "\n".join(report_lines)
