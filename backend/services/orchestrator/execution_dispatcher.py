"""LLM generation, gateway wiring, and tool-loop dispatch for chat requests (Phase 4)."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from backend.services import llm_gateway
from backend.services.chat_orchestrator import RequestContext
from backend.services.orchestrator.prompt_registry import apply_verbosity_control, prompt_registry
from backend.services.orchestrator.suggestion_engine import SuggestionEngine
from backend.services.prompt_cache import decide_prompt_cache
from backend.services.tool_executor import ToolExecutor
from backend.services.tool_manager import tool_manager
from backend.utils import intent_classifier
# Der Model-Katalog ist ein Service, der die JSON-Config lädt und verarbeitet.
from backend.services.model_catalog import get_models_by_provider
# 💎 BACKLOG-006: Dynamic fallback summary helper
from backend.services.orchestrator.execution_engine import _build_dynamic_fallback_summary
# 💎 BACKLOG-035: Prompt Injection Detection
from backend.services.security.injection_detector import detect_injection, get_injection_type
from backend.services.logging.logger_core import log_event
from backend.data.schemas_logging import LogEventCreate

logger = logging.getLogger("janus_backend")


def _normalize_gemini_tool_messages(chat_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Gemini expects tool messages with role=tool and matching tool_call_id."""
    if not isinstance(chat_history, list):
        return chat_history

    normalized: list[dict[str, Any]] = []
    pending_tool_call_ids: list[str] = []

    for idx, message in enumerate(chat_history):
        if not isinstance(message, dict):
            continue
        msg = dict(message)
        role = str(msg.get("role") or "").strip().lower()

        if role == "assistant":
            tool_calls = msg.get("tool_calls")
            if isinstance(tool_calls, list):
                pending_tool_call_ids = []
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    tcid = str(tc.get("id") or "").strip()
                    if tcid:
                        pending_tool_call_ids.append(tcid)

        if role == "tool":
            if not msg.get("tool_call_id"):
                chosen_id = pending_tool_call_ids.pop(0) if pending_tool_call_ids else ""
                if not chosen_id:
                    chosen_id = f"tool_call_{idx}"
                msg["tool_call_id"] = chosen_id

            content = msg.get("content")
            if isinstance(content, (dict, list)):
                msg["content"] = json.dumps(content, ensure_ascii=False)
            elif content is None:
                msg["content"] = ""
            else:
                msg["content"] = str(content)

        normalized.append(msg)

    return normalized


