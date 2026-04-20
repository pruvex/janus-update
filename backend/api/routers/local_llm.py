from typing import Any, Dict, Optional

import logging
import threading
import time
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi import Request
from pydantic import BaseModel, Field, model_validator

from backend.services.ollama_manager import ollama_manager

router = APIRouter(prefix="/local-llm", tags=["Local LLM"])
logger = logging.getLogger("janus_backend")
_PULL_STATUS_CACHE_TTL_SECONDS = 2.0
_pull_status_cache_lock = threading.Lock()
_pull_status_cache: Dict[str, Dict[str, Any]] = {}
_last_nodes_poll: Optional[float] = None


class PullModelRequest(BaseModel):
    model_id: str = Field(..., description="Ollama model identifier, e.g. llama3:8b")
    node_id: Optional[str] = Field(None, description="Optional target node_id for the download")


class LocalLlmConfigRequest(BaseModel):
    ollama_base_url: str = Field(..., description="Base URL of Ollama server, e.g. http://localhost:11434")


class OllamaNodeCreateRequest(BaseModel):
    name: str = Field(..., description="Display name for node")
    # New canonical field
    base_url: Optional[str] = Field(
        None,
        description="Base URL for node, e.g. http://192.168.178.20:11434",
    )
    # Backward-compatibility for existing frontend payloads
    url: Optional[str] = Field(
        None,
        description="Legacy alias for base_url.",
    )
    api_key: Optional[str] = Field(None, description="Optional API key (currently unused by Ollama manager).")
    is_active: bool = Field(True, description="Whether node should be active by default (currently ignored on create).")

    @model_validator(mode="after")
    def validate_url_fields(self) -> "OllamaNodeCreateRequest":
        if not str(self.base_url or self.url or "").strip():
            raise ValueError("Either 'base_url' or 'url' is required")
        return self

    @property
    def normalized_url(self) -> str:
        return str(self.base_url or self.url or "").strip()


@router.get("/config")
async def get_local_llm_config() -> Dict[str, str]:
    return ollama_manager.get_config()


@router.post("/config")
async def update_local_llm_config(request: LocalLlmConfigRequest) -> Dict[str, str]:
    try:
        return ollama_manager.update_config(request.ollama_base_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/nodes")
async def get_ollama_nodes() -> Dict[str, Any]:
    global _last_nodes_poll
    now = time.monotonic()
    interval = None
    if _last_nodes_poll is not None:
        interval = now - _last_nodes_poll
    _last_nodes_poll = now
    nodes = ollama_manager.get_nodes()
    node_count = len(nodes.get("nodes", []))
    active_node = nodes.get("active_node_id")
    interval_display = f"{round(interval, 2)}s" if interval is not None else "first poll"
    logger.info(
        "Polling /local-llm/nodes interval=%s node_count=%s active_node=%s",
        interval_display,
        node_count,
        active_node,
        extra={
            "interval_s": round(interval, 2) if interval is not None else None,
            "node_count": node_count,
            "active_node": active_node,
        },
    )
    return nodes


@router.post("/nodes")
async def create_ollama_node(request: OllamaNodeCreateRequest) -> Dict[str, Any]:
    try:
        return ollama_manager.add_node(name=request.name, url=request.normalized_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/nodes/activate/{node_id}")
async def activate_ollama_node(node_id: str) -> Dict[str, Any]:
    try:
        return ollama_manager.activate_node(node_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/nodes/{node_id}")
async def delete_ollama_node(node_id: str) -> Dict[str, Any]:
    try:
        return ollama_manager.delete_node(node_id)
    except ValueError as exc:
        detail = str(exc)
        status_code = 422 if "cannot be deleted" in detail else 404
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/check")
async def check_ollama() -> Dict[str, bool]:
    return ollama_manager.check_ollama()


@router.get("/recommendations")
async def get_recommendations() -> Dict[str, Any]:
    return ollama_manager.analyze_system()


@router.get("/models")
async def get_local_models() -> Dict[str, Any]:
    models = ollama_manager.get_unified_model_list()
    return {"provider": "ollama", "models": models}


@router.get("/updates")
async def get_update_snapshot() -> Dict[str, Any]:
    return ollama_manager.get_update_snapshot()


@router.post("/updates/refresh")
async def refresh_update_snapshot(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    def _run_refresh() -> None:
        try:
            ollama_manager.check_for_updates()
            ollama_manager.check_ollama_binary_update()
        except Exception as exc:
            logger.warning("Ollama update refresh failed: %s", exc)

    background_tasks.add_task(_run_refresh)
    return {"status": "started", "message": "Update-Check laeuft im Hintergrund."}


@router.delete("/models/{model_id}")
async def delete_local_model(model_id: str) -> Dict[str, Any]:
    try:
        return ollama_manager.delete_model(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/pull-status/{model_id}")
async def get_pull_status(model_id: str, request: Request) -> Dict[str, Any]:
    client_host = str(request.client.host if request.client else "unknown")
    cache_key = f"{client_host}:{model_id}"
    now = time.monotonic()

    with _pull_status_cache_lock:
        cached = _pull_status_cache.get(cache_key)
        if cached and (now - float(cached.get("ts") or 0.0)) < _PULL_STATUS_CACHE_TTL_SECONDS:
            payload = cached.get("payload")
            if isinstance(payload, dict):
                return dict(payload)

    try:
        payload = ollama_manager.get_pull_status(model_id)
        with _pull_status_cache_lock:
            _pull_status_cache[cache_key] = {
                "ts": now,
                "payload": dict(payload),
            }
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _run_pull_in_background(model_id: str, node_id: Optional[str]) -> None:
    try:
        ollama_manager.pull_model(model_id, node_id=node_id)
    except Exception as exc:
        logger.warning("Background Ollama pull failed for %s@%s: %s", model_id, node_id, exc)


@router.post("/pull", status_code=202)
async def pull_model(request: PullModelRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    status = ollama_manager.check_ollama()
    if not status.get("running"):
        raise HTTPException(
            status_code=400,
            detail="Ollama service is not running. Start Ollama first and retry.",
        )

    try:
        payload = ollama_manager.queue_pull_model(request.model_id, node_id=request.node_id)
        if payload.get("status") == "started":
            background_tasks.add_task(_run_pull_in_background, request.model_id, request.node_id)
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
