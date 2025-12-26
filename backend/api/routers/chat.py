import logging
import os
import traceback
from typing import List

from backend.data import crud, schemas
from backend.data.database import get_db
from backend.services.chat_orchestrator import ChatOrchestrator
from backend.services.context_manager import ContextManager
from backend.utils.config_loader import load_model_catalog
from backend.utils.paths import get_app_data_dir
from fastapi import APIRouter, Depends, HTTPException
from openai import RateLimitError
from sqlalchemy.orm import Session
from tenacity import RetryError

router = APIRouter()
logger = logging.getLogger("janus_backend")


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


@router.post("/chat")
async def chat(
    request: schemas.ChatRequest, orchestrator: ChatOrchestrator = Depends(get_orchestrator)
):
    try:
        return await orchestrator.handle_chat_request(request)
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
