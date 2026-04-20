import json
import logging
import re
from typing import Callable, Dict, List, Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from backend.data.models import Memory, Message
from backend.data.schemas import ExtractedFact
from backend.services.orchestrator.schemas import AuditContext, OrchestratorContext

logger = logging.getLogger("janus_backend")

RECENT_ASSISTANT_MESSAGES_TO_KEEP = 3
RECENT_ASSISTANT_MAX_CHARS = 4000
OLDER_ASSISTANT_TRUNCATE_THRESHOLD = 1600
OLDER_ASSISTANT_HEAD_CHARS = 800
OLDER_ASSISTANT_TAIL_CHARS = 400


class OrchestratorContextManager:
    """Handles conversational context assembly, memory parsing, and audit filename resolution."""

    def __init__(self, db: Session):
        self.db = db

    def resolve_audit_filename(self, chat_id: Optional[int], messages: List[str]) -> str:
        """Infer PDF audit document base name from recent messages and DB snippets.

        Args:
            chat_id: Current chat, or ``None`` to scan only ``messages``.
            messages: In-memory strings to scan first (e.g. user + model text).

        Returns:
            Stem filename without ``.pdf``, or ``dokument`` if nothing matches.
        """
        scan_sources: List[str] = [str(msg or "") for msg in (messages or [])]

        if chat_id is not None:
            recent_msgs = (
                self.db.query(Message)
                .filter(Message.chat_id == chat_id)
                .order_by(Message.id.desc())
                .limit(50)
                .all()
            )
            scan_sources.extend(str(msg.content or "") for msg in recent_msgs)

            recent_memories = (
                self.db.query(Memory)
                .filter(or_(Memory.chat_id == chat_id, Memory.chat_id.is_(None)))
                .order_by(desc(Memory.last_accessed_at), desc(Memory.created_at))
                .limit(20)
                .all()
            )
            scan_sources.extend(str(mem.snippet or "") for mem in recent_memories)

        patterns = [
            r"DATEI-UPLOAD '(.+?)\.pdf'",
            r"SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD '([^']+?)\.pdf'",
            r"Dokument: ([^,\s]+)\.pdf",
        ]
        for source in scan_sources:
            for pattern in patterns:
                match = re.search(pattern, source, re.IGNORECASE)
                if match:
                    resolved = match.group(1).strip()
                    if resolved:
                        logger.info("[CONTEXT] Audit-Dateiname aufgeloest: %s", resolved)
                        return resolved
        return "dokument"

    def get_recent_memories_raw(self, limit: int = 20, exclude_vision_for_unknown: bool = False) -> List[ExtractedFact]:
        """Load recent memory rows and parse JSON snippets into ``ExtractedFact`` models.

        Args:
            limit: Max rows by descending id.
            exclude_vision_for_unknown: If True, drop rows whose ``source_type`` looks like vision.

        Returns:
            Parsed facts; invalid JSON rows are skipped.
        """
        try:
            recent_query = self.db.query(Memory)
            if exclude_vision_for_unknown:
                recent_query = recent_query.filter(or_(Memory.source_type.is_(None), ~Memory.source_type.ilike("vision%")))
            recent_mems = recent_query.order_by(desc(Memory.id)).limit(limit).all()
            extracted_facts = []
            for mem in recent_mems:
                try:
                    data = json.loads(mem.snippet)
                    fact = ExtractedFact(
                        fact=data.get("fact", ""),
                        category=data.get("category", "Allgemein"),
                        type=data.get("type", "GENERAL"),
                        expires_in_hours=None,
                        canonical_key=data.get("canonical_key"),
                        subject_role=data.get("subject_role"),
                        subject_pet_type=None,
                        subject_relative_type=None,
                        subject_name=data.get("subject_name"),
                        predicate=data.get("predicate"),
                        object_value=data.get("object_value"),
                        evidence=data.get("evidence", ""),
                    )
                    extracted_facts.append(fact)
                except Exception:
                    continue
            return extracted_facts
        except Exception:
            logger.error("Error in orchestrator.context_manager.get_recent_memories_raw", exc_info=True)
            return []

    def _build_memories_text(self, chat_id: Optional[int], limit: int = 20) -> List[str]:
        memories: List[str] = []
        if chat_id is None:
            return memories
        try:
            recent_memories = (
                self.db.query(Memory)
                .filter(or_(Memory.chat_id == chat_id, Memory.chat_id.is_(None)))
                .order_by(desc(Memory.last_accessed_at), desc(Memory.created_at))
                .limit(limit)
                .all()
            )
            for mem in recent_memories:
                snippet = str(getattr(mem, "snippet", "") or "").strip()
                if snippet:
                    memories.append(snippet)
        except Exception:
            logger.error("Error in orchestrator.context_manager._build_memories_text", exc_info=True)
        return memories

    def assemble_history(
        self,
        *,
        chat_id: Optional[int],
        role_mapper: Callable[[str], str],
        limit: int = 8,
    ) -> OrchestratorContext:
        """Build chat history + memory strings for one orchestrator turn.

        Args:
            chat_id: Chat to load messages for; ``None`` yields empty history.
            role_mapper: Maps DB role labels to LLM roles (e.g. ``user`` / ``assistant``).
            limit: Max *pairs* / window size for included messages (newest first scan).

        Returns:
            ``OrchestratorContext`` with ``history``, raw memory lines, and default audit context.
        """
        history_buffer: List[Dict[str, str]] = []
        found_in_history = False
        try:
            past_msgs = (
                self.db.query(Message)
                .filter(Message.chat_id == chat_id)
                .order_by(Message.id.desc())
                .limit(limit)
                .all()
            )
            past_msgs = past_msgs[::-1]

            assistant_indices = [
                idx for idx, message in enumerate(past_msgs)
                if str(getattr(message, "role", "")) == "assistant"
            ]
            latest_assistant_index = assistant_indices[-1] if assistant_indices else -1
            recent_assistant_indices = set(assistant_indices[-RECENT_ASSISTANT_MESSAGES_TO_KEEP:])

            for idx, msg in enumerate(past_msgs):
                content = msg.content or ""
                if msg.role == "assistant":
                    if idx == latest_assistant_index:
                        # Harte Regel: Der direkte Vor-Turn des Assistant bleibt immer vollständig,
                        # damit Referenzen wie "Punkt 6" zuverlässig funktionieren.
                        pass
                    elif idx in recent_assistant_indices:
                        if len(content) > RECENT_ASSISTANT_MAX_CHARS:
                            cut_len = len(content) - RECENT_ASSISTANT_MAX_CHARS
                            content = (
                                content[:RECENT_ASSISTANT_MAX_CHARS]
                                + f"\n\n... [Historie gekuerzt: {cut_len} Zeichen am Ende ausgeblendet] ..."
                            )
                    elif len(content) > OLDER_ASSISTANT_TRUNCATE_THRESHOLD:
                        cut_len = len(content) - (OLDER_ASSISTANT_HEAD_CHARS + OLDER_ASSISTANT_TAIL_CHARS)
                        content = (
                            content[:OLDER_ASSISTANT_HEAD_CHARS]
                            + f"\n\n... [Historie komprimiert: {cut_len} Zeichen ausgeblendet, um den Fokus zu halten] ...\n\n"
                            + content[-OLDER_ASSISTANT_TAIL_CHARS:]
                        )
                if len(content.strip()) > 0:
                    role = role_mapper(msg.role)
                    history_buffer.append({"role": role, "content": content})
        except Exception:
            logger.error("Error in orchestrator.context_manager.assemble_history", exc_info=True)
            history_buffer.append(
                {
                    "role": "system",
                    "content": (
                        "HINWEIS: Der Verlauf konnte nicht vollständig geladen werden. "
                        "Der folgende Antwortlauf erfolgt mit unvollständigem Kontext."
                    ),
                }
            )

        if chat_id is not None:
            try:
                recent_scan_msgs = (
                    self.db.query(Message)
                    .filter(Message.chat_id == chat_id)
                    .order_by(Message.id.desc())
                    .limit(50)
                    .all()
                )
                scan_sources = [str(msg.content or "") for msg in recent_scan_msgs]
                found_in_history = any(
                    re.search(pattern, source, re.IGNORECASE)
                    for source in scan_sources
                    for pattern in [
                        r"DATEI-UPLOAD '(.+?)\.pdf'",
                        r"SYSTEM-INSTRUKTION FÜR DATEI-UPLOAD '([^']+?)\.pdf'",
                        r"Dokument: ([^,\s]+)\.pdf",
                    ]
                )
            except Exception:
                logger.error("Error in orchestrator.context_manager.assemble_history history-scan", exc_info=True)

        audit_context = AuditContext(
            doc_name=self.resolve_audit_filename(chat_id, []),
            found_in_history=found_in_history,
        )
        context_payload = {
            "history": history_buffer,
            "memories": self._build_memories_text(chat_id=chat_id),
            "audit_context": audit_context.model_dump(),
        }
        return OrchestratorContext.model_validate(context_payload)
