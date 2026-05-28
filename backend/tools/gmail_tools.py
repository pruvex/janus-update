import base64
import json
import logging
import os.path
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import keyring
from bs4 import BeautifulSoup  # NEU: Importieren
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from backend.data.schemas_tools import ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1, tool_ok_v1
from backend.utils.paths import get_app_data_dir
from backend.utils.security_utils import secure_filename

# Configure logger
logger = logging.getLogger("janus_backend")

# Use the same SCOPES as in calendar_tools.py to maintain consistency
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Keyring Service-Namen für Google-Tokens und Client-Geheimnisse
GOOGLE_TOKEN_KEY = "janus_google_token"
GOOGLE_CLIENT_SECRETS_KEY = "janus_google_client_secrets"

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# NEU: Sicheres Verzeichnis für Anhänge
ATTACHMENT_UPLOAD_DIR = os.path.join(get_app_data_dir(), "temp_email_attachments")
os.makedirs(ATTACHMENT_UPLOAD_DIR, exist_ok=True)
logger.info(f"Sicheres Verzeichnis für E-Mail-Anhänge: {ATTACHMENT_UPLOAD_DIR}")

_MAIL_TAGS = ["email", "communication"]


def _mail_ok(
    data: dict,
    *,
    message: Optional[str] = None,
    started_at: float,
    suggest_follow_up: bool = True,
    primary_entity_id: Optional[str] = None,
) -> ToolResultV1:
    return tool_ok_v1(
        data,
        message=message,
        tags=_MAIL_TAGS,
        started_at=started_at,
        suggest_follow_up=suggest_follow_up,
        primary_entity_id=primary_entity_id,
    )


def _mail_err(code: str, message: str, *, details: Optional[dict] = None, started_at: float) -> ToolResultV1:
    return tool_err_v1(code, message, details=details, tags=_MAIL_TAGS, started_at=started_at)


def _get_google_client_secrets():
    """Ruft Client-Geheimnisse aus dem Keyring ab oder lädt sie aus der Datei und speichert sie dann im Keyring."""
    client_secrets_json = keyring.get_password(
        "janus_google_credentials", GOOGLE_CLIENT_SECRETS_KEY
    )
    if client_secrets_json:
        return json.loads(client_secrets_json)

    # Fallback: Lade aus Umgebungsvariablen und speichere im Keyring
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if client_id and client_secret:
        client_secrets = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"],
                "javascript_origins": ["http://localhost"],
            }
        }
        keyring.set_password(
            "janus_google_credentials", GOOGLE_CLIENT_SECRETS_KEY, json.dumps(client_secrets)
        )
        logger.info("Google Client-Geheimnisse aus Umgebungsvariablen geladen und im Keyring gespeichert.")
        return client_secrets

    logger.error("Google Client-Geheimnisse weder im Keyring noch in Umgebungsvariablen gefunden.")
    return None


def _get_gmail_service(expected_email: Optional[str] = None, force_select_account: bool = False):
    """Returns an authenticated Gmail service client."""
    creds = None
    token_json = keyring.get_password("janus_google_tokens", GOOGLE_TOKEN_KEY)
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except Exception as e:
            logger.warning(
                f"Fehler beim Laden des Tokens aus dem Keyring: {e}. Versuche Neuauthentifizierung."
            )
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Ensure all required scopes are in the refresh token
            if all(s in creds.scopes for s in SCOPES):
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(
                        f"Fehler beim Aktualisieren des Tokens: {e}. Versuche Neuauthentifizierung."
                    )
                    creds = None
            else:
                creds = None  # Force re-authentication if scopes are missing

    if not creds:  # Run the flow if creds is None
        client_secrets = _get_google_client_secrets()
        if not client_secrets:
            raise Exception(
                "Google Client-Geheimnisse nicht verfügbar. Bitte credentials.json bereitstellen oder im Keyring speichern."
            )

        flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
        oauth_kwargs: Dict[str, Any] = {}
        if force_select_account:
            oauth_kwargs["prompt"] = "select_account consent"
        if expected_email:
            oauth_kwargs["login_hint"] = expected_email
        creds = flow.run_local_server(port=0, **oauth_kwargs)

    # Save the updated credentials
    keyring.set_password("janus_google_tokens", GOOGLE_TOKEN_KEY, creds.to_json())
    logger.info("Google Gmail Token im Keyring gespeichert/aktualisiert.")

    service = build("gmail", "v1", credentials=creds)
    return service


