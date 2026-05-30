"""
Mail API router for Janus Mail bootstrap state.
"""

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from backend.data.schemas_mail import (
    MailAccountConnectRequest,
    MailAiAnalyzeRequest,
    MailAiAnalyzeResponse,
    MailAiDraftRequest,
    MailAiDraftResponse,
    MailAiSettingsRequest,
    MailConnectionStatus,
    MailMessageActionResult,
    MailMessageDetail,
    MailMessageMoveRequest,
    MailThreadListResponse,
)
from backend.services.mail import MailService
from backend.services.mail.mail_ai_assist_service import MailAiAssistService
from backend.services.mail.mail_service import MailServiceError

logger = logging.getLogger("janus_backend.mail_router")

router = APIRouter(prefix="/mail", tags=["mail"])
_mail_service = MailService()
_mail_ai_service = MailAiAssistService()


@router.get("/sync/status", response_model=MailConnectionStatus)
async def get_mail_sync_status() -> MailConnectionStatus:
    """
    Return Gmail connection state for Janus Mail shell bootstrap.
    """
    try:
        result = _mail_service.get_connection_status()
        logger.info("[MAIL] sync/status -> status=%s account=%s", result.status, result.account_hint)
        return result
    except Exception as exc:
        logger.error("Error while resolving mail sync status: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve mail connection status.",
        )


@router.get("/threads", response_model=MailThreadListResponse)
async def get_mail_threads(
    folder: str = "inbox",
    q: str | None = None,
    max_results: int = 20,
    page_token: str | None = None,
) -> MailThreadListResponse:
    """
    Return inbox thread rows for Janus Mail shell.
    """
    try:
        result = _mail_service.list_inbox_threads(
            folder=folder,
            query=q,
            max_results=max_results,
            page_token=page_token,
        )
        threads = result.get("threads", []) if isinstance(result, dict) else result.threads
        next_page = result.get("next_page_token") if isinstance(result, dict) else result.next_page_token
        logger.info(
            "[MAIL] threads -> folder=%s q=%s count=%s next=%s",
            folder,
            (q or "").strip()[:80],
            len(threads),
            bool(next_page),
        )
        return result
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while resolving mail inbox threads: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load inbox threads.",
        ) from exc


@router.get("/messages/{message_id}", response_model=MailMessageDetail)
async def get_mail_message_detail(message_id: str) -> MailMessageDetail:
    """
    Return full message detail for right-side preview panel.
    """
    try:
        return _mail_service.get_message_detail(message_id)
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while resolving mail message detail: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load mail message detail.",
        ) from exc


@router.post("/messages/{message_id}/trash", response_model=MailMessageActionResult)
async def trash_mail_message(message_id: str) -> MailMessageActionResult:
    try:
        return _mail_service.trash_message(message_id)
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while trashing mail message: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trash mail message.",
        ) from exc


@router.post("/messages/{message_id}/move", response_model=MailMessageActionResult)
async def move_mail_message(message_id: str, body: MailMessageMoveRequest) -> MailMessageActionResult:
    try:
        return _mail_service.move_message(message_id, body.target_folder)
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while moving mail message: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to move mail message.",
        ) from exc


@router.get("/messages/{message_id}/attachments/{attachment_id}")
async def download_mail_attachment(message_id: str, attachment_id: str) -> Response:
    try:
        payload = _mail_service.download_attachment(message_id, attachment_id)
        filename = str(payload.get("filename") or "attachment.bin")
        mime_type = str(payload.get("mime_type") or "application/octet-stream")
        content = payload.get("content") or b""
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=content, media_type=mime_type, headers=headers)
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while downloading mail attachment: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download mail attachment.",
        ) from exc


@router.post("/messages/send", response_model=MailMessageActionResult)
async def send_mail_message(
    to: str = Form(...),
    subject: str = Form(""),
    body: str = Form(""),
    cc: str = Form(""),
    bcc: str = Form(""),
    in_reply_to: str = Form(""),
    references: str = Form(""),
    source_message_id: str = Form(""),
    include_original_attachments: bool = Form(False),
    attachments: list[UploadFile] = File(default_factory=list),
) -> MailMessageActionResult:
    try:
        prepared_attachments: list[tuple[str, bytes, str | None]] = []
        for file in attachments:
            content = await file.read()
            prepared_attachments.append((file.filename or "attachment.bin", content, file.content_type))
        return _mail_service.send_message(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            in_reply_to=in_reply_to,
            references=references,
            source_message_id=source_message_id,
            include_original_attachments=include_original_attachments,
            attachments=prepared_attachments,
        )
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while sending mail message: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send mail message.",
        ) from exc


@router.post("/disconnect", response_model=MailMessageActionResult)
async def disconnect_mail_account() -> MailMessageActionResult:
    try:
        _mail_service.disconnect_account()
        logger.info("[MAIL] disconnect -> ok")
        return MailMessageActionResult(
            ok=True,
            message="Gmail-Verbindung getrennt.",
            message_id="account",
            target_folder=None,
        )
    except Exception as exc:
        logger.error("Error while disconnecting mail account: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect mail account.",
        ) from exc


@router.post("/accounts/connect", response_model=MailConnectionStatus)
async def connect_mail_account(body: MailAccountConnectRequest) -> MailConnectionStatus:
    try:
        logger.info("[MAIL] connect requested -> email=%s", body.email)
        result = _mail_service.connect_account(body.email)
        logger.info("[MAIL] connect success -> account=%s", result.account_hint)
        return result
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while connecting mail account: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect mail account.",
        ) from exc


@router.post("/accounts/activate", response_model=MailConnectionStatus)
async def activate_mail_account(body: MailAccountConnectRequest) -> MailConnectionStatus:
    try:
        logger.info("[MAIL] activate requested -> email=%s", body.email)
        result = _mail_service.activate_account(body.email)
        logger.info("[MAIL] activate success -> account=%s", result.account_hint)
        return result
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        logger.error("Error while activating mail account: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate mail account: {exc}",
        ) from exc


@router.post("/ai/settings")
async def set_mail_ai_settings(body: MailAiSettingsRequest) -> dict:
    try:
        return _mail_ai_service.set_settings(
            global_enabled=body.global_enabled,
            thread_id=body.thread_id,
            thread_enabled=body.thread_enabled,
        )
    except Exception as exc:
        logger.error("Error while setting mail ai settings: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save AI settings.") from exc


@router.post("/ai/analyze", response_model=MailAiAnalyzeResponse)
async def analyze_mail_thread(body: MailAiAnalyzeRequest) -> MailAiAnalyzeResponse:
    try:
        if not _mail_ai_service.is_thread_allowed(body.message_id):
            raise HTTPException(status_code=403, detail="AI Mail Assist ist fuer diesen Thread nicht freigegeben.")
        detail = _mail_service.get_message_detail(body.message_id)
        return await _mail_ai_service.analyze_with_llm(detail.model_dump())
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error while analyzing mail thread: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to analyze mail thread.") from exc


@router.post("/ai/draft", response_model=MailAiDraftResponse)
async def draft_mail_reply(body: MailAiDraftRequest) -> MailAiDraftResponse:
    try:
        if not _mail_ai_service.is_thread_allowed(body.message_id):
            raise HTTPException(status_code=403, detail="AI Mail Assist ist fuer diesen Thread nicht freigegeben.")
        detail = _mail_service.get_message_detail(body.message_id)
        return await _mail_ai_service.draft_with_llm(detail.model_dump(), body.tone)
    except MailServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error while drafting mail reply: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to draft mail reply.") from exc
