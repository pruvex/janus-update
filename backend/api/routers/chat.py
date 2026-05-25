import logging
import os
import traceback
import json
import asyncio
import time
import uuid
from typing import List, Optional

from backend.data import crud, schemas
from backend.data.database import get_db
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.context_manager import ContextManager
from backend.services.orchestrator.schemas import ExecutionResponse
from backend.services.orchestrator.stream_protocol import StreamEvent
from backend.utils.config_loader import load_model_catalog
from backend.utils.paths import get_app_data_dir
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from openai import RateLimitError
from sqlalchemy.orm import Session
from tenacity import RetryError

router = APIRouter()
logger = logging.getLogger("janus_backend")


def _emit_stream_audit(event: str, payload: dict) -> None:
    """Structured stream audit marker for parallel-debug analysis."""
    try:
        blob = {"event": event, **payload}
        logger.info("STREAM_AUDIT %s", json.dumps(blob, ensure_ascii=False, default=str))
    except Exception:
        logger.warning("STREAM_AUDIT_EMIT_FAILED event=%s", event, exc_info=True)


def _emit_token_audit(payload: dict) -> None:
    """Structured token/cost marker bound to one stream request."""
    try:
        logger.info("TOKEN_AUDIT %s", json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        logger.warning("TOKEN_AUDIT_EMIT_FAILED", exc_info=True)


def _stream_event_to_frontend_sse_line(ev: StreamEvent) -> Optional[str]:
    """
    Map internal StreamEvent → legacy frontend SSE JSON (chat.js / ChatView):
    type text (+ partial), metadata (usage/cost), error, done is sent by the router after the generator ends.
    """
    t = ev.type
    if t == "text_delta":
        if ev.content is None:
            return None
        payload = {"type": "text", "content": str(ev.content), "partial": True}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    if t == "usage":
        blob = ev.content if isinstance(ev.content, dict) else {}
        usage = blob.get("usage") or {}
        cost = blob.get("cost") or {}
        payload = {"type": "metadata", "usage": usage, "cost": cost}
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    if t == "metadata":
        blob = ev.content
        if isinstance(blob, str):
            try:
                blob = json.loads(blob)
            except Exception:
                pass

        # Deep Unpack: Falls das Metadata-Event ein Tool-Result-Wrapper ist
        if isinstance(blob, dict) and blob.get("role") == "tool" and "content" in blob:
            try:
                inner_content = blob["content"]
                if isinstance(inner_content, str):
                    inner_blob = json.loads(inner_content)
                    if isinstance(inner_blob, dict) and "data" in inner_blob:
                        blob = inner_blob["data"]  # Entpackt die ToolResultV1 Daten
            except Exception:
                pass
        # Fallback: Falls data bereits direkt als Dictionary vorliegt
        elif isinstance(blob, dict) and "data" in blob and isinstance(blob["data"], dict):
            blob = blob["data"]

        # 💎 MCL: Ensure data field is merged to top level for video cards
        final_payload = {"type": "metadata"}
        if isinstance(blob, dict):
            if "data" in blob and isinstance(blob["data"], dict):
                final_payload.update(blob["data"])  # videos, mode etc. auf Top-Level!
            else:
                final_payload.update(blob)
        return f"data: {json.dumps(final_payload, ensure_ascii=False, default=str)}\n\n"
    if t == "stream_complete":
        text = ""
        if isinstance(ev.content, dict):
            text = str(ev.content.get("text") or "")
        if not text and isinstance(ev.metadata, dict):
            text = str(ev.metadata.get("text") or "")
        payload = {"type": "text", "content": text, "partial": False}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    if t == "modal_request":
        # Parity mit POST /api/chat: ``modal_request`` kommt erst nach finalize_response_async (URL-Erkennung).
        mr = ev.content if isinstance(ev.content, dict) else {}
        payload = {"type": "modal_request", "modal_request": mr}
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    if t == "error":
        msg = str(ev.content or "")
        if not msg and isinstance(ev.metadata, dict):
            msg = str(ev.metadata.get("message") or "stream error")
        payload = {"type": "error", "message": msg}
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    if t == "tool_result":
        # 💎 PATH-SENTINEL: Propagate permission_required (and future tool events) to UI
        blob = ev.content if isinstance(ev.content, dict) else {}
        result = blob.get("result") if isinstance(blob, dict) else None
        payload = {"type": "tool_result", "result": result}
        if isinstance(ev.metadata, dict):
            payload["name"] = ev.metadata.get("name")
            payload["tool_call_id"] = ev.metadata.get("tool_call_id")
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    if t == "status_update":
        # 💎 CU-4: Status-Update für UI-Feedback bei langen Anfragen
        blob = ev.content if isinstance(ev.content, dict) else {}
        payload = {"type": "status_update", "status": blob.get("status")}
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    if t == "tool_end":
        # BACKLOG-031: surface successful tool executions to the SSE stream so the
        # Playwright runner (and any future UI tool indicator) can observe which
        # tool was triggered. We map tool_end -> tool_result with result=None so
        # the frontend's existing permission_required handler does not fire on
        # this telemetry frame (it explicitly requires result.status === 'permission_required').
        md = ev.metadata if isinstance(ev.metadata, dict) else {}
        name = md.get("name")
        if not name:
            return None
        payload = {
            "type": "tool_result",
            "result": None,
            "name": name,
            "tool_call_id": md.get("id") or md.get("tool_call_id"),
        }
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
    # tool_start / provider finish / done: omit for legacy UI (or use StreamEvent.to_sse() in a debug client)
    return None


def get_model_catalog_dep():
    return load_model_catalog()


def get_context_manager(model_catalog: dict = Depends(get_model_catalog_dep)):
    return ContextManager(model_catalog=model_catalog.values())


def get_orchestrator(
    db: Session = Depends(get_db),
    context_manager: ContextManager = Depends(get_context_manager),
    model_catalog: dict = Depends(get_model_catalog_dep),
) -> ChatOrchestrator:
    return ChatOrchestrator(
        db=db,
        context_manager=context_manager,
        model_catalog=model_catalog,
        config_file_path=os.path.join(get_app_data_dir(), "config.json"),
        template_config_file_path=os.path.join("backend", "config", "config.json"),
        personalities_file_path=os.path.join(get_app_data_dir(), "personalities.json"),
        template_personalities_file_path=os.path.join("backend", "config", "personalities.json"),
    )


@router.post("/chat", response_model=ExecutionResponse)
async def chat(
    request: schemas.ChatRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator)
):
    try:
        result = await orchestrator.handle_chat_request(request, background_tasks)
        # ExecutionResponse inkl. optionalem modal_request (Pydantic serialisiert verschachtelte Models).
        if isinstance(result, ExecutionResponse):
            return result
        return ExecutionResponse.model_validate(result)
    except RetryError as e:
        if isinstance(e.last_attempt.exception(), RateLimitError):
            logger.error(f"OpenAI quota exceeded. Aborting request. Error: {e}")
            raise HTTPException(status_code=429, detail="OpenAI quota exceeded.")
        tb_str = traceback.format_exc()
        logger.error(f"A retryable error occurred: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"A persistent error occurred: {e}")
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chats", response_model=schemas.ChatResponse)
async def create_chat(chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    # Hinweis: Die Zusammenfassungs-Logik (Summarizer) wurde hier vereinfacht,
    # um Zyklen zu vermeiden. Sie sollte idealerweise im Orchestrator oder Background-Task leben.
    return crud.create_chat(db, title=chat.title, project_id=chat.project_id)


@router.get("/chats", response_model=List[schemas.ChatResponse])
async def get_all_chats(
    db: Session = Depends(get_db), 
    include_archived: bool = False,
    project_id: int = None
):
    return crud.get_chats(db, include_archived=include_archived, project_id=project_id)


@router.get("/chats/{chat_id}", response_model=schemas.ChatResponse)
async def get_chat_details(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.get_chat_by_id(db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.get("/chats/{chat_id}/messages", response_model=List[schemas.MessageResponse])
async def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = crud.get_messages_by_chat_id(db, chat_id)
    for message in messages:
        if message.content is None:
            message.content = ""
    return messages


@router.put("/chats/{chat_id}/title")
async def update_chat_title(
    chat_id: int, title_update: schemas.ChatTitleUpdate, db: Session = Depends(get_db)
):
    chat = crud.update_chat_title(db, chat_id, title_update.title)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat title updated successfully"}


@router.put("/chats/{chat_id}/llm", response_model=schemas.ChatResponse)
async def update_chat_header_llm(
    chat_id: int,
    llm_update: schemas.ChatHeaderLlmUpdate,
    db: Session = Depends(get_db),
):
    payload = llm_update.model_dump()
    provider = (
        payload["provider"]
        if "provider" in llm_update.model_fields_set
        else crud.CHAT_UPDATE_UNSET
    )
    model = (
        payload["model"]
        if "model" in llm_update.model_fields_set
        else crud.CHAT_UPDATE_UNSET
    )
    chat = crud.update_chat_header_llm(db, chat_id, provider, model)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.put("/chats/{chat_id}/archive")
async def toggle_chat_archive(chat_id: int, db: Session = Depends(get_db)):
    chat = crud.toggle_archive_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat archive status toggled", "is_archived": chat.is_archived}


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    if not crud.delete_chat(db, chat_id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}


@router.post("/chat/stream")
async def chat_stream(
    starlette_request: Request,
    request: schemas.ChatRequest,
    background_tasks: BackgroundTasks,
    orchestrator: ChatOrchestrator = Depends(get_orchestrator),
):
    """SSE-Stream: echte Token-/Tool-Events aus ``handle_chat_request_stream`` (legacy JSON für das Frontend).

    Persistenz/Fact-Extraktion laufen in ``finalize_response_async`` erst nach Ende des Orchestrator-Generators
    (nach dem letzten ``yield``). ``BackgroundTasks`` wird an den Orchestrator durchgereicht wie bei ``/chat``;
    die Finalize-Pipeline nutzt aktuell keine FastAPI-BackgroundTasks (Fakten: ``asyncio.create_task``).
    """

    request_id = str(uuid.uuid4())
    started_at = time.time()
    chat_id = request.chat_id
    provider = str(request.provider or "").strip().lower() or None
    model = str(request.model or "").strip() or None
    window_id = (
        starlette_request.headers.get("x-janus-window-id")
        or starlette_request.headers.get("x-window-id")
        or None
    )
    client_host = starlette_request.client.host if starlette_request.client else None
    stream_status = "ok"
    stream_error = None
    usage_event_index = 0
    cumulative_input_tokens = 0
    cumulative_output_tokens = 0
    cumulative_total_tokens = 0
    cumulative_total_cost = 0.0

    _emit_stream_audit(
        "stream_start",
        {
            "request_id": request_id,
            "chat_id": chat_id,
            "window_id": window_id,
            "provider": provider,
            "model": model,
            "client_host": client_host,
            "started_at_epoch_ms": int(started_at * 1000),
        },
    )

    async def event_generator():
        nonlocal stream_status, stream_error, usage_event_index, cumulative_input_tokens
        nonlocal cumulative_output_tokens, cumulative_total_tokens, cumulative_total_cost
        try:
            async for ev in orchestrator.handle_chat_request_stream(request, background_tasks):
                if await starlette_request.is_disconnected():
                    stream_status = "client_disconnected"
                    logger.info("Client disconnected during stream (orchestrator)")
                    return
                if ev.type == "usage" and isinstance(ev.content, dict):
                    usage_event_index += 1
                    u = ev.content.get("usage") or {}
                    c = ev.content.get("cost") or {}
                    in_tok = int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
                    out_tok = int(u.get("output_tokens") or u.get("completion_tokens") or 0)
                    total_tok = int(u.get("total_tokens") or (in_tok + out_tok))
                    cached_tok = int(u.get("cached_tokens") or u.get("prompt_tokens_cached") or 0)
                    total_cost = float(c.get("total_cost") or 0.0)
                    cumulative_input_tokens += in_tok
                    cumulative_output_tokens += out_tok
                    cumulative_total_tokens += total_tok
                    cumulative_total_cost += total_cost
                    _emit_token_audit(
                        {
                            "request_id": request_id,
                            "chat_id": chat_id,
                            "window_id": window_id,
                            "provider": provider,
                            "model": model,
                            "usage_event_index": usage_event_index,
                            "input_tokens": in_tok,
                            "output_tokens": out_tok,
                            "total_tokens": total_tok,
                            "cached_tokens": cached_tok,
                            "total_cost_eur": total_cost,
                            "cum_input_tokens": cumulative_input_tokens,
                            "cum_output_tokens": cumulative_output_tokens,
                            "cum_total_tokens": cumulative_total_tokens,
                            "cum_total_cost_eur": cumulative_total_cost,
                        }
                    )
                line = _stream_event_to_frontend_sse_line(ev)
                if line:
                    yield line
            if await starlette_request.is_disconnected():
                stream_status = "client_disconnected"
                logger.info("Client disconnected before done signal")
                return
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except asyncio.CancelledError:
            stream_status = "cancelled"
            logger.info("Stream generator cancelled (client disconnected)")
            raise
        except Exception as e:
            stream_status = "error"
            stream_error = str(e)
            logger.error("Error in chat stream: %s", e, exc_info=True)
            err = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err)}\n\n"
        finally:
            ended_at = time.time()
            _emit_stream_audit(
                "stream_end",
                {
                    "request_id": request_id,
                    "chat_id": chat_id,
                    "window_id": window_id,
                    "provider": provider,
                    "model": model,
                    "status": stream_status,
                    "error": stream_error,
                    "ended_at_epoch_ms": int(ended_at * 1000),
                    "duration_ms": int((ended_at - started_at) * 1000),
                    "usage_events": usage_event_index,
                    "cum_input_tokens": cumulative_input_tokens,
                    "cum_output_tokens": cumulative_output_tokens,
                    "cum_total_tokens": cumulative_total_tokens,
                    "cum_total_cost_eur": round(cumulative_total_cost, 8),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
