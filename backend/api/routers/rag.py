import asyncio
import logging
from typing import Any, Dict

from backend.services import rag_manager
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("janus_backend")

# State-Management (aus main.py extrahiert)
RAG_INDEXING_STATUS: Dict[str, Any] = {
    "in_progress": False,
    "total_files": 0,
    "processed_files": 0,
    "current_file": "",
    "message": "Keine Indexierung aktiv.",
}


class RagFolderRequest(BaseModel):
    path: str
    collection_name: str


@router.get("/rag/collections")
async def get_rag_collections():
    return {"collections": rag_manager.list_collections()}


@router.get("/rag/indexing-status")
async def get_indexing_status():
    return RAG_INDEXING_STATUS


@router.post("/rag/index-folder")
async def index_folder(request: RagFolderRequest):
    if RAG_INDEXING_STATUS["in_progress"]:
        raise HTTPException(status_code=409, detail="Eine Indexierung läuft bereits.")

    try:
        RAG_INDEXING_STATUS.update(
            {
                "in_progress": True,
                "total_files": 0,
                "processed_files": 0,
                "message": "Indexierung wird gestartet...",
            }
        )
        asyncio.create_task(
            asyncio.to_thread(
                rag_manager.process_and_index_folder,
                request.path,
                RAG_INDEXING_STATUS,
                request.collection_name,
            )
        )
        return {"message": "Indexierung gestartet."}
    except Exception as e:
        RAG_INDEXING_STATUS["in_progress"] = False
        logger.error(f"Fehler beim Start der Ordner-Indexierung: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Start der Indexierung.")
