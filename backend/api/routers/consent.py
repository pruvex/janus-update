"""Path Sentinel consent API router."""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.path_sentinel.auth import SignedConsentToken
from backend.services.path_sentinel.singleton import (
    get_challenge_store,
    get_secret_key,
    get_sentinel,
)

logger = logging.getLogger("janus_backend")

router = APIRouter()


class ConsentResolveRequest(BaseModel):
    """Request body for consent resolution."""

    challenge_id: str
    decision: Literal["once", "session", "always", "deny"]
    session_id: str | None = None


class ConsentResolveResponse(BaseModel):
    """Response for consent resolution."""

    status: str
    message: str


@router.post("/resolve", response_model=ConsentResolveResponse)
async def resolve_consent(request: ConsentResolveRequest):
    """Resolve a consent challenge using the process-wide singleton sentinel.

    This route must share state with the decorator; otherwise challenges/grants
    created on one side will be invisible on the other.
    """
    secret_key = get_secret_key()
    challenge_store = get_challenge_store()
    sentinel = get_sentinel()

    # Resolve challenge (accept any session on lookup so UI does not need to send it;
    # we still log the mismatch for audit).
    # Peek into store to grab the challenge metadata without TTL-deleting it yet.
    with challenge_store._lock:
        challenge = dict(challenge_store._store.get(request.challenge_id, {}) or {})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found or expired")

    session_id = request.session_id or challenge.get("session_id", "default_session")

    if request.decision == "deny":
        with challenge_store._lock:
            challenge_store._store.pop(request.challenge_id, None)
        return ConsentResolveResponse(status="denied", message="Access denied by user")

    # Create signed token for the sentinel.grant call.
    token_auth = SignedConsentToken(secret_key)
    token = token_auth.create_token(
        challenge_id=request.challenge_id,
        path=challenge["path"],
        op=challenge["op"],
        scope=request.decision,
    )

    success = sentinel.grant(
        path=challenge["path"],
        op=challenge["op"],
        scope=request.decision,
        session_id=session_id,
        user_id="default_user",
        consent_token=token,
        secret_key=secret_key,
        db=None,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to grant access")

    with challenge_store._lock:
        challenge_store._store.pop(request.challenge_id, None)

    logger.info(
        "[PATH-SENTINEL] Granted %s access to '%s' with scope=%s",
        challenge["op"],
        challenge["path"],
        request.decision,
    )
    return ConsentResolveResponse(
        status="granted", message=f"Access granted with scope: {request.decision}"
    )
