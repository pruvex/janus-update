import hashlib
import json
import os
import re
from typing import Any

import keyring
from backend.data.schemas_mail import MailAiAnalyzeResponse, MailAiDraftResponse
from backend.services import llm_gateway
from backend.utils.config_loader import load_config_data
from backend.utils.paths import get_app_data_dir


class MailAiAssistService:
    SETTINGS_FILE = os.path.join(get_app_data_dir(), "mail_ai_assist_settings_v1.json")

    def _load(self) -> dict[str, Any]:
        if not os.path.exists(self.SETTINGS_FILE):
            return {"global_enabled": False, "threads": {}}
        try:
            with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {"global_enabled": False, "threads": {}}
        if not isinstance(data, dict):
            return {"global_enabled": False, "threads": {}}
        threads = data.get("threads")
        if not isinstance(threads, dict):
            threads = {}
        return {"global_enabled": bool(data.get("global_enabled", False)), "threads": threads}

    def _save(self, data: dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.SETTINGS_FILE), exist_ok=True)
        payload = {
            "global_enabled": bool(data.get("global_enabled", False)),
            "threads": data.get("threads") if isinstance(data.get("threads"), dict) else {},
        }
        with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    def set_settings(self, *, global_enabled: bool, thread_id: str | None = None, thread_enabled: bool | None = None) -> dict:
        current = self._load()
        current["global_enabled"] = bool(global_enabled)
        if thread_id and isinstance(thread_enabled, bool):
            current["threads"][str(thread_id)] = bool(thread_enabled)
        self._save(current)
        return current

    def is_thread_allowed(self, thread_id: str) -> bool:
        current = self._load()
        if not current.get("global_enabled", False):
            return False
        return bool((current.get("threads") or {}).get(str(thread_id), False))

    @staticmethod
    def _signature(detail: dict[str, Any]) -> str:
        raw = f"{detail.get('id','')}|{detail.get('date','')}|{str(detail.get('snippet',''))[:120]}"
        return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]

    @staticmethod
    def _summary(text: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
        if not cleaned:
            return "Keine verwertbaren Inhalte im Thread."
        first = re.split(r"[.!?]\s+", cleaned, maxsplit=1)[0]
        return first[:320]

    @staticmethod
    def _reply_needed(text: str) -> str:
        low = str(text or "").lower()
        if "?" in low or re.search(r"\b(bitte|kannst du|deadline|termin|rückmeldung|rueckmeldung)\b", low):
            return "yes"
        return "likely_no"

    @staticmethod
    def _priority(subject: str, sender: str) -> str:
        s = str(subject or "").lower()
        f = str(sender or "").lower()
        if re.search(r"\b(rechnung|invoice|mahnung|deadline|dringend)\b", s) or re.search(r"\b(chef|boss|bank)\b", f):
            return "high"
        if re.search(r"\b(newsletter|promo|angebot)\b", s):
            return "low"
        return "medium"

    async def analyze_with_llm(self, detail: dict[str, Any]) -> MailAiAnalyzeResponse:
        provider, model_id = self._resolve_text_model()
        if not provider or not model_id:
            return self.degraded_analyze(detail, "AI provider is not configured for Mail Assist.")
        prompt = (
            "Du analysierst genau eine E-Mail fuer Janus Mail. "
            "Antworte ausschliesslich als JSON mit Feldern: summary, reply_needed, priority. "
            "reply_needed muss 'yes' oder 'likely_no' sein. priority muss 'high'|'medium'|'low' sein."
        )
        content = (
            f"From: {detail.get('from_display','')}\n"
            f"Subject: {detail.get('subject','')}\n"
            f"Date: {detail.get('date','')}\n"
            f"Body:\n{str(detail.get('body_text') or detail.get('snippet') or '')[:8000]}"
        )
        try:
            result = await llm_gateway.call_llm(
                provider=provider,
                model_id=model_id,
                api_key="",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                ],
                force_no_tools=True,
            )
            parsed = self._extract_json_payload(str(result.get("text") or result.get("content") or ""))
            summary = str(parsed.get("summary") or "").strip()
            reply_needed = str(parsed.get("reply_needed") or "").strip().lower()
            priority = str(parsed.get("priority") or "").strip().lower()
            if (
                not summary
                or reply_needed not in {"yes", "likely_no"}
                or priority not in {"high", "medium", "low"}
            ):
                return self.degraded_analyze(detail, "AI provider returned an invalid analysis payload.")
            return MailAiAnalyzeResponse(
                summary=summary[:500],
                reply_needed=reply_needed,
                priority=priority,
                stale=False,
                signature=self._signature(detail),
            )
        except Exception:
            return self.degraded_analyze(detail, "AI provider failed while analyzing this thread.")

    def degraded_analyze(self, detail: dict[str, Any], message: str) -> MailAiAnalyzeResponse:
        return MailAiAnalyzeResponse(
            summary="AI-Analyse ist aktuell nicht verfuegbar.",
            reply_needed="unknown",
            priority="unknown",
            stale=False,
            signature=self._signature(detail),
            degraded=True,
            error_message=message,
        )

    def analyze(self, detail: dict[str, Any]) -> MailAiAnalyzeResponse:
        text = str(detail.get("body_text") or detail.get("snippet") or "")
        return MailAiAnalyzeResponse(
            summary=self._summary(text),
            reply_needed=self._reply_needed(text),
            priority=self._priority(detail.get("subject", ""), detail.get("from_display", "")),
            stale=False,
            signature=self._signature(detail),
        )

    def draft(self, detail: dict[str, Any], tone: str) -> MailAiDraftResponse:
        subject = str(detail.get("subject") or "(Kein Betreff)")
        sender = str(detail.get("from_display") or "Ihnen")
        tone_key = str(tone or "neutral").strip().lower()
        if tone_key == "kurz":
            body = "Danke für die Nachricht. Ich melde mich zeitnah mit den nächsten Schritten."
        elif tone_key == "freundlich":
            body = "Vielen Dank für Ihre Nachricht. Ich habe alles gelesen und antworte Ihnen gern zeitnah mit den Details."
        elif tone_key == "formal":
            body = "Vielen Dank für Ihre Nachricht. Ich bestätige den Eingang und werde Ihnen kurzfristig eine Rückmeldung übermitteln."
        else:
            body = "Danke für die Nachricht. Ich habe den Punkt notiert und komme zeitnah mit einer Rückmeldung auf Sie zu."
        return MailAiDraftResponse(
            draft=f"Bezug: {subject}\n\nHallo {sender},\n\n{body}\n\nBeste Grüße"
        )

    async def draft_with_llm(self, detail: dict[str, Any], tone: str) -> MailAiDraftResponse:
        provider, model_id = self._resolve_text_model()
        if not provider or not model_id:
            return self.degraded_draft("AI provider is not configured for Mail Assist.")
        prompt = (
            "Erzeuge einen kurzen, sendefertigen deutschen Antwortentwurf fuer eine E-Mail. "
            "Kein Markdown. Kein Betreff. Nur den Mailtext. Ton beachten: "
            f"{str(tone or 'neutral')}."
        )
        content = (
            f"From: {detail.get('from_display','')}\n"
            f"Subject: {detail.get('subject','')}\n"
            f"Body:\n{str(detail.get('body_text') or detail.get('snippet') or '')[:8000]}"
        )
        try:
            result = await llm_gateway.call_llm(
                provider=provider,
                model_id=model_id,
                api_key="",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                ],
                force_no_tools=True,
            )
            draft = str(result.get("text") or result.get("content") or "").strip()
            if not draft:
                return self.degraded_draft("AI provider returned an empty draft.")
            return MailAiDraftResponse(draft=draft[:4000])
        except Exception:
            return self.degraded_draft("AI provider failed while drafting this reply.")

    @staticmethod
    def degraded_draft(message: str) -> MailAiDraftResponse:
        return MailAiDraftResponse(draft="", degraded=True, error_message=message)

    @staticmethod
    def _extract_json_payload(raw: str) -> dict[str, Any]:
        text = str(raw or "").strip()
        if not text:
            return {}
        if "```" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        try:
            return json.loads(text)
        except Exception:
            m = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not m:
                return {}
            try:
                return json.loads(m.group(0))
            except Exception:
                return {}

    @staticmethod
    def _resolve_text_model() -> tuple[str, str]:
        try:
            config = load_config_data() or {}
            last_model = str(config.get("last_used_model") or "").strip()
            catalog = llm_gateway.get_cached_model_catalog() or {}
            if last_model and isinstance(catalog.get(last_model), dict):
                info = catalog[last_model]
                if str(info.get("type") or "").lower() == "text":
                    provider = str(info.get("provider") or "").lower()
                    if provider and keyring.get_password("Janus-Projekt", provider):
                        return provider, last_model
        except Exception:
            pass
        return "", ""
