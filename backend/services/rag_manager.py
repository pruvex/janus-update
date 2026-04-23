# backend/rag_manager.py

import logging
import os
import re
import time
from typing import List, Optional, Dict, Any

import chromadb
import ebooklib
from backend.utils.paths import get_app_data_dir
from bs4 import BeautifulSoup
from chromadb.utils import embedding_functions
from ebooklib import epub
from pypdf import PdfReader
from sqlalchemy.orm import Session

from backend.data.schemas_tools import ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1

logger = logging.getLogger("janus_backend")

CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- LAZY LOADING FÜR EMBEDDING-FUNKTION ---
_embedding_function = None

def get_embedding_function():
    """
    Lädt die SentenceTransformerEmbeddingFunction nur beim ersten Aufruf ("lazy").
    """
    global _embedding_function
    if _embedding_function is None:
        logger.info(f"LAZY LOAD (RAG): Lade Embedding-Modell '{EMBEDDING_MODEL}' jetzt...")
        start_time = time.time()
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        end_time = time.time()
        logger.info(f"LAZY LOAD (RAG): Embedding-Modell in {end_time - start_time:.2f} Sekunden geladen.")
    return _embedding_function
# --- ENDE LAZY LOADING ---

logger = logging.getLogger("janus_backend")



def _get_or_create_collection(collection_name: str):
    """Holt oder erstellt eine ChromaDB-Collection mit validem Namen."""
    sanitized_name = collection_name.lower()
    sanitized_name = re.sub(r'[^a-z0-9_-]', '', sanitized_name).strip('_-')
    if len(sanitized_name) < 3: 
        sanitized_name = f"col_{sanitized_name}"
    if len(sanitized_name) > 63: 
        sanitized_name = sanitized_name[:63]

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=sanitized_name,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def _split_text(text, chunk_size=700, chunk_overlap=150):
    if not text:
        return []
    length = len(text)
    chunks = []
    start = 0
    while start < length:
        preferred_end = min(start + chunk_size, length)
        chunk_end = preferred_end
        if preferred_end < length:
            newline_pos = text.rfind("\n", start + 1, preferred_end)
            if newline_pos > start:
                chunk_end = newline_pos
        if chunk_end <= start:
            chunk_end = preferred_end
        chunk_text = text[start:chunk_end].strip()
        if chunk_text:
            chunks.append(chunk_text)
        if chunk_end >= length:
            break
        next_start = chunk_end - chunk_overlap
        if next_start <= start:
            next_start = chunk_end
        start = next_start
    return chunks


def index_document(db_session, document_id: int):
    """Indiziert ein bereits gespeichertes Dokument synchron."""
    from backend.data.models import Document

    doc = db_session.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.warning(f"Document-ID {document_id} nicht gefunden. Indexierung übersprungen.")
        return

    process_and_index_single_document(doc.file_path, document_id, doc.filename, db_session)


def add_text_to_collection(text_content: str, source_identifier: str, collection_name: str):
    """
    Nimmt einen Textblock, zerlegt ihn in Chunks und fügt ihn einer Collection hinzu.

    Args:
        text_content (str): Der komplette Text, der indexiert werden soll.
        source_identifier (str): Eine eindeutige Kennung für die Quelle (z.B. URL oder Dateiname).
        collection_name (str): Der Name der ChromaDB Collection.
    """
    try:
        collection_name = collection_name.lower().replace(" ", "_").replace("-", "_")
        logger.info(f"Füge Text von '{source_identifier}' zur Sammlung '{collection_name}' hinzu.")
        collection = _get_or_create_collection(collection_name)
        chunks = _split_text(text_content)
        if not chunks:
            logger.warning(f"Kein Text zum Indexieren aus '{source_identifier}' gefunden.")
            return
        ids = [f"{collection_name}_{source_identifier}_chunk_{i}" for i in range(len(chunks))]
        collection.add(documents=chunks, ids=ids)
        logger.info(f"Text von '{source_identifier}' erfolgreich in '{collection_name}' indexiert ({len(chunks)} Chunks).")
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen von Text zur Sammlung '{collection_name}': {e}", exc_info=True)


