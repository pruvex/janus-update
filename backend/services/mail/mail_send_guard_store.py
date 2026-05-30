"""
In-memory guard store for chat-triggered mail send confirmations.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Dict, Optional

from backend.data.database import SessionLocal
from backend.data.models import AppState

@dataclass
class PendingMailSend:
    to: str
    subject: str
    body: str
    cc: str = ""
    bcc: str = ""
    mode: str = "new"
    context_hint: str = ""
    attachments: list[tuple[str, bytes, str | None]] | None = None


_PENDING_BY_CHAT: Dict[int, PendingMailSend] = {}
_APPSTATE_KEY_PREFIX = "mail_pending_send:"


def _serialize_pending(pending: PendingMailSend) -> str:
    attachments_payload = []
    for item in list(pending.attachments or []):
        if not isinstance(item, tuple) or len(item) < 2:
            continue
        filename = str(item[0] or "").strip()
        content = item[1]
        mime_type = item[2] if len(item) > 2 else None
        if not filename or not isinstance(content, (bytes, bytearray)):
            continue
        attachments_payload.append(
            {
                "filename": filename,
                "content_b64": base64.b64encode(bytes(content)).decode("ascii"),
                "mime_type": str(mime_type or "") or None,
            }
        )
    payload = {
        "to": pending.to,
        "subject": pending.subject,
        "body": pending.body,
        "cc": pending.cc,
        "bcc": pending.bcc,
        "mode": pending.mode,
        "context_hint": pending.context_hint,
        "attachments": attachments_payload,
    }
    return json.dumps(payload, ensure_ascii=False)


def _deserialize_pending(raw: str) -> Optional[PendingMailSend]:
    try:
        data = json.loads(str(raw or ""))
    except Exception:
        return None
    attachments: list[tuple[str, bytes, str | None]] = []
    for a in list(data.get("attachments") or []):
        if not isinstance(a, dict):
            continue
        filename = str(a.get("filename") or "").strip()
        content_b64 = str(a.get("content_b64") or "").strip()
        mime_type = str(a.get("mime_type") or "").strip() or None
        if not filename or not content_b64:
            continue
        try:
            content = base64.b64decode(content_b64.encode("ascii"))
        except Exception:
            continue
        attachments.append((filename, content, mime_type))
    return PendingMailSend(
        to=str(data.get("to") or ""),
        subject=str(data.get("subject") or ""),
        body=str(data.get("body") or ""),
        cc=str(data.get("cc") or ""),
        bcc=str(data.get("bcc") or ""),
        mode=str(data.get("mode") or "new"),
        context_hint=str(data.get("context_hint") or ""),
        attachments=attachments or None,
    )


def set_pending_mail_send(chat_id: int, pending: PendingMailSend) -> None:
    cid = int(chat_id)
    _PENDING_BY_CHAT[cid] = pending
    key = f"{_APPSTATE_KEY_PREFIX}{cid}"
    db = SessionLocal()
    try:
        row = db.query(AppState).filter(AppState.key == key).first()
        payload = _serialize_pending(pending)
        if row is None:
            db.add(AppState(key=key, value=payload))
        else:
            row.value = payload
        db.commit()
    finally:
        db.close()


def get_pending_mail_send(chat_id: int) -> Optional[PendingMailSend]:
    cid = int(chat_id)
    pending = _PENDING_BY_CHAT.get(cid)
    if pending is not None:
        return pending
    key = f"{_APPSTATE_KEY_PREFIX}{cid}"
    db = SessionLocal()
    try:
        row = db.query(AppState).filter(AppState.key == key).first()
        if row is None:
            return None
        restored = _deserialize_pending(row.value)
        if restored is not None:
            _PENDING_BY_CHAT[cid] = restored
        return restored
    finally:
        db.close()


def pop_pending_mail_send(chat_id: int) -> Optional[PendingMailSend]:
    cid = int(chat_id)
    pending = get_pending_mail_send(cid)
    _PENDING_BY_CHAT.pop(cid, None)
    key = f"{_APPSTATE_KEY_PREFIX}{cid}"
    db = SessionLocal()
    try:
        row = db.query(AppState).filter(AppState.key == key).first()
        if row is not None:
            db.delete(row)
            db.commit()
    finally:
        db.close()
    return pending
