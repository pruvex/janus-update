import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from backend.data import crud
from backend.data.models import Document
from backend.services.orchestrator.schemas import AuditContext, ExecutionResponse, SyncResult

logger = logging.getLogger("janus_backend")


class OrchestratorStatusSync:
    """Synchronizes persistence side effects (messages, audit status, response payload)."""

    def __init__(self, db: Session):
        self.db = db

    def persist_audit_status(self, audit_context: AuditContext) -> bool:
        target_status = str(audit_context.status or "").strip().lower()
        if target_status not in {"warning", "verified", "new"}:
            return False

        search_name = str(audit_context.doc_name or "").replace(".pdf", "").strip()
        if not search_name:
            return False

        try:
            candidate_docs = (
                self.db.query(Document)
                .filter(Document.filename.ilike(f"%{search_name}%"))
                .all()
            )
            if not candidate_docs:
                return False

            target_doc = next(
                (doc for doc in candidate_docs if "_korrigiert" not in str(doc.filename or "").lower()),
                candidate_docs[0],
            )
            if target_doc.audit_status == target_status:
                return False

            target_doc.audit_status = target_status
            self.db.commit()
            logger.info(
                "AUDIT-STATUS persisted via single path: doc=%s status=%s details=%s",
                target_doc.filename,
                target_status,
                audit_context.details or {},
            )
            return True
        except Exception:
            self.db.rollback()
            logger.error("Error in orchestrator.status_sync.persist_audit_status", exc_info=True)
            return False

    def persist_assistant_message(
        self,
        chat_id: Optional[int],
        execution_response: ExecutionResponse,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> SyncResult:
        if not chat_id:
            return SyncResult(status="skipped", message_id=None, success=False)
        text = str(execution_response.text or "").strip()
        image_path = str(execution_response.image_url or "").strip() or None
        modal_request = execution_response.modal_request
        if hasattr(modal_request, "model_dump"):
            try:
                modal_request = modal_request.model_dump()
            except Exception:
                modal_request = None
        if not isinstance(modal_request, dict):
            modal_request = None
        if not text and not image_path:
            return SyncResult(status="skipped", message_id=None, success=False)
        logger.info("💎 VIDEO-LIST-METADATA: persist_assistant_message: extra_metadata keys=%s", list(extra_metadata.keys()) if extra_metadata else None)
        if extra_metadata and "video_list_metadata" in extra_metadata:
            vlm = extra_metadata["video_list_metadata"]
            logger.info("💎 VIDEO-LIST-METADATA: persist_assistant_message: video_list_metadata has %d videos", len(vlm.get("videos", [])) if isinstance(vlm, dict) else 0)
        db_message = crud.create_message(
            self.db,
            chat_id,
            "assistant",
            text,
            image_path=image_path,
            metadata=extra_metadata,
            modal_request=modal_request,
        )
        return SyncResult(status="persisted", message_id=getattr(db_message, "id", None), success=True)

    def sync_execution(
        self,
        *,
        chat_id: Optional[int],
        execution_response: ExecutionResponse,
        audit_context: AuditContext,
    ) -> SyncResult:
        message_sync = self.persist_assistant_message(chat_id, execution_response)
        if audit_context.status:
            self.persist_audit_status(audit_context)
        return message_sync

    def build_api_response(
        self,
        *,
        execution_response: ExecutionResponse,
    ) -> ExecutionResponse:
        response_payload = execution_response.model_copy(deep=True)
        response_payload.sender = "model"
        if execution_response.ui_command:
            logger.info(
                ">>> ORCHESTRATOR ERFOLG: UI-Kommando '%s' wird an Frontend gesendet.",
                execution_response.ui_command.get("ui_action"),
            )
        return response_payload
