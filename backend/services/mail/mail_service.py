"""
Mail service bootstrap for Janus Mail connection-state handling.
"""

import json
import logging
import os
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.message import EmailMessage
from typing import Dict, Optional, Tuple

import keyring
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from backend.data.schemas_mail import (
    MailAttachmentSummary,
    MailConnectionStatus,
    MailMessageActionResult,
    MailMessageDetail,
    MailThreadListResponse,
    MailThreadSummary,
)
from backend.tools.gmail_tools import GOOGLE_TOKEN_KEY, SCOPES, _get_gmail_service
from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend.mail_service")


class MailServiceError(Exception):
    def __init__(self, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class MailService:
    """Service layer for Mail bootstrap and connection-state evaluation."""

    TOKEN_KEYRING_SERVICE = "janus_google_tokens"
    TOKENS_STORE_FILE = os.path.join(get_app_data_dir(), "mail_accounts_v2.json")
    FOLDER_LABELS = {
        "inbox": "INBOX",
        "sent": "SENT",
        "drafts": "DRAFT",
        "trash": "TRASH",
    }

    @staticmethod
    def _token_key_for_email(email: str) -> str:
        return f"{GOOGLE_TOKEN_KEY}::{email}"

    def _load_tokens_store(self) -> Dict:
        if not os.path.exists(self.TOKENS_STORE_FILE):
            return {"active_email": "", "accounts": []}
        try:
            with open(self.TOKENS_STORE_FILE, "r", encoding="utf-8") as f:
                parsed = json.load(f)
        except Exception:
            return {"active_email": "", "accounts": []}
        if not isinstance(parsed, dict):
            return {"active_email": "", "accounts": []}
        active_email = str(parsed.get("active_email") or "").strip().lower()
        accounts = parsed.get("accounts")
        if not isinstance(accounts, list):
            accounts = []
        accounts = [str(a).strip().lower() for a in accounts if isinstance(a, str) and "@" in a]
        return {"active_email": active_email, "accounts": accounts}

    def get_known_accounts(self) -> tuple[list[str], str]:
        store = self._load_tokens_store()
        accounts = list(store.get("accounts") or [])
        active = str(store.get("active_email") or "").strip().lower()
        return accounts, active

    def _save_tokens_store(self, payload: Dict) -> None:
        os.makedirs(os.path.dirname(self.TOKENS_STORE_FILE), exist_ok=True)
        active_email = str(payload.get("active_email") or "").strip().lower()
        accounts = payload.get("accounts")
        if not isinstance(accounts, list):
            accounts = []
        accounts = [str(a).strip().lower() for a in accounts if isinstance(a, str) and "@" in a]
        with open(self.TOKENS_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"active_email": active_email, "accounts": accounts}, f, ensure_ascii=False)

    def _get_active_token_json(self) -> tuple[str | None, str]:
        store = self._load_tokens_store()
        active_email = str(store.get("active_email") or "").strip().lower()
        accounts = list(store.get("accounts") or [])
        logger.info("[MAIL] token-store state -> active=%s accounts=%d", active_email or "-", len(accounts))
        if not active_email and accounts:
            active_email = accounts[0]
            self._save_tokens_store({"active_email": active_email, "accounts": accounts})
            logger.info("[MAIL] token-store auto-activate first account -> %s", active_email)
        if active_email:
            token = keyring.get_password(self.TOKEN_KEYRING_SERVICE, self._token_key_for_email(active_email))
            if token:
                logger.info("[MAIL] token source -> per-account key for %s", active_email)
                return token, active_email
            logger.warning("[MAIL] active account token missing -> %s", active_email)
            return None, active_email
        legacy = keyring.get_password(self.TOKEN_KEYRING_SERVICE, GOOGLE_TOKEN_KEY)
        if legacy:
            logger.info("[MAIL] token source -> legacy single token")
            return legacy, ""
        return None, ""

    def _persist_refreshed_token(self, active_email: str, token_json: str) -> None:
        email = str(active_email or "").strip().lower()
        if not email:
            return
        try:
            keyring.set_password(self.TOKEN_KEYRING_SERVICE, self._token_key_for_email(email), token_json)
        except Exception:
            pass

    def _ensure_account_in_store(self, email: str, token_json: str) -> None:
        normalized = str(email or "").strip().lower()
        if not normalized or "@" not in normalized:
            return
        store = self._load_tokens_store()
        accounts = list(store.get("accounts") or [])
        if normalized not in accounts:
            accounts.append(normalized)
        active = str(store.get("active_email") or "").strip().lower() or normalized
        self._save_tokens_store({"active_email": active, "accounts": accounts})
        try:
            keyring.set_password(self.TOKEN_KEYRING_SERVICE, self._token_key_for_email(normalized), token_json)
        except Exception:
            pass

    def get_connection_status(self) -> MailConnectionStatus:
        token_json, active_email = self._get_active_token_json()
        if not token_json:
            return MailConnectionStatus(status="disconnected", error_message="No Gmail token configured.")
        try:
            token_info = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as exc:
            logger.warning("Failed to parse Gmail credentials from keyring: %s", exc)
            return MailConnectionStatus(
                status="sync_error",
                account_hint=active_email or None,
                error_message="Stored Gmail credentials are invalid.",
            )
        has_scopes, missing_scopes = self._has_required_scopes(creds)
        if not has_scopes:
            return MailConnectionStatus(
                status="missing_scope",
                error_message=f"Missing required Gmail scopes: {', '.join(missing_scopes)}",
            )
        resolved_hint = self._resolve_account_hint(creds, token_info)
        account_hint = resolved_hint or active_email
        if account_hint:
            self._ensure_account_in_store(account_hint, token_json)
        if creds.valid or (creds.expired and creds.refresh_token):
            return MailConnectionStatus(status="connected", account_hint=account_hint)
        return MailConnectionStatus(
            status="sync_error",
            account_hint=account_hint,
            error_message="Gmail token exists but is not currently usable.",
        )

    def disconnect_account(self) -> None:
        store = self._load_tokens_store()
        accounts = list(store.get("accounts") or [])
        self._save_tokens_store({"active_email": "", "accounts": accounts})
        try:
            keyring.delete_password(self.TOKEN_KEYRING_SERVICE, GOOGLE_TOKEN_KEY)
        except Exception:
            pass

    def connect_account(self, expected_email: str) -> MailConnectionStatus:
        desired = str(expected_email or "").strip().lower()
        if not desired or "@" not in desired:
            raise MailServiceError("Bitte eine gueltige E-Mail-Adresse eingeben.", status_code=400)
        try:
            keyring.delete_password(self.TOKEN_KEYRING_SERVICE, GOOGLE_TOKEN_KEY)
        except Exception:
            pass
        try:
            service = _get_gmail_service(expected_email=desired, force_select_account=True)
            profile = service.users().getProfile(userId="me").execute() or {}
        except Exception as exc:
            logger.warning("Gmail connect flow failed: %s", exc)
            raise MailServiceError("Google-Verbindung konnte nicht aufgebaut werden.", status_code=500) from exc
        connected = str(profile.get("emailAddress") or "").strip().lower()
        if not connected:
            raise MailServiceError("Google-Konto konnte nicht eindeutig ermittelt werden.", status_code=500)
        if connected != desired:
            try:
                keyring.delete_password(self.TOKEN_KEYRING_SERVICE, GOOGLE_TOKEN_KEY)
            except Exception:
                pass
            raise MailServiceError(
                f"Verbundenes Konto '{connected}' passt nicht zu '{desired}'. Bitte erneut mit dem gewuenschten Konto anmelden.",
                status_code=409,
            )
        latest_token_json = keyring.get_password(self.TOKEN_KEYRING_SERVICE, GOOGLE_TOKEN_KEY)
        if not latest_token_json:
            raise MailServiceError("Google-Token konnte nicht gespeichert werden.", status_code=500)
        store = self._load_tokens_store()
        accounts = list(store.get("accounts") or [])
        if connected not in accounts:
            accounts.append(connected)
        try:
            keyring.set_password(self.TOKEN_KEYRING_SERVICE, self._token_key_for_email(connected), latest_token_json)
        except Exception as exc:
            raise MailServiceError(f"Token konnte nicht gespeichert werden: {exc}", status_code=500) from exc
        self._save_tokens_store({"active_email": connected, "accounts": accounts})
        return MailConnectionStatus(status="connected", provider="gmail", account_hint=connected)

    def activate_account(self, email: str) -> MailConnectionStatus:
        target = str(email or "").strip().lower()
        if not target or "@" not in target:
            raise MailServiceError("Bitte eine gueltige E-Mail-Adresse eingeben.", status_code=400)
        store = self._load_tokens_store()
        accounts = list(store.get("accounts") or [])
        token_json = keyring.get_password(self.TOKEN_KEYRING_SERVICE, self._token_key_for_email(target))
        if not token_json:
            legacy = keyring.get_password(self.TOKEN_KEYRING_SERVICE, GOOGLE_TOKEN_KEY)
            if legacy:
                try:
                    token_info = json.loads(legacy)
                    creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                    resolved = str(self._resolve_account_hint(creds, token_info) or "").strip().lower()
                    if resolved == target:
                        token_json = legacy
                        try:
                            keyring.set_password(
                                self.TOKEN_KEYRING_SERVICE,
                                self._token_key_for_email(target),
                                legacy,
                            )
                        except Exception:
                            pass
                except Exception:
                    token_json = None
        # Validate token payload before activating account. Invalid payloads should
        # trigger reconnect path in frontend (404 -> accounts/connect).
        if token_json:
            try:
                token_info = json.loads(token_json)
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
                has_scopes, _missing_scopes = self._has_required_scopes(creds)
                if not has_scopes:
                    token_json = None
            except Exception:
                token_json = None

        if not token_json:
            # Cleanup stale/invalid token entry for this account key.
            try:
                keyring.delete_password(self.TOKEN_KEYRING_SERVICE, self._token_key_for_email(target))
            except Exception:
                pass
            raise MailServiceError(f"Konto '{target}' ist nicht gespeichert.", status_code=404)
        if target not in accounts:
            accounts.append(target)
        self._save_tokens_store({"active_email": target, "accounts": accounts})
        logger.info("[MAIL] activate applied -> active=%s accounts=%d", target, len(accounts))
        return MailConnectionStatus(status="connected", provider="gmail", account_hint=target)

    def _resolve_account_hint(self, creds: Credentials, token_info: dict) -> str | None:
        try:
            service = build("gmail", "v1", credentials=creds)
            profile = service.users().getProfile(userId="me").execute() or {}
            email = str(profile.get("emailAddress") or "").strip()
            if email:
                return email
        except Exception:
            pass
        for key in ("email", "email_address", "account_email", "client_id"):
            value = str(token_info.get(key) or "").strip()
            if value:
                return value
        return None

    @staticmethod
    def _has_required_scopes(creds: Credentials) -> Tuple[bool, list[str]]:
        current_scopes = set(getattr(creds, "scopes", []) or [])
        missing_scopes = [scope for scope in SCOPES if scope not in current_scopes]
        return len(missing_scopes) == 0, missing_scopes

    def _get_existing_credentials(self) -> tuple[Credentials, Dict]:
        token_json, active_email = self._get_active_token_json()
        if not token_json:
            raise MailServiceError("No Gmail token configured.", status_code=400)
        try:
            token_info = json.loads(token_json)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as exc:
            logger.warning("Failed to parse Gmail credentials from keyring: %s", exc)
            raise MailServiceError("Stored Gmail credentials are invalid.", status_code=400) from exc
        has_scopes, missing_scopes = self._has_required_scopes(creds)
        if not has_scopes:
            raise MailServiceError(
                f"Missing required Gmail scopes: {', '.join(missing_scopes)}",
                status_code=400,
            )
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    refreshed = creds.to_json()
                    self._persist_refreshed_token(active_email, refreshed)
                except Exception as exc:
                    logger.warning("Failed to refresh Gmail credentials: %s", exc)
                    raise MailServiceError(
                        "Gmail token refresh failed. Please reconnect Gmail.",
                        status_code=503,
                    ) from exc
            else:
                raise MailServiceError("Gmail token exists but is not currently usable.", status_code=503)
        return creds, token_info

    @staticmethod
    def _extract_header(message: Dict, header_name: str) -> str:
        headers = (message.get("payload") or {}).get("headers") or []
        for header in headers:
            if str(header.get("name", "")).lower() == header_name.lower():
                return str(header.get("value", ""))
        return ""

    @staticmethod
    def _has_attachments(message: Dict) -> bool:
        payload = message.get("payload") or {}

        def walk(part: Dict) -> bool:
            if not isinstance(part, dict):
                return False
            filename = str(part.get("filename") or "").strip()
            body = part.get("body") or {}
            attachment_id = str(body.get("attachmentId") or "").strip()
            mime_type = str(part.get("mimeType") or "").strip().lower()
            # Gmail may have attachment parts without filename (inline/forwarded cases).
            # Treat any non-text part with attachmentId as attachment.
            if attachment_id and (filename or mime_type not in {"text/plain", "text/html"}):
                return True
            for child in part.get("parts") or []:
                if walk(child):
                    return True
            return False

        return walk(payload)

    def list_inbox_threads(
        self,
        *,
        folder: str = "inbox",
        query: Optional[str] = None,
        max_results: int = 20,
        page_token: Optional[str] = None,
    ) -> MailThreadListResponse:
        folder_key = str(folder or "inbox").strip().lower()
        label_id = self.FOLDER_LABELS.get(folder_key)
        if not label_id:
            raise MailServiceError(f"Unsupported mail folder: {folder}", status_code=400)
        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)
        req = {"userId": "me", "labelIds": [label_id], "maxResults": max(1, min(int(max_results), 50))}
        if query:
            req["q"] = query
        if page_token:
            req["pageToken"] = page_token
        results = service.users().messages().list(**req).execute()
        messages = results.get("messages", []) or []
        threads: list[MailThreadSummary] = []
        for message_info in messages:
            msg_id = str(message_info.get("id", "")).strip()
            if not msg_id:
                continue
            message = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
            threads.append(
                MailThreadSummary(
                    id=msg_id,
                    from_display=self._extract_header(message, "From"),
                    subject=self._extract_header(message, "Subject"),
                    date=self._extract_header(message, "Date"),
                    internal_date_ms=int(str(message.get("internalDate") or "0") or 0),
                    snippet=str(message.get("snippet", "") or ""),
                    unread="UNREAD" in (message.get("labelIds") or []),
                    has_attachments=self._has_attachments(message),
                )
            )
        return MailThreadListResponse(provider="gmail", threads=threads, next_page_token=results.get("nextPageToken"))

    def get_message_detail(self, message_id: str) -> MailMessageDetail:
        msg_id = str(message_id or "").strip()
        if not msg_id:
            raise MailServiceError("Message id is required.", status_code=400)
        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)
        message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        payload = message.get("payload") or {}
        return MailMessageDetail(
            id=msg_id,
            from_display=self._extract_header(message, "From"),
            to_display=self._extract_header(message, "To"),
            subject=self._extract_header(message, "Subject"),
            date=self._extract_header(message, "Date"),
            snippet=str(message.get("snippet", "") or ""),
            body_text=self._extract_body_text(payload),
            message_id_header=self._extract_header(message, "Message-ID"),
            references_header=self._extract_header(message, "References"),
            attachments=self._collect_attachments(payload),
        )

    def _collect_attachments(self, payload: Dict) -> list[MailAttachmentSummary]:
        collected: list[MailAttachmentSummary] = []

        def walk(part: Dict) -> None:
            if not isinstance(part, dict):
                return
            filename = str(part.get("filename") or "").strip()
            body = part.get("body") or {}
            attachment_id = str(body.get("attachmentId") or "").strip()
            if filename and attachment_id:
                collected.append(
                    MailAttachmentSummary(
                        attachment_id=attachment_id,
                        filename=filename,
                        mime_type=str(part.get("mimeType") or "application/octet-stream"),
                        size=int(body.get("size") or 0),
                    )
                )
            for child in part.get("parts") or []:
                walk(child)

        walk(payload or {})
        return collected

    def _find_attachment_metadata(self, payload: Dict, attachment_id: str) -> tuple[str, str]:
        target = str(attachment_id or "").strip()
        filename = "attachment.bin"
        mime_type = "application/octet-stream"

        def walk(part: Dict) -> bool:
            nonlocal filename, mime_type
            body = part.get("body") or {}
            aid = str(body.get("attachmentId") or "").strip()
            if aid and aid == target:
                filename = str(part.get("filename") or filename)
                mime_type = str(part.get("mimeType") or mime_type)
                return True
            for child in part.get("parts") or []:
                if isinstance(child, dict) and walk(child):
                    return True
            return False

        walk(payload or {})
        return filename, mime_type

    def download_attachment(self, message_id: str, attachment_id: str) -> Dict:
        msg_id = str(message_id or "").strip()
        att_id = str(attachment_id or "").strip()
        if not msg_id or not att_id:
            raise MailServiceError("Message id and attachment id are required.", status_code=400)
        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)
        message = service.users().messages().get(userId="me", id=msg_id, format="full").execute() or {}
        payload = message.get("payload") or {}
        filename, mime_type = self._find_attachment_metadata(payload, att_id)
        attachment = (
            service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=msg_id, id=att_id)
            .execute()
            or {}
        )
        data = str(attachment.get("data") or "").strip()
        if not data:
            raise MailServiceError("Attachment payload is empty.", status_code=404)
        content = urlsafe_b64decode(data.encode("ascii"))
        return {"filename": filename, "mime_type": mime_type, "content": content}

    def _extract_body_text(self, payload: Dict) -> str:
        body = ""
        parts = payload.get("parts") or []
        if parts:
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    data = ((part.get("body") or {}).get("data") or "").strip()
                    if data:
                        return urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
            for part in parts:
                if part.get("mimeType") == "text/html":
                    data = ((part.get("body") or {}).get("data") or "").strip()
                    if data:
                        html = urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
                        return BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)
            for part in parts:
                body = self._extract_body_text(part)
                if body:
                    return body
        elif payload.get("mimeType") == "text/plain":
            data = ((payload.get("body") or {}).get("data") or "").strip()
            if data:
                return urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
        elif payload.get("mimeType") == "text/html":
            data = ((payload.get("body") or {}).get("data") or "").strip()
            if data:
                html = urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
                return BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)
        return body

    def trash_message(self, message_id: str) -> MailMessageActionResult:
        msg_id = str(message_id or "").strip()
        if not msg_id:
            raise MailServiceError("Message id is required.", status_code=400)
        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)
        service.users().messages().trash(userId="me", id=msg_id).execute()
        return MailMessageActionResult(
            ok=True,
            message_id=msg_id,
            message="Mail wurde in den Papierkorb verschoben.",
            target_folder="trash",
        )

    def move_message(self, message_id: str, target_folder: str) -> MailMessageActionResult:
        msg_id = str(message_id or "").strip()
        if not msg_id:
            raise MailServiceError("Message id is required.", status_code=400)
        folder_key = str(target_folder or "").strip().lower()
        if folder_key == "archive":
            creds, _token_info = self._get_existing_credentials()
            service = build("gmail", "v1", credentials=creds)
            # Gmail archive = remove INBOX label without moving to TRASH.
            service.users().messages().modify(
                userId="me",
                id=msg_id,
                body={"removeLabelIds": ["INBOX"]},
            ).execute()
            return MailMessageActionResult(
                ok=True,
                message_id=msg_id,
                message="Mail wurde archiviert.",
                target_folder="archive",
            )
        label_id = self.FOLDER_LABELS.get(folder_key)
        if not label_id:
            raise MailServiceError(f"Unsupported target folder: {target_folder}", status_code=400)
        if folder_key == "trash":
            return self.trash_message(msg_id)
        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)
        remove_labels = [v for k, v in self.FOLDER_LABELS.items() if k != folder_key]
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"addLabelIds": [label_id], "removeLabelIds": remove_labels},
        ).execute()
        return MailMessageActionResult(
            ok=True,
            message_id=msg_id,
            message=f"Mail wurde nach {folder_key} verschoben.",
            target_folder=folder_key,
        )

    @staticmethod
    def _split_recipients(raw: str) -> list[str]:
        text = str(raw or "").replace(";", ",")
        items = [x.strip() for x in text.split(",")]
        return [x for x in items if x and "@" in x]

    def send_message(
        self,
        *,
        to: str,
        subject: str = "",
        body: str = "",
        cc: str = "",
        bcc: str = "",
        attachments: Optional[list[tuple[str, bytes, str | None]]] = None,
        in_reply_to: str = "",
        references: str = "",
        source_message_id: str = "",
        include_original_attachments: bool = False,
    ) -> MailMessageActionResult:
        to_list = self._split_recipients(to)
        cc_list = self._split_recipients(cc)
        bcc_list = self._split_recipients(bcc)
        if not to_list:
            raise MailServiceError("Mindestens ein Empfaenger (To) ist erforderlich.", status_code=400)

        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)

        msg = EmailMessage()
        msg["To"] = ", ".join(to_list)
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        if bcc_list:
            msg["Bcc"] = ", ".join(bcc_list)
        msg["Subject"] = str(subject or "")
        if str(in_reply_to or "").strip():
            msg["In-Reply-To"] = str(in_reply_to).strip()
        if str(references or "").strip():
            msg["References"] = str(references).strip()
        msg.set_content(str(body or ""))

        merged_attachments: list[tuple[str, bytes, str | None]] = list(attachments or [])
        if include_original_attachments and str(source_message_id or "").strip():
            merged_attachments.extend(self._load_attachments_from_message(str(source_message_id).strip(), service))
        for filename, content, content_type in merged_attachments:
            if not content:
                continue
            guessed = str(content_type or "application/octet-stream")
            if "/" in guessed:
                maintype, subtype = guessed.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"
            msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=str(filename or "attachment.bin"))

        raw = urlsafe_b64encode(msg.as_bytes()).decode("ascii")
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute() or {}
        msg_id = str(sent.get("id") or "sent")
        return MailMessageActionResult(
            ok=True,
            message_id=msg_id,
            message="E-Mail wurde gesendet.",
            target_folder="sent",
        )

    def verify_message_in_sent(self, message_id: str) -> bool:
        msg_id = str(message_id or "").strip()
        if not msg_id:
            return False
        creds, _token_info = self._get_existing_credentials()
        service = build("gmail", "v1", credentials=creds)
        message = service.users().messages().get(userId="me", id=msg_id, format="minimal").execute() or {}
        labels = set(message.get("labelIds") or [])
        return "SENT" in labels

    def _load_attachments_from_message(
        self,
        source_message_id: str,
        service,
    ) -> list[tuple[str, bytes, str | None]]:
        message = service.users().messages().get(userId="me", id=source_message_id, format="full").execute() or {}
        payload = message.get("payload") or {}
        parts: list[dict] = []

        def walk(part: Dict) -> None:
            if not isinstance(part, dict):
                return
            filename = str(part.get("filename") or "").strip()
            body = part.get("body") or {}
            has_data = bool(str(body.get("data") or "").strip())
            has_attachment_id = bool(str(body.get("attachmentId") or "").strip())
            if filename and (has_data or has_attachment_id):
                parts.append(part)
            for child in part.get("parts") or []:
                walk(child)

        walk(payload)
        loaded: list[tuple[str, bytes, str | None]] = []
        for part in parts:
            filename = str(part.get("filename") or "attachment.bin")
            mime_type = str(part.get("mimeType") or "application/octet-stream")
            body = part.get("body") or {}
            data = str(body.get("data") or "").strip()
            attachment_id = str(body.get("attachmentId") or "").strip()
            if not data and attachment_id:
                attachment = (
                    service.users()
                    .messages()
                    .attachments()
                    .get(userId="me", messageId=source_message_id, id=attachment_id)
                    .execute()
                    or {}
                )
                data = str(attachment.get("data") or "").strip()
            if not data:
                continue
            try:
                content = urlsafe_b64decode(data.encode("ascii"))
            except Exception:
                continue
            loaded.append((filename, content, mime_type))
        return loaded

    def find_latest_message_by_sender(self, sender_query: str, *, folder: str = "inbox") -> Optional[MailMessageDetail]:
        query = str(sender_query or "").strip().lower()
        if not query:
            return None
        rows = self.list_inbox_threads(folder=folder, max_results=25).threads
        for row in rows:
            from_text = str(row.from_display or "").lower()
            if query in from_text:
                try:
                    return self.get_message_detail(row.id)
                except Exception:
                    return None
        return None
