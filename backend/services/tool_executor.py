# backend/services/tool_executor.py
import asyncio
import inspect
import json
import logging
import os
import pathlib
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.data.models import SkillTelemetry
from backend.data.schemas import SkillResponse
from backend.data.schemas_tools import ToolResultV1
from backend.services.policy_engine import PolicyEngine
from backend.services.skill_router import SkillNotFoundError, skill_router
from backend.services.tool_argument_sanitizer import sanitize_tool_arguments
from backend.services.tool_manager import tool_manager
from pydantic import BaseModel
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1
from backend.services.logging.logger_core import log_event, LogEventCreate

logger = logging.getLogger("janus_backend")


async def open_knowledge_document(filename: str, db: Session) -> ToolResultV1:
    from backend.data.models import Document

    started = time.perf_counter()
    tags = ["knowledge", "documents"]
    try:

        def _normalize(term: str) -> str:
            return (
                str(term or "")
                .lower()
                .replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss")
            )

        search_term = _normalize(filename)
        doc = (
            db.query(Document)
            .filter(
                (Document.filename.ilike(f"%{filename}%"))
                | (Document.filename.ilike(f"%{search_term}%"))
            )
            .first()
        )

        if doc:
            logger.info(f"UI-Aktion: Öffne Dokument '{doc.filename}' (ID: {doc.id})")
            msg = f"Das Dokument '{doc.filename}' wird jetzt im Knowledge Center geöffnet."
            return tool_ok_v1(
                {
                    "ui_action": "open_pdf",
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "result": msg,
                },
                message=msg,
                tags=tags,
                started_at=started,
                primary_entity_id=str(doc.id),
            )

        all_docs = db.query(Document).all()
        doc_list = ", ".join([d.filename for d in all_docs])
        err_msg = (
            f"Ich konnte '{filename}' nicht finden. "
            f"Verfügbare PDFs: {doc_list if doc_list else 'Keine'}"
        )
        return tool_err_v1("NOT_FOUND", err_msg, tags=tags, started_at=started)
    except Exception as e:
        logger.error("open_knowledge_document: %s", e, exc_info=True)
        return tool_err_v1("OPERATION_FAILED", str(e), tags=tags, started_at=started)


async def list_knowledge_documents(db: Session) -> ToolResultV1:
    """Gibt eine Liste aller PDFs in der Datenbank zurück."""
    from backend.data.models import Document

    started = time.perf_counter()
    tags = ["knowledge", "documents"]
    try:
        docs = db.query(Document).all()
        if not docs:
            msg = "Die Wissensdatenbank ist aktuell leer. Du musst den User bitten, eine PDF hochzuladen."
            return tool_ok_v1({"result": msg, "documents": []}, message=msg, tags=tags, started_at=started)
        filenames = [d.filename for d in docs]
        msg = f"In der Datenbank registrierte Dokumente: {', '.join(filenames)}"
        return tool_ok_v1(
            {"result": msg, "documents": filenames},
            message=msg,
            tags=tags,
            started_at=started,
        )
    except Exception as e:
        logger.error("list_knowledge_documents: %s", e, exc_info=True)
        return tool_err_v1("OPERATION_FAILED", str(e), tags=tags, started_at=started)


async def _read_file_fulltext(
    file_path: str,
    started: float,
    tags: List[str],
) -> Optional[ToolResultV1]:
    """Read full text from a file on disk (PDF via PyMuPDF/pypdf, else UTF-8 text)."""
    ext = os.path.splitext(file_path)[1].lower()
    filename_only = os.path.basename(file_path)

    def _extract() -> Optional[str]:
        try:
            if ext == ".pdf":
                try:
                    import fitz  # PyMuPDF
                    doc_pdf = fitz.open(file_path)
                    text = "\n".join((page.get_text() or "") for page in doc_pdf)
                    doc_pdf.close()
                    return text.strip()
                except Exception:
                    from pypdf import PdfReader
                    reader = PdfReader(file_path)
                    return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
            elif ext == ".docx":
                try:
                    import docx  # python-docx
                    d = docx.Document(file_path)
                    return "\n".join(p.text for p in d.paragraphs).strip()
                except Exception as exc:
                    logger.warning("DOCX read failed for %s: %s", file_path, exc)
                    return None
            else:
                with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                    return fh.read().strip()
        except Exception as exc:
            logger.warning("File read failed for %s: %s", file_path, exc)
            return None

    content = await asyncio.to_thread(_extract)
    if not content:
        return None

    # Inject source header directly into content to make it inseparable for LLMs
    source_header = f"[DOKUMENT-QUELLE: {file_path}]"
    content = f"{source_header}\n\n{content}"

    return tool_ok_v1(
        {
            "content": content,
            "source": "rag_v2_filesystem",
            "filename": filename_only,
            "file_path": file_path,
        },
        message=f"Volltext aus Quell-Datei geladen ({ext or 'text'}).",
        tags=tags,
        started_at=started,
    )


