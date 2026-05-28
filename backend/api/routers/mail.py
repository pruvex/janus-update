"""
Mail API router for Janus Mail bootstrap state.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.data.schemas_mail import (
    MailAccountConnectRequest,
    MailConnectionStatus,
    MailMessageActionResult,
    MailMessageDetail,
    MailMessageMoveRequest,
    MailThreadListResponse,
)
from backend.services.mail import MailService
from backend.services.mail.mail_service import MailServiceError

logger = logging.getLogger("janus_backend.mail_router")

router = APIRouter(prefix="/mail", tags=["mail"])
_mail_service = MailService()


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