def _extract_text_from_epub(file_path: str) -> str:
    try:
        book = epub.read_epub(file_path)
        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            soup.get_text(separator="\n", strip=True)
            chapters.append(soup.get_text(separator="\n", strip=True))
        return "\n\n".join(chapters)
    except Exception as e:
        logger.error(f"Fehler beim Extrahieren von EPUB {os.path.basename(file_path)}: {e}")
        return ""


def process_and_index_folder(folder_path: str, collection_name: str, status_dict: Optional[Dict[str, Any]] = None):
    """Verarbeitet einen Ordner mit Dokumenten und indiziert sie in der angegebenen Collection.
    
    Args:
        folder_path: Pfad zum zu verarbeitenden Ordner
        collection_name: Name der Ziel-Collection
        status_dict: Optionales Dict für Fortschrittsupdates (kompatibel mit bestehendem Code)
    """
    if status_dict is None: 
        status_dict = {}
    
    logger.info(f"Starte Indexierung für Ordner: '{folder_path}' in Sammlung: '{collection_name}'")
    if not os.path.isdir(folder_path):
        if status_dict: 
            status_dict.update({"in_progress": False, "message": "Fehler: Ordner nicht gefunden."})
        logger.error(f"Ordner nicht gefunden: {folder_path}")
        return

    try:
        collection = _get_or_create_collection(collection_name)
        supported_extensions = (".pdf", ".epub")
        supported_files = [f for f in os.listdir(folder_path) if f.lower().endswith(supported_extensions)]
        
        if status_dict: 
            status_dict["total_files"] = len(supported_files)

        for i, filename in enumerate(supported_files):
            if status_dict: 
                status_dict.update({
                    "processed_files": i, 
                    "current_file": filename, 
                    "message": f"Verarbeite Datei {i + 1}/{len(supported_files)}..."
                })
            logger.info(f"Verarbeite: {filename} ({i + 1}/{len(supported_files)})")

            full_text = ""
            full_path = os.path.join(folder_path, filename)
            try:
                if filename.lower().endswith(".pdf"):
                    reader = PdfReader(full_path)
                    full_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                elif filename.lower().endswith(".epub"):
                    full_text = _extract_text_from_epub(full_path)

                if full_text:
                    chunks = _split_text(full_text)
                    ids = [f"{collection_name}_{filename}_chunk_{j}" for j in range(len(chunks))]
                    if chunks: 
                        collection.add(documents=chunks, ids=ids)
                else:
                    logger.warning(f"Kein Text aus {filename} extrahiert. Datei wird übersprungen.")
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung von {filename}: {e}", exc_info=True)

        final_msg = f"Indexierung von {len(supported_files)} Dateien für Sammlung '{collection_name}' erfolgreich abgeschlossen."
        if status_dict: 
            status_dict.update({
                "in_progress": False, 
                "processed_files": len(supported_files), 
                "current_file": "", 
                "message": final_msg
            })
        logger.info(final_msg)
    except Exception as e:
        error_msg = f"Kritischer Fehler bei Indexierung: {e}"
        if status_dict: 
            status_dict.update({"in_progress": False, "message": error_msg})
        logger.error(error_msg, exc_info=True)