def get_latest_emails(
    max_results: int = 5, query: Optional[str] = None, fetch_body: bool = False
) -> ToolResultV1:
    """
    Sucht und listet E-Mails auf. Benutze dieses Tool IMMER, wenn du E-Mails finden musst.
    Setze 'fetch_body' auf True, wenn die Anfrage des Benutzers eine Zusammenfassung, Übersetzung oder eine andere Detailanalyse des E-Mail-Inhalts erfordert.
    """
    t0 = time.perf_counter()
    try:
        service = _get_gmail_service()
        request_params = {"userId": "me", "labelIds": ["INBOX"], "maxResults": max_results}
        if query:
            request_params["q"] = query

        results = service.users().messages().list(**request_params).execute()
        messages_info = results.get("messages", [])

        if not messages_info:
            return _mail_ok(
                {"raw_emails": [], "listing_text": "", "message_count": 0},
                message="No emails found matching your criteria.",
                started_at=t0,
            )

        output_parts = ["Here are your latest emails:"]
        raw_emails_for_context = []

        for message_info in messages_info:
            msg_id = message_info["id"]

            # --- START FINAL FIX: Hole immer 'full' wenn body gebraucht wird ---
            format_type = "full" if fetch_body else "metadata"
            metadata_headers = ["From", "Subject", "Date"]

            message = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format=format_type, metadataHeaders=metadata_headers)
                .execute()
            )
            # --- END FINAL FIX ---

            payload = message.get("payload", {})
            headers = payload.get("headers", [])
            email_from, email_subject, email_date = "N/A", "N/A", "N/A"
            for header in headers:
                name = header.get("name")
                if name == "From":
                    email_from = header.get("value")
                elif name == "Subject":
                    email_subject = header.get("value")
                elif name == "Date":
                    email_date = header.get("value")

            email_snippet = message.get("snippet", "").strip()
            email_body = ""

            if fetch_body:
                if "parts" in payload:
                    for part in payload.get("parts", []):
                        if part.get("mimeType") == "text/plain":
                            data = part.get("body", {}).get("data")
                            if data:
                                email_body = base64.urlsafe_b64decode(data.encode("ASCII")).decode(
                                    "utf-8"
                                )
                                break  # Bevorzuge Plain-Text
                    # Fallback zu HTML, wenn kein Plain-Text gefunden wurde
                    if not email_body:
                        for part in payload.get("parts", []):
                            if part.get("mimeType") == "text/html":
                                data = part.get("body", {}).get("data")
                                if data:
                                    decoded_html = base64.urlsafe_b64decode(
                                        data.encode("ASCII")
                                    ).decode("utf-8")
                                    soup = BeautifulSoup(decoded_html, "html.parser")
                                    email_body = soup.get_text(separator="\n", strip=True)
                                    break
                elif "body" in payload and payload.get("body", {}).get("data"):
                    data = payload.get("body").get("data")
                    if data:
                        email_body = base64.urlsafe_b64decode(data.encode("ASCII")).decode("utf-8")

            output_parts.append(
                f"- ID: {msg_id}\n  From: {email_from}\n  Subject: {email_subject}\n  Date: {email_date}\n  Snippet: {email_snippet}"
                f"\n  Body: {email_body if email_body else 'Not fetched.'}"
            )
            raw_emails_for_context.append(
                {"id": msg_id, "from": email_from, "subject": email_subject}
            )

        listing_text = "\n\n".join(output_parts)
        return _mail_ok(
            {
                "raw_emails": raw_emails_for_context,
                "listing_text": listing_text,
                "message_count": len(raw_emails_for_context),
            },
            message=listing_text,
            started_at=t0,
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred in get_latest_emails: {e}", exc_info=True)
        return _mail_err("GMAIL_LIST_FAILED", f"An unexpected error occurred: {str(e)}", started_at=t0)


def _get_email_body(payload: Dict[str, Any]) -> str:
    """
    Rekursive Hilfsfunktion, um den Textkörper aus verschachtelten E-Mail-Teilen zu extrahieren.
    Priorisiert text/plain, fällt aber auf text/html zurück.
    """
    body = ""
    if "parts" in payload:
        # Suche zuerst nach einem Plain-Text-Teil
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                body_encoded = part.get("body", {}).get("data", "")
                if body_encoded:
                    return base64.urlsafe_b64decode(body_encoded.encode("ASCII")).decode("utf-8")
                # Wenn kein Plain-Text gefunden wurde, suche nach einem HTML-Teil
        for part in payload["parts"]:
            if part["mimeType"] == "text/html":
                body_encoded = part.get("body", {}).get("data", "")
                if body_encoded:
                    html_body = base64.urlsafe_b64decode(body_encoded.encode("ASCII")).decode(
                        "utf-8"
                    )
                    soup = BeautifulSoup(html_body, "html.parser")
                    return soup.get_text(separator="\n", strip=True)
        # Wenn immer noch nichts gefunden, rekursiv weitersuchen
        for part in payload["parts"]:
            body = _get_email_body(part)
            if body:
                return body
    elif payload.get("mimeType") == "text/plain":
        body_encoded = payload.get("body", {}).get("data", "")
        if body_encoded:
            return base64.urlsafe_b64decode(body_encoded.encode("ASCII")).decode("utf-8")
    elif payload.get("mimeType") == "text/html":
        body_encoded = payload.get("body", {}).get("data", "")
        if body_encoded:
            html_body = base64.urlsafe_b64decode(body_encoded.encode("ASCII")).decode("utf-8")
            soup = BeautifulSoup(html_body, "html.parser")
            return soup.get_text(separator="\n", strip=True)

    return body


def read_email(email_id: str, **kwargs) -> ToolResultV1:
    """
    Liest den vollständigen Inhalt einer EINZELNEN, spezifischen E-Mail.
    Benutze dieses Werkzeug IMMER UND AUSSCHLIESSLICH als Folgeschritt, NACHDEM 'get_latest_emails' eine Liste angezeigt hat und der Benutzer eine davon lesen möchte (z.B. "Lies die erste E-Mail" oder "Öffne die Mail von Facebook").
    Dieses Werkzeug ist NICHT für die Suche nach E-Mails gedacht.
    """
    t0 = time.perf_counter()
    try:
        email_list_context = kwargs.get("email_list_context")
        final_email_id = None
        llm_clue = email_id  # Der Wert, den das LLM uns gibt
        if not email_list_context:
            logger.warning(
                "read_email aufgerufen, aber kein E-Mail-Kontext gefunden. Versuche, den Hinweis direkt als ID zu verwenden."
            )
            final_email_id = llm_clue
        else:
            logger.info(f"Validiere LLM-Hinweis '{llm_clue}' anhand des E-Mail-Kontexts.")

            # 1. Versuch: Ist der Hinweis eine Positionsangabe (z.B. "1", "2")?
            try:
                position_index = int(float(llm_clue)) - 1
                if 0 <= position_index < len(email_list_context):
                    final_email_id = email_list_context[position_index]["id"]
                    logger.info(
                        f"Hinweis als Position '{llm_clue}' interpretiert. Korrekte ID ist '{final_email_id}'."
                    )
            except (ValueError, IndexError):
                # Es war keine gültige Zahl, weiter zum nächsten Versuch.
                pass

            # 2. Versuch (falls 1. fehlschlug): Ist der Hinweis ein Name im Absender oder Betreff?
            if not final_email_id:
                clue_lower = llm_clue.lower()
                possible_matches = []
                for email_data in email_list_context:
                    sender = email_data.get("from", "").lower()
                    subject = email_data.get("subject", "").lower()
                    if clue_lower in sender or clue_lower in subject:
                        possible_matches.append(email_data)

                if len(possible_matches) == 1:
                    final_email_id = possible_matches[0]["id"]
                    logger.info(
                        f"Hinweis '{llm_clue}' eindeutig im Kontext gefunden. Korrekte ID ist '{final_email_id}'."
                    )
                elif len(possible_matches) > 1:
                    logger.error(
                        f"Hinweis '{llm_clue}' ist mehrdeutig und passt auf mehrere E-Mails im Kontext."
                    )
                    return _mail_err(
                        "AMBIGUOUS_EMAIL_REFERENCE",
                        f"Die Anfrage ist mehrdeutig. Mehrere E-Mails passen auf die Beschreibung '{llm_clue}'. Bitte präzisiere deine Anfrage.",
                        started_at=t0,
                    )

            # 3. Versuch (letzte Hoffnung): Ist der Hinweis vielleicht doch eine gültige ID?
            if not final_email_id:
                if any(email["id"] == llm_clue for email in email_list_context):
                    logger.info(f"Hinweis '{llm_clue}' ist eine gültige ID aus dem Kontext.")
                    final_email_id = llm_clue

        if not final_email_id:
            logger.error(f"Konnte den Hinweis '{llm_clue}' keiner E-Mail im Kontext zuordnen.")
            return _mail_err(
                "EMAIL_NOT_IN_CONTEXT",
                f"Fehler: Ich konnte die E-Mail '{llm_clue}' in der Liste nicht finden.",
                started_at=t0,
            )

        try:
            service = _get_gmail_service()
            msg_data = (
                service.users().messages().get(userId="me", id=final_email_id, format="full").execute()
            )

            payload = msg_data.get("payload", {})
            body_data = _get_email_body(payload)
            if not body_data:
                return _mail_ok(
                    {
                        "email": None,
                        "empty_body": True,
                        "email_id": final_email_id,
                    },
                    message="Die E-Mail scheint keinen lesbaren Textinhalt zu haben.",
                    started_at=t0,
                    suggest_follow_up=False,
                    primary_entity_id=str(final_email_id),
                )

            headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

            email_payload = {
                "from": headers.get("from", "Unbekannt"),
                "subject": headers.get("subject", "Kein Betreff"),
                "date": headers.get("date", "Unbekannt"),
                "body": body_data.strip(),
            }
            return _mail_ok(
                {"email": email_payload, "email_id": final_email_id},
                started_at=t0,
                primary_entity_id=str(final_email_id),
            )

        except Exception as e:
            logger.error(f"Error reading email with ID {final_email_id}: {str(e)}", exc_info=True)
            return _mail_err("GMAIL_READ_FAILED", f"Fehler beim Lesen der E-Mail: {str(e)}", started_at=t0)
    except Exception as e:
        logger.error(f"read_email failed unexpectedly: {e}", exc_info=True)
        return _mail_err(
            "GMAIL_READ_FAILED",
            f"Fehler beim Lesen der E-Mail: {str(e)}",
            started_at=t0,
        )


def send_email(
    to: str, subject: str, body: str, attachment_path: Optional[str] = None
) -> ToolResultV1:
    """
    Benutze dieses Werkzeug IMMER, wenn der Benutzer explizit den Befehl gibt, eine E-Mail zu senden.
    Es erstellt und versendet eine E-Mail. Es kann optional eine einzelne Datei vom lokalen Dateisystem anhängen.
    Der Pfad zum Anhang muss ein absoluter Pfad sein, den der Benutzer angibt.
    """
    t0 = time.perf_counter()
    logger.info(f"Versuch, eine E-Mail zu senden an: {to}, Betreff: '{subject}'")
    if attachment_path:
        logger.info(f"Mit Anhang: {attachment_path}")

    try:
        service = _get_gmail_service()

        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject

        message.attach(MIMEText(body, "plain"))

        if attachment_path:
            # NEU: Sicherheitsprüfung für Anhangpfad
            normalized_attachment_path = os.path.normpath(attachment_path)
            if not normalized_attachment_path.startswith(os.path.normpath(ATTACHMENT_UPLOAD_DIR)):
                logger.error(
                    f"Versuch, eine Datei außerhalb des zulässigen Anhang-Verzeichnisses anzuhängen: {attachment_path}"
                )
                return _mail_err(
                    "ATTACHMENT_PATH_FORBIDDEN",
                    "Fehler: Es dürfen nur Dateien aus dem sicheren Anhang-Verzeichnis angehängt werden.",
                    started_at=t0,
                )

            if not os.path.exists(attachment_path):
                logger.error(f"Anhang-Datei nicht gefunden: {attachment_path}")
                return _mail_err(
                    "ATTACHMENT_NOT_FOUND",
                    f"Fehler: Die Anhang-Datei wurde unter '{attachment_path}' nicht gefunden.",
                    started_at=t0,
                )

            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)

            filename = secure_filename(os.path.basename(attachment_path))  # Bereinige den Dateinamen
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}",
            )
            message.attach(part)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message_body = {"raw": encoded_message}

        logger.info("Sende E-Mail über die Google-API...")
        sent_message = (
            service.users().messages().send(userId="me", body=create_message_body).execute()
        )

        message_id = sent_message.get("id")
        logger.info(f"E-Mail erfolgreich gesendet. Nachrichten-ID: {message_id}")

        return _mail_ok(
            {
                "message_id": message_id,
                "to": to,
                "subject": subject,
            },
            message=f"E-Mail an '{to}' wurde erfolgreich mit der ID '{message_id}' versendet.",
            started_at=t0,
            primary_entity_id=str(message_id) if message_id else None,
        )

    except Exception as e:
        logger.error("Fehler beim Senden der E-Mail.", exc_info=True)
        return _mail_err("GMAIL_SEND_FAILED", f"Fehler beim Senden der E-Mail: {e}", started_at=t0)
