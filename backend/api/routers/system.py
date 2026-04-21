import json
import logging
import os
from datetime import datetime

import keyring
from backend.data import crud
from backend.services.telemetry_service import submit_feedback_async
from backend.utils.config_loader import initialize_file_from_template, load_model_catalog
from backend.utils.paths import get_app_data_dir, resource_path
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
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