def query_knowledge_base(query_text: str, filename: Optional[str] = None, n_results: int = 15) -> ToolResultV1:
    """Durchsucht die hochgeladenen PDFs nach relevanten Textstellen."""
    started = time.perf_counter()
    tags = ["knowledge", "rag"]
    
    # PHYSICAL DUPLICATE DETECTION: Check for multiple files with the same name
    # This must happen before any retrieval to ensure the AI is warned about duplicates
    duplicate_warning = None
    if filename:
        try:
            from backend.services.filesystem_manager import find_files
            from pathlib import PurePath
            # Use stem for search (without extension) to catch aegypten.pdf, aegypten.PDF, etc.
            needle_stem = PurePath(filename).stem.lower()
            stem_pattern = f"{needle_stem}.*"
            fs_result = find_files(
                pattern=stem_pattern,
                max_results=100,
                search_all_drives=False
            )
            if fs_result and fs_result.data and fs_result.data.get("matches"):
                physical_matches = fs_result.data["matches"]
                # Filter by exact stem match to avoid false positives
                filtered_physical = [
                    p for p in physical_matches
                    if PurePath(p).stem.lower() == needle_stem
                ]
                if len(filtered_physical) > 1:
                    # Generate content previews for each duplicate
                    from backend.services.rag.index_store import IndexStore
                    from backend.utils.paths import get_app_data_dir
                    index_db = Path(get_app_data_dir()) / "knowledge_index_v2.db"
                    store = IndexStore(db_path=str(index_db))
                    
                    path_previews = {}
                    for path in sorted(filtered_physical):
                        try:
                            chunks = store.get_chunks_by_file(path, limit=2)
                            if chunks:
                                preview = chunks[0].get("text", "")[:200]
                                path_previews[path] = preview
                            else:
                                path_previews[path] = "[DATEI GEFUNDEN, ABER NOCH NICHT INDIZIERT]"
                        except Exception:
                            path_previews[path] = "[DATEI GEFUNDEN, ABER NOCH NICHT INDIZIERT]"
                    
                    store.close()
                    
                    # Build warning block with previews
                    paths_info = ""
                    for path in sorted(filtered_physical):
                        preview = path_previews.get(path, "[Keine Vorschau]")
                        paths_info += f"\n  - {path}\n    Vorschau: {preview}\n"
                    duplicate_warning = f"!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!\nDateiname: {filename}\nGefundene Pfade:{paths_info}"
                    logger.info(f"[DUPLICATE-DETECTION] Found {len(filtered_physical)} copies of '{filename}'")
        except Exception as exc:
            logger.warning(f"Physical duplicate detection failed for '{filename}': {exc}")
    
    try:
        collection = _get_or_create_collection("janus_global_documents")
        clean_query = query_text.replace(".pdf", "").replace(".PDF", "").strip()
        candidate_query = clean_query or query_text

        results = None
        if filename:
            clean_filename = filename.split("/")[-1].split("\\")[-1]
            clean_filename = clean_filename.replace(".pdf", "").replace(".PDF", "").strip()
            if clean_filename:
                search_filter = {"filename": {"$in": [filename, clean_filename]}}
                logger.info(f"RAG: Suche gezielt in Datei: {clean_filename}")
                results = collection.query(
                    query_texts=[candidate_query],
                    n_results=n_results,
                    where=search_filter,
                )

        # LOCKDOWN: When filename filter is active, NEVER fall back to global search
        # If the specific file search returns 0 results, return empty instead of searching globally
        if filename and (not results or not results.get("documents") or not results["documents"][0]):
            logger.warning(f"RAG: Datei '{clean_filename}' nicht gefunden oder keine Treffer. Kein Fallback auf globale Suche.")
            error_msg = f"Keine relevanten Informationen in Datei '{clean_filename}' gefunden."
            if duplicate_warning:
                error_msg = f"{duplicate_warning}\n\n{error_msg}"
            return tool_err_v1(
                "NOT_FOUND",
                error_msg,
                tags=tags,
                started_at=started,
            )

        # LOCKDOWN: If no filename specified, allow global search. If filename was specified and we reach here,
        # we already have results (the check above would have returned if filename search failed).
        if not filename and (not results or not results.get("documents") or not results["documents"][0]):
            logger.info("RAG: Kein Filter gesetzt. Starte globale Suche...")
            results = collection.query(
                query_texts=[candidate_query],
                n_results=n_results,
            )

        if not results or not results.get("documents") or not results["documents"][0]:
            return tool_err_v1(
                "NOT_FOUND",
                "Keine relevanten Informationen in der Wissensdatenbank gefunden.",
                tags=tags,
                started_at=started,
            )

        context_parts = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = documents[:5]
        metadatas = metadatas[: len(documents)]

        hits: List[Dict[str, Any]] = []
        for i, doc_text in enumerate(documents):
            meta = metadatas[i] if i < len(metadatas) else {}
            page_raw = meta.get("page") or meta.get("page_label") or "unbekannt"
            try:
                page_number = int(page_raw)
            except (TypeError, ValueError):
                page_number = page_raw
            fname = meta.get("filename") or filename or "Dokument"

            truncated_text = doc_text or ""
            if isinstance(truncated_text, str) and len(truncated_text) > 2500:
                truncated_text = truncated_text[:2500].rstrip()

            context_parts.append(f"[QUELLE: {fname}, SEITE: {page_number}]\nTEXT: {truncated_text}")
            hits.append({
                "source": fname,
                "page": page_number,
                "snippet": truncated_text,
            })

        context = "\n---\n".join(context_parts)
        
        # Inject duplicate warning into successful results if present
        if duplicate_warning:
            context = f"{duplicate_warning}\n\n{context}"
        primary_hit = hits[0] if hits else {"source": filename or "Dokument", "page": None}
        data = {
            "context": context,
            "hits": hits,
            "hit_count": len(hits),
            "primary_source": primary_hit.get("source"),
            "primary_page": primary_hit.get("page"),
        }

        short_msg = f"{len(hits)} Treffer in der Wissensdatenbank."
        return tool_ok_v1(data, message=short_msg, tags=tags, started_at=started)
    except Exception as e:
        logger.error(f"RAG Error: {e}", exc_info=True)
        return tool_err_v1(
            "OPERATION_FAILED",
            f"Fehler bei der Suche: {str(e)}",
            tags=tags,
            started_at=started,
        )