async def _v2_fulltext_fallback(
    filename: str,
    started: float,
    tags: List[str],
    absolute_path: Optional[str] = None,
) -> Optional[ToolResultV1]:
    """Resolve a filename via RAG-V2 IndexStore (endswith match) and read the file from disk.
    
    DUPLICATE HANDLING LOGIC (always enforced):
    1. Physical duplicate scan runs FIRST (before any file reading)
    2. If duplicates found:
       - Build warning_block with all paths
       - If no absolute_path: Content Withholding (return ONLY warning)
       - If absolute_path: Read file + prepend warning to content
    3. If no duplicates: Normal single-file flow
    """
    if not filename:
        return None
    store = None  # FIX #1: Managed lifecycle — close only at the end
    try:
        from backend.services.rag.index_store import IndexStore
        from backend.utils.paths import get_app_data_dir

        index_db = os.path.join(get_app_data_dir(), "knowledge_index_v2.db")
        if not os.path.exists(index_db):
            return None

        # Robust path-based matching: compare by stem (no extension, lowercase)
        # Normalize paths for Windows compatibility (backslashes -> forward slashes)
        from pathlib import PurePath

        def _normalize_path(p: str) -> str:
            """Convert backslashes to forward slashes and lowercase for path comparison."""
            return p.replace("\\", "/").lower() if p else p

        needle_basename = PurePath(filename).name.lower()
        needle_stem = PurePath(needle_basename).stem

        store = IndexStore(db_path=index_db)
        raw_matches = store.find_by_filename(needle_stem)

        def _stem_match(path: str) -> bool:
            base = PurePath(_normalize_path(path)).name
            return base == needle_basename or PurePath(base).stem == needle_stem

        matches = [m for m in raw_matches if _stem_match(m.path)]
        if not matches:
            return None

        # Initialize path_previews for potential duplicate handling
        path_previews = {}
        duplicate_paths = None  # Will hold paths if duplicates found
        new_paths = []  # Unindexed paths found during duplicate scan

        # PHYSICAL DUPLICATE DETECTION: Run FIRST before any reading decision
        # This ensures warning_block is always generated when duplicates exist
        try:
            from backend.services.filesystem_manager import find_files
            stem_pattern = f"{needle_stem}.*"
            fs_result = find_files(
                pattern=stem_pattern,
                max_results=100,
                search_all_drives=False
            )
            if fs_result and fs_result.data and fs_result.data.get("matches"):
                physical_matches = fs_result.data["matches"]
                filtered_physical = [
                    p for p in physical_matches
                    if PurePath(p).stem.lower() == needle_stem
                ]
                if len(filtered_physical) > 1:
                    duplicate_paths = sorted(filtered_physical)
                    logger.info(
                        f"[DUPLICATE-DETECTION] Physical search found {len(filtered_physical)} "
                        f"copies of '{filename}': {duplicate_paths}"
                    )

                    # Identify new (unindexed) paths - validate both DB entry AND chunks
                    indexed_paths_normalized = {pathlib.Path(m.path).resolve().as_posix().lower() for m in matches}

                    new_paths = []
                    for path in duplicate_paths:
                        normalized_path = pathlib.Path(path).resolve().as_posix().lower()
                        is_in_db = normalized_path in indexed_paths_normalized

                        if not is_in_db:
                            # Path not in DB at all -> needs ingestion
                            new_paths.append(path)

                    # Auto-Ingest in background
                    if new_paths:
                        logger.info(f"[AUTO-INGEST] Found {len(new_paths)} unindexed files, triggering background ingestion: {new_paths}")
                        def _background_ingest(paths_to_ingest):
                            logger.info(f"[AUTO-INGEST] Background thread STARTED for {len(paths_to_ingest)} files: {paths_to_ingest}")
                            try:
                                from backend.services.rag.ingestion import IngestionRun
                                # Use parent of first file as root_dir (IngestionRun needs
                                # a valid existing directory for start_run)
                                root_dir = str(pathlib.Path(paths_to_ingest[0]).parent.resolve())
                                logger.info(f"[AUTO-INGEST] Initializing IngestionRun with root_dir: {root_dir}")
                                mgr = IngestionRun(root_dir=root_dir)
                                try:
                                    logger.info(f"[AUTO-INGEST] Calling mgr.run_partial with file_paths: {paths_to_ingest}")
                                    mgr.run_partial(file_paths=paths_to_ingest)
                                    logger.info(f"[AUTO-INGEST] Completed ingestion for {len(paths_to_ingest)} files")
                                except Exception as exc:
                                    logger.error(f"[AUTO-INGEST] Failed to ingest files: {exc}", exc_info=True)
                            except Exception as exc:
                                logger.error(f"[AUTO-INGEST] Could not initialize IngestionRun: {exc}", exc_info=True)
                            logger.info(f"[AUTO-INGEST] Background thread FINISHED")
                        logger.info(f"[AUTO-INGEST] Starting background thread...")
                        threading.Thread(target=_background_ingest, args=(list(new_paths),), daemon=True).start()

                    # Generate content previews for all duplicate paths
                    try:
                        for path in duplicate_paths:
                            try:
                                chunks = store.get_chunks_by_file(path, limit=2)
                                if chunks:
                                    preview = chunks[0].get("text", "")[:200]
                                    path_previews[path] = preview
                                else:
                                    path_previews[path] = "[NICHT INDIZIERT - AKTION ERFORDERLICH: Nutze 'knowledge.read_full_text' mit dem Parameter 'absolute_path' für diesen Pfad, um den Text jetzt live zu lesen!]"
                            except Exception as exc:
                                logger.warning("Failed to get preview for '%s': %s", path, exc)
                                path_previews[path] = "[NICHT INDIZIERT - AKTION ERFORDERLICH: Nutze 'knowledge.read_full_text' mit dem Parameter 'absolute_path' für diesen Pfad, um den Text jetzt live zu lesen!]"
                    except Exception as exc:
                        logger.warning("Content preview generation failed: %s", exc)
        except Exception as exc:
            logger.warning("Physical duplicate detection failed for '%s': %s", filename, exc)

        # DUPLICATE HANDLING: If duplicates found, enforce warning + decide on content
        if duplicate_paths:
            # Build warning block (always included when duplicates exist)
            paths_info = ""
            for path in duplicate_paths:
                preview = path_previews.get(path, "[Keine Vorschau]")
                paths_info += f"\n  - {path}\n    Vorschau: {preview}\n"
            
            auto_ingest_notice = ""
            if new_paths:
                auto_ingest_notice = f"\n[SYSTEM] Ich habe die Indizierung für {len(new_paths)} neue Datei(en) soeben automatisch gestartet. Sie stehen in wenigen Sekunden im RAG zur Verfügung.\n"
            
            warning_block = f"!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!\nDateiname: {filename}\nGefundene Pfade:{paths_info}{auto_ingest_notice}"

            # CONTENT WITHHOLDING: No absolute_path provided → return ONLY warning
            if not absolute_path:
                logger.info(f"[CONTENT-WITHHOLDING] Duplicates found for '{filename}' without absolute_path. Forcing agentic loop.")
                full_warning = f"{warning_block}\nAKTION ERFORDERLICH: Rufe für JEDEN Pfad oben 'knowledge.read_full_text' mit dem Parameter 'absolute_path' auf, um den Inhalt zu lesen und einen Vergleich zu erstellen."
                return tool_ok_v1(
                    data={"content": full_warning},
                    message=f"Mehrere Dateien gefunden ({len(duplicate_paths)}). Die KI muss nun die einzelnen Pfade autonom auslesen.",
                    started_at=started,
                    tags=tags,
                )

            # ABSOLUTE_PATH PROVIDED: Read the specific file + prepend warning
            logger.info(f"[DUPLICATE-WITH-PINNING] absolute_path provided for '{filename}'. Reading file with warning prepended.")
            if not os.path.exists(absolute_path):
                logger.warning(f"absolute_path '{absolute_path}' does not exist for duplicate resolution")
                return None
            
            result = await _read_file_fulltext(absolute_path, started=started, tags=tags)
            if result:
                # Prepend warning to content
                result.data["content"] = f"{warning_block}\nAktuelle Auswahl (via absolute_path): {absolute_path}\n\n{result.data['content']}"
            return result

        # NO DUPLICATES: Normal single-file flow
        # Prefer exact basename match, else most recent indexed_at
        exact = [m for m in matches if PurePath(m.path).name.lower() == needle_basename]
        chosen = (exact or sorted(matches, key=lambda m: m.indexed_at, reverse=True))[0]

        if not os.path.exists(chosen.path):
            logger.warning("RAG V2 resolved %s but file missing on disk: %s", filename, chosen.path)
            return None

        return await _read_file_fulltext(chosen.path, started=started, tags=tags)
    except Exception as exc:
        logger.warning("V2 fulltext fallback failed for '%s': %s", filename, exc)
        return None
    finally:
        # FIX #1 contd: Close store AFTER all usage
        if store is not None:
            try:
                store.close()
            except Exception:
                pass


