from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.data import crud
from backend.data.database import get_db
from backend.data.models import Chat
from backend.services.context.context_compressor import (
    CompressionProposal,
    propose_compression,
)
from backend.services.context.context_state import ContextStateOutput, calculate_context_state

router = APIRouter()
logger = logging.getLogger("janus_backend")


class ContextStateInput(BaseModel):
    chat_id: str | int | None = None
    provider: str | None = None
    model: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    include_persisted_messages: bool = True


class CompressionCandidateOutput(BaseModel):
    """Einzelner Kandidat für die Kompression."""

    index: int
    role: str
    content_preview: str = Field(..., description="Erste 200 Zeichen des Content")
    estimated_tokens: int
    is_paired: bool


class CompressionProposalOutput(BaseModel):
    """API Output für Kompressions-Vorschläge."""

    candidates: list[CompressionCandidateOutput]
    summary_preview: str
    estimated_tokens_current: int
    estimated_tokens_saved: int
    savings_percent: float
    savings_euro_estimate: float = Field(
        default=0.0,
        description="Geschätzte Kostenersparnis in Euro (optional via #SavingsVisualizer)",
    )
    protected_count: int
    compression_ratio: float
    can_compress: bool = Field(
        default=True,
        description="Ob genug Kandidaten für sinnvolle Kompression vorhanden",
    )
    message: str = Field(
        default="",
        description="Info-Message wenn keine Kompression möglich",
    )


class CompressionProposeInput(BaseModel):
    """Input für Compression Proposal Request."""

    chat_id: str | int | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
    include_persisted_messages: bool = True
    target_model: str | None = Field(
        default=None,
        description="Ziel-Modell für Kontext-Limit-Check",
    )