def list_collections() -> list[str]:
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return [c.name for c in client.list_collections()]
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Sammlungen: {e}", exc_info=True)
        return []


def get_all_documents_from_collection(collection_name: str, limit: int = 15) -> List[str]:
    """Holt eine Liste von Dokumenteninhalten aus einer spezifischen Collection."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name=collection_name)
        results = collection.get(limit=limit, include=["documents"])
        documents = results.get("documents")
        if not documents:
            return []
        return documents
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Dokumenten aus Collection '{collection_name}': {e}", exc_info=True)
        return []


def process_and_index_single_document(file_path: str, document_id: int, filename: str, db_session):
    logger.info(f"Starte Indexierung für Dokument ID {document_id}: {filename}")
    collection_name = "janus_global_documents"
    
    try:
        collection = _get_or_create_collection(collection_name)
        
        reader = PdfReader(file_path)
        full_text_chunks = []
        metadatas = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                chunks = _split_text(text)
                for i, chunk in enumerate(chunks):
                    full_text_chunks.append(chunk)
                    metadatas.append({
                        "document_id": document_id,
                        "filename": filename,
                        "page": page_num + 1,
                        "chunk_index": i,
                        "source_type": "tabletop_rulebook",
                    })
        
        if not full_text_chunks:
            raise ValueError("Kein lesbarer Text in der PDF gefunden.")

        ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(full_text_chunks))]
        collection.add(documents=full_text_chunks, metadatas=metadatas, ids=ids)
        logger.info(f"Dokument {filename} mit {len(reader.pages)} Seiten erfolgreich vektorisiert.")

        from backend.data.models import Document
        doc = db_session.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.is_indexed = True
            db_session.commit()
            
    except Exception as e:
        logger.error(f"Fehler bei Vektorisierung von Doc {document_id}: {e}", exc_info=True)
        from backend.data.models import Document
        doc = db_session.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.error_message = str(e)
            db_session.commit()


def delete_document_index(db: Session, document_id: int):
    """Entfernt ein Dokument physikalisch aus ChromaDB und SQL (Safe Path)."""
    try:
        import backend.services.vector_service as vs
        v_service = getattr(vs, "vector_service", None)

        if v_service and hasattr(v_service, "delete_by_document_id"):
            v_service.delete_by_document_id(document_id)
            logger.info(f"RAG PURGE SUCCESS: Vektoren für ID {document_id} aus ChromaDB entfernt.")
        else:
            logger.error(f"RAG PURGE FAIL: Vector Service Instanz im Namespace nicht gefunden.")

        from backend.data.models import Document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            db.delete(doc)
            db.commit()
            logger.info(f"RAG PURGE SUCCESS: Dokument ID {document_id} aus SQL-DB entfernt.")
        return True
    except Exception as e:
        logger.error(f"Kritischer Fehler bei RAG Purge (ID {document_id}): {e}")
        if db: db.rollback()
        return False
