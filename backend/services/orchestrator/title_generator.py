"""Background chat title generation (Smart Chat Naming — Task 021) + category (Task 027)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import keyring

from backend.data import crud
from backend.data.database import SessionLocal
from backend.services import llm_gateway

logger = logging.getLogger("janus_backend")

# Provider-kohärente Background-Modelle (kein Cross-Provider-Fallback).
_BACKGROUND_TITLE_MODEL_BY_PROVIDER: Dict[str, str] = {
    "openai": "gpt-5.4-nano",
    "gemini": "gemini-3-flash-preview",
}

_MAX_TITLE_WORDS = 5

# Smart Grouping (Task 027): feste LLM-Kategorien — DB-Spalte `chats.category`
_CHAT_CATEGORIES = frozenset(
    {"coding", "cooking", "personal", "business", "research", "general"}
)
_DEFAULT_CATEGORY = "general"

_LEAN_SYSTEM_PROMPT = (
    "Du erzeugst einen kurzen Chat-Titel und ordnest die Konversation einer Kategorie zu.\n"
    "Regeln für den Titel: höchstens 5 Wörter; keine Füllwörter; keine Satzzeichen am Ende; "
    "Sprache wie der überwiegende Teil der Nutzernachrichten unten.\n"
    "Antworte NUR mit validem JSON: {\"title\": \"...\", \"category\": \"...\"}. "
    "Nutze für die Kategorie exakt einen der Begriffe aus dieser Liste: "
    "coding, cooking, personal, business, research, general."
)


def _normalize_title(raw: str) -> str:
    s = str(raw or "").strip()
    for ch in ('"', "'", "„", "“", "”", "«", "»"):
        s = s.strip(ch)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[.!?;:,\-–—]+$", "", s).strip()
    words = s.split() if s else []
    if len(words) > _MAX_TITLE_WORDS:
        words = words[:_MAX_TITLE_WORDS]
    out = " ".join(words).strip()
    return out or "Neuer Chat"


def _first_messages_transcript(messages: List[Any], limit: int = 2) -> str:
    lines: List[str] = []
    for m in messages[:limit]:
        role = str(getattr(m, "role", "") or "").strip().lower()
        content = str(getattr(m, "content", "") or "").strip()
        if not content:
            continue
        label = "Nutzer" if role == "user" else "Assistent"
        lines.append(f"{label}: {content}")
    return "\n".join(lines).strip()


def _topic_hash_from_transcript(transcript: str) -> str:
    normalized = re.sub(r"\s+", " ", transcript.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _strip_code_fences(text: str) -> str:
    t = (text or "").strip()
    if not t.startswith("```"):
        return t
    lines = t.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _extract_json_object_fragment(text: str) -> Optional[str]:
    """Erstes vollständiges {...}-Fragment (robust gegen Markdown/Freitext)."""
    s = _strip_code_fences(text)
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(s)):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None


def _normalize_category(raw: Any) -> str:
    s = str(raw or "").strip().lower()
    if s in _CHAT_CATEGORIES:
        return s
    return _DEFAULT_CATEGORY


def _parse_title_category_payload(raw_llm: str) -> Optional[Tuple[str, str]]:
    """
    Parst JSON mit title + category. Gibt None zurück, wenn kein brauchbarer Titel extrahiert werden kann.
    """
    frag = _extract_json_object_fragment(raw_llm)
    if not frag:
        return None
    try:
        data = json.loads(frag)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    title = data.get("title")
    if title is None:
        return None
    title_s = str(title).strip()
    if not title_s:
        return None
    cat = _normalize_category(data.get("category"))
    return (title_s, cat)


def _extract_title_raw_from_llm_result(result: Any) -> str:
    """Extrahiert sichtbaren Text aus call_llm/generate_response (inkl. Edge-Cases)."""
    if not isinstance(result, dict):
        return ""
    if str(result.get("type") or "").strip().lower() == "tool_code":
        logger.warning("[TITLE-JOB] LLM-Antwort ist tool_code ohne Nutzertext — ignoriert.")
        return ""
    text = result.get("text") or result.get("content")
    if text is None and isinstance(result.get("raw_assistant_response"), dict):
        text = (result["raw_assistant_response"] or {}).get("content")
    return str(text or "").strip()


def _get_keyring_api_key(provider: str) -> str:
    key = keyring.get_password("Janus-Projekt", str(provider).lower())
    return (key or "").strip()


def _resolve_title_provider_model_api_key(active_provider: str) -> Tuple[Optional[str], Optional[str], str]:
    """Resolve provider-coherent model + API key for title background jobs."""
    provider = str(active_provider or "").strip().lower()
    model = _BACKGROUND_TITLE_MODEL_BY_PROVIDER.get(provider)
    if not model:
        return None, None, ""
    api_key = _get_keyring_api_key(provider)
    if not api_key:
        return None, None, ""
    return provider, model, api_key


async def run_chat_title_job(chat_id: int, *, active_provider: str) -> None:
    """
    Lädt die ersten zwei Nachrichten, ruft das Speed-Modell via llm_gateway auf,
    speichert den Titel und setzt auto_generated=True sowie last_topic_hash.
    """
    db = SessionLocal()
    try:
        chat = crud.get_chat_by_id(db, chat_id)
        if not chat:
            logger.warning("[TITLE-JOB] Chat %s nicht gefunden.", chat_id)
            return

        messages = crud.get_messages_by_chat_id(db, chat_id)
        if len(messages) < 2:
            logger.info("[TITLE-JOB] Chat %s: weniger als 2 Nachrichten — Abbruch.", chat_id)
            return

        transcript = _first_messages_transcript(messages, limit=2)
        if not transcript:
            logger.info("[TITLE-JOB] Chat %s: leerer Transcript — Abbruch.", chat_id)
            return

        provider, model, api_key = _resolve_title_provider_model_api_key(active_provider)
        if not provider or not model:
            logger.warning(
                "[TITLE-JOB] Kein provider-kohärentes Modell für active_provider='%s' auflösbar.",
                active_provider,
            )
            return
        if not api_key:
            logger.warning("[TITLE-JOB] Kein API-Key für Provider '%s'.", provider)
            return

        user_prompt = (
            f"Konversation (Ausschnitt):\n---\n{transcript}\n---\n"
            "Antworte nur mit dem JSON-Objekt (title + category), keine andere Einleitung."
        )
        messages_llm: List[Dict[str, Any]] = [
            {"role": "system", "content": _LEAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            result = await llm_gateway.call_llm(
                provider=provider,
                model_id=model,
                api_key=api_key,
                messages=messages_llm,
                force_no_tools=True,
                max_completion_tokens=160,
            )
        except Exception as exc:
            logger.error("[TITLE-JOB] LLM-Aufruf fehlgeschlagen (chat=%s): %s", chat_id, exc, exc_info=True)
            return

        raw_text = _extract_title_raw_from_llm_result(result)
        parsed = _parse_title_category_payload(raw_text)
        if not parsed:
            logger.warning(
                "[TITLE-JOB] Chat %s: kein parsbares JSON mit title (raw=%r) — Abbruch ohne last_topic_hash.",
                chat_id,
                (raw_text[:200] + "…") if len(raw_text) > 200 else raw_text,
            )
            return

        raw_title, category = parsed
        title = _normalize_title(raw_title)
        if title == "Neuer Chat" or not str(title).strip():
            logger.warning(
                "[TITLE-JOB] Chat %s: kein brauchbarer Titel nach Normalisierung (raw_title=%r) — Abbruch.",
                chat_id,
                raw_title,
            )
            return

        topic_hash = _topic_hash_from_transcript(transcript)

        chat.title = title
        chat.category = category
        chat.auto_generated = True
        chat.last_topic_hash = topic_hash
        db.add(chat)
        db.commit()
        db.refresh(chat)
        logger.info(
            "[TITLE-JOB] Chat %s Titel=%r category=%r",
            chat_id,
            title,
            category,
        )
    except Exception as exc:
        logger.exception("[TITLE-JOB] Unerwarteter Fehler (chat=%s): %s", chat_id, exc)
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()