async def get_full_document_text(filename: str, db: Session, absolute_path: Optional[str] = None) -> ToolResultV1:
    """Liefert den kompletten Text einer Datei, ohne die Chroma-Kürzung.

    Zuerst wird die Legacy-Document-Tabelle (Uploads) geprüft. Schlägt das fehl,
    wird die RAG-V2 Fuzzy-Filename-Resolution verwendet, um Dateien zu finden,
    die via globaler Indizierung aufgenommen wurden (z. B. ~/Desktop, ~/Documents).
    Absolute Pfade werden ebenfalls direkt akzeptiert.
    
    PATH-PINNING: Wenn absolute_path gesetzt ist, hat dieser Parameter ABSOLUTE
    PRIORITÄT: filename wird ignoriert, keine Dubletten-Prüfung, direktes Lesen vom
    angegebenen Pfad. Dies ermöglicht Agentic AI-Loops zur autonomen Dubletten-Auflösung.
    
    Args:
        filename: Dateiname oder relativer Pfad (wird ignoriert wenn absolute_path gesetzt)
        db: Database session
        absolute_path: Optionaler absoluter Pfad für Path-Pinning - wenn gesetzt, wird diese
                       Datei direkt von der Festplatte gelesen (ignoriert filename, Index und Dubletten-Suche)
    """
    from backend.data.models import Document

    started = time.perf_counter()
    tags = ["knowledge", "documents"]
    try:
        # --- V2 RESOLUTION FIRST (handles duplicates, auto-ingest, warning injection) ---
        # _v2_fulltext_fallback handles BOTH filename-only AND absolute_path calls.
        # It always runs physical duplicate detection and prepends warnings.
        v2_result = await _v2_fulltext_fallback(filename, started=started, tags=tags, absolute_path=absolute_path)
        if v2_result is not None:
            return v2_result

        # --- DIRECT PATH FALLBACK: If V2 couldn't resolve but path exists on disk ---
        if absolute_path and os.path.exists(absolute_path):
            logger.info(f"[ABSOLUTE-PATH FALLBACK] V2 miss, reading directly from disk: {absolute_path}")
            result = await _read_file_fulltext(absolute_path, started=started, tags=tags)
            if result is not None:
                return result

        if filename and (os.path.isabs(filename) or filename.startswith(("/", "\\"))):
            if os.path.exists(filename):
                result = await _read_file_fulltext(filename, started=started, tags=tags)
                if result is not None:
                    return result

        # Legacy Document lookup (uploaded PDFs in DB)
        doc = (
            db.query(Document)
            .filter(Document.filename.ilike(f"%{filename}%"))
            .order_by(Document.id.desc())
            .first()
        )
        if not doc:
            return tool_err_v1(
                "NOT_FOUND",
                f"Datei '{filename}' nicht gefunden.",
                tags=tags,
                started_at=started,
            )

        direct_content = getattr(doc, "content", None)
        if direct_content:
            msg = "Volltext aus Datenbank geladen."
            return tool_ok_v1(
                {
                    "content": direct_content,
                    "source": "db",
                    "filename": doc.filename,
                    "document_id": doc.id,
                },
                message=msg,
                tags=tags,
                started_at=started,
                primary_entity_id=str(doc.id),
            )

        def _fetch_from_chroma(document_id: int):
            try:
                import chromadb
                from backend.services.rag_manager import CHROMA_PATH

                client = chromadb.PersistentClient(path=CHROMA_PATH)
                collection = client.get_collection(name="janus_global_documents")
                results = collection.get(
                    where={"document_id": document_id},
                    include=["documents", "metadatas"],
                    limit=10000,
                )
                chunks = []
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                for idx, chunk_text in enumerate(documents):
                    metadata = metadatas[idx] if idx < len(metadatas) else {}
                    chunk_index = metadata.get("chunk_index", idx)
                    chunks.append((chunk_index, chunk_text or ""))
                if not chunks:
                    return None
                chunks.sort(key=lambda item: item[0])
                combined = "\n".join(text for _, text in chunks if text)
                return combined or "\n".join(text for _, text in chunks)
            except Exception as exc:
                logger.warning("Chroma-Fetch fehlgeschlagen: %s", exc)
                return None

        chroma_text = await asyncio.to_thread(_fetch_from_chroma, doc.id)
        if chroma_text and chroma_text.strip():
            msg = "Volltext aus ChromaDB geladen."
            return tool_ok_v1(
                {
                    "content": chroma_text,
                    "source": "chroma",
                    "filename": doc.filename,
                    "document_id": doc.id,
                },
                message=msg,
                tags=tags,
                started_at=started,
                primary_entity_id=str(doc.id),
            )

        if doc.file_path and os.path.exists(doc.file_path):
            def _read_pdf(path: str):
                from pypdf import PdfReader

                reader = PdfReader(path)
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages).strip()

            try:
                pdf_text = await asyncio.to_thread(_read_pdf, doc.file_path)
                if pdf_text:
                    msg = "Volltext aus Quell-PDF geladen."
                    return tool_ok_v1(
                        {
                            "content": pdf_text,
                            "source": "pdf_file",
                            "filename": doc.filename,
                            "document_id": doc.id,
                        },
                        message=msg,
                        tags=tags,
                        started_at=started,
                        primary_entity_id=str(doc.id),
                    )
            except Exception as exc:
                logger.warning("PDF-Lesen fehlgeschlagen für %s: %s", doc.file_path, exc)

        return tool_err_v1(
            "NO_TEXT_EXTRACTED",
            "Die Datei enthält keinen direkt abrufbaren Text.",
            details={"filename": filename, "document_id": doc.id},
            tags=tags,
            started_at=started,
        )
    except Exception as e:
        logger.error("get_full_document_text: %s", e, exc_info=True)
        return tool_err_v1("OPERATION_FAILED", str(e), tags=tags, started_at=started)


