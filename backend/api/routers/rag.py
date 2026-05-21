import asyncio
import logging
import os
import shutil
from typing import Any, Dict

from backend.services import rag_manager
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.data.database import get_db, SessionLocal
from backend.data import crud, schemas
from backend.data.models import Document
from backend.services.ops_kill_switches import require_memory_rag_enabled, require_write_operations_enabled
from backend.utils.paths import get_user_docs_dir
from pydantic import BaseModel

router = APIRouter(prefix="/rag")
logger = logging.getLogger("janus_backend")

DOCUMENTS_DIR = get_user_docs_dir()
DEFAULT_MAX_DOCUMENT_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_DOCUMENT_UPLOAD_TYPES = {"application/pdf", "application/x-pdf"}


async def _write_limited_upload(file: UploadFile, file_path: str) -> int:
    max_bytes = int(os.getenv("JANUS_MAX_DOCUMENT_UPLOAD_BYTES", str(DEFAULT_MAX_DOCUMENT_UPLOAD_BYTES)))
    total = 0
    with open(file_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                logger.warning(
                    "[ABUSE-LIMIT] scope=upload-document filename_len=%s bytes_over_limit=true",
                    len(file.filename or ""),
                )
                raise HTTPException(
                    status_code=413,
                    detail="Die PDF-Datei ist zu groß. Bitte lade eine kleinere Datei hoch.",
                )
            buffer.write(chunk)
    return total

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


@router.get("/collections")
async def get_rag_collections():
    require_memory_rag_enabled()
    return {"collections": rag_manager.list_collections()}


@router.get("/indexing-status")
async def get_indexing_status():
    return RAG_INDEXING_STATUS


@router.post("/index-folder")
async def index_folder(request: RagFolderRequest):
    require_memory_rag_enabled()
    require_write_operations_enabled()
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


@router.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    require_memory_rag_enabled()
    require_write_operations_enabled()
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt.")
    if file.content_type and file.content_type not in ALLOWED_DOCUMENT_UPLOAD_TYPES:
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien sind erlaubt.")

    from backend.services.rag_manager import process_and_index_single_document

    clean_filename = (
        os.path.basename(file.filename).replace(" ", "_")
                     .replace("(", "")
                     .replace(")", "")
    )
    existing_doc = db.query(Document).filter(Document.filename == clean_filename).first()
    if existing_doc:
        logger.info(f"Duplikat-Check: Datei '{file.filename}' existiert bereits (ID: {existing_doc.id}).")
        return {
            "status": "already_exists",
            "message": f"Die Datei '{file.filename}' ist bereits in deiner Wissensdatenbank vorhanden.",
            "document_id": existing_doc.id
        }

    upload_dir = os.path.join(os.path.expanduser("~"), "Documents", "JanusPDFs", "Uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, clean_filename)

    try:
        await _write_limited_upload(file, file_path)
    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Fehler beim Speichern der Datei: {e}")
        raise HTTPException(status_code=500, detail="Datei konnte nicht gespeichert werden.")

    new_doc = crud.create_document(db, filename=clean_filename, file_path=file_path)

    asyncio.create_task(asyncio.to_thread(
        process_and_index_single_document,
        file_path,
        new_doc.id,
        file.filename,
        SessionLocal()
    ))

    return {
        "status": "uploaded",
        "document_id": new_doc.id,
        "message": f"Datei '{file.filename}' erfolgreich hochgeladen."
    }


@router.get("/documents", response_model=list[schemas.DocumentResponse])
async def get_documents(db: Session = Depends(get_db)):
    require_memory_rag_enabled()
    # 💎 FILE GUARD: Self-cleaning system - remove ghost files from SQL and ChromaDB
    all_docs = db.query(Document).order_by(Document.upload_date.desc()).all()
    existing_docs = []
    
    for doc in all_docs:
        if not os.path.exists(doc.file_path):
            # Ghost File detected - clean up SQL and ChromaDB
            logger.info(f"💎 FILE-GUARD: Ghost file detected (ID: {doc.id}, path: {doc.file_path}). Removing from SQL and ChromaDB.")
            
            # Remove from ChromaDB vectors
            from backend.services.rag_manager import delete_document_index
            try:
                delete_document_index(db, doc.id)
            except Exception as e:
                logger.error(f"💎 FILE-GUARD: Failed to delete vectors for doc ID {doc.id}: {e}")
            
            # Remove from SQL database
            db.delete(doc)
            logger.info(f"💎 FILE-GUARD: Deleted SQL entry for ghost file ID {doc.id}")
        else:
            existing_docs.append(doc)
    
    # Commit deletions if any ghost files were found
    if len(existing_docs) < len(all_docs):
        db.commit()
        logger.info(f"💎 FILE-GUARD: Cleaned up {len(all_docs) - len(existing_docs)} ghost files.")
    
    return existing_docs


@router.get("/files/{document_id}")
async def serve_document(document_id: int, db: Session = Depends(get_db)):
    require_memory_rag_enabled()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    return FileResponse(path=doc.file_path, filename=doc.filename, media_type='application/pdf')


@router.get("/search-ids")
async def search_doc_ids(query: str, db: Session = Depends(get_db)):
    require_memory_rag_enabled()
    from backend.services.rag_manager import _get_or_create_collection

    collection = _get_or_create_collection("janus_global_documents")
    results = collection.query(
        query_texts=[query],
        n_results=20,
        include=["metadatas", "documents"],
    )

    hits: dict[int, int] = {}
    query_lower = query.lower()

    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    for text_list, meta_list in zip(documents, metadatas):
        for text, meta in zip(text_list, meta_list):
            if not isinstance(text, str) or not isinstance(meta, dict):
                continue
            if query_lower not in text.lower():
                continue
            document_id = meta.get("document_id")
            if document_id is None:
                continue
            try:
                d_id = int(document_id)
            except (TypeError, ValueError):
                continue
            page = meta.get("page")
            try:
                page_num = int(page) if page is not None else 1
            except (TypeError, ValueError):
                page_num = 1
            if d_id not in hits or page_num < hits[d_id]:
                hits[d_id] = page_num

    logger.info(f"SEARCH-LOG: Suche nach '{query}' fand Treffer: {hits}")
    return [{"id": doc_id, "page": page} for doc_id, page in hits.items()]
