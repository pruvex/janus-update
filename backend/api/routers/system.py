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
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.data.database import get_db

router = APIRouter()
logger = logging.getLogger("janus_backend")

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
                skill=result.skill,
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
                    .insert(insight_data.model_dump(mode='json'))
                    .execute()
                )
                stored_insights.append(insight_data.model_dump(mode='json'))
            except Exception as e:
                logger.error(f"[INSIGHT-ENGINE] Failed to store insight for {result.skill}/{result.model}: {e}")
        
        logger.info(f"[INSIGHT-ENGINE] Generated and stored {len(stored_insights)} insights")
        
        return {
            "message": f"Generated {len(stored_insights)} insights",
            "insights": stored_insights
        }
        
    except Exception as e:
        logger.error("[INSIGHT-ENGINE] Failed to generate insights: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


@router.get("/system/optimization-report")
async def get_optimization_report(skill: Optional[str] = None):
    """
    D13: Janus Optimization Engine — Rule-Based System Optimization Report.
    
    Loads latest actions from logs_actions table and formats as Markdown report
    for AI Studio integration.
    
    Args:
        skill: Optional skill name to filter the report on a specific tool
    """
    try:
        from backend.services.logging.supabase_client import get_supabase_client
        
        logger.info(f"[OPTIMIZATION-ENGINE] Generating optimization report (skill filter: {skill})")
        
        supabase = get_supabase_client()
        
        # Fetch latest actions (last 24 hours, sorted by priority)
        query = (
            supabase
            .table("logs_actions")
            .select("*")
            .gte("generated_at", (datetime.utcnow() - timedelta(hours=24)).isoformat())
        )
        
        # Apply skill filter if provided
        if skill:
            query = query.eq("skill", skill)
        
        response = query.order("priority", desc=True).execute()
        
        actions = response.data if response.data else []
        
        if not actions:
            if skill:
                return f"# Optimization Report\n\nNo actions generated for skill '{skill}' in the last 24 hours. System is operating normally."
            return "# Optimization Report\n\nNo actions generated in the last 24 hours. System is operating normally."
        
        # Format as Markdown
        report = format_optimization_report(actions)
        
        logger.info(f"[OPTIMIZATION-ENGINE] Generated report with {len(actions)} actions")
        return report
        
    except Exception as e:
        logger.error("[OPTIMIZATION-ENGINE] Failed to generate report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


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