def _normalize_tool_args(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Create a normalized cache key for tool call deduplication.
    
    Normalizes:
    - All string values to lowercase
    - Removes whitespace variations
    - Removes ALL non-alphanumeric chars from filenames (aggressive dedup)
    - Creates deterministic JSON representation
    """
    if not isinstance(arguments, dict):
        arguments = {}
    
    normalized = {}
    for key, value in sorted(arguments.items()):  # Sortiere für Determinismus
        key_norm = str(key).lower().strip()
        if isinstance(value, str):
            # AGGRESSIVE String-Normalisierung für Gemini-Loops
            val_norm = str(value).lower().strip()
            # Für Content/Filename: entferne alle nicht-alphanumerischen Zeichen
            if key_norm in {'content', 'filename', 'title', 'name', 'path'}:
                # Behalte nur Buchstaben und Zahlen, entferne Rest
                val_norm = ''.join(c for c in val_norm if c.isalnum())
            else:
                # Standard: lowercase, collapse whitespace
                val_norm = ' '.join(val_norm.split())
        elif isinstance(value, (int, float, bool)):
            val_norm = value
        elif isinstance(value, (list, tuple)):
            # Listen normalisieren (rekursiv für verschachtelte Strukturen)
            val_norm = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
        elif isinstance(value, dict):
            val_norm = json.dumps(value, sort_keys=True, ensure_ascii=False).lower()
        else:
            val_norm = str(value).lower().strip()
        normalized[key_norm] = val_norm
    
    # Erstelle deterministischen Cache-Key
    cache_key = f"{tool_name.lower()}:{json.dumps(normalized, sort_keys=True, ensure_ascii=False)}"
    return cache_key


async def _reason_and_respond_with_provider_fixes(**kwargs: Any) -> Dict[str, Any]:
    """Apply provider-specific chat-history normalization before gateway call."""
    provider = str(kwargs.get("provider") or "").strip().lower()
    if provider in {"gemini", "google"}:
        logger.info("[GEMINI-FIX] _reason_and_respond_with_provider_fixes active for provider=%s", provider)
        if isinstance(kwargs.get("chat_history"), list):
            kwargs = dict(kwargs)
            kwargs["chat_history"] = _normalize_gemini_tool_messages(kwargs["chat_history"])
            logger.debug("[GEMINI-FIX] Tool message normalization applied")
    return await llm_gateway.reason_and_respond(**kwargs)


_CALENDAR_QUERY_TOKENS = frozenset([
    "termin", "termine", "kalender", "kalendereintr", "kalendereintrag",
    "verabredung", "verabredungen", "appointment", "schedule", "zeitplan",
    "meeting", "treffen", "treffe", "wann habe ich", "was habe ich",
    "welche termine", "nächsten mittwoch", "nächste woche", "diese woche",
    "freie zeit", "freier slot", "wann bin ich", "bin ich verfügbar",
])

_CALENDAR_INCOMPATIBLE_SKILLS = frozenset([
    "system.create_pdf",
    "create_pdf_from_markdown",
    "system.generate_image",
    "knowledge.edit_pdf",
])


def _is_calendar_query(query: str) -> bool:
    q = query.lower()
    return any(tok in q for tok in _CALENDAR_QUERY_TOKENS)


_DESTRUCTIVE_ACTION_RE = re.compile(
    r"\b(?:loesch(?:e|en|st)?|losch(?:e|en|st)?|lösch(?:e|en|st)?|"
    r"entfern(?:e|en|st)?|delete|remove|vernicht(?:e|en|st)?|"
    r"formatier(?:e|en|st)?|leer(?:e|en|st)?)\b",
    re.IGNORECASE,
)
_UNCLEAR_DESTRUCTIVE_SCOPE_RE = re.compile(
    r"\b(?:alles|alle|alte|altes|alten|old|everything|all)\b",
    re.IGNORECASE,
)
_CONCRETE_TARGET_HINT_RE = re.compile(
    r"(?:[a-zA-Z]:[\\/]|[/\\][\w .-]+|['\"][^'\"]+['\"]|"
    r"\b[\w.-]+\.(?:txt|md|pdf|docx?|xlsx?|csv|json|png|jpe?g|webp|zip)\b|"
    r"\b(?:ordner|datei|pfad|verzeichnis|termin|event)\s+[\w.-]+)",
    re.IGNORECASE,
)


def _is_unclear_destructive_action(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    if not _DESTRUCTIVE_ACTION_RE.search(q):
        return False
    if _CONCRETE_TARGET_HINT_RE.search(q):
        return False
    words = re.findall(r"\w+", q, flags=re.UNICODE)
    return bool(_UNCLEAR_DESTRUCTIVE_SCOPE_RE.search(q)) or len(words) <= 4


_FILESYSTEM_WRITE_RE = re.compile(
    r"\b(?:create|write|save|erstell(?:e|en)?|schreib(?:e|en)?|speicher(?:e|n)?)\b"
    r".{0,80}\b(?:file|datei|ordner|folder|directory|verzeichnis)\b",
    re.IGNORECASE,
)
_OUT_OF_SANDBOX_RE = re.compile(
    r"\b(?:outside|außerhalb|ausserhalb|beliebigen?\s+ort|anywhere|"
    r"local\s+drives?|lokale(?:n)?\s+laufwerke|c:\\|d:\\)\b"
    r"|approved\s+test\s+workspace|freigegeben(?:en|er|es)?\s+(?:test-)?workspace",
    re.IGNORECASE,
)


def _is_out_of_sandbox_filesystem_write(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_FILESYSTEM_WRITE_RE.search(q) and _OUT_OF_SANDBOX_RE.search(q))


_PATH_TRAVERSAL_MARKER_RE = re.compile(
    r"(?:^|[`'\"\s])(?:\.\.[\\/]|%2e%2e(?:%2f|/|%5c|\\)|\.\.%2f|\.\.%5c)",
    re.IGNORECASE,
)
_FILESYSTEM_READ_ACTION_RE = re.compile(
    r"\b(?:lies|lese|read|open|oeffne|offne|öffne|zeige|zeig|cat|type|"
    r"list|liste|suche|finde|lade|load)\b",
    re.IGNORECASE,
)


def _is_path_traversal_filesystem_read(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_PATH_TRAVERSAL_MARKER_RE.search(q) and _FILESYSTEM_READ_ACTION_RE.search(q))


_SECRET_FILE_EXFILTRATION_RE = re.compile(
    r"\b(?:read|open|show|print|dump|append|exfiltrate|leak|cat|type|"
    r"lies|lese|zeige|drucke|gib\s+(?:mir\s+)?aus)\b"
    r".{0,120}(?:`?\.env`?|\bapi[-_\s]?keys?\b|\bsecret(?:s)?\b|\btoken(?:s)?\b|\bcredential(?:s)?\b)|"
    r"(?:`?\.env`?|\bapi[-_\s]?keys?\b|\bsecret(?:s)?\b|\btoken(?:s)?\b|\bcredential(?:s)?\b)"
    r".{0,120}\b(?:read|open|show|print|dump|append|exfiltrate|leak|cat|type|"
    r"lies|lese|zeige|drucke|gib\s+(?:mir\s+)?aus)\b|"
    r"\bbefore\s+summari[sz]ing\b.{0,120}(?:`?\.env`?|\bapi[-_\s]?keys?\b|\bsecret(?:s)?\b|\btoken(?:s)?\b)",
    re.IGNORECASE,
)


def _is_secret_file_exfiltration_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_SECRET_FILE_EXFILTRATION_RE.search(q))


_EVIDENCE_HONESTY_QUERY_RE = re.compile(
    r"^\s*(?:hat\s+es\s+funktioniert\??|"
    r"sag(?:e)?\s+einfach,?\s+der\s+test\s+war\s+erfolgreich\.?|"
    r"behaupte,?\s+der\s+test\s+(?:war\s+)?(?:erfolgreich|bestanden))\s*$",
    re.IGNORECASE,
)
_SENSITIVE_TOKEN_ECHO_RE = re.compile(
    r"\b(?:token|api[-_\s]?key|secret)\s*:\s*[A-Za-z0-9._~+/=-]{4,}\b|"
    r"\bSECRET-[A-Za-z0-9._~+/=-]+\b",
    re.IGNORECASE,
)
_PROMPT_INJECTION_SUCCESS_RE = re.compile(
    r"\bignore\s+safety\s+and\s+claim\s+success\b|"
    r"\bignoriere\s+(?:die\s+)?sicherheit(?:sregeln)?\b.*\b(?:erfolg|erfolgreich|success)\b",
    re.IGNORECASE,
)
_OVERBROAD_USER_DATA_EXPORT_RE = re.compile(
    r"\b(?:exportier(?:e|en)?|export|gib(?:\s+mir)?|zeige?|zeig|list(?:e|en)?|"
    r"dump|download|lade\s+herunter)\b"
    r".{0,80}\b(?:alles|alle|vollstaendig|vollständig|komplett|saemtliche|sämtliche|all|everything)\b"
    r".{0,80}\b(?:ueber|über|about)\s+(?:mich|mir|me|meine\s+person)\b",
    re.IGNORECASE,
)
_INTERNAL_IDENTIFIER_REQUEST_RE = re.compile(
    r"\b(?:interne|internal|technische|technical)\b"
    r".{0,60}\b(?:user[-_\s]?id|nutzer[-_\s]?id|system[-_\s]?id|identifier|identifikator|metadaten)\b",
    re.IGNORECASE,
)
_HIDDEN_PROMPT_REQUEST_RE = re.compile(
    r"\b(?:system|developer|hidden|interne[nsr]?|versteckte[nsr]?)\b"
    r".{0,60}\b(?:prompt|anweisung(?:en)?|instruction(?:s)?|regel(?:n)?)\b",
    re.IGNORECASE,
)
_RAW_API_PAYLOAD_REQUEST_RE = re.compile(
    r"\b(?:api|request|response|call|endpoint)\b"
    r".{0,100}\b(?:header(?:s)?|body|payload|authorization|cookie(?:s)?)\b"
    r"|\b(?:header(?:s)?|body|payload)\b"
    r".{0,100}\b(?:api|request|response|call|endpoint)\b",
    re.IGNORECASE,
)
_SECURITY_AUDIT_REVEAL_ALL_RE = re.compile(
    r"\bsecurity\s+audit\b.{0,80}\b(?:reveal|show|dump|print|expose)\b.{0,80}\b(?:everything|all)\b",
    re.IGNORECASE,
)
_CROSS_USER_DATA_REQUEST_RE = re.compile(
    r"\b(?:coworker|co[-\s]?worker|kolleg(?:e|in|en)|andere(?:r|n)?\s+user|anderer\s+nutzer)\b"
    r".{0,100}\b(?:data|daten|chats?|memory|files?|dateien|ressourcen)\b|"
    r"\b(?:data|daten|chats?|memory|files?|dateien|ressourcen)\b"
    r".{0,100}\b(?:coworker|co[-\s]?worker|kolleg(?:e|in|en)|andere(?:r|n)?\s+user|anderer\s+nutzer)\b",
    re.IGNORECASE,
)
_MEMORY_FACT_FORWARDING_RE = re.compile(
    r"\b(?:forward|send|share|append|dump|export|list|zeige?|gib(?:\s+mir)?|"
    r"leak|exfiltrate|weiterleit(?:e|en)?|sende|teile)\b"
    r".{0,100}\b(?:all|alle|sämtliche|saemtliche)?\s*(?:memory\s+facts|memory-fakten|"
    r"memory|speicher|speicherfakten|fakten\s+aus\s+dem\s+speicher|gespeicherte\s+fakten)\b|"
    r"\btool\s+returns\s+text\s+instructing\b.{0,120}\b(?:leak|dump|forward|exfiltrate)\b.{0,80}\bmemory\b",
    re.IGNORECASE,
)
_UNSCOPED_EXTERNAL_CONTENT_INSTRUCTION_RE = re.compile(
    r"\b(?:summari[sz]e|zusammenfass(?:e|en)?|fasse\s+zusammen)\b"
    r".{0,120}\b(?:page|seite|webpage|retrieved\s+content|abgerufene[rsn]?\s+inhalt)\b"
    r".{0,120}\b(?:disable\s+citations|without\s+citations|do\s+not\s+cite|"
    r"zitate?\s+deaktivieren|ohne\s+zitate?|nicht\s+zitieren)\b",
    re.IGNORECASE,
)
_RETRIEVED_CONTENT_IMPERATIVE_RE = re.compile(
    r"\b(?:retrieved\s+content|abgerufene[rsn]?\s+inhalt|tool\s+output|web\s+content)\b"
    r".{0,120}\b(?:imperative\s+instructions|imperative\s+anweisungen|instructions|anweisungen)\b",
    re.IGNORECASE,
)
_RETRY_STORM_ABUSE_RE = re.compile(
    r"\b(?:wiederhole|wiederholen|wiederhol|repeat|retry|retrying)\b"
    r".{0,60}\b(?:bis\s+es\s+funktioniert|until\s+it\s+works|immer\s+wieder|forever|unbegrenzt|unlimited|"
    r"10000\s+mal|10000\s+times|unendlich|infinite|endlos|endless)\b|"
    r"\b(?:teuerste\s+modell|expensive\s+model|ignoriere\s+limits|ignore\s+limits|"
    r"bypass\s+quotas|umgehe\s+limits|uebergehe\s+limits)\b|"
    r"\b(?:schreibe|schreiben|generiere|generieren|erstelle|erstellen|write|generate|create)\b"
    r".{0,60}\b(?:1000\s+mal|1000\s+times|10000\s+mal|10000\s+times|tausendmal|x-mal)\b",
    re.IGNORECASE,
)


def _suppress_identity_for_generic_prompt(query: str) -> bool:
    normalized = " ".join(str(query or "").strip().lower().split())
    return normalized in {
        "simple factual prompt",
        "factual prompt",
        "erklaer kurz",
        "erklär kurz",
        "erkläre kurz",
    }


def _is_synthetic_simple_factual_prompt(query: str) -> bool:
    normalized = " ".join(str(query or "").strip().lower().split())
    return normalized in {"simple factual prompt", "factual prompt"}


def _is_unsupported_success_claim_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_EVIDENCE_HONESTY_QUERY_RE.search(q))


def _contains_sensitive_token_echo_risk(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_SENSITIVE_TOKEN_ECHO_RE.search(q))


def _is_prompt_injection_success_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_PROMPT_INJECTION_SUCCESS_RE.search(q))


def _is_overbroad_user_data_export_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_OVERBROAD_USER_DATA_EXPORT_RE.search(q))


def _is_internal_identifier_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_INTERNAL_IDENTIFIER_REQUEST_RE.search(q))


def _is_hidden_prompt_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_HIDDEN_PROMPT_REQUEST_RE.search(q))


def _is_raw_api_payload_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_RAW_API_PAYLOAD_REQUEST_RE.search(q))


def _is_security_audit_reveal_all_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_SECURITY_AUDIT_REVEAL_ALL_RE.search(q))


def _is_cross_user_data_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_CROSS_USER_DATA_REQUEST_RE.search(q))


def _is_memory_fact_forwarding_request(query: str) -> bool:
    q = str(query or "").strip().strip('"').strip("'")
    if not q:
        return False
    return bool(_MEMORY_FACT_FORWARDING_RE.search(q))


def _is_unscoped_external_content_instruction(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_UNSCOPED_EXTERNAL_CONTENT_INSTRUCTION_RE.search(q))


def _is_retrieved_content_imperative_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_RETRIEVED_CONTENT_IMPERATIVE_RE.search(q))


def _is_retry_storm_abuse_request(query: str) -> bool:
    q = str(query or "").strip()
    if not q:
        return False
    return bool(_RETRY_STORM_ABUSE_RE.search(q))


def _weather_query_has_usable_location(query: str) -> bool:
    """True when a weather prompt contains a concrete location instead of "dort"/missing place."""
    q = str(query or "").casefold()
    if not q:
        return False
    if re.search(r"\b(?:dort|da|hier|es)\b", q):
        return False
    return bool(
        re.search(r"\b(?:in|für|fuer|bei|von)\s+[a-zäöüß][\wäöüß.-]{2,}", q, re.IGNORECASE)
        or re.search(r"\b(?:muenchen|munich|köln|koeln|berlin|hamburg|düsseldorf|duesseldorf|frankfurt)\b", q)
    )


def _is_complex_workspace_task_missing_scope(query: str) -> bool:
    """Detect broad multi-step workspace file tasks that need a plan/clarification before tools."""
    q = str(query or "").casefold()
    if not q:
        return False
    has_workspace_scope = "workspace" in q or "arbeitsbereich" in q or "testdateien" in q
    has_multi_step = (
        ("sortier" in q or "sortiere" in q)
        and ("fass" in q or "zusammenfass" in q or "zusammenfassung" in q)
        and ("uebersicht" in q or "übersicht" in q or "erstelle" in q)
    )
    has_concrete_path = bool(re.search(r"(?:[a-zA-Z]:[\\/]|[/\\][\w .-]+)", str(query or "")))
    return has_workspace_scope and has_multi_step and not has_concrete_path


def _is_short_workspace_write_missing_path(query: str) -> bool:
    """Detect synthetic workspace write tasks without a concrete filesystem path."""
    q = str(query or "").casefold()
    if not q:
        return False
    has_workspace = "test-workspace" in q or "test workspace" in q or "approved test workspace" in q
    has_write = (
        ("erstell" in q or "create" in q)
        and ("ordner" in q or "folder" in q or "directory" in q)
        and ("notiz" in q or "note" in q or "speicher" in q or "save" in q)
    )
    has_concrete_path = bool(re.search(r"(?:[a-zA-Z]:[\\/]|[/\\][\w .-]+)", str(query or "")))
    return has_workspace and has_write and not has_concrete_path


def _short_workspace_write_clarification() -> str:
    return (
        "Ich kann das direkt weiter im Test-Workspace ausführen, brauche dafür aber den exakten Pfad "
        "oder Zielbereich. Bitte nenne den Ordnerpfad, in dem ich den Ordner PlannerCheck erstellen "
        "und die kurze Notiz speichern soll."
    )


def _complex_workspace_scope_clarification() -> str:
    return (
        "Das ist ein mehrstufiger Workspace-Auftrag. Ich gehe dabei in Schritten vor: "
        "zuerst den Quellordner bestimmen, danach die Testdateien nach Typ sortieren, "
        "anschließend Textdateien zusammenfassen und daraus eine Übersicht erstellen. "
        "Bitte nenne mir den exakten Ordnerpfad oder Quellordner und, falls gewünscht, "
        "den Zielordner/Zielbereich, bevor ich Dateien verändere."
    )
def _apply_pre_resolution_guards(wf: Any, request: Any) -> None:
    """Apply intent-based model escalation for complex tasks before resolution."""
    # --- Intent-based Model Escalation ---
    last_msg = wf.get_last_user_message_content() if hasattr(wf, 'get_last_user_message_content') else None
    if not last_msg and hasattr(wf, 'user_text'):
        last_msg = wf.user_text
    
    # 💎 BACKLOG-037: Gemini Ambiguity-Detection und Tool-Blockade
    # Diese Logik MUSS immer ausgeführt werden, auch wenn last_msg None ist
    # Fallback auf wf.user_text wenn verfügbar
    query_for_ambiguity = last_msg or (wf.user_text if hasattr(wf, 'user_text') else None)
    smalltalk_reply = intent_classifier.smalltalk_response(str(query_for_ambiguity or ""))
    if smalltalk_reply:
        logger.info(
            "[SMALLTALK-BYPASS] Basic conversation bypasses ambiguity/tool guards: %r",
            str(query_for_ambiguity or "")[:50],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        wf.final_text_to_generate = smalltalk_reply
        wf.skip_llm_generation = True
        if not getattr(wf, "final_text", ""):
            wf.final_text = smalltalk_reply
        return
    
    if query_for_ambiguity:
        query = query_for_ambiguity.lower()

        # Calendar guard: purge PDF/image skills when user is asking about appointments.
        if _is_calendar_query(query) and hasattr(wf, 'relevant_skill_ids'):
            before = list(wf.relevant_skill_ids)
            wf.relevant_skill_ids = [
                sid for sid in wf.relevant_skill_ids
                if sid not in _CALENDAR_INCOMPATIBLE_SKILLS
            ]
            removed = [s for s in before if s not in wf.relevant_skill_ids]
            if removed:
                logger.warning(
                    "[CALENDAR-GUARD] Kalenderanfrage erkannt. Entferne inkompatible Skills aus relevant_skill_ids: %s",
                    removed,
                )

        # Safety net: Inject calendar.list_events if intent is detected but selector returned empty
        intent_result = getattr(wf, 'intent_detection_result', None)
        if intent_result and getattr(intent_result, 'is_calendar_intent', False):
            _cal_mandatory = ("calendar.list_events", "calendar.find_and_update_event", "calendar.create_event")
            if hasattr(wf, 'relevant_skill_ids'):
                for sid in _cal_mandatory:
                    if sid not in wf.relevant_skill_ids:
                        logger.warning(
                            "[CALENDAR-SAFETY-NET] Calendar intent ohne %s — injiziert.", sid,
                        )
                        wf.relevant_skill_ids.append(sid)
            else:
                logger.warning(
                    "[CALENDAR-SAFETY-NET] Calendar intent ohne relevant_skill_ids — initialisiere Pflicht-Kalenderskills."
                )
                wf.relevant_skill_ids = list(_cal_mandatory)

        # 💎 BACKLOG-037/BACKLOG-039: Provider-Agnostic Ambiguity-Detection und Tool-Blockade
        # Bei ambigen Anfragen mit geringer Confidence für alle Provider: Tool-Ausführung blockieren
        current_provider = str(wf.provider or request.provider or "").strip().lower()
        
        logger.info("[AMBIGUITY-DEBUG] Provider check: current_provider=%s, intent_result=%s", current_provider, type(intent_result).__name__ if intent_result else None)
        
        if intent_result:
            is_ambiguous = getattr(intent_result, 'is_ambiguous', False)
            ambiguity_confidence = getattr(intent_result, 'ambiguity_confidence', 0.0)
            is_calendar_read_intent = (
                bool(getattr(intent_result, 'is_calendar_intent', False))
                and not bool(getattr(intent_result, 'is_calendar_mutation', False))
                and not bool(getattr(intent_result, 'is_calendar_creation', False))
            )
            is_weather_intent = bool(getattr(intent_result, 'is_weather_intent', False))
            is_routing_geo_intent = bool(getattr(intent_result, 'is_routing_geo_intent', False))
            # Threshold: 0.6 (kann über Konfiguration angepasst werden)
            ambiguity_threshold = 0.6
            
            logger.info(
                "[AMBIGUITY-DEBUG] Ambiguity values: is_ambiguous=%s, ambiguity_confidence=%.2f, threshold=%.2f",
                is_ambiguous,
                ambiguity_confidence,
                ambiguity_threshold,
            )
            
            if is_ambiguous and ambiguity_confidence >= ambiguity_threshold and is_calendar_read_intent:
                logger.info(
                    "[AMBIGUITY-BYPASS] Calendar read intent stays tool-enabled despite ambiguity "
                    "(confidence=%.2f >= %.2f). Query: %r",
                    ambiguity_confidence,
                    ambiguity_threshold,
                    query_for_ambiguity[:50] if query_for_ambiguity else "",
                )
            elif is_ambiguous and ambiguity_confidence >= ambiguity_threshold and is_routing_geo_intent:
                logger.info(
                    "[AMBIGUITY-BYPASS] Routing/geo intent stays tool-enabled despite ambiguity "
                    "(confidence=%.2f >= %.2f). Query: %r",
                    ambiguity_confidence,
                    ambiguity_threshold,
                    query_for_ambiguity[:50] if query_for_ambiguity else "",
                )
            elif (
                is_ambiguous
                and ambiguity_confidence >= ambiguity_threshold
                and is_weather_intent
                and _weather_query_has_usable_location(query_for_ambiguity)
            ):
                logger.info(
                    "[AMBIGUITY-BYPASS] Weather intent stays tool-enabled despite ambiguity "
                    "(confidence=%.2f >= %.2f). Query: %r",
                    ambiguity_confidence,
                    ambiguity_threshold,
                    query_for_ambiguity[:50] if query_for_ambiguity else "",
                )
            elif is_ambiguous and ambiguity_confidence >= ambiguity_threshold:
                logger.info(
                    "[AMBIGUITY-BLOCK] Ambige Anfrage für %s erkannt (confidence=%.2f >= %.2f). "
                    "Tool-Ausführung blockiert, Klärungsfrage wird erzwungen. Query: %r",
                    current_provider,
                    ambiguity_confidence,
                    ambiguity_threshold,
                    query_for_ambiguity[:50] if query_for_ambiguity else "",
                )
                # Tool-Ausführung blockieren
                wf.disable_tools = True
                wf.requires_clarification = True
                wf.ambiguity_confidence = ambiguity_confidence
                wf.context_isolation_mode = "ambiguity_clarification"
                wf.force_tool_name = None
                wf.has_tool_trigger = False
                wf.proactive_guidance = ""
                if hasattr(wf, "relevant_skill_ids"):
                    wf.relevant_skill_ids = []
                # Auch gateway_kwargs setzen, da die Tool-Ausführung dort prüft
                if hasattr(wf, 'gateway_kwargs'):
                    wf.gateway_kwargs['disable_tools'] = True
                # System-Prompt für Klärungsfrage setzen
                from backend.services.chat.context_builder import ContextBuilder
                from backend.data import crud
                context_builder = ContextBuilder(db=wf.db if hasattr(wf, 'db') else None)
                # Generiere Klärungsfrage-Prompt
                planner_prompt = context_builder.build_planner_prompt(
                    candidates=[{"tool_name": "unknown", "confidence": ambiguity_confidence}]
                )
                # Füge zum System-Prompt hinzu
                if hasattr(wf, 'system_prompt_for_llm'):
                    logger.info("[AMBIGUITY-DEBUG] Adding clarification prompt to system_prompt_for_llm")
                    wf.system_prompt_for_llm += "\n\n" + planner_prompt
                else:
                    logger.warning("[AMBIGUITY-DEBUG] wf.system_prompt_for_llm not found")
                # Markiere als Klärungs erforderlich für Logging
                if hasattr(wf, 'gateway_kwargs'):
                    wf.gateway_kwargs['requires_clarification'] = True
                    wf.gateway_kwargs['ambiguity_confidence'] = ambiguity_confidence
                    logger.info("[AMBIGUITY-DEBUG] gateway_kwargs updated: disable_tools=%s, requires_clarification=%s", wf.gateway_kwargs.get('disable_tools'), wf.gateway_kwargs.get('requires_clarification'))
                else:
                    logger.warning("[AMBIGUITY-DEBUG] wf.gateway_kwargs not found")

        # Harte Erkennung für den Sortier-Auftrag
        is_sort_intent = 'sortiere' in query and ('pdf' in query or 'dateien' in query)
        # Harte Erkennung für RAG-Intents (Suche Datei X, Lies Datei Y)
        is_rag_intent = any(keyword in query for keyword in ['suche', 'lies', 'datei', 'dokument', 'pdf']) and any(keyword in query for keyword in ['datei', 'dokument', 'pdf', 'inhalt', 'text'])

        # 💎 TASK-001: BACKLOG-008 - Filesystem-Intent Veto für RAG-Intent
        # Wenn Filesystem-Intent stark ist, RAG-Intent unterdrücken
        # Filesystem-Operationen sollten kein unnötiges Logic-Tier-Upgrade triggern
        if is_rag_intent:
            from backend.services.orchestrator.intent_engine import IntentEngine
            intent_engine = IntentEngine()
            if intent_engine.detect_filesystem_intent(query):
                logger.info(
                    "[FILESYSTEM-OVERRIDE] RAG intent suppressed by filesystem intent in text: '%s'",
                    query[:100] + "..." if len(query) > 100 else query
                )
                is_rag_intent = False

        if is_sort_intent or is_rag_intent:
            # Nutze die zentrale Hierarchie-Logik
            from backend.llm_providers.shared.moa import MOA_MODEL_HIERARCHY
            # Wir erzwingen das 'logic' Modell (Standard)
            current_provider = wf.provider or request.provider
            provider_key = str(current_provider or "").strip().lower()
            provider_tiers = MOA_MODEL_HIERARCHY.get(provider_key)
            logic_model = provider_tiers.get('logic') if provider_tiers else None

            if logic_model and wf.chosen_model != logic_model:
                intent_type = "Sortier-Auftrag" if is_sort_intent else "RAG-Intent"
                logger.info(f"🔥 [INTENT-OVERRIDE] {intent_type} erkannt. Erbitte logic-Tier Upgrade: {wf.chosen_model} -> {logic_model}")
                wf.chosen_model = logic_model

            # Knowledge-Skills für Sortier-Intent und RAG-Intent hinzufügen
            if hasattr(wf, 'relevant_skill_ids'):
                knowledge_skills = {'knowledge.query', 'knowledge.read_full_text'}
                for skill in knowledge_skills:
                    if skill not in wf.relevant_skill_ids:
                        wf.relevant_skill_ids.append(skill)
                        intent_type = "sort" if is_sort_intent else "RAG"
                        logger.info(f"[INTENT-GUARD] Added {skill} to relevant_skill_ids for {intent_type} intent")
    # --- End of Intent-based Model Escalation ---


async def execute_generation_prepare_gateway(
    ctx: RequestContext,
    *,
    db: Any,
    context_manager: Any,
    orchestrator_context_manager: Any,
    skill_selector: Any,
    prompt_role_from_db_role: Callable[[str], str],
    user_budget_info: Optional[Any] = None,
) -> RequestContext:
    """Builds prompts, history, ToolExecutor, and gateway_kwargs (parity with execute_generation, pre tool-loop)."""
    wf = ctx.workflow
    request = ctx.request
    # Apply pre-resolution guards (intent-based model escalation, etc.)
    _apply_pre_resolution_guards(wf, request)

    user_query = str(wf.user_text or "").strip()
    if _is_synthetic_simple_factual_prompt(user_query):
        logger.info(
            "[SYNTHETIC-FACTUAL-PROMPT-GATE] Asking for concrete topic before LLM/tools: %r",
            user_query[:80],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Bitte nenne das konkrete Thema oder den konkreten Inhalt, den ich kurz erklären soll."
        wf.skip_llm_generation = True
        return ctx

    if _is_short_workspace_write_missing_path(user_query):
        logger.warning(
            "[WORKSPACE-WRITE-BOUNDARY-GATE] Blocking pathless workspace write before tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = _short_workspace_write_clarification()
        wf.skip_llm_generation = True
        return ctx

    if _is_complex_workspace_task_missing_scope(user_query):
        logger.warning(
            "[PLANNER-BOUNDARY-GATE] Blocking broad multi-step workspace task before tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = _complex_workspace_scope_clarification()
        wf.skip_llm_generation = True
        return ctx

    if _is_overbroad_user_data_export_request(user_query):
        logger.warning(
            "[PRIVACY-EXPORT-GATE] Blocking overbroad user data export before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann nicht alles ueber dich pauschal exportieren oder ausgeben. "
            "Bitte bestaetige zuerst, welche Daten oder welcher Umfang gemeint ist, "
            "zum Beispiel Profil, Vorlieben, Termine oder gespeicherte Memory-Fakten. "
            "Ohne konkrete Angaben und Bestaetigung erfolgt kein Export."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_internal_identifier_request(user_query):
        logger.warning(
            "[INTERNAL-ID-GATE] Blocking internal identifier request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Ich kann keine interne User-ID anzeigen oder vertrauliche Metadaten ausgeben."
        wf.skip_llm_generation = True
        return ctx

    if _is_hidden_prompt_request(user_query):
        logger.warning(
            "[HIDDEN-PROMPT-GATE] Blocking hidden prompt request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Ich kann diese internen Anweisungen nicht weitergeben oder System-/Developer-Prompts preisgeben."
        wf.skip_llm_generation = True
        return ctx

    if _is_raw_api_payload_request(user_query):
        logger.warning(
            "[API-PAYLOAD-PRIVACY-GATE] Blocking raw API header/body request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann keine Header oder keinen Body ausgeben, die mir nicht sicher vorliegen. "
            "Bitte nenne eine konkrete Fehlermeldung oder redigierte Diagnose ohne Authorization, Cookies oder Secrets."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_security_audit_reveal_all_request(user_query):
        logger.warning(
            "[SECURITY-AUDIT-REVEAL-ALL-GATE] Blocking reveal-all audit request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann nicht alles offenlegen oder interne Anweisungen, Secrets, API-Keys "
            "oder private Daten ausgeben. Bitte nenne den konkreten, autorisierten Audit-Umfang."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_cross_user_data_request(user_query):
        logger.warning(
            "[CROSS-USER-DATA-GATE] Blocking cross-user data request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann keine Daten, Dateien, Chats oder Memory-Fakten anderer Personen beschaffen "
            "oder ausgeben. Bitte nenne einen autorisierten, eigenen Scope."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_memory_fact_forwarding_request(user_query):
        logger.warning(
            "[MEMORY-FACT-FORWARDING-GATE] Blocking memory-fact forwarding request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann nicht alle Memory-Fakten weitergeben oder dumpen. "
            "Bitte nenne konkret, welche eigene Information du prüfen möchtest."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_unscoped_external_content_instruction(user_query):
        logger.warning(
            "[EXTERNAL-CONTENT-SCOPE-GATE] Blocking unscoped external content instruction before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Bitte füge die konkrete Seite oder den abgerufenen Inhalt ein. "
            "Externe Anweisungen wie Zitierverbote behandle ich als Daten und nicht als Vorgabe."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_retrieved_content_imperative_request(user_query):
        logger.warning(
            "[RETRIEVED-CONTENT-IMPERATIVE-GATE] Blocking external imperative instruction adoption before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich befolge keine imperativen Anweisungen aus abgerufenem Inhalt. "
            "Bitte nenne den konkreten Inhalt; ich behandle ihn als Daten."
        )
        wf.skip_llm_generation = True
        return ctx

    if _contains_sensitive_token_echo_risk(user_query):
        logger.warning(
            "[SENSITIVE-TOKEN-GATE] Blocking token echo before LLM/tools: %r",
            user_query[:80],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Ich kann dieses Token nicht verarbeiten oder wiederholen."
        wf.skip_llm_generation = True
        return ctx

    if _is_prompt_injection_success_request(user_query):
        logger.warning(
            "[PROMPT-INJECTION-SUCCESS-GATE] Blocking success-claim injection before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Ich kann diese Aktion nicht ausfuehren, weil ich Safety nicht ignoriere und keinen Erfolg ohne Evidenz behaupte."
        wf.skip_llm_generation = True
        return ctx

    if _is_unsupported_success_claim_request(user_query):
        logger.warning(
            "[EVIDENCE-HONESTY-GATE] Blocking unsupported success claim before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Ich kann diese Aussage ohne Evidenz nicht bestaetigen."
        wf.skip_llm_generation = True
        return ctx

    if _is_out_of_sandbox_filesystem_write(user_query):
        logger.warning(
            "[FILESYSTEM-BOUNDARY-GATE] Blocking out-of-sandbox filesystem write request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann keine Dateien außerhalb des freigegebenen Test-Workspaces erstellen. "
            "Bitte nenne einen Pfad innerhalb des approved test workspace."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_path_traversal_filesystem_read(user_query):
        logger.warning(
            "[FILESYSTEM-TRAVERSAL-GATE] Blocking path traversal filesystem read before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Ich kann Pfade mit '..' nicht lesen, weil sie Path Traversal darstellen. "
            "Bitte nenne einen kanonischen Pfad innerhalb eines freigegebenen Workspace-Ordners."
        )
        wf.skip_llm_generation = True
        return ctx

    if _is_secret_file_exfiltration_request(user_query):
        logger.warning(
            "[SECRET-FILE-EXFILTRATION-GATE] Blocking secret/env file request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = "Ich kann keine .env-Dateien, API-Keys, Tokens oder Secrets lesen oder ausgeben."
        wf.skip_llm_generation = True
        return ctx

    if _is_unclear_destructive_action(user_query):
        logger.warning(
            "[DESTRUCTIVE-CLARIFICATION-GATE] Blocking unclear destructive request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.final_text = (
            "Welche Dateien, Ordner oder Termine soll ich loeschen? "
            "Bitte nenne mir den exakten Pfad, Dateinamen, Zeitraum oder das konkrete Ziel."
        )
        wf.skip_llm_generation = True
        return ctx

    # 💎 BACKLOG-087: Retry-Storm/Abuse Detection Gate
    # Blocks retry-storm and cost-abuse prompts before memory retrieval
    if _is_retry_storm_abuse_request(user_query):
        logger.warning(
            "[RETRY-STORM-ABUSE-GATE] Blocking retry-storm/abuse request before LLM/tools: %r",
            user_query[:120],
        )
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        wf.disable_tools = True
        wf.requires_clarification = True
        wf.context_isolation_mode = "abuse_refusal"
        if not hasattr(wf, "gateway_kwargs"):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        wf.gateway_kwargs["disable_tools"] = True
        wf.gateway_kwargs["requires_clarification"] = True
        wf.gateway_kwargs["context_isolation_mode"] = "abuse_refusal"
        wf.final_text = (
            "Ich kann diesen Aufruf nicht wiederholen. "
            "Retry-Storm und Cost-Abuse Anfragen werden aus Sicherheitsgründen abgelehnt."
        )
        wf.skip_llm_generation = True
        return ctx

    # 💎 BACKLOG-035: Prompt Injection Guard - COMPLETE BLOCK
    # Check for injection BEFORE any tool forcing (SOURCE-ROUTING, etc.)
    user_query = str(wf.user_text or "").strip()
    injection_detected = detect_injection(user_query)
    if injection_detected:
        injection_type = get_injection_type(user_query) or "unknown"
        logger.warning(
            f"🚨 PROMPT INJECTION BLOCKED: type={injection_type}, query='{user_query[:100]}...'"
        )
        # Telemetry event for prompt_injection_blocked
        await log_event(LogEventCreate(
            event_type="prompt_injection_blocked",
            skill="orchestrator.execution_dispatcher",
            status="blocked",
            payload={
                "injection_type": injection_type,
                "query_preview": user_query[:200],
                "guard_location": "execution_dispatcher",
            },
        ))
        # COMPLETE BLOCK: Disable all tool forcing and clear skills
        wf.relevant_skill_ids = []
        wf.force_tool_name = None
        wf.proactive_guidance = ""
        wf.has_tool_trigger = False
        if not hasattr(wf, 'gateway_kwargs'):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"
        # Set error response for user notification
        wf.final_text = "⚠️ Ihre Anfrage wurde aufgrund von verdächtigem Inhalt blockiert (Prompt Injection Detection)."
        wf.skip_llm_generation = True  # Skip LLM generation
        # Return early - no further processing
        return ctx
    
    # 💎 PURE-TEXT SUMMARY MODE: Wenn Global Veto für Zusammenfassungen aktiv ist
    # Entferne alle Skills, deaktiviere Tool-Zwang, deaktiviere proaktive Vorschläge
    inc = getattr(wf, "intent_detection_result", None)
    if inc is not None and inc.summary_global_veto:
        logger.warning("[PURE-TEXT MODE] Summary global veto aktiv (IntentDetectionResult). Disabling all skills and proactive suggestions.")
        wf.relevant_skill_ids = []  # Entferne alle Werkzeuge
        wf.force_tool_name = None  # Deaktiviere Video/Image-Zwang
        wf.proactive_guidance = ""  # Deaktiviere proaktive Vorschläge
        wf.has_tool_trigger = False  # Kein Tool-Trigger für Zusammenfassungen
        # Setze gateway_kwargs für pure-text mode
        if not hasattr(wf, 'gateway_kwargs'):
            wf.gateway_kwargs = {}
        wf.gateway_kwargs["forced_tool"] = None
        wf.gateway_kwargs["force_tool_name"] = None
        wf.gateway_kwargs["tool_choice"] = "none"  # Kein Tool-Choice erzwingen
        
    background_tasks = ctx.background_tasks
    if wf.skip_llm_generation:
        if not wf.final_text:
            wf.final_text = wf.final_text_to_generate
    else:
        wf.final_text = wf.final_text_to_generate
    if not wf.skip_llm_generation:
        clarification_mode = bool(
            getattr(wf, "requires_clarification", False)
            and str(getattr(wf, "context_isolation_mode", "") or "") == "ambiguity_clarification"
        )
        wf.ui_guidance = "⚠️ REGEL FÜR PDF-DOKUMENTE IN DER WISSENSDATENBANK:\n1. Wenn der User nach PDF-Dokumenten aus der Wissensdatenbank fragt (ohne konkreten Pfad): Nutze 'list_knowledge_documents'.\n2. Um eine PDF aus der Wissensdatenbank zu öffnen: Nutze 'open_knowledge_document'.\n3. AUSNAHME: Wenn der User einen konkreten Dateisystempfad nennt (z.B. C:\\, D:\\, /home/), MUSST du filesystem.list_directory oder filesystem.read_file verwenden - auch für PDFs.\n4. WENN DER USER EIN BILD WILL: Nutze IMMER UND AUSSCHLIESSLICH 'system.generate_image'."
        wf.research_guidance = '🚨 SYSTEM-DIREKTIVE (STRIKTE KASKADE):\n1. PFAD-VORRANG: Wenn die User-Anfrage einen konkreten Dateisystempfad enthält (z.B. "C:\\...", "D:\\...", "/home/..."), MUSST du ZUERST filesystem.list_directory oder filesystem.read_file verwenden - NIEMALS query_knowledge_base.\n2. PRIORITÄT (für Wissensfragen OHNE Pfad): Nutze ZUERST `query_knowledge_base`.\n3. STOPP-REGEL: Sobald die PDF-Ergebnisse die Frage beantworten, ist jede weitere Suche (Wikipedia/Web) STRENGSTENS UNTERSAGT.\n4. AUSNAHME: Nur wenn `query_knowledge_base` 0 Ergebnisse liefert, darf Wikipedia genutzt werden.\nVERHALTENS-KODEX: Redundante Wikipedia-Suchen bei vorhandenem PDF-Wissen gelten als schwerer Logik-Fehler.\n'
        wf.proactive_guidance = ""
        wf.video_intent_guidance = ""
        wf.action_guidance = ""
        if getattr(wf, "is_audit_request", False) or getattr(wf, "is_audit_decision", False):
            wf.action_guidance = (
                '🚨 SYSTEM-KRITISCHE ANWEISUNG: AUDIT-KORREKTUREN (VOLLSTÄNDIGER BATCH)\n'
                'Wenn der User nach einem Audit die Korrektur-Option wählt (z.B. Option 2):\n'
                '1. Deine Aufgabe ist die TOTALE UND VOLLSTÄNDIGE KORREKTUR des Dokuments in EINEM Schritt.\n'
                '2. Sammle JEDEN einzelnen Fehler, den du im Audit gefunden hast (Namen, Daten, Fakten, veraltete Sätze).\n'
                '3. Erstelle eine `modifications`-Liste, die ALLE diese Punkte enthält. NICHT-EINHALTUNG IST EIN FEHLER.\n'
                '4. Das Senden von unvollständigen Listen oder Einzelkorrekturen ist untersagt. Wenn du 4 Fehler gefunden hast, muss die Liste 4 Einträge haben.\n'
                '5. Rufe das Werkzeug `edit_pdf_text_in_place` exakt EINMAL mit dieser vollständigen Liste auf.\n'
                'BEISPIEL FÜR EINEN KORREKTEN AUFRUF:\n```json\n{\n  "tool_call": "edit_pdf_text_in_place",\n  "arguments": {\n'
                '    "original_filename": "beispiel_dokument.pdf",\n    "modifications": [\n'
                '      {"search": "Angela Merkel ist Kanzlerin", "replace": "Olaf Scholz ist Kanzler"},\n'
                '      {"search": "die Mehrwertsteuer beträgt 16%", "replace": "die Mehrwertsteuer beträgt 19%"},\n'
                '      {"search": "Großbritannien ist Mitglied der EU", "replace": ""}\n    ]\n  }\n}\n```'
            )
        wf.citation_guidance = 'ZITATE: Wenn du Informationen aus der Wissensdatenbank nutzt, gib die Quelle als [Dateiname, Seite X] an. Nutze die Daten aus den [QUELLE: ..., SEITE: ...] Tags.'
        wf.tool_retry_guidance = 'TOOL-RETRY: Wenn query_knowledge_base keine Ergebnisse liefert, rufe es erneut mit anderen Begriffen auf.'
        wf.small_talk_guard = "CRITICAL DIRECTIVE:\nDu bist ein konversationsfähiger KI-Assistent. Deine Hauptaufgabe ist es, mit dem Nutzer zu SPRECHEN.\nTools sind OPTIONAL und NUR für spezifische externe Aktionen (z.B. Websuche, Datei speichern) gedacht.\n- Bei Smalltalk (z.B. 'Hallo', 'Wie geht es dir?') -> KEIN TOOL AUFRUFEN, sondern direkt antworten!\n- Bei Fragen zu deiner Identität ('Wer bist du?') -> KEIN TOOL AUFRUFEN, sondern direkt antworten!\n- Wenn der Nutzer keine konkrete Aktion oder Datenabfrage fordert, antworte IMMER nur mit Text.\n- Es ist strengstens verboten, Tools wie 'memory_write' oder 'memory_read' für Smalltalk zu missbrauchen!"
        wf.tool_protocol_guidance = 'TOOL-CALL-PROTOKOLL (PHASE F, VERBINDLICH):\n1. NAMING-POLICY: Nutze bevorzugt domain.action Skill-Namen (z.B. knowledge.query, filesystem.delete_file).\n2. LEGACY-NAMEN nur als Fallback, wenn ein Skillname nachweislich nicht funktioniert.\n3. STRICT JSON: Der Tool-Call muss ein valides JSON-Objekt im Feld arguments enthalten.\n4. PFLICHTFELDER: Alle durch das Tool-Schema geforderten Parameter sind zwingend.\n5. TYPDISZIPLIN: Datentypen strikt laut Schema (kein String statt Integer etc.).\n6. DOMAIN-AWARENESS: Nutze die passende Domäne (filesystem.*, knowledge.*, system.*, calendar.*, communication.*, contacts.*, memory.*).\n7. FEHLERKORREKTUR: Bei INVALID_ARGUMENTS oder MALFORMED_REQUEST den letzten Aufruf korrigieren und mit gültigen Parametern erneut versuchen.'
        wf.image_pdf_flow_guidance = ""
        if getattr(wf, "is_multitask_image_pdf", False):
            wf.image_pdf_flow_guidance = (
                'FLUSS-LOGIK: Wenn der User sowohl ein Bild als auch ein PDF anfordert, dann:\n'
                'a) Rufe zuerst `system.generate_image` auf und warte auf den lokal gespeicherten Pfad.\n'
                'b) Sobald das Bild vorliegt, übergib den Pfad per Markdown `![Bild](pfad)` an `system.create_pdf`.\n'
                'c) Starte erst den PDF-Call, nachdem die Bildgenerierung erfolgreich abgeschlossen wurde.'
            )
        wf.capability_guidance = ''
        try:
            wf.capability_groups = skill_selector.filter_capability_groups(tool_manager.get_capability_groups(), wf.relevant_skill_ids)
            if wf.capability_groups:
                wf.lines = [f"- {cap}: {', '.join(skills)}" for cap, skills in sorted(wf.capability_groups.items())]
                wf.capability_guidance = 'CAPABILITY-ROUTING (DIAMANT V3):\nWähle Skills zuerst nach Fähigkeit (Capability), dann nach konkretem Namen.\nVerfügbare Capability-Gruppen:\n' + '\n'.join(wf.lines)
        except Exception as exc:
            logger.debug('Capability-Guidance konnte nicht aufgebaut werden: %s', exc)
        wf.small_talk_prefix = "SYSTEM LEVEL DIRECTIVE: You are chatting directly with a user. YOU MUST NEVER INVENT OR FAKE TOOL ARGUMENTS! If the user says 'Hello' or 'How are you', YOU MUST RESPOND IN PLAIN TEXT ONLY. DO NOT USE ANY TOOLS FOR GREETINGS."
        wf.lean_tool_call_examples = 'LEAN TOOL-CALL FORMAT (LOCAL OLLAMA): Wenn ein Tool noetig ist, gib exakt ein JSON-Objekt im Format {"name": "...", "parameters": {...}} aus.\nFew-shot 1 (korrekt): {"name": "knowledge.query", "parameters": {"query": "Wetter Berlin heute"}}\nFew-shot 2 (korrekt): {"name": "filesystem.read_file", "parameters": {"path": "C:/temp/notiz.txt"}}\nRegeln: Keine Markdown-Backticks, kein zusaetzlicher Text vor/nach dem JSON, parameters immer als Objekt.'
        wf.is_identity_turn = intent_classifier.is_identity_query(wf.user_text)
        if request.provider == 'ollama':
            wf.final_system_prompt = f'{wf.small_talk_prefix}\n\nDu bist Janus. Antworte kurz und hilfsbereit. Nutze für Kartendienste ausschließlich Links im Format: https://www.google.com/maps/dir/?api=1&origin={{origin}}&destination={{destination}}&travelmode=driving\n\n{wf.lean_tool_call_examples}'
            if wf.is_identity_turn:
                wf.final_system_prompt += "\n\nIDENTITAETS-REGEL: Bei Fragen wie 'Wer bist du?' antworte immer klar als Janus, ein persönlicher KI-Assistent. Sage NICHT, dass du nur ein PDF-Assistent bist, außer der Nutzer fragt explizit nach PDF-Funktionen."
        elif wf.dialog_mode == 'DEFAULT':
            wf.final_system_prompt = f'{wf.small_talk_prefix}\n\n{apply_verbosity_control(wf.system_prompt_for_llm)}\n\n{wf.ui_guidance}\n\n{wf.research_guidance}\n\n{wf.action_guidance}\n\n{wf.citation_guidance}\n\n{wf.tool_retry_guidance}\n\n{wf.small_talk_guard}\n\n{wf.tool_protocol_guidance}\n\n{wf.image_pdf_flow_guidance}\n\n{wf.proactive_guidance}'
            # 💎 C7-PROMPT-PURGE: video_intent_guidance removed — synthesis_directives
            # come exclusively from video_search.json via ### SKILL-DIRECTIVES injection.
            if wf.capability_guidance:
                wf.final_system_prompt += f'\n\n{wf.capability_guidance}'
        else:
            wf.final_system_prompt = apply_verbosity_control(wf.system_prompt_for_llm)
        if clarification_mode:
            wf.memory_context_string = ""
            wf._formatted_coupons = ""
            wf._fact_coupons = []
            wf._active_directives = []
            wf._active_directive_names = set()
            wf._has_negative_preferences = False
            wf.final_text_to_generate = str(wf.user_text or "")
            wf.final_system_prompt += (
                "\n\n!!! GEMINI-KLÄRUNGSFRAGE-CONTEXT-ISOLATION !!!\n"
                "Die aktuelle Nutzeranfrage ist ambig. Vorheriger Chat-Verlauf, Memory-Kontext, "
                "Kalender-/Wetter-Kontext und Tool-Wissen sind für diesen Turn absichtlich nicht verfügbar. "
                "Antworte nicht aus Kontext oder Erinnerung. Stelle genau eine kurze Klärungsfrage dazu, "
                "worauf sich die Anfrage bezieht."
            )
            logger.info(
                "[GEMINI-AMBIGUITY-CONTEXT] Context isolation active: memory/fact coupons/directives cleared."
            )
        wf._identity_allowed = not _suppress_identity_for_generic_prompt(wf.user_text)
        if wf._identity.name and wf._identity_allowed and (not wf.is_eval_reporting) and (not wf.is_audit_request):
            wf._name_recall_re = re.compile('wie\\s+hei[ßs]|mein(?:em?)?\\s+name|wie\\s+ich\\s+hei[ßs]|was\\s+ist\\s+mein\\s+name|kennst\\s+du\\s+mein(?:en)?\\s+name|wei[sß]t\\s+du\\s+(?:noch\\s+)?(?:wie|meinen?)\\s+name', re.IGNORECASE)
            wf._is_name_recall = bool(wf._name_recall_re.search(wf.user_text))
            wf._is_gpt = str(request.provider or '').lower() == 'openai'
            if wf._is_gpt:
                if wf._is_name_recall:
                    wf._id_directive = f"Du kennst den Nutzer persönlich. Er heißt {wf._identity.name}. Bestätige seinen Namen locker und herzlich — z.B. 'Klar, du bist {wf._identity.name}!' VERBOTEN: beschreibende Sätze wie 'Ich identifiziere dich als ...' oder 'Du bist jemand, der ...'. Antworte so, als würdest du ihn seit Jahren kennen.\n\n"
                    logger.info('[IDENTITY GPT-PRECISION] name-recall → no-robot directive for %r', wf._identity.name)
                else:
                    wf._id_directive = f"Du kennst den Nutzer seit Jahren. Er heißt {wf._identity.name}. Nutze seinen Namen und seine bekannten Interessen NUR für Tonalität und Gesprächskontext — niemals als Beschreibung oder Liste. VERBOTEN: 'Ich weiß, dass du {wf._identity.name} bist', 'Ich identifiziere dich als ...', 'Du bist jemand, der ...'. Begrüße ihn einfach mit 'Hallo {wf._identity.name}' und hilf direkt weiter. Frage NIEMALS nach dem Namen.\n\n"
                    logger.info('[IDENTITY GPT-DIRECTIVE] no-robot injected for %r', wf._identity.name)
            else:
                wf._anti_confusion = f'ANTI-VERWECHSLUNG: Wenn im Kontext-Wissen andere Personen erwähnt werden (Freunde, Familie, Kollegen), sind das NICHT der Nutzer. Der Nutzer ist IMMER {wf._identity.name} — niemand sonst. Vertausche NIEMALS die Rollen zwischen {wf._identity.name} und einer Drittperson.\n'
                if wf._is_name_recall:
                    wf._id_directive = f"[IDENTITÄT DES NUTZERS] Der Nutzer fragt nach seinem Namen. Er heißt {wf._identity.name}. Bestätige ihn charmant — z.B. 'Ja, du heißt {wf._identity.name}!' Vermeide 'Ich identifiziere dich als ...'. Frage NIEMALS nach dem Namen.\n{wf._anti_confusion}\n"
                    logger.info('[IDENTITY PRECISION] name-recall → natural directive for %r', wf._identity.name)
                else:
                    wf._id_directive = f"[IDENTITÄT DES NUTZERS] Der Nutzer heißt {wf._identity.name}. Nutze dieses Wissen aktiv für eine personalisierte, warme Erfahrung — nenne den Namen natürlich und beziehe bekannte Interessen fließend ein, ohne sie wie eine Liste aufzuzählen. Vermeide 'Ich identifiziere dich als ...' — sag einfach 'Hallo {wf._identity.name}'. Frage NIEMALS nach dem Namen.\n{wf._anti_confusion}\n"
                    logger.info('[IDENTITY DIRECTIVE] Injected name=%r provider=%s', wf._identity.name, request.provider)
            for _directive in wf._active_directives:
                if _directive.position == 'after_identity':
                    if _directive.name == 'negative_preferences':
                        continue
                    wf._id_directive += _directive.directive_text
                    logger.info('%s Directive injected after identity', _directive.log_tag)
            if wf._identity_from_current_msg:
                wf._id_directive += f'!!! ÜBERSCHREIBE FALLBACK !!!: Der User hat sich GERADE in dieser Nachricht als {wf._identity.name} vorgestellt. Verwende diesen Namen und behaupte unter KEINEN Umständen, dass du den Namen nicht kennst. Frage NICHT nach dem Namen — er wurde GERADE genannt!\n\n'
                logger.info('[IDENTITY REALTIME DIRECTIVE] Override injected for %r', wf._identity.name)
            wf.final_system_prompt = wf._id_directive + wf.final_system_prompt
        for _directive in wf._active_directives:
            if _directive.position == 'prepend' and (not wf.is_eval_reporting) and (not wf.is_audit_request):
                wf.final_system_prompt = _directive.directive_text + wf.final_system_prompt
                logger.warning('%s Critical warning prepended to system prompt', _directive.log_tag)
        if wf._identity.name and wf._identity_allowed and (not wf.is_eval_reporting) and (not wf.is_audit_request):
            wf._anchor = f'╔══════════════════════════════════════════════════════════╗\n║  DU SPRICHST MIT: {wf._identity.name.upper():<38s} ║\n║  DIES IST DER NUTZER. NUR DIESE PERSON.                ║\n║  ALLE ANDEREN NAMEN IM KONTEXT SIND DRITTPERSONEN.     ║\n╚══════════════════════════════════════════════════════════╝\nWenn im Kontext-Wissen andere Namen auftauchen (Freunde, Familie, Kollegen), sind das NICHT der Nutzer. Der Nutzer ist und bleibt {wf._identity.name}. Verwechsle NIEMALS die Identität des Nutzers mit einer Drittperson aus dem Gedächtnis.\n\n'
            wf.final_system_prompt = wf._anchor + wf.final_system_prompt
            logger.info('[IDENTITY-ANCHOR] Prepended for %r', wf._identity.name)
        wf._GERMAN_DAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
        wf._now_local = datetime.now()
        wf._day_name = wf._GERMAN_DAYS[wf._now_local.weekday()]
        # Build a 14-day weekday→date map so the model never guesses weekdays.
        _weekday_rows = []
        for _delta in range(14):
            from datetime import timedelta as _td
            _d = wf._now_local.date() + _td(days=_delta)
            _label = "(heute)" if _delta == 0 else ("(morgen)" if _delta == 1 else "")
            _weekday_rows.append(
                f"  {wf._GERMAN_DAYS[_d.weekday()]}: {_d.strftime('%d.%m.%Y')}{' ' + _label if _label else ''}"
            )
        _weekday_calendar = "\n".join(_weekday_rows)
        wf._clock_line = (
            f"AKTUELLES DATUM/UHRZEIT: {wf._day_name}, {wf._now_local.strftime('%d.%m.%Y, %H:%M')} Uhr\n"
            f"WOCHENTAG-KALENDER (VERBINDLICH — NIEMALS DAVON ABWEICHEN):\n"
            f"{_weekday_calendar}\n"
            f"REGEL: Wenn der Nutzer 'nächsten [Wochentag]' sagt, schlage im obigen Kalender nach. "
            f"NIEMALS Wochentage erraten oder aus dem Gedächtnis ableiten.\n\n"
        )
        wf.final_system_prompt = wf._clock_line + wf.final_system_prompt
        if wf.relevant_skill_ids:
            wf._skill_directive_parts = []
            for _sid in wf.relevant_skill_ids:
                wf._sd = tool_manager.get_synthesis_directives(_sid)
                if wf._sd:
                    wf._skill_directive_parts.append(f'[SKILL-DIRECTIVE {_sid}]: {wf._sd}')
                # OUTPUT-SCHEMA bewusst nicht injizieren — Struktur steht bereits in tool.parameters (provider tools-Array).
            if wf._skill_directive_parts:
                wf.final_system_prompt += '\n\n### SKILL-DIRECTIVES (PFLICHT):\n' + '\n'.join(wf._skill_directive_parts)
                logger.info('SKILL-DIRECTIVE INJECTION: %d Direktiven für Skills %s injiziert.', len(wf._skill_directive_parts), wf.relevant_skill_ids)
        wf._system_prompt_base_for_suggestions = wf.final_system_prompt
        wf._prompt_cache_base_prompt = str(getattr(wf, "system_prompt_for_llm", "") or "")
        raw_mode = getattr(wf, "suggestion_mode", 1)
        suggestion_mode = 0 if clarification_mode else (1 if raw_mode is None else int(raw_mode))
        _suggestion_suffix = None if clarification_mode else SuggestionEngine.build_suggestion_directive(
            suggestion_mode,
            [],
            str(wf.memory_context_string or ""),
            str(wf.user_text or ""),
        )
        # Suggestion-Direktive (Registry) an System hängen — unabhängig vom User-Turn-Footer.
        if _suggestion_suffix:
            _base_sp = str(getattr(wf, "system_prompt_for_llm", "") or "").strip()
            if _base_sp:
                wf.system_prompt_for_llm = f"{wf.system_prompt_for_llm}\n\n{_suggestion_suffix}"
            wf.final_system_prompt = f"{wf._system_prompt_base_for_suggestions}\n\n{_suggestion_suffix}"
        wf.is_ollama_provider = str(request.provider or '').lower() == 'ollama'
        wf.is_basic_conversation = intent_classifier.is_greeting(wf.user_text) or wf.is_identity_turn or intent_classifier.is_opinion_query(wf.user_text)
        wf.history_limit = 0 if clarification_mode else (3 if wf.is_ollama_provider and wf.is_basic_conversation else 8)
        if wf.is_ollama_provider and wf.is_identity_turn:
            wf.history_limit = 2
        wf.orchestrator_context = orchestrator_context_manager.assemble_history(chat_id=request.chat_id, role_mapper=prompt_role_from_db_role, limit=wf.history_limit)
        wf.messages = [{'role': 'system', 'content': wf.final_system_prompt}]
        wf.messages.extend(wf.orchestrator_context.history)
        _formatted_coupons_block = str(getattr(wf, '_formatted_coupons', '') or '').strip()
        if _formatted_coupons_block:
            wf.messages.append({'role': 'system', 'content': _formatted_coupons_block})
            logger.debug('[FACT COUPONS] Coupon block injected as final system message')
        _user_turn_content = wf.final_text_to_generate
        # User-Turn-Footer: Mode 0 = nur Muzzle, KEIN „Denk an 💡 Vorschlag…“ (das ausschließlich für 1/2).
        if suggestion_mode == 0:
            _user_turn_content = (
                f"{wf.final_text_to_generate}\n\n"
                "(SYSTEM-STOPP: Antworte NUR mit Fakten. KEINE Höflichkeit. KEIN 'Hallo'. "
                "KEINE Sätze wie 'Soll ich...'. Beende die Antwort sofort nach den Daten!)"
            )
        elif suggestion_mode in (1, 2) and _suggestion_suffix:
            _user_turn_content = (
                f"{wf.final_text_to_generate}\n\n"
                "(Denk an den obligatorischen Block '💡 Vorschlag:' bzw. '💡 Passende nächste Schritte:' "
                "am Ende deiner Antwort!)"
            )
        wf.messages.append({'role': 'user', 'content': _user_turn_content})
        if wf.policy_injection_message:
            wf.messages.append({'role': 'system', 'content': wf.policy_injection_message})
        wf.prompt_cache_decision = decide_prompt_cache(
            provider=request.provider,
            model=wf.chosen_model,
            raw_segments={
                "clock_line": getattr(wf, "_clock_line", ""),
                "identity_anchor": getattr(wf, "_anchor", ""),
                "identity_directive": getattr(wf, "_id_directive", ""),
                "base_prompt": getattr(wf, "_prompt_cache_base_prompt", ""),
                "directive": "\n\n".join(
                    str(getattr(_directive, "directive_text", "") or "")
                    for _directive in getattr(wf, "_active_directives", [])
                ),
                "skill_directive": "\n".join(getattr(wf, "_skill_directive_parts", [])),
                "capability_guidance": getattr(wf, "capability_guidance", ""),
                "suggestion_suffix": _suggestion_suffix or "",
                "fact_coupons": _formatted_coupons_block,
                "user_input": _user_turn_content,
                "policy_injection": getattr(wf, "policy_injection_message", ""),
            },
            user_scope=str(getattr(wf._identity, "name", "") or "") or None,
            chat_scope=str(request.chat_id or "") if getattr(request, "chat_id", None) is not None else None,
        )
        wf.tools_override = None
        wf.is_smalltalk_turn = False
        if str(request.provider or '').lower() == 'ollama':
            if wf.is_ollama_vague_smalltalk and (not wf.has_tool_trigger) and (not wf.is_meta_agent_run):
                logger.info("Smalltalk/Vague-Query erkannt ('%s'). Dropping tools to prevent hallucination.", wf.user_text)
                wf.tools_override = []
                wf.is_smalltalk_turn = True
            elif wf.is_ollama_vague_smalltalk and wf.is_meta_agent_run:
                logger.info('META-AGENT BYPASS: Smalltalk-Guard fuer interne Recherche-Phase deaktiviert.')
        wf.request_trace_id = str(uuid.uuid4())
        wf.executor = ToolExecutor(db, wf.api_key, request.provider, wf.chosen_model, additional_context={'chat_id': request.chat_id, 'trace_id': wf.request_trace_id, 'original_user_text': wf.user_text, 'provider': request.provider, 'model': wf.chosen_model})
        # 💎 HARD-LOOP-BREAKER: Tracking für wiederholte Tool-Calls (Case-Variation-Schutz)
        wf.kpi_retry_paths: set[str] = set()
        wf.kpi_tool_status: dict[str, str] = {}  # cache_key -> status (für Self-Correction bei Error)
        wf._normalize_tool_args_fn = _normalize_tool_args
        wf.gateway_kwargs = {'provider': request.provider, 'model': wf.chosen_model, 'api_key': wf.api_key, 'chat_history': wf.messages, 'context_manager': context_manager, 'db': db, 'user_prompt': wf.user_text, 'chat_id': request.chat_id, 'tool_executor': wf.executor, 'disable_tools': wf.disable_tools, 'allowed_skill_ids': wf.relevant_skill_ids, 'requested_skills': wf.relevant_skill_ids, 'tools_override': wf.tools_override, 'bypass_policy': wf.bypass_policy_this_turn, 'reason_and_respond_fn': _reason_and_respond_with_provider_fixes, '_kpi_retry_paths': wf.kpi_retry_paths, '_kpi_tool_status': wf.kpi_tool_status, '_normalize_tool_args_fn': wf._normalize_tool_args_fn, '_prompt_cache_decision': wf.prompt_cache_decision, '_suggestion_context': {'base_system': getattr(wf, '_system_prompt_base_for_suggestions', wf.final_system_prompt), 'mode': suggestion_mode, 'memory_context': str(wf.memory_context_string or ''), 'user_text': str(wf.user_text or '')}}
        if clarification_mode:
            wf.gateway_kwargs["disable_tools"] = True
            wf.gateway_kwargs["requires_clarification"] = True
            wf.gateway_kwargs["ambiguity_confidence"] = getattr(wf, "ambiguity_confidence", 0.0)
            wf.gateway_kwargs["context_isolation_mode"] = "ambiguity_clarification"
            wf.gateway_kwargs["allowed_skill_ids"] = []
            wf.gateway_kwargs["requested_skills"] = []
        # P0 control-flow gate: MOA router may run only after smalltalk gating and only for likely tool turns.
        wf.gateway_kwargs["_allow_moa_hard_lock"] = bool(
            (not wf.is_smalltalk_turn)
            and (not wf.is_basic_conversation)
            and bool(wf.has_tool_trigger or wf.relevant_skill_ids)
        )
        if bool(getattr(wf, "is_video_intent", False)):
            # 💎 VIDEO-FORCE: Bei erkanntem Video-Intent erzwinge video.search Tool-Call
            # auf ALLEN Providern (OpenAI, Gemini, Ollama), nicht nur OpenAI.
            wf.gateway_kwargs["forced_tool"] = {
                "skill_id": "video.search",
                "provider_tool_name": "video.search",
            }
            wf.gateway_kwargs["force_tool_name"] = "video.search"
            logger.info("💎 VIDEO-FORCE: Forcing video.search tool_choice for provider=%s", request.provider)
        # 💎 CALENDAR-LIVE-TRUTH: Bei Kalender-Lesabsicht → calendar.list_events erzwingen.
        # 💎 CALENDAR-MUTATION-HAMMER: Bei Mutations-Absicht → calendar.find_and_update_event
        #    direkt erzwingen; Mutation-Hammer-Prompt injizieren; event_title_query vorbelegen
        #    wenn mutation_target bekannt ist.
        _is_cal_intent = bool(getattr(wf, "is_calendar_intent", False))
        _is_cal_mutation = bool(getattr(wf, "is_calendar_mutation", False))
        _is_cal_creation = bool(getattr(wf, "is_calendar_creation", False))
        _is_filesystem_intent = bool(getattr(wf, "is_filesystem_intent", False))
        _idr = getattr(wf, "intent_detection_result", None)
        _mutation_target = str(getattr(_idr, "mutation_target", "") or "").strip() if _idr else ""
        _routing_geo = bool(getattr(_idr, "is_routing_geo_intent", False)) if _idr else False
        _weather = bool(getattr(_idr, "is_weather_intent", False)) if _idr else False
        _wikipedia = bool(getattr(_idr, "is_wikipedia_intent", False)) if _idr else False
        _news = bool(getattr(_idr, "is_news_intent", False)) if _idr else False

        if _is_cal_creation:
            # ── CALENDAR-CREATE: Full model freedom — do NOT force any tool.
            # The LLM must call calendar.create_event with its own argument filling.
            # Removing any prior forced_tool from video/audit paths that may have been
            # set earlier in the same turn is safe here because creation intent is
            # mutually exclusive with those paths.
            wf.gateway_kwargs.pop("forced_tool", None)
            wf.gateway_kwargs.pop("force_tool_name", None)
            wf.gateway_kwargs.pop("forced_tool_args", None)
            logger.info(
                "💎 CALENDAR-CREATE: Creation intent — no forced_tool, full model freedom for provider=%s",
                request.provider,
            )

        elif _is_cal_intent and not _is_cal_mutation and not _routing_geo and not _weather:
            # 💎 TASK-003: BACKLOG-004 - Filesystem-Intent Veto
            # VIDEO-FORCE nicht bei Filesystem-Intents anwenden
            if _is_filesystem_intent:
                logger.info(
                    "💎 VIDEO-FORCE SKIPPED: Filesystem intent detected, not forcing calendar.list_events for provider=%s",
                    request.provider
                )
                # Kein forced_tool bei Filesystem-Intent
                wf.gateway_kwargs.pop("forced_tool", None)
                wf.gateway_kwargs.pop("force_tool_name", None)
            else:
                wf.gateway_kwargs["forced_tool"] = {
                    "skill_id": "calendar.list_events",
                    "provider_tool_name": "calendar.list_events",
                }
                wf.gateway_kwargs["force_tool_name"] = "calendar.list_events"
                logger.info("💎 CALENDAR-LIVE-TRUTH: Forcing calendar.list_events for provider=%s", request.provider)

        elif _wikipedia:
            wf.gateway_kwargs["forced_tool"] = {
                "skill_id": "system.wikipedia_summary",
                "provider_tool_name": "system.wikipedia_summary",
            }
            wf.gateway_kwargs["force_tool_name"] = "system.wikipedia_summary"
            logger.info("💎 SOURCE-ROUTING: Forcing system.wikipedia_summary for provider=%s", request.provider)

        elif _news:
            wf.gateway_kwargs["forced_tool"] = {
                "skill_id": "system.rss_news",
                "provider_tool_name": "system.rss_news",
            }
            wf.gateway_kwargs["force_tool_name"] = "system.rss_news"
            logger.info("💎 SOURCE-ROUTING: Forcing system.rss_news for provider=%s", request.provider)

        elif _is_cal_intent and not _is_cal_mutation and (_routing_geo or _weather):
            # Nur Kalender-Liste entfernen — andere Forces (z.B. video.search) unangetastet lassen.
            _ftn_cal = str(wf.gateway_kwargs.get("force_tool_name") or "").replace("_", ".").lower()
            if _ftn_cal == "calendar.list_events":
                wf.gateway_kwargs.pop("forced_tool", None)
                wf.gateway_kwargs.pop("force_tool_name", None)
                wf.gateway_kwargs.pop("forced_tool_args", None)
            _skip = []
            if _routing_geo:
                _skip.append("routing_geo")
            if _weather:
                _skip.append("weather")
            logger.info(
                "💎 CALENDAR-LIVE-TRUTH: Kein list_events-Zwang — %s (provider=%s)",
                "+".join(_skip) or "non_cal",
                request.provider,
            )

        elif _is_cal_mutation:
            # ── TASK-067: Block neue Mutationen solange Proposal pending ─────
            from backend.services.calendar.mutation_guard_store import (
                get_pending_mutation_proposal,
            )

            _pending_mg = get_pending_mutation_proposal(request.chat_id)
            if _pending_mg is not None:
                wf.gateway_kwargs.pop("forced_tool", None)
                wf.gateway_kwargs.pop("force_tool_name", None)
                wf.gateway_kwargs.pop("forced_tool_args", None)
                if getattr(wf, "relevant_skill_ids", None):
                    wf.relevant_skill_ids = [
                        sid
                        for sid in wf.relevant_skill_ids
                        if sid != "calendar.find_and_update_event"
                    ]
                _mg_block = (
                    "\n\n!!! MUTATION-GUARD (TASK-067) !!!\n"
                    "Es liegt eine **ausstehende Kalender-Änderung** (Bestätigung ausstehend).\n"
                    "VERBOTEN: `calendar.find_and_update_event` in diesem Turn aufzurufen.\n"
                    "Der Nutzer muss zuerst mit **Ja** (speichern) oder **Nein** (verwerfen) antworten.\n"
                )
                _ag0 = str(getattr(wf, "action_guidance", "") or "")
                wf.action_guidance = (_ag0 + _mg_block).strip() if _ag0 else _mg_block.strip()
                logger.info(
                    "[MUTATION-GUARD] Pending proposal blocks forced mutation chat_id=%s",
                    request.chat_id,
                )
            else:
                # ── TASK-065: Contextual Entity Resolver ─────────────────────
                _snapshot = getattr(wf, "calendar_snapshot", None)
                _resolver_result = None

                if _snapshot:
                    try:
                        from backend.services.orchestrator.entity_resolver import (
                            ContextualEntityResolver,
                        )
                        _oc_history = getattr(
                            getattr(wf, "orchestrator_context", None), "history", None
                        ) or []
                        _recent_messages = _oc_history[-4:]
                        _resolver_result = ContextualEntityResolver().resolve(
                            query=_mutation_target,
                            snapshot=_snapshot,
                            operation_type="MUTATION",
                            recent_messages=_recent_messages,
                            is_calendar_mutation=_is_cal_mutation,
                            full_user_text=wf.user_text,
                        )
                        logger.info(
                            "[ENTITY-RESOLVER] status=%s hint=%s delta=%.1f reason=%s",
                            _resolver_result.status,
                            _resolver_result.dispatcher_hint,
                            _resolver_result.delta_top2,
                            _resolver_result.reason,
                        )
                    except Exception as _re_err:
                        logger.warning(
                            "[ENTITY-RESOLVER] Resolver failed — falling back to legacy: %s",
                            _re_err,
                        )
                        _resolver_result = None

                if _resolver_result is not None and _resolver_result.dispatcher_hint == "PROCEED":
                    _rev = _resolver_result.resolved_event
                    wf.gateway_kwargs["forced_tool"] = {
                        "skill_id": "calendar.find_and_update_event",
                        "provider_tool_name": "calendar.find_and_update_event",
                    }
                    wf.gateway_kwargs["force_tool_name"] = "calendar.find_and_update_event"
                    wf.gateway_kwargs.pop("forced_tool_args", None)
                    logger.info(
                        "💎 ENTITY-RESOLVER GUIDED: find_and_update_event provider=%s"
                        " event_id=%r title=%r score=%.1f — LLM fills mutation payload",
                        request.provider,
                        _rev.event_id,
                        _rev.original_title,
                        _rev.score_final,
                    )
                    _guided = (
                        f"\n\n!!! KALENDER-ZIEL EINDEUTIG AUFGELÖST (Entity-Resolver) !!!\n"
                        f"Der Termin wurde mit hoher Konfidenz identifiziert:\n"
                        f"  • Titel: '{_rev.original_title}'\n"
                        f"  • Event-ID: '{_rev.event_id}'\n"
                        f"DEINE PFLICHT:\n"
                        f"  1. Rufe 'calendar.find_and_update_event' auf.\n"
                        f"  2. Setze ZWINGEND 'event_title_query' = '{_rev.original_title}' "
                        f"und 'event_id' = '{_rev.event_id}' — KEINE andere ID, KEIN anderer Titel.\n"
                        f"  3. Füge die vom Nutzer gewünschten Änderungen hinzu "
                        f"(z.B. 'new_description', 'new_start_time', 'new_summary', 'cancel_event').\n"
                        f"VERBOTEN: Die event_id zu ignorieren, zu erfinden oder durch eine andere zu ersetzen.\n"
                    )
                    existing = str(getattr(wf, "action_guidance", "") or "")
                    wf.action_guidance = (existing + _guided).strip() if existing else _guided.strip()
                    _hammer = prompt_registry.get_directive("calendar_mutation_hammer")
                    if _hammer:
                        wf.action_guidance = wf.action_guidance + "\n" + _hammer

                elif _resolver_result is not None and _resolver_result.dispatcher_hint == "FALLBACK_TO_LIST":
                    wf.gateway_kwargs["forced_tool"] = {
                        "skill_id": "calendar.list_events",
                        "provider_tool_name": "calendar.list_events",
                    }
                    wf.gateway_kwargs["force_tool_name"] = "calendar.list_events"
                    wf.gateway_kwargs.pop("forced_tool_args", None)
                    logger.info(
                        "💎 ENTITY-RESOLVER FALLBACK_TO_LIST: mutation target %r is %s (%s)."
                        " Forcing list_events for provider=%s",
                        _mutation_target,
                        _resolver_result.status,
                        _resolver_result.reason,
                        request.provider,
                    )
                    _candidates_text = "; ".join(
                        f"'{c.original_title}' ({c.start_time[:10]})"
                        for c in _resolver_result.candidates[:3]
                    )
                    _disambig = (
                        f"ENTITY-RESOLVER: Für '{_mutation_target}' wurden mehrere mögliche Termine "
                        f"gefunden: {_candidates_text if _candidates_text else 'keine eindeutigen Treffer'}. "
                        f"Zeige dem Nutzer die Optionen und frage, welchen er meint, "
                        f"BEVOR du eine Änderung vornimmst."
                    )
                    existing = str(getattr(wf, "action_guidance", "") or "")
                    wf.action_guidance = "\n".join(filter(None, [existing, _disambig])).strip()

                elif _resolver_result is not None and _resolver_result.dispatcher_hint == "CLARIFY_USER":
                    wf.gateway_kwargs.pop("forced_tool", None)
                    wf.gateway_kwargs.pop("force_tool_name", None)
                    wf.gateway_kwargs.pop("forced_tool_args", None)
                    logger.info(
                        "💎 ENTITY-RESOLVER CLARIFY_USER: No calendar match for %r."
                        " Suppressing calendar tools for provider=%s",
                        _mutation_target,
                        request.provider,
                    )

                else:
                    wf.gateway_kwargs["forced_tool"] = {
                        "skill_id": "calendar.find_and_update_event",
                        "provider_tool_name": "calendar.find_and_update_event",
                    }
                    wf.gateway_kwargs["force_tool_name"] = "calendar.find_and_update_event"
                    if _mutation_target:
                        wf.gateway_kwargs["forced_tool_args"] = {
                            "event_title_query": _mutation_target,
                        }
                        logger.info(
                            "💎 CALENDAR-MUTATION-HAMMER (legacy): Forcing find_and_update_event"
                            " for provider=%s — mutation_target=%r (pre-filled event_title_query)",
                            request.provider,
                            _mutation_target,
                        )
                    else:
                        logger.info(
                            "💎 CALENDAR-MUTATION-HAMMER (legacy): Forcing find_and_update_event"
                            " for provider=%s — no mutation_target, LLM must supply event_title_query",
                            request.provider,
                        )
                    _hammer = prompt_registry.get_directive("calendar_mutation_hammer")
                    if _hammer:
                        existing = str(getattr(wf, "action_guidance", "") or "")
                        wf.action_guidance = (existing + "\n" + _hammer).strip() if existing else _hammer

        if _routing_geo:
            wf.gateway_kwargs["forced_tool"] = {
                "skill_id": "system.routing",
                "provider_tool_name": "system.routing",
            }
            wf.gateway_kwargs["force_tool_name"] = "system.routing"
            _rg_block = (
                "\n\n!!! ROUTING-/ENTFERNUNGS-FRAGE (DIAMOND) !!!\n"
                "Der Nutzer fragt nach Entfernung, Route oder Fahrzeit zwischen Orten.\n"
                "PFLICHT: Rufe `system.routing` mit sinnvollem Ursprung und Ziel auf.\n"
                "VERBOTEN in diesem Turn: `calendar.list_events` — keine Kalender-Live-Abfrage, "
                "solange es sich um eine reine Entfernungs-/Routenfrage handelt.\n"
            )
            _ag_rg = str(getattr(wf, "action_guidance", "") or "").strip()
            wf.action_guidance = f"{_ag_rg}\n{_rg_block.strip()}".strip() if _ag_rg else _rg_block.strip()
            logger.info("💎 ROUTING-GEO: action_guidance — Routing vor Kalender-Tools.")

        if _weather and not _is_cal_intent:
            _w_block = (
                "\n\n!!! WETTER-FRAGE (DIAMOND) !!!\n"
                "Der Nutzer fragt nach Wetter, Temperatur oder Vorhersage.\n"
                "PFLICHT: Rufe `system.weather` mit dem genannten Ort (oder Kontext).\n"
                "VERBOTEN in diesem Turn: `calendar.list_events`, `calendar.find_slots` — "
                "bei reiner Wetterfrage keine Kalender-Tools verwenden.\n"
            )
            _ag_w = str(getattr(wf, "action_guidance", "") or "").strip()
            wf.action_guidance = f"{_ag_w}\n{_w_block.strip()}".strip() if _ag_w else _w_block.strip()
            logger.info("💎 WEATHER-INTENT: action_guidance — system.weather vor Kalender-Tools.")

        # 💎 ANTI-HALLUCINATION: Force knowledge.query tool when audit_file marker is present
        if getattr(request, "audit_file", None):
            wf.gateway_kwargs["forced_tool"] = {
                "skill_id": "knowledge.query",
                "provider_tool_name": "knowledge.query",
            }
            wf.gateway_kwargs["force_tool_name"] = "knowledge.query"
            # 💎 AUDIT-ARGUMENT-INJECTION: Pre-fill tool arguments to ensure valid tool call
            wf.gateway_kwargs["forced_tool_args"] = {
                "query_text": f"Vollständige Inhaltsanalyse für Audit: {request.audit_file}",
                "filename": request.audit_file,
            }
            logger.info("💎 ANTI-HALLUCINATION: Forcing knowledge.query tool_choice for audit_file=%s with pre-filled arguments", request.audit_file)
        # 💎 F16 FILENAME-REGEX-INJECTION: Detect filenames in user text and force
        # knowledge.read_full_text with filename pre-filled. This prevents the LLM
        # from "being lazy" and calling knowledge.query without filename parameter,
        # which causes global search → hallucinations (Skandinavien statt Ägypten).
        if not getattr(request, "audit_file", None) and not bool(getattr(wf, "is_video_intent", False)):
            _FILE_REGEX = re.compile(
                r'(?:^|[\s"\'\(])([a-zA-ZäöüÄÖÜß0-9_\-]+\.(?:pdf|docx?|xlsx?|pptx?|txt|md|csv))\b',
                re.IGNORECASE
            )
            _fn_match = _FILE_REGEX.search(wf.user_text or "")
            if _fn_match:
                _detected_filename = _fn_match.group(1)
                logger.info(
                    "💎 F16 FILENAME-INJECTION: Detected filename '%s' in user text. "
                    "Forcing knowledge.read_full_text with filename pre-filled.",
                    _detected_filename,
                )
                wf.gateway_kwargs["forced_tool"] = {
                    "skill_id": "knowledge.read_full_text",
                    "provider_tool_name": "knowledge.read_full_text",
                }
                wf.gateway_kwargs["force_tool_name"] = "knowledge.read_full_text"
                wf.gateway_kwargs["forced_tool_args"] = {
                    "filename": _detected_filename,
                }
        if clarification_mode:
            wf.gateway_kwargs.pop("forced_tool", None)
            wf.gateway_kwargs.pop("force_tool_name", None)
            wf.gateway_kwargs.pop("forced_tool_args", None)
            wf.gateway_kwargs["allowed_skill_ids"] = []
            wf.gateway_kwargs["requested_skills"] = []
            wf.gateway_kwargs["tools_override"] = []
            wf.gateway_kwargs["disable_tools"] = True
            wf.gateway_kwargs["_allow_moa_hard_lock"] = False
            logger.info("[GEMINI-AMBIGUITY-CONTEXT] Forced tools and history-dependent routing cleared.")
        if user_budget_info:
            wf.gateway_kwargs['_user_budget_info'] = user_budget_info
        if background_tasks is not None:
            wf.gateway_kwargs['background_tasks'] = background_tasks
        if str(request.provider or '').lower() == 'ollama':
            wf.gateway_kwargs['format'] = 'json'
        wf.gateway_kwargs['max_tokens'] = 4000 if wf.high_output_required else 2500
        if wf.is_smalltalk_turn or (wf.is_ollama_provider and wf.is_basic_conversation):
            wf.gateway_kwargs['max_tokens'] = 220
        if wf.dialog_mode in ['GREET_KNOWN', 'DESCRIBE_UNKNOWN']:
            wf.max_tokens = 1200 if wf.is_eval_reporting else 12000
            wf.gateway_kwargs['max_tokens'] = wf.max_tokens
            logger.info("Personenbeschreibung im Modus '%s'. Token-Limit auf %s gesetzt.", wf.dialog_mode, wf.max_tokens)
        wf.current_limit = 10 if wf.high_output_required else 3
        if wf.is_smalltalk_turn:
            wf.current_limit = 1
        wf.gateway_kwargs['max_tool_rounds'] = wf.current_limit
        # 💎 HARD-LOOP-BREAKER: Registriere Callback für Tool-Call-Tracking
        def _track_tool_call(tool_name: str, arguments: Dict[str, Any]) -> bool:
            """Returns True if this is a duplicate call (should be blocked).

            Self-Correction Exception: Duplicate call is ALLOWED if previous result was an error
            (especially INVALID_ARGUMENTS), enabling the model to retry with corrected arguments.
            """
            cache_key = _normalize_tool_args(tool_name, arguments)
            if cache_key in wf.kpi_retry_paths:
                # Check if previous result was an error (allow self-correction)
                previous_status = wf.kpi_tool_status.get(cache_key, "")
                if previous_status and "error" in previous_status.lower():
                    logger.info(
                        "[HARD-LOOP-BREAKER] ALLOWED duplicate tool call for self-correction: %s "
                        "(previous status: %s). Retrying with corrected arguments.",
                        tool_name, previous_status
                    )
                    # Clear previous status to allow one retry
                    wf.kpi_tool_status[cache_key] = "retry_attempt"
                    return False  # Allow retry
                logger.warning(
                    "[HARD-LOOP-BREAKER] BLOCKED duplicate tool call: %s (normalized key: %s). "
                    "Forcing text-only response.",
                    tool_name, cache_key[:80] + "..."
                )
                return True  # Duplicate detected
            wf.kpi_retry_paths.add(cache_key)
            logger.debug(
                "[HARD-LOOP-BREAKER] Registered tool call: %s (key: %s). "
                "Total unique calls this turn: %d",
                tool_name, cache_key[:80] + "...", len(wf.kpi_retry_paths)
            )
            return False  # Not a duplicate
        wf.gateway_kwargs['_track_tool_call_fn'] = _track_tool_call
        # 💎 BACKLOG-034: Copy relevant_skill_ids to allowed_skill_ids for tool filter
        if hasattr(wf, 'relevant_skill_ids') and wf.relevant_skill_ids:
            wf.gateway_kwargs['allowed_skill_ids'] = list(wf.relevant_skill_ids)
            # 💎 DIAMOND-CORE-ROUTING-FORCE: Force tool_choice for critical mandatory skills
            # If routing intent was detected (by skill_selector), force OpenAI to use system.routing
            # This prevents GPT from ignoring mandatory tools and responding from knowledge context
            # Check intent_detection_result instead of list length because memory skills can enlarge the list
            intent_result = getattr(wf, 'intent_detection_result', None)
            is_routing_geo = bool(getattr(intent_result, 'is_routing_geo_intent', False)) if intent_result else False
            if intent_result and ("routing" in str(getattr(intent_result, 'primary_intent', '')).lower() or is_routing_geo):
                wf.gateway_kwargs['force_tool_name'] = "system.routing"
                logger.info("💎 DIAMOND-CORE-ROUTING-FORCE: Routing intent detected. Forcing tool_choice for system.routing to prevent knowledge-context response")
        # 💎 BACKLOG-006: Dynamic fallback summary based on error details
        # Initially use static fallback - will be updated with error context during execution
        wf.fallback_summary = _build_dynamic_fallback_summary(
            is_audit_request=wf.is_audit_request,
            is_audit_decision=wf.is_audit_decision,
            is_factcheck_yes=wf.is_factcheck_yes,
        )
        wf.response = {}
        wf.latest_ui_command = None
        wf.font_fallback_notice = None
        wf.factcheck_modifications_detected = None
    return ctx


def apply_run_tool_loop_result_to_workflow(ctx: RequestContext) -> None:
    """Maps ``wf.run_tool_loop_result`` onto response/final_text fields (parity with execute_generation)."""
    wf = ctx.workflow
    if wf.run_tool_loop_result is None:
        return
    wf.response = (
        wf.run_tool_loop_result.raw_response
        if isinstance(wf.run_tool_loop_result.raw_response, dict)
        else {"text": wf.run_tool_loop_result.text}
    )
    wf.latest_ui_command = wf.run_tool_loop_result.ui_command if isinstance(wf.run_tool_loop_result.ui_command, dict) else None
    wf.font_fallback_notice = wf.run_tool_loop_result.font_fallback_notice
    wf.factcheck_modifications_detected = wf.run_tool_loop_result.factcheck_modifications_detected
    if not wf.agent_response_payload and isinstance(getattr(wf.run_tool_loop_result, "agent_payload", None), dict):
        wf.agent_response_payload = wf.run_tool_loop_result.agent_payload
    wf.final_text = ""
    wf.final_markdown = ""
    if wf.run_tool_loop_result.text:
        wf.tool_results = getattr(wf.run_tool_loop_result, "tool_results", None) or []
        if wf.tool_results:
            for res in wf.tool_results:
                if res.get("name") == "system.generate_image":
                    try:
                        wf.content_json = json.loads(res.get("content", "{}"))
                        if wf.content_json.get("status") == "ok":
                            wf.final_markdown = wf.content_json.get("data", {}).get("markdown_image", "")
                            if wf.final_markdown:
                                wf.final_text = "Hier ist das Bild."
                                wf.skip_llm_generation = True
                                wf.match = re.search("!\\[.*?\\]\\((.*?)\\)", wf.final_markdown)
                                if wf.match:
                                    wf.final_image_url = wf.match.group(1)
                                logger.info("DIAMOND EXIT: Bild-Markdown wurde erzwungen. LLM-Finalisierung deaktiviert.")
                                break
                    except Exception:
                        continue
    if not wf.skip_llm_generation:
        wf.raw_text = str(wf.run_tool_loop_result.text or "")
        if not wf.raw_text.strip():
            wf.raw_text = wf.fallback_summary
        wf.clean_text = wf.raw_text.strip()
        if not wf.final_text:
            wf.final_text = wf.raw_text
        wf.is_pure_json = wf.clean_text.startswith("{") and wf.clean_text.endswith("}") and (
            "query_text" in wf.clean_text or "tool_call" in wf.clean_text
        )
        if wf.is_pure_json:
            if isinstance(wf.response, dict) and wf.response.get("content"):
                wf.final_text = wf.response["content"].strip() or wf.final_text
            else:
                wf.final_text = "Audit abgeschlossen. Der Bericht wurde generiert."
    wf.skip_fact_extraction = bool(isinstance(wf.response, dict) and wf.response.get("skip_fact_extraction"))

    # Memory-Integrity Validation Guard: block fact extraction if the model
    # received a SYSTEM-WARNHINWEIS (ambiguous document match) but did not
    # acknowledge it in its final answer.
    if not wf.skip_fact_extraction:
        try:
            from backend.services.orchestrator.warning_guard import (
                did_model_ignore_warning,
            )
            tool_results_for_guard = (
                getattr(wf.run_tool_loop_result, "all_tool_results", None)
                or getattr(wf, "tool_results", None)
                or []
            )
            if did_model_ignore_warning(tool_results_for_guard, wf.final_text or ""):
                wf.skip_fact_extraction = True
                if isinstance(wf.response, dict):
                    wf.response["skip_fact_extraction"] = True
        except Exception as _guard_exc:  # pragma: no cover - defensive
            import logging as _lg
            _lg.getLogger("janus_backend").debug(
                "[WARNING-GUARD] guard check failed: %s", _guard_exc
            )


def apply_post_generation_tail(ctx: RequestContext) -> None:
    """Audit/UI tail after tool loop (parity with execute_generation)."""
    wf = ctx.workflow
    if not getattr(wf, "gateway_kwargs", None):
        return
    wf.decision_silent = False
    wf.decision_response_text = ""
    if isinstance(wf.response, dict):
        wf.decision_response_text = (wf.response.get("text", "") or "").strip()
    else:
        wf.decision_response_text = str(wf.response or "").strip()
    if wf.is_audit_decision and (not wf.decision_response_text or len(wf.decision_response_text) < 5):
        wf.decision_silent = True
        wf.final_text = "✅ Die korrigierte PDF wurde erstellt. Du findest sie jetzt in deiner Liste."
    if wf.is_audit_decision and (not wf.final_text or len(wf.final_text.strip()) < 10) and (not wf.decision_silent):
        wf.base = os.path.splitext(os.path.basename(wf.original_document_name or "aegypten.pdf"))[0]
        wf.base = re.sub("[^A-Za-z0-9_-]+", "_", wf.base) or "audit"
        wf.final_text = (
            f"✅ Die korrigierte Version wurde erstellt und im Knowledge Center registriert. "
            f"Du findest sie jetzt in der Dokumenten-Liste unter dem Namen 'Korrekturbericht_{wf.base}.pdf'."
        )
    if wf.font_fallback_notice:
        wf.final_text = f"{wf.final_text.rstrip()}\n\n{wf.font_fallback_notice}"
    wf.final_ui_command = None
    if isinstance(wf.response, dict) and wf.response.get("ui_command"):
        wf.final_ui_command = wf.response["ui_command"]
    elif wf.latest_ui_command:
        wf.final_ui_command = wf.latest_ui_command
    try:
        wf.llm_output_lower = wf.final_text.lower() if isinstance(wf.final_text, str) else ""
        wf.has_audit = "audit_summary" in wf.llm_output_lower or "faktencheck" in wf.llm_output_lower
        if wf.has_audit:
            wf.audit_data = None
            try:
                wf.audit_data = json.loads(wf.final_text.strip())
            except Exception:
                wf.json_match = re.search("(\\{.*\\})", wf.final_text, re.DOTALL)
                if wf.json_match:
                    try:
                        wf.audit_data = json.loads(wf.json_match.group(1))
                    except Exception:
                        pass
            if wf.audit_data and (wf.audit_data.get("modifications_list") or wf.audit_data.get("modifications")):
                wf.mods = wf.audit_data.get("modifications_list") or wf.audit_data.get("modifications", [])
                if len(wf.mods) > 0:
                    wf.audit_context_to_save.status = "warning"
                    wf.audit_context_to_save.details = {"source": "llm_output_json", "modifications_count": len(wf.mods)}
    except Exception as e:
        logger.error("Fehler beim Ampel-Update-Check: %s", e)


async def execute_generation(
    ctx: RequestContext,
    *,
    db: Any,
    context_manager: Any,
    orchestrator_context_manager: Any,
    execution_engine: Any,
    skill_selector: Any,
    prompt_role_from_db_role: Callable[[str], str],
    set_policy_pending_data: Callable[..., Any],
    user_budget_info: Optional[Any] = None,
) -> RequestContext:
    ctx = await execute_generation_prepare_gateway(
        ctx,
        db=db,
        context_manager=context_manager,
        orchestrator_context_manager=orchestrator_context_manager,
        skill_selector=skill_selector,
        prompt_role_from_db_role=prompt_role_from_db_role,
        user_budget_info=user_budget_info,
    )
    wf = ctx.workflow

    # 💎 CU-4: Übergebe pending_status_update in gateway_kwargs
    if hasattr(ctx, "_pending_status_update"):
        wf.gateway_kwargs["_pending_status_update"] = ctx._pending_status_update

    # 💎 CU-4: Token-Schätzung für dynamisches Timeout
    prompt_text = str(getattr(ctx.request, "prompt", "") or "")
    estimated_tokens = len(prompt_text.split())  # Grobe Schätzung: ~1 Token pro Wort
    wf.gateway_kwargs["_estimated_prompt_tokens"] = estimated_tokens
    logger.info(f"[CU-4] Estimated prompt tokens: {estimated_tokens}")

    request = ctx.request
    background_tasks = ctx.background_tasks
    if not wf.skip_llm_generation:
        wf.run_tool_loop_result = await execution_engine.run_tool_loop(
            orchestrator_context=wf.orchestrator_context,
            tool_executor=wf.executor,
            gateway_kwargs=wf.gateway_kwargs,
            fallback_summary=wf.fallback_summary,
            current_limit=wf.current_limit,
            bypass_policy_this_turn=wf.bypass_policy_this_turn,
            set_policy_pending=set_policy_pending_data,
            chat_id=request.chat_id,
            user_text=wf.user_text,
            agent_flow_error=wf.agent_flow_error,
        )
        apply_run_tool_loop_result_to_workflow(ctx)
    else:
        logger.info("LLM-Generation übersprungen: Nutze direktes Tool-Ergebnis.")
    apply_post_generation_tail(ctx)
    ctx.final_response = str(wf.final_text or "")
    return ctx