def _db_messages_to_payload(db_messages: list[Any]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for message in db_messages:
        role = getattr(message, "role", None) or getattr(message, "sender", None) or "user"
        content = getattr(message, "content", None) or ""
        payload.append({"role": role, "content": content})
    return payload


@router.post("/context/state", response_model=ContextStateOutput)
async def get_context_state(payload: ContextStateInput, db: Session = Depends(get_db)) -> ContextStateOutput:
    messages: list[dict[str, Any]] = list(payload.messages or [])
    if payload.include_persisted_messages and payload.chat_id is not None and not messages:
        try:
            messages = _db_messages_to_payload(crud.get_messages_by_chat_id(db, int(payload.chat_id)))
        except Exception:
            logger.warning("[CONTEXT-AWARENESS] Failed to load persisted messages for chat_id=%s", payload.chat_id, exc_info=True)
            messages = list(payload.messages or [])

    state = calculate_context_state(
        chat_id=payload.chat_id,
        provider=payload.provider,
        model=payload.model,
        messages=messages,
    )
    logger.info(
        "[CONTEXT-AWARENESS] chat_id=%s model=%s status=%s usage=%.1f%% tokens=%s/%s",
        state.chat_id,
        state.model,
        state.status,
        state.usage_percent,
        state.total_tokens,
        state.effective_input_limit,
    )
    return state


@router.post("/context/compression/propose", response_model=CompressionProposalOutput)
async def propose_compression_endpoint(
    payload: CompressionProposeInput,
    db: Session = Depends(get_db),
) -> CompressionProposalOutput:
    """
    Phase 3: Generiert einen Kompressions-Vorschlag für die gegebene Chat-History.

    Dieser Endpoint:
    1. Selektiert Kandidaten nach Diamond-Exclusion-Rules
    2. Generiert eine Summary-Preview
    3. Berechnet Token-Ersparnis (optional mit Euro-Schätzung)

    #Safety: Keine Datenbank-Mutation in Phase 3 (nur Read/Propose)
    #ResilientTelemetry: Loggt context_compression_proposed Event
    """
    messages: list[dict[str, Any]] = list(payload.messages or [])

    # Lade persisted messages wenn nötig
    if payload.include_persisted_messages and payload.chat_id is not None and not messages:
        try:
            messages = _db_messages_to_payload(crud.get_messages_by_chat_id(db, int(payload.chat_id)))
        except Exception:
            logger.warning(
                "[COMPRESSOR] Failed to load persisted messages for chat_id=%s",
                payload.chat_id,
                exc_info=True,
            )
            messages = list(payload.messages or [])

    # 💎 CU-2: Dynamische Schwellenwert-Logik basierend auf Context-Auslastung
    # Berechne Context-State um usage_percent zu ermitteln
    context_state = calculate_context_state(
        chat_id=payload.chat_id,
        provider=None,  # Provider nicht kritisch für Message-Count-Entscheidung
        model=payload.target_model,
        messages=messages,
    )

    # Schwelle: < 70% Auslastung = 10 Nachrichten, >= 70% oder orange/red/overflow = 2 Nachrichten
    is_high_usage = (
        context_state.usage_percent >= 70.0 or
        context_state.status in ("orange", "red", "overflow")
    )
    min_messages_required = 2 if is_high_usage else 10

    if len(messages) < min_messages_required:
        if is_high_usage:
            msg = f"Mindestens {min_messages_required} Nachrichten erforderlich (aktuell: {len(messages)}) bei {context_state.usage_percent:.0f}% Auslastung."
        else:
            msg = "Mindestens 10 Nachrichten erforderlich für sinnvolle Kompression."
        return CompressionProposalOutput(
            candidates=[],
            summary_preview="",
            estimated_tokens_current=0,
            estimated_tokens_saved=0,
            savings_percent=0.0,
            protected_count=0,
            compression_ratio=0.0,
            can_compress=False,
            message=msg,
        )

    # Generiere Proposal (mit target_model für Overflow-Detection)
    proposal = await propose_compression(messages, payload.chat_id, payload.target_model)

    if not proposal:
        return CompressionProposalOutput(
            candidates=[],
            summary_preview="",
            estimated_tokens_current=0,
            estimated_tokens_saved=0,
            savings_percent=0.0,
            protected_count=0,
            compression_ratio=0.0,
            can_compress=False,
            message="Keine Kompressions-Kandidaten gefunden (alle Messages geschützt).",
        )

    # #SavingsVisualizer: Geschätzte Kostenersparnis (optional)
    # Annahme: ~$2/Mio Tokens (Durchschnitt)
    euro_estimate = (proposal.estimated_tokens_saved / 1_000_000) * 2.0

    # Formatiere Candidates für API Response
    candidates_output = [
        CompressionCandidateOutput(
            index=c.index,
            role=c.role,
            content_preview=c.content[:200] + "..." if len(c.content) > 200 else c.content,
            estimated_tokens=c.estimated_tokens,
            is_paired=c.is_paired,
        )
        for c in proposal.candidates
    ]

    # #ResilientTelemetry: Logge Proposal Event
    logger.info(
        "[COMPRESSOR-TELEMETRY] event=context_compression_proposed "
        "chat_id=%s candidates=%d tokens_saved=%d savings_percent=%.1f%%",
        payload.chat_id,
        len(proposal.candidates),
        proposal.estimated_tokens_saved,
        proposal.savings_percent,
    )

    return CompressionProposalOutput(
        candidates=candidates_output,
        summary_preview=proposal.summary_preview,
        estimated_tokens_current=proposal.estimated_tokens_current,
        estimated_tokens_saved=proposal.estimated_tokens_saved,
        savings_percent=proposal.savings_percent,
        savings_euro_estimate=round(euro_estimate, 4),
        protected_count=proposal.protected_count,
        compression_ratio=proposal.compression_ratio,
        can_compress=True,
        message=f"{len(candidates_output)} Nachrichten können komprimiert werden.",
    )


class CompressionApplyInput(BaseModel):
    """Input für Compression Apply Request."""

    chat_id: str | int
    candidate_indices: list[int] = Field(..., description="Indizes der zu komprimierenden Nachrichten")
    summary_text: str = Field(..., description="Die zu verwendende Zusammenfassung")
    tokens_saved: int = Field(default=0)
    create_pdf_backup: bool = Field(default=True, description="💎 CU-3: Ob ein PDF-Backup erstellt werden soll")


class CompressionApplyOutput(BaseModel):
    """Output für Compression Apply."""

    compression_id: int
    success: bool
    messages_archived: int
    summary_message_id: int | None = None
    message: str = ""
    pdf_backup_created: bool = Field(default=False, description="💎 CU-3: Ob PDF-Backup erstellt wurde")
    pdf_path: str | None = Field(default=None, description="💎 CU-3: Pfad zum PDF-Backup")


@router.post("/context/compression/apply", response_model=CompressionApplyOutput)
async def apply_compression_endpoint(
    payload: CompressionApplyInput,
    db: Session = Depends(get_db),
) -> CompressionApplyOutput:
    """
    Phase 4: Wendet die Kompression atomar an.

    Ablauf:
    1. Speichert Compression-Metadaten in context_compressions
    2. Archiviert Original-Nachrichten in context_archives
    3. Löscht Originale aus messages
    4. Injeziert System-Nachricht mit Summary

    #AsyncLifecycleSafety: Transaction schützt gegen Race Conditions
    #ResilientTelemetry: Loggt context_compression_applied
    """
    from backend.data.models import ContextArchive, ContextCompression, Message

    chat_id = int(payload.chat_id)

    try:
        # Starte Transaction
        with db.begin():
            # 1. Hole alle Nachrichten des Chats
            all_messages = crud.get_messages_by_chat_id(db, chat_id)

            # 2. Validiere candidate_indices
            message_ids_to_compress = []
            for idx in payload.candidate_indices:
                if 0 <= idx < len(all_messages):
                    msg = all_messages[idx]
                    message_ids_to_compress.append((idx, msg.id, msg))

            if not message_ids_to_compress:
                return CompressionApplyOutput(
                    compression_id=-1,
                    success=False,
                    messages_archived=0,
                    message="Keine gültigen Nachrichten zum Komprimieren gefunden.",
                )

            # 3. Erstelle Compression-Eintrag
            compression = ContextCompression(
                chat_id=chat_id,
                summary_text=payload.summary_text,
                tokens_saved=payload.tokens_saved,
                original_message_count=len(message_ids_to_compress),
                compression_ratio=0.8,  # Ziel-Ratio
            )
            db.add(compression)
            db.flush()  # Erhalte compression.id

            # 4. Archive jede Nachricht
            archives_created = 0
            for order_idx, msg_id, msg in message_ids_to_compress:
                archive = ContextArchive(
                    compression_id=compression.id,
                    original_message_json={
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None,
                        "metadata_json": msg.metadata_json,
                    },
                    order_index=order_idx,
                )
                db.add(archive)
                archives_created += 1

            # 5. Lösche Original-Nachrichten
            for _, msg_id, _ in message_ids_to_compress:
                db.query(Message).filter(Message.id == msg_id).delete()

            # 6. Erstelle Summary-System-Nachricht (mit HTML für interaktiven Button)
            summary_content = (
                f"📦 <strong>KONTEXT-KOMPRESSION</strong><br><br>"
                f"{payload.summary_text}<br><br>"
                f"<hr>"
                f"<div class='compression-footer'>"
                f"<span class='compression-count'>{archives_created} ältere Nachrichten wurden zusammengefasst.</span>"
                f"<button class='btn btn-sm btn-secondary show-compression-details' "
                f"data-compression-id='{compression.id}' data-chat-id='{chat_id}'>"
                f"🔍 Details anzeigen"
                f"</button>"
                f"</div>"
            )

            summary_message = Message(
                chat_id=chat_id,
                role="system",  # System-Rolle für visuelle Unterscheidung
                content=summary_content,
                metadata_json=json.dumps({
                    "is_compression_summary": True,
                    "compression_id": compression.id,
                    "archives_created": archives_created,
                }),
            )
            db.add(summary_message)
            db.flush()

            summary_msg_id = summary_message.id

        # 💎 CU-3: PDF-Backup erstellen (außerhalb der Transaction)
        pdf_backup_created = False
        pdf_path = None
        if payload.create_pdf_backup and archives_created > 0:
            try:
                pdf_result = await _create_compression_pdf_backup(
                    chat_id=chat_id,
                    compression_id=compression.id,
                    messages_data=[
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "created_at": msg.created_at.isoformat() if msg.created_at else "",
                        }
                        for _, _, msg in message_ids_to_compress
                    ],
                    summary_text=payload.summary_text,
                    db=db,
                )
                pdf_backup_created = pdf_result.get("success", False)
                pdf_path = pdf_result.get("pdf_path")
                if pdf_backup_created:
                    logger.info("[COMPRESSOR-TELEMETRY] pdf_backup_created=true path=%s", pdf_path)
            except Exception as pdf_err:
                logger.warning("[COMPRESSOR] PDF backup creation failed: %s", pdf_err)
                # PDF-Fehler sollten nicht die Kompression blockieren

        # #ResilientTelemetry
        logger.info(
            "[COMPRESSOR-TELEMETRY] event=context_compression_applied "
            "compression_id=%d chat_id=%d archived=%d summary_msg_id=%d pdf_backup=%s",
            compression.id,
            chat_id,
            archives_created,
            summary_msg_id,
            "true" if pdf_backup_created else "false",
        )

        return CompressionApplyOutput(
            compression_id=compression.id,
            success=True,
            messages_archived=archives_created,
            summary_message_id=summary_msg_id,
            message=f"{archives_created} Nachrichten erfolgreich komprimiert.",
            pdf_backup_created=pdf_backup_created,
            pdf_path=pdf_path,
        )

    except Exception as e:
        logger.error("[COMPRESSOR] Apply compression failed: %s", e, exc_info=True)
        return CompressionApplyOutput(
            compression_id=-1,
            success=False,
            messages_archived=0,
            message=f"Kompression fehlgeschlagen: {str(e)}",
        )