class ToolExecutor:
    def __init__(self, db: Session, api_key: str, provider: str, model: str, additional_context: dict = None, disable_tools: bool = False):
        self.db = db
        self.api_key = api_key
        self.provider = provider
        self.model = model
        self.additional_context = additional_context or {}
        
        # Sicherstellen, dass Tools geladen sind, bevor wir sie manipulieren
        if not tool_manager.get_all_tools():
            from backend import tool_registry as registry
            registry.register_all_tools()

        self.tool_manager = tool_manager
        self.disable_tools = disable_tools
        if disable_tools:
            logger.info("ToolExecutor initialisiert im 'disabled' Modus. Keine Tools werden geladen.")

        # Mapping für bekannte Halluzinations-/Alias-Namen.
        target_memory_tool = "memory_write"  # NEU: Zeige auf das neue V2 Tool
        target_memory_read_tool = "memory_read"  # NEU: Lese-Tool

        self.tool_aliases = {
            # ═══════════════════════════════════════════════════════════════════════════
            # MEMORY WRITE ALIASE - Legacy -> memory_write (V2.1 Gold Standard)
            # ═══════════════════════════════════════════════════════════════════════════
            "save_core_memory_fact": target_memory_tool,
            "memory.save_core_fact": target_memory_tool,
            "save_user_preference": target_memory_tool,
            "update_core_memory": target_memory_tool,
            "remember_preference_tool": target_memory_tool,
            "save_preference": target_memory_tool,
            "store_memory": target_memory_tool,
            "remember_this": target_memory_tool,
            "add_memory": target_memory_tool,
            "upsert_user_preference": target_memory_tool,
            "remember_user_preference": target_memory_tool,
            "save_memory": target_memory_tool,
            "update_core_memory_users_preference": target_memory_tool,
            "update_user_preferences": target_memory_tool,
            "save_core_memory_tool": target_memory_tool,
            "core_memory_save": target_memory_tool,
            "persist_memory": target_memory_tool,
            "memory.persist": target_memory_tool,
            "memory.add": target_memory_tool,
            "memory.store": target_memory_tool,
            "create_memory": target_memory_tool,
            "insert_memory": target_memory_tool,
            "write_memory": target_memory_tool,
            # ═══════════════════════════════════════════════════════════════════════════
            # MEMORY READ ALIASE - Legacy -> memory_read (V2.1 Gold Standard)
            # ═══════════════════════════════════════════════════════════════════════════
            "get_core_memory_facts": target_memory_read_tool,
            "memory.get_core_memory_facts": target_memory_read_tool,
            "search_past_conversation_summaries": target_memory_read_tool,
            "search_past_conversation_summaries_tool": target_memory_read_tool,
            "memory.search_summaries": target_memory_read_tool,
            "retrieve_memory": target_memory_read_tool,
            "get_memory": target_memory_read_tool,
            "fetch_memory": target_memory_read_tool,
            "search_memories": target_memory_read_tool,
            "recall_memory": target_memory_read_tool,
            "recall": target_memory_read_tool,
            "remember": target_memory_read_tool,
            "search_memory": target_memory_read_tool,
            "lookup_memory": target_memory_read_tool,
            "find_memory": target_memory_read_tool,
            "query_memory": target_memory_read_tool,
            "memory.query": target_memory_read_tool,
            "memory.retrieve": target_memory_read_tool,
            "memory.search": target_memory_read_tool,
            "memory.lookup": target_memory_read_tool,
            "memory.recall": target_memory_read_tool,
            "get_memories": target_memory_read_tool,
            "list_memories": target_memory_read_tool,
            "fetch_memories": target_memory_read_tool,
            "search_summaries": target_memory_read_tool,
            "conversation_search": target_memory_read_tool,
            "past_conversation_search": target_memory_read_tool,
            # ═══════════════════════════════════════════════════════════════════════════
            # MEMORY UPDATE ALIASE - Legacy -> memory_update (V2.1 Gold Standard)
            # ═══════════════════════════════════════════════════════════════════════════
            "update_memory": "memory_update",
            "edit_memory": "memory_update",
            "modify_memory": "memory_update",
            "change_memory": "memory_update",
            "correct_memory": "memory_update",
            "memory.edit": "memory_update",
            "memory.modify": "memory_update",
            "memory.update": "memory_update",
            # ═══════════════════════════════════════════════════════════════════════════
            # Contact Aliase
            "add_contact": "create_or_update_contact_tool",
            "update_contact": "create_or_update_contact_tool",
            "create_contact": "create_or_update_contact_tool",
            # File Aliase
            "write_file": "create_file_tool",
            "make_file": "create_file_tool",
            # Routing Alias
            "get_distance_and_route_tool": "system.routing",
        }

    async def execute_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        trace_id: Optional[str] = None,
        is_internal_call: bool = False,
    ) -> Dict[str, Any]:
        """Führt einen einzelnen Tool-Aufruf aus."""

        started_at = time.perf_counter()
        request_trace_id = str(trace_id or self.additional_context.get("trace_id") or uuid.uuid4())
        raw_arguments = dict(tool_args or {})

        if self.disable_tools:
            blocked = SkillResponse(
                status="error",
                error={"code": "TOOLS_DISABLED", "message": "Tool-Ausführung ist deaktiviert."},
            ).model_dump()
            return self._finalize_tool_result(
                original_name=str(tool_name or ""),
                skill_id=str(tool_name or ""),
                payload=blocked,
                started_at=started_at,
                trace_id=request_trace_id,
                arguments_json=raw_arguments,
                call_type="internal" if is_internal_call else "external",
            )

        original_name = tool_name

        # 1. Alias-Prüfung
        if not tool_manager.get_tool(tool_name) and tool_name in self.tool_aliases:
            tool_name = self.tool_aliases[tool_name]
            logger.info(f"Tool-Alias angewendet: '{original_name}' -> '{tool_name}'")

        # 2. Tool via SkillRouter auflösen
        lookup_name = tool_name
        try:
            tool_def = skill_router.get_tool_definition(lookup_name)
            resolved_name = tool_def.name
            canonical_skill_id = self.tool_manager.get_skill_id(resolved_name)
        except SkillNotFoundError as exc:
            logger.error(
                "SKILL-ROUTER: Tool/Skill '%s' (mapped from '%s') nicht gefunden.",
                tool_name,
                original_name,
            )
            error_payload = SkillResponse(
                status="error",
                error={
                    "code": "SKILL_NOT_FOUND",
                    "message": str(exc),
                    "details": {"requested": original_name, "resolved": tool_name},
                },
            ).model_dump()
            return self._finalize_tool_result(
                original_name=original_name,
                skill_id=str(tool_name or original_name),
                payload=error_payload,
                started_at=started_at,
                trace_id=request_trace_id,
                arguments_json=raw_arguments,
                call_type="internal" if is_internal_call else "external",
            )

        try:
            args_schema = getattr(tool_def, "args_schema", None)
            if args_schema and hasattr(args_schema, "model_validate"):
                try:
                    validated = args_schema.model_validate(tool_args)
                    if hasattr(validated, "model_dump"):
                        tool_args = validated.model_dump(exclude_none=True)
                except ValidationError as exc:
                    logger.warning("INVALID_ARGUMENTS for tool '%s': %s", resolved_name, exc)
                    invalid_payload = SkillResponse(
                        status="error",
                        error={
                            "code": "INVALID_ARGUMENTS",
                            "message": "Tool-Parameter verletzen das erwartete Schema.",
                            "details": {"validation_errors": exc.errors()},
                        },
                    ).model_dump()
                    return self._finalize_tool_result(
                        original_name=original_name,
                        skill_id=canonical_skill_id,
                        payload=invalid_payload,
                        started_at=started_at,
                        trace_id=request_trace_id,
                        arguments_json=raw_arguments,
                        call_type="internal" if is_internal_call else "external",
                    )

            # 3. Legacy-Argumentformen harmonisieren.
            # NUR eingreifen wenn Legacy-Parameter erkannt werden,
            # NICHT wenn korrekte V2.1-Parameter vorliegen.
            _MEMORY_WRITE_LEGACY_KEYS = {"preference", "new_memory", "preference_value", "new_preferences", "key", "value"}
            if resolved_name in ("save_core_memory_fact", "memory_write"):
                has_legacy_args = bool(_MEMORY_WRITE_LEGACY_KEYS & set(tool_args.keys()))
                if has_legacy_args or (not tool_args.get("fact") and tool_args):
                    fact = (
                        tool_args.get("fact")
                        or tool_args.get("preference")
                        or tool_args.get("new_memory")
                        or tool_args.get("preference_value")
                        or tool_args.get("new_preferences")
                        or tool_args.get("key")
                        or tool_args.get("value")
                    )

                    if not fact and ("key" in tool_args or "value" in tool_args):
                        parts = []
                        if "key" in tool_args:
                            parts.append(f"{tool_args['key']}")
                        if "value" in tool_args:
                            parts.append(f"{tool_args['value']}")
                        fact = ": ".join(parts)

                    if isinstance(fact, dict):
                        fact = ", ".join([f"{k}: {v}" for k, v in fact.items()])

                    if fact:
                        category = tool_args.get("category", "Allgemein")
                        # Bewahre V2.1-Felder die evtl. parallel geliefert wurden
                        preserved = {}
                        for k in ("subject_name", "priority_override", "ttl_days", "tags", "evidence"):
                            if k in tool_args:
                                preserved[k] = tool_args[k]
                        tool_args = {"fact": fact, "category": category, **preserved}

            # Legacy-Argumentformen für memory_read (get_core_memory_facts)
            _MEMORY_READ_LEGACY_KEYS = {"search", "search_term", "topic", "subject"}
            if resolved_name in ("get_core_memory_facts", "memory_read"):
                has_legacy_args = bool(_MEMORY_READ_LEGACY_KEYS & set(tool_args.keys()))
                if has_legacy_args or (not tool_args.get("query") and tool_args):
                    query = (
                        tool_args.get("query")
                        or tool_args.get("search")
                        or tool_args.get("search_term")
                        or tool_args.get("topic")
                        or tool_args.get("subject")
                        or tool_args.get("key")
                    )

                    if query:
                        # Bewahre V2.1-Felder die evtl. parallel geliefert wurden
                        preserved = {}
                        for k in ("filter_tags", "min_priority", "include_expired", "limit"):
                            if k in tool_args:
                                preserved[k] = tool_args[k]
                        tool_args = {"query": query, "limit": preserved.pop("limit", 5), **preserved}

            if resolved_name == "edit_pdf_text_in_place":
                if not tool_args.get("modifications") and ("search_text" in tool_args or "replace_text" in tool_args):
                    legacy_search = tool_args.pop("search_text", None)
                    legacy_replace = tool_args.pop("replace_text", None)
                    modifications = []
                    if legacy_search or legacy_replace:
                        modifications.append({
                            "search": legacy_search or "",
                            "replace": legacy_replace or "",
                        })
                    if modifications:
                        tool_args["modifications"] = modifications
                if not tool_args.get("modifications"):
                    logger.warning("edit_pdf_text_in_place called without modifications list; defaulting to empty array")
                    tool_args["modifications"] = []

            if canonical_skill_id == "system.create_pdf":
                if not str(tool_args.get("content") or "").strip():
                    legacy_content = tool_args.get("markdown_content")
                    if str(legacy_content or "").strip():
                        tool_args["content"] = legacy_content
                if not str(tool_args.get("filename") or "").strip():
                    legacy_filename = tool_args.get("pdf_filename") or tool_args.get("file_name")
                    if str(legacy_filename or "").strip():
                        tool_args["filename"] = legacy_filename

                include_image_requested = bool(tool_args.get("include_image"))
                if include_image_requested and not str(tool_args.get("image_path") or "").strip():
                    markdown_content = str(tool_args.get("content") or "")
                    image_match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", markdown_content)
                    if image_match:
                        tool_args["image_path"] = image_match.group(1).strip()

                content_value = tool_args.get("content")
                if not str(content_value or "").strip():
                    missing_content_payload = SkillResponse(
                        status="error",
                        error={
                            "code": "MISSING_CONTENT",
                            "message": "Der Inhalt fuer das PDF fehlt. Du musst zuerst Informationen mit anderen Tools wie country_info oder routing sammeln.",
                        },
                    ).model_dump()
                    return self._finalize_tool_result(
                        original_name=original_name,
                        skill_id=canonical_skill_id,
                        payload=missing_content_payload,
                        started_at=started_at,
                        trace_id=request_trace_id,
                        arguments_json=raw_arguments,
                        call_type="internal" if is_internal_call else "external",
                    )
            if canonical_skill_id == "system.websearch":
                request_provider = str(
                    self.provider or self.additional_context.get("provider_id") or ""
                ).strip().lower()
                request_model = str(self.model or "").strip()
                forced_websearch_provider = str(
                    self.additional_context.get("websearch_fallback_provider") or ""
                ).strip().lower()

                # Diamond rule: when Janus itself runs on OpenAI, the native
                # OpenAI websearch provider must be used, regardless of what the
                # LLM tried to pass in the tool arguments. This prevents
                # accidental downgrades to legacy wrappers or DDG fallbacks.
                if forced_websearch_provider in {"openai", "gemini", "ollama"}:
                    tool_args["provider"] = forced_websearch_provider
                    if forced_websearch_provider == "gemini":
                        tool_args["model"] = "gemini-3-flash-preview"
                    elif request_model and not str(tool_args.get("model") or "").strip():
                        tool_args["model"] = request_model
                    logger.warning(
                        "WEBSEARCH-EXECUTOR: forced provider fallback active -> provider='%s' model='%s'",
                        tool_args.get("provider"),
                        tool_args.get("model") or "<missing>",
                    )
                elif request_provider == "openai":
                    tool_args["provider"] = "openai"
                    if request_model:
                        tool_args["model"] = request_model
                    logger.info(
                        "WEBSEARCH-EXECUTOR: enforced native OpenAI websearch (model='%s').",
                        request_model or "<missing>",
                    )
                else:
                    if request_provider:
                        tool_args["provider"] = request_provider
                    if request_model and not str(tool_args.get("model") or "").strip():
                        tool_args["model"] = request_model

                logger.info(
                    "WEBSEARCH-EXECUTOR: forwarding request provider='%s' model='%s' to system.websearch",
                    tool_args.get("provider") or request_provider or "<missing>",
                    tool_args.get("model") or request_model or "<missing>",
                )
                wf_obj = self.additional_context.get("_workflow")
                raw_q = str(tool_args.get("query") or "").strip()
                if raw_q and wf_obj is not None and getattr(wf_obj, "is_video_intent", False):
                    q_low = raw_q.lower()
                    refined = raw_q
                    if "site:youtube.com" not in q_low and "site:youtube." not in q_low:
                        refined = f"{refined} site:youtube.com"
                    if "2024" not in raw_q and "2025" not in raw_q and "2026" not in raw_q:
                        refined = f"{refined} {datetime.utcnow().year}"
                    tool_args["query"] = refined
            tool_args = sanitize_tool_arguments(
                canonical_skill_id,
                tool_args,
                provider=self.provider,
                original_user_text=self.additional_context.get("original_user_text"),
            )
            logger.info(
                "Executing tool '%s' (resolved='%s', requested='%s') with args: %s",
                canonical_skill_id,
                resolved_name,
                original_name,
                tool_args,
            )

            # 4. Kontextabhängigkeiten injizieren.
            context_vars = {
                "db": self.db,
                "api_key": self.api_key,
                "provider": self.provider,
                "model": self.model,
                "call_internal_skill": self.call_internal_skill,
                **self.additional_context,
            }

            callable_func = tool_def.func
            if inspect.ismethod(callable_func) and getattr(callable_func, "__self__", None) is not None:
                callable_func = callable_func.__func__

            final_args = {}
            try:
                sig = inspect.signature(callable_func)
            except (ValueError, TypeError):
                sig = None

            if sig is None:
                final_args = dict(tool_args)
            else:
                consumed_tool_arg_keys = set()
                has_var_keyword = False

                for param_name, param in sig.parameters.items():
                    if param_name in tool_args:
                        final_args[param_name] = tool_args[param_name]
                        consumed_tool_arg_keys.add(param_name)
                    elif param_name in context_vars:
                        final_args[param_name] = context_vars[param_name]
                    elif param.kind == inspect.Parameter.VAR_KEYWORD:
                        has_var_keyword = True

                for param_name, param in sig.parameters.items():
                    if param_name in final_args:
                        continue
                    annotation = param.annotation
                    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                        final_args[param_name] = annotation.model_validate(tool_args)
                        consumed_tool_arg_keys.update(tool_args.keys())

                if has_var_keyword:
                    for key, value in tool_args.items():
                        if key not in consumed_tool_arg_keys and key not in final_args:
                            final_args[key] = value

            # 5. Ausführung mit zentralem Timeout-Enforcement (aus Skill-JSON)
            timeout_s = self.tool_manager.get_timeout_seconds(canonical_skill_id)
            if asyncio.iscoroutinefunction(callable_func):
                coro = callable_func(**final_args)
            else:
                coro = asyncio.to_thread(callable_func, **final_args)
            try:
                execution_result = await asyncio.wait_for(coro, timeout=timeout_s)
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Skill '{canonical_skill_id}' hat das Timeout von {timeout_s:.1f}s überschritten."
                )

            if isinstance(execution_result, BaseModel):
                raw_payload = execution_result.model_dump()
            elif isinstance(execution_result, list) and all(isinstance(item, BaseModel) for item in execution_result):
                raw_payload = [item.model_dump() for item in execution_result]
            else:
                raw_payload = execution_result

            content_payload = self._ensure_skill_response(raw_payload)

            # 6. Zentrale Output-Schema-Validierung (Soft-Fail)
            output_schema = self.tool_manager.get_output_schema(canonical_skill_id)
            if output_schema is not None and content_payload.get("status") == "ok":
                try:
                    output_schema.model_validate(content_payload.get("data") or {})
                except Exception as schema_exc:
                    logger.warning(
                        "OUTPUT_SCHEMA_VIOLATION for skill '%s': %s",
                        canonical_skill_id,
                        schema_exc,
                    )

            return self._finalize_tool_result(
                original_name=original_name,
                skill_id=canonical_skill_id,
                payload=content_payload,
                started_at=started_at,
                trace_id=request_trace_id,
                arguments_json=raw_arguments,
                call_type="internal" if is_internal_call else "external",
            )

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            error_payload = SkillResponse(
                status="error",
                error={"code": "OPERATION_FAILED", "message": f"Error executing tool: {str(e)}"},
            ).model_dump()
            error_skill_id = self.tool_manager.get_skill_id(str(tool_name or original_name))
            return self._finalize_tool_result(
                original_name=original_name,
                skill_id=error_skill_id,
                payload=error_payload,
                started_at=started_at,
                trace_id=request_trace_id,
                arguments_json=raw_arguments,
                call_type="internal" if is_internal_call else "external",
            )

    async def call_internal_skill(self, skill_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a nested skill call for composite handlers without LLM involvement."""
        request_trace_id = str(self.additional_context.get("trace_id") or uuid.uuid4())
        requested_skill = str(skill_id or "").strip()
        call_args = dict(args or {})

        if not requested_skill:
            return SkillResponse(
                status="error",
                error={
                    "code": "SKILL_NOT_FOUND",
                    "message": "Interner Skill-Aufruf ohne skill_id ist ungueltig.",
                },
            ).model_dump()

        try:
            resolved_name = skill_router.resolve_tool_name(requested_skill)
        except SkillNotFoundError as exc:
            return SkillResponse(
                status="error",
                error={
                    "code": "SKILL_NOT_FOUND",
                    "message": str(exc),
                    "details": {"requested": requested_skill, "internal_call": True},
                },
            ).model_dump()

        canonical_skill_id = self.tool_manager.get_skill_id(resolved_name)
        policy_targets = [str(resolved_name)]
        if canonical_skill_id and canonical_skill_id not in policy_targets:
            policy_targets.append(str(canonical_skill_id))

        for policy_target in policy_targets:
            policy_decision = PolicyEngine.evaluate(policy_target, self.db)
            if policy_decision == "REQUIRE_CONSENT":
                return SkillResponse(
                    status="permission_required",
                    error={
                        "code": "USER_CONSENT_NEEDED",
                        "message": (
                            f"Interner Skill-Aufruf '{requested_skill}' wurde durch Policy blockiert "
                            f"(target={policy_target})."
                        ),
                        "details": {
                            "requested": requested_skill,
                            "resolved": resolved_name,
                            "policy_target": policy_target,
                            "internal_call": True,
                        },
                    },
                ).model_dump()

        wrapped_result = await self.execute_tool_call(
            requested_skill,
            call_args,
            trace_id=request_trace_id,
            is_internal_call=True,
        )
        return self._decode_tool_content(wrapped_result)

    async def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        bypass_policy: bool = False,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """Führt eine Liste von Tool-Aufrufen parallel aus."""
        logger.info(f"DEBUG-LOGGING: Context contains keys: {self.additional_context.keys()}")
        result_slots = [None] * len(tool_calls)
        pending_tasks = []
        pending_indices = []
        trace_id = str(self.additional_context.get("trace_id") or uuid.uuid4())
        per_skill_counts: Dict[str, int] = {}

        if bypass_policy:
            logger.info("EXECUTOR: Policy Bypass ist AKTIV. Sicherheitschecks werden übersprungen.")

        logger.info(
            f"EXECUTOR: execute_tool_calls aufgerufen. Bypass={bypass_policy}, DryRun={dry_run}, Anzahl Tools={len(tool_calls)}"
        )

        # Extract context data for logging
        ctx_data = self.additional_context or {}
        provider = str(ctx_data.get("provider") or "MISSING_PROVIDER")
        model = str(ctx_data.get("model") or ctx_data.get("model_id") or "MISSING_MODEL")
        session_id = str(ctx_data.get("chat_id") or ctx_data.get("session_id") or "MISSING_SESSION")

        for idx, tool_call in enumerate(tool_calls):
            function = tool_call.get("function", {})
            func_name = function.get("name")
            try:
                func_args = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                func_args = {}
            if not isinstance(func_args, dict):
                func_args = {}

            started_at = time.perf_counter()

            resolved_name = func_name
            try:
                resolved_name = skill_router.resolve_tool_name(func_name)
            except SkillNotFoundError as exc:
                error_payload = SkillResponse(
                    status="error",
                    error={
                        "code": "SKILL_NOT_FOUND",
                        "message": str(exc),
                        "details": {"requested": func_name},
                    },
                ).model_dump()
                result = self._finalize_tool_result(
                    original_name=str(func_name or ""),
                    skill_id=str(func_name or ""),
                    payload=error_payload,
                    started_at=started_at,
                    trace_id=trace_id,
                    arguments_json=func_args,
                )
                result["tool_call_id"] = tool_call.get("id")
                result_slots[idx] = result
                continue

            skill_id = self.tool_manager.get_skill_id(resolved_name)
            allowed_skill_ids = self.additional_context.get("allowed_skill_ids")
            if isinstance(allowed_skill_ids, (list, set, tuple)):
                allowed_set = {str(item) for item in allowed_skill_ids if str(item).strip()}
                requested_skill = str(skill_id or resolved_name or func_name or "").strip()
                if allowed_set and requested_skill not in allowed_set:
                    disallowed_payload = SkillResponse(
                        status="error",
                        error={
                            "code": "TOOL_NOT_ALLOWED_IN_PHASE",
                            "message": (
                                f"Tool/Skill '{requested_skill}' ist in dieser Phase nicht erlaubt."
                            ),
                            "details": {
                                "allowed_skill_ids": sorted(allowed_set),
                                "requested_skill": requested_skill,
                            },
                        },
                    ).model_dump()
                    result = self._finalize_tool_result(
                        original_name=str(func_name or ""),
                        skill_id=requested_skill,
                        payload=disallowed_payload,
                        started_at=started_at,
                        trace_id=trace_id,
                        arguments_json=func_args,
                    )
                    result["tool_call_id"] = tool_call.get("id")
                    result_slots[idx] = result
                    continue

            limit = self.tool_manager.get_max_calls_per_turn(skill_id)
            current_count = per_skill_counts.get(skill_id, 0) + 1
            per_skill_counts[skill_id] = current_count
            if current_count > limit:
                rate_payload = SkillResponse(
                    status="error",
                    error={
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": (
                            f"Skill '{skill_id}' darf pro Turn maximal {limit}x aufgerufen werden."
                        ),
                        "details": {
                            "skill_id": skill_id,
                            "max_calls_per_turn": limit,
                            "attempted_call": current_count,
                        },
                    },
                ).model_dump()
                result = self._finalize_tool_result(
                    original_name=str(func_name or ""),
                    skill_id=skill_id,
                    payload=rate_payload,
                    started_at=started_at,
                    trace_id=trace_id,
                    arguments_json=func_args,
                )
                result["tool_call_id"] = tool_call.get("id")
                result_slots[idx] = result
                continue

            # POLICY CHECK (nur wenn kein Bypass gesetzt ist)
            if not bypass_policy:
                policy_decision = PolicyEngine.evaluate(resolved_name, self.db)
                if policy_decision == "REQUIRE_CONSENT":
                    logger.warning(f"POLICY BLOCK: {resolved_name} benötigt User-Consent.")
                    consent_prompt = (
                        f"SICHERHEITS-SPERRE: Das Tool '{resolved_name}' ist potenziell gefährlich. "
                        "Du DARFST es jetzt NICHT ausführen. Frage den User stattdessen exakt dies: "
                        "'Diese Aktion erfordert eine Freigabe. Möchtest du die Aktion 1. Einmalig erlauben, "
                        "2. In Zukunft immer ohne Nachfragen erlauben, oder 3. Abbrechen?'\n\n"
                        "🚨 STRIKTE REGEL FÜR DEINE NÄCHSTE AKTION:\n"
                        f"- Wenn der User mit '1' antwortet: Rufe AUSSCHLIESSLICH das Tool '{resolved_name}' auf.\n"
                        f"- Wenn der User mit '2' antwortet: Rufe ZUERST 'system_grant_permission' auf und danach '{resolved_name}'.\n"
                        "- Wenn der User mit '3' antwortet: Bestätige den Abbruch."
                    )
                    blocked_response = SkillResponse(
                        status="permission_required",
                        data={
                            "skill_id": skill_id,
                            "resolved_name": resolved_name,
                            "arguments": func_args,
                            "consent_options": ["one_time", "always_allow", "cancel"],
                        },
                        error={"code": "USER_CONSENT_NEEDED", "message": consent_prompt},
                    ).model_dump()
                    result = self._finalize_tool_result(
                        original_name=str(func_name or ""),
                        skill_id=skill_id,
                        payload=blocked_response,
                        started_at=started_at,
                        trace_id=trace_id,
                        arguments_json=func_args,
                    )
                    result["tool_call_id"] = tool_call.get("id")
                    result_slots[idx] = result
                    continue
            else:
                logger.info(f"EXECUTOR: Policy Check für {resolved_name} übersprungen (Bypass aktiv).")
                if resolved_name == "system_grant_permission":
                    logger.warning("BYPASS-SCHUTZ: Verhindere automatischen Grant bei Einmal-Bypass.")
                    continue

            if dry_run:
                dry_payload = SkillResponse(
                    status="dry_run_success",
                    data={
                        "skill_id": skill_id,
                        "planned_call": {
                            "name": str(func_name or ""),
                            "arguments": func_args,
                        },
                    },
                ).model_dump()
                result = self._finalize_tool_result(
                    original_name=str(func_name or ""),
                    skill_id=skill_id,
                    payload=dry_payload,
                    started_at=started_at,
                    trace_id=trace_id,
                    arguments_json=func_args,
                )
                result["tool_call_id"] = tool_call.get("id")
                result_slots[idx] = result
                continue

            pending_indices.append(idx)
            # Create a wrapper that handles logging
            async def _execute_with_logging(skill_id, func_name, func_args, trace_id, idx):
                start_time = time.perf_counter()
                
                # Log tool start
                try:
                    await log_event(LogEventCreate(
                        session_id=session_id,
                        provider=provider,
                        model=model,
                        skill=skill_id,
                        event_type="tool_start",
                        payload={"arguments": func_args}
                    ))
                except Exception as log_exc:
                    logger.error(f"Failed to log tool_start event: {log_exc}")

                # Execute the tool
                result = await self.execute_tool_call(func_name, func_args, trace_id=trace_id)

                # Log tool end
                latency_ms = int((time.perf_counter() - start_time) * 1000)
                status = "success" if result.get("status") in ("ok", "dry_run_success") else "error"
                try:
                    await log_event(LogEventCreate(
                        session_id=session_id,
                        provider=provider,
                        model=model,
                        skill=skill_id,
                        event_type="tool_end",
                        status=status,
                        payload={"result": result.get("data") if status == "success" else result.get("error")},
                        latency_ms=latency_ms
                    ))
                except Exception as log_exc:
                    logger.error(f"Failed to log tool_end event: {log_exc}")

                return result

            pending_tasks.append(_execute_with_logging(skill_id or resolved_name or func_name or "", func_name, func_args, trace_id, idx))

        if pending_tasks:
            execution_results = await asyncio.gather(*pending_tasks)
            for slot_idx, execution_result in zip(pending_indices, execution_results):
                execution_result["tool_call_id"] = tool_calls[slot_idx].get("id")
                result_slots[slot_idx] = execution_result

        return [res for res in result_slots if res is not None]

    def _ensure_skill_response(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            status = payload.get("status")
            if status in {"ok", "error", "dry_run_success", "permission_required"} and (
                "data" in payload or "error" in payload
            ):
                return payload
            output_text = payload.get("output")
            if isinstance(output_text, str) and output_text.lower().startswith("fehler:"):
                lowered = output_text.lower()
                code = "OPERATION_FAILED"
                if "nicht erlaubt" in lowered or "permission" in lowered:
                    code = "PERMISSION_DENIED"
                return SkillResponse(
                    status="error",
                    error={"code": code, "message": output_text},
                ).model_dump()
            if "error" in payload:
                error_payload = {"message": payload.pop("error")}
                if payload:
                    error_payload["details"] = payload
                return SkillResponse(status="error", error=error_payload).model_dump()
        return SkillResponse(status="ok", data=payload).model_dump()

    def _finalize_tool_result(
        self,
        *,
        original_name: str,
        skill_id: str,
        payload: Dict[str, Any],
        started_at: float,
        trace_id: str,
        arguments_json: Optional[Dict[str, Any]],
        call_type: str = "external",
    ) -> Dict[str, Any]:
        elapsed_ms = (time.perf_counter() - started_at) * 1000.0
        final_payload = dict(payload or {})
        final_payload["execution_time_ms"] = round(elapsed_ms, 3)

        status = str(final_payload.get("status", ""))
        success = status in ("ok", "dry_run_success")
        error_code: Optional[str] = None
        error_obj = final_payload.get("error")
        if isinstance(error_obj, dict):
            raw_error_code = error_obj.get("code")
            if raw_error_code is not None:
                error_code = str(raw_error_code)

        self._record_skill_telemetry(
            trace_id=trace_id,
            skill_id=str(skill_id or original_name or "unknown"),
            success=success,
            latency_ms=elapsed_ms,
            error_code=error_code,
            arguments_json=arguments_json,
            response_json=final_payload,
            call_type=call_type,
        )

        return {
            "role": "tool",
            "name": original_name,
            "content": json.dumps(final_payload, ensure_ascii=False),
            "_arguments_json": dict(arguments_json or {}),
            "_skill_id": str(skill_id or original_name or "unknown"),
        }

    def _record_skill_telemetry(
        self,
        *,
        trace_id: str,
        skill_id: str,
        success: bool,
        latency_ms: float,
        error_code: Optional[str],
        arguments_json: Optional[Dict[str, Any]],
        response_json: Optional[Dict[str, Any]],
        call_type: str = "external",
    ) -> None:
        chat_id = self.additional_context.get("chat_id")
        if chat_id is None:
            chat_id = self.additional_context.get("request_chat_id")

        sanitized_call_type = "internal" if str(call_type or "").lower() == "internal" else "external"
        telemetry_arguments = dict(arguments_json or {})
        telemetry_response = dict(response_json or {})
        if sanitized_call_type == "internal":
            telemetry_arguments["__call_type"] = "internal"
            telemetry_response["__call_type"] = "internal"

        telemetry = SkillTelemetry(
            trace_id=str(trace_id or uuid.uuid4()),
            skill_id=str(skill_id or "unknown"),
            success=bool(success),
            latency_ms=float(latency_ms),
            error_code=error_code,
            arguments_json=telemetry_arguments,
            response_json=telemetry_response,
            chat_id=chat_id if isinstance(chat_id, int) else None,
        )

        try:
            self.db.add(telemetry)
            self.db.commit()
        except Exception as exc:
            logger.warning("Telemetry logging failed for skill '%s': %s", skill_id, exc)
            try:
                self.db.rollback()
            except Exception:
                pass

    def _decode_tool_content(self, wrapped_result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(wrapped_result, dict):
            return SkillResponse(
                status="error",
                error={"code": "OPERATION_FAILED", "message": "Interner Skill-Aufruf lieferte kein gueltiges Ergebnis."},
            ).model_dump()

        content_raw = wrapped_result.get("content")
        if isinstance(content_raw, str):
            try:
                parsed = json.loads(content_raw)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        if isinstance(content_raw, dict):
            return content_raw

        return SkillResponse(
            status="error",
            error={"code": "OPERATION_FAILED", "message": "Interner Skill-Aufruf konnte nicht dekodiert werden."},
        ).model_dump()
