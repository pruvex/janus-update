import logging
import os
import traceback
import json
import asyncio
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
    # tool_start / tool_end / provider finish / done: omit for legacy UI (or use StreamEvent.to_sse() in a debug client)
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

    async def event_generator():
        try:
            async for ev in orchestrator.handle_chat_request_stream(request, background_tasks):
                if await starlette_request.is_disconnected():
                    logger.info("Client disconnected during stream (orchestrator)")
                    return
                line = _stream_event_to_frontend_sse_line(ev)
                if line:
                    yield line
            if await starlette_request.is_disconnected():
                logger.info("Client disconnected before done signal")
                return
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except asyncio.CancelledError:
            logger.info("Stream generator cancelled (client disconnected)")
            raise
        except Exception as e:
            logger.error("Error in chat stream: %s", e, exc_info=True)
            err = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