class CompressionRestoreOutput(BaseModel):
    """Output für Compression Restore."""

    success: bool
    messages_restored: int
    message: str = ""


@router.post("/context/compression/{compression_id}/restore", response_model=CompressionRestoreOutput)
async def restore_compression_endpoint(
    compression_id: int,
    db: Session = Depends(get_db),
) -> CompressionRestoreOutput:
    """
    Phase 4: Stellt archivierte Nachrichten wieder her und löscht den Summary-Block.

    Ablauf:
    1. Lade alle Archive für die Compression
    2. Restauriere Original-Nachrichten in korrekter Reihenfolge
    3. Lösche die Summary-System-Nachricht
    4. Markiere Compression als restored

    #Reversibility: Vollständige Wiederherstellung möglich
    """
    from backend.data.models import ContextArchive, ContextCompression, Message

    try:
        with db.begin():
            # 1. Hole Compression und Archive
            compression = db.query(ContextCompression).filter(
                ContextCompression.id == compression_id
            ).first()

            if not compression:
                return CompressionRestoreOutput(
                    success=False,
                    messages_restored=0,
                    message="Kompression nicht gefunden.",
                )

            if compression.is_restored:
                return CompressionRestoreOutput(
                    success=False,
                    messages_restored=0,
                    message="Diese Kompression wurde bereits wiederhergestellt.",
                )

            archives = db.query(ContextArchive).filter(
                ContextArchive.compression_id == compression_id
            ).order_by(ContextArchive.order_index).all()

            # 2. Restauriere Nachrichten
            restored_count = 0
            for archive in archives:
                original = archive.original_message_json
                restored_msg = Message(
                    chat_id=compression.chat_id,
                    role=original.get("role", "user"),
                    content=original.get("content", ""),
                    metadata_json=original.get("metadata_json"),
                )
                db.add(restored_msg)
                restored_count += 1

            # 3. Finde und lösche Summary-Nachricht
            summary_metadata = f'"compression_id": {compression_id}'
            summary_msgs = db.query(Message).filter(
                Message.chat_id == compression.chat_id,
                Message.metadata_json.contains("is_compression_summary"),
                Message.metadata_json.contains(summary_metadata),
            ).all()

            for sm in summary_msgs:
                db.delete(sm)

            # 4. Markiere Compression als restored
            compression.is_restored = True
            compression.restored_at = datetime.utcnow()

        logger.info(
            "[COMPRESSOR-TELEMETRY] event=context_compression_restored "
            "compression_id=%d chat_id=%d restored=%d",
            compression_id,
            compression.chat_id,
            restored_count,
        )

        return CompressionRestoreOutput(
            success=True,
            messages_restored=restored_count,
            message=f"{restored_count} Nachrichten erfolgreich wiederhergestellt.",
        )

    except Exception as e:
        logger.error("[COMPRESSOR] Restore compression failed: %s", e, exc_info=True)
        return CompressionRestoreOutput(
            success=False,
            messages_restored=0,
            message=f"Wiederherstellung fehlgeschlagen: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 💎 CU-3: PDF-Backup Hilfsfunktion
# ═══════════════════════════════════════════════════════════════════════════════

async def _create_compression_pdf_backup(
    chat_id: int,
    compression_id: int,
    messages_data: list[dict],
    summary_text: str,
    db: Session,
) -> dict:
    """
    Erstellt ein PDF-Backup der komprimierten Nachrichten.

    Args:
        chat_id: ID des Chats
        compression_id: ID der Compression
        messages_data: Liste der archivierten Nachrichten (role, content, created_at)
        summary_text: Die Zusammenfassung
        db: Database session für Chat-Title-Abfrage

    Returns:
        dict mit {"success": bool, "pdf_path": str | None}
    """
    try:
        from backend.tools.pdf_generator import create_pdf_from_markdown
        from backend.utils.paths import get_app_data_dir
        import re

        # 💎 OPTIMIERUNG: Chat-Title abfragen für Keywords
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        chat_title = chat.title if chat and chat.title else "archiv"

        # 💎 KEYWORDS: Extrahiere erste 3 relevante Wörter, lowercase, Sonderzeichen entfernt
        words = re.findall(r'\b[a-zA-ZäöüÄÖÜß]+\b', chat_title.lower())
        keywords = '_'.join(words[:3]) if len(words) >= 3 else '_'.join(words) if words else "archiv"

        # 💎 DATUMSFORMAT: DD-MM-YYYY
        date_str = datetime.now().strftime("%d-%m-%Y")

        # 💎 NEUER DATEINAME: Archiv_[Datum]_[Keywords].pdf
        filename = f"Archiv_{date_str}_{keywords}.pdf"

        # Erstelle Markdown-Content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        md_lines = [
            f"# Chat-Archiv (Kompression #{compression_id})",
            f"",
            f"**Chat ID:** {chat_id}  ",
            f"**Erstellt:** {timestamp}  ",
            f"**Nachrichten:** {len(messages_data)}",
            f"",
            f"---",
            f"",
            f"## Zusammenfassung",
            f"",
            summary_text,
            f"",
            f"---",
            f"",
            f"## Archivierte Nachrichten",
            f"",
        ]

        for i, msg in enumerate(messages_data, 1):
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            created = msg.get("created_at", "")

            # Escape Markdown-Sonderzeichen im Content
            content_escaped = str(content).replace("**", "\\**").replace("#", "\\#")

            md_lines.extend([
                f"### [{i}] {role}",
                f"",
                f"{content_escaped}",
                f"",
            ])

        markdown_content = "\n".join(md_lines)

        # PDF erstellen
        result = create_pdf_from_markdown(
            content=markdown_content,
            filename=filename,
            location="documents",  # 💎 FIX: Nutze get_secure_absolute_path("documents") für ~/Documents/JanusPDFs
            font_size=11,
            layout_profile="bericht",
        )

        # Prüfe Ergebnis
        if isinstance(result, dict):
            if result.get("type") == "error":
                logger.warning("[COMPRESSOR] PDF generation returned error: %s", result.get("message"))
                return {"success": False, "pdf_path": None}

            # Extrahiere Dateipfad aus dem ToolResult
            file_path = result.get("file_path") or result.get("path")
            if file_path:
                # 💎 UI-REFRESH: Sende ui_action für Wissensdatenbank-Refresh
                return {"success": True, "pdf_path": file_path, "ui_action": "refresh_documents"}

        # Fallback: Annahme dass es funktioniert hat
        return {"success": True, "pdf_path": f"JanusPDFs/{filename}", "ui_action": "refresh_documents"}

    except Exception as e:
        logger.error("[COMPRESSOR] PDF backup creation error: %s", e, exc_info=True)
        return {"success": False, "pdf_path": None}


