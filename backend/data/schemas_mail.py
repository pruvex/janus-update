"""
Pydantic Schemas for Janus Mail bootstrap and connection status.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MailConnectionStatus(BaseModel):
    """
    Compact mail connection status contract for the Mail shell.
    """

    status: Literal["connected", "disconnected", "missing_scope", "sync_error"] = Field(
        ...,
        description="Resolved Gmail connection state for the Mail module.",
    )
    provider: Literal["gmail"] = Field("gmail")
    account_hint: Optional[str] = Field(
        None,
        description="Optional account hint for UI visibility, never a secret.",
    )
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(
        None,
        description="Human-readable status reason without sensitive data.",
    )


class MailThreadSummary(BaseModel):
    """
    Compact Inbox thread row for Janus Mail shell.
    """

    id: str = Field(..., description="Gmail message ID used as thread row handle for now.")
    from_display: str = Field("", description="Raw From header value.")
    subject: str = Field("", description="Mail subject line.")
    date: str = Field("", description="Raw Date header value.")
    snippet: str = Field("", description="Gmail snippet preview.")
    unread: bool = Field(False, description="Whether the message is currently unread.")


class MailThreadListResponse(BaseModel):
    """
    Inbox list response for Janus Mail shell phase.
    """

    provider: Literal["gmail"] = Field("gmail")
    threads: list[MailThreadSummary] = Field(default_factory=list)
    next_page_token: Optional[str] = Field(
        None,
        description="Pagination token for follow-up list request.",
    )


class MailMessageDetail(BaseModel):
    """
    Full message detail for right-side preview panel.
    """

    id: str = Field(...)
    from_display: str = Field("")
    to_display: str = Field("")
    subject: str = Field("")
    date: str = Field("")
    snippet: str = Field("")
    body_text: str = Field("")


class MailMessageMoveRequest(BaseModel):
    target_folder: Literal["inbox", "sent", "drafts", "trash"] = Field(...)


class MailMessageActionResult(BaseModel):
    ok: bool = Field(True)
    message: str = Field("")
    message_id: str = Field(...)
    target_folder: Optional[str] = Field(None)


class MailAccountConnectRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=320)