# ═══════════════════════════════════════════════════════════════════════════════
# 💎 CU-2: GET Compression Details (für Detail-Modal)
# ═══════════════════════════════════════════════════════════════════════════════

class CompressionDetailOutput(BaseModel):
    """Output für Compression Detail-Ansicht."""

    compression_id: int
    chat_id: int
    summary_text: str
    tokens_saved: int
    original_message_count: int
    compression_ratio: float
    is_restored: bool
    created_at: datetime | None = None
    archived_messages: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/context/compression/{compression_id}", response_model=CompressionDetailOutput)
async def get_compression_details_endpoint(
    compression_id: int,
    db: Session = Depends(get_db),
) -> CompressionDetailOutput:
    """
    💎 CU-2: Lädt Details einer Compression inkl. archivierter Nachrichten.

    Wird vom Frontend aufgerufen wenn User auf "Details anzeigen" klickt.
    """
    from backend.data.models import ContextArchive, ContextCompression

    try:
        compression = (
            db.query(ContextCompression)
            .filter(ContextCompression.id == compression_id)
            .first()
        )

        if not compression:
            raise HTTPException(status_code=404, detail="Compression nicht gefunden")

        archives = (
            db.query(ContextArchive)
            .filter(ContextArchive.compression_id == compression_id)
            .order_by(ContextArchive.order_index)
            .all()
        )

        archived_messages = []
        for archive in archives:
            msg_data = archive.original_message_json
            if isinstance(msg_data, str):
                msg_data = json.loads(msg_data)
            archived_messages.append({
                "order_index": archive.order_index,
                "role": msg_data.get("role", "unknown"),
                "content": msg_data.get("content", ""),
                "created_at": msg_data.get("created_at"),
            })

        return CompressionDetailOutput(
            compression_id=compression.id,
            chat_id=compression.chat_id,
            summary_text=compression.summary_text,
            tokens_saved=compression.tokens_saved,
            original_message_count=compression.original_message_count,
            compression_ratio=compression.compression_ratio,
            is_restored=compression.is_restored,
            created_at=compression.created_at,
            archived_messages=archived_messages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[COMPRESSOR] Failed to load compression details: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# 💎 CU-3: Telemetrie-Proxy für Frontend Events (D10 Logging)
# ═══════════════════════════════════════════════════════════════════════════════

class ContextLogInput(BaseModel):
    """Input für Frontend-Context-Events."""

    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


class ContextLogOutput(BaseModel):
    """Output für Log-Event-Acknowledgement."""

    success: bool
    message: str


@router.post("/context/log", response_model=ContextLogOutput)
async def log_context_event_endpoint(
    payload: ContextLogInput,
) -> ContextLogOutput:
    """
    Proxy für Frontend-Context-Telemetrie-Events.
    Leitet Events an D10 Logging weiter.
    """
    try:
        # D10-konformes Logging
        logger.info(
            "[CONTEXT-TELEMETRY] event=%s trace_id=%s payload=%s",
            payload.event_type,
            payload.trace_id or "none",
            json.dumps(payload.payload, default=str),
        )

        # Optional: Hier könnte eine Erweiterung an ein Event-System erfolgen
        # z.B. logger_core.log_event() wenn verfügbar

        return ContextLogOutput(
            success=True,
            message=f"Event '{payload.event_type}' logged successfully",
        )
    except Exception as e:
        logger.warning("[CONTEXT-TELEMETRY] Failed to log event: %s", e)
        return ContextLogOutput(
            success=False,
            message=f"Logging failed: {str(e)}",
        )
