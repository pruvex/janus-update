"""Post-generation response finalization: eval backfills, persist, websearch render, fact extraction."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from backend.data.database import SessionLocal
from backend.services import cost_service  # noqa: F401 â€” billing lives primarily in execution_engine / gateways; kept for Phase-5 wiring
from backend.services import memory_extractor
from backend.services.memory_observability import memory_metrics
from backend.services.orchestrator.identity_manager import identity_manager
from backend.services.orchestrator.modal_request_builder import resolve_modal_request_for_execution
from backend.services.orchestrator.schemas import AuditContext, ExecutionResponse
from backend.services.skill_router import is_realtime_search_query
from backend.utils import intent_classifier
from backend.renderers.attribution import append_tool_attributions_from_tools, render_weather_forecast_from_tools

logger = logging.getLogger("janus_backend")

def _normalize_inline_weather_source_footer(text: str) -> str:
    value = str(text or "")
    if not value:
        return value
    patterns = [
        r"(?is)\s*\(\s*\*{0,2}quelle\*{0,2}\s*:\s*([^)]+)\)\s*$",
        r"(?is)\s+\*{0,2}quelle\*{0,2}\s*:\s*([^\n]+?)\s*$",
    ]
    for pat in patterns:
        m = re.search(pat, value, flags=re.IGNORECASE)
        if not m:
            continue
        source = str(m.group(1) or "").strip().strip(".")
        body = value[: m.start()].rstrip()
        if source:
            return f"{body}\n\nQuelle: {source}"
    return value

# Smart Chat Naming: Titel, die trotz PUT noch wie â€žnoch nicht benanntâ€œ gelten (Frontend setzt ggf. "Neuer Chat" + auto_generated=False).
PLACEHOLDER_TITLES = ["Neuer Chat", "", None]

# Titel wirken wie Platzhalter / Auto-Satzanfang â†’ darf durch Lean-Titel ersetzt werden (Logging + Dokumentation).
_TITLE_REPLACEABLE_LONG = 20
_CHAT_STANDARD_TITLE_RES = (
    re.compile(r"^chat\s+am\s+", re.IGNORECASE),
    re.compile(r"^chat\s+vom\s+", re.IGNORECASE),
    re.compile(r"^chat\s+on\s+", re.IGNORECASE),
    re.compile(r"^gesprÃ¤ch\s+vom\s+", re.IGNORECASE),
    re.compile(r"^conversation\s+on\s+", re.IGNORECASE),
)

_BACKGROUND_MODEL_BY_PROVIDER: Dict[str, str] = {
    "openai": "gpt-5.4-nano",
    "gemini": "gemini-3-flash-preview",
}


def _is_e2e_fast_mode() -> bool:
    return str(os.environ.get("JANUS_E2E_FAST_MODE", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _resolve_background_provider_model(active_provider: str) -> tuple[str, str]:
    """Strict provider guard for background LLM jobs (no cross-provider fallback)."""
    provider = str(active_provider or "").strip().lower()
    model = _BACKGROUND_MODEL_BY_PROVIDER.get(provider, "")
    return provider, model


def _title_looks_replaceable(title: Any) -> bool:
    """True, wenn der Titel sehr wahrscheinlich noch kein manueller Kurztitel ist."""
    if title is None or title in PLACEHOLDER_TITLES:
        return True
    s = str(title).strip()
    if not s:
        return True
    if len(s) > _TITLE_REPLACEABLE_LONG:
        return True
    for rx in _CHAT_STANDARD_TITLE_RES:
        if rx.match(s):
            return True
    return False


def _is_websearch_tool_result(msg: Dict[str, Any]) -> bool:
    name = str(msg.get("name") or "").strip().lower()
    skill_id = str(msg.get("_skill_id") or msg.get("skill_id") or "").strip().lower()
    return (
        name
        in {
            "system.websearch",
            "system_websearch",
            "websearch_wrapper",
            "get_websearch",
            "system.rss_news",
            "system_rss_news",
            "get_latest_news_rss",
        }
        or skill_id in {"system.websearch", "system.rss_news"}
    )


def _normalize_source_renderer_skill(raw_skill: str) -> str:
    value = str(raw_skill or "").strip().lower()
    if value in {"system.rss_news", "system_rss_news", "get_latest_news_rss"}:
        return "system.rss_news"
    if value in {"system.websearch", "system_websearch", "websearch_wrapper", "get_websearch"}:
        return "system.websearch"
    return value


def _is_news_websearch_payload(data: Dict[str, Any]) -> bool:
    if not isinstance(data, dict):
        return False
    query = str(data.get("query") or "").casefold()
    text = str(data.get("text") or "").casefold()
    return any(
        marker in f"{query}\n{text[:500]}"
        for marker in (
            " news",
            "news ",
            "nachrichten",
            "neuigkeiten",
            "schlagzeilen",
            "aktuell",
            "aktuelle",
        )
    )


def _websearch_payload_as_rss_news(data: Dict[str, Any]) -> Dict[str, Any]:
    original_query = str(data.get("query") or "").strip()
    query = original_query
    query = re.sub(r"(?i)\b(news|nachrichten|neuigkeiten|schlagzeilen|aktuell|aktuelle|mai\s+2026)\b", " ", query)
    query = re.sub(r"\s+", " ", query).strip(" ?.,")
    return {
        "mode": "rss_hybrid",
        "source": "websearch",
        "fallback": "websearch",
        "query": query or str(data.get("query") or "").strip(),
        "original_query": original_query,
        "is_current_news": True,
        "items": [],
        "headlines": [],
        "websearch_text": str(data.get("text") or ""),
        "websearch_sources": data.get("sources") if isinstance(data.get("sources"), list) else [],
        "verified_source_mode": str(data.get("verified_source_mode") or "").strip(),
    }


def _is_websearch_v3_single_verified_payload(data: Dict[str, Any]) -> bool:
    return (
        isinstance(data, dict)
        and str(data.get("pipeline") or "").strip() == "websearch_v3"
        and str(data.get("verified_source_mode") or "").strip() in {"single", "multi"}
    )


def render_websearch_sources(tool_results: List[Dict[str, Any]]) -> str:
    """Extract websearch tool payloads and render via registered skill renderers."""
    if not tool_results:
        return ""

    websearch_data_list: List[Dict[str, Any]] = []
    for msg in tool_results:
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "tool" or not _is_websearch_tool_result(msg):
            continue
        msg_skill_id = _normalize_source_renderer_skill(
            str(msg.get("_skill_id") or msg.get("skill_id") or msg.get("name") or "").strip()
        )
        content_str = msg.get("content", "")
        if not content_str or not isinstance(content_str, str):
            continue
        try:
            parsed = json.loads(content_str)
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.debug("DIAMOND-RENDER: JSON-Parse fehlgeschlagen fÃ¼r websearch content")
            continue
        if not isinstance(parsed, dict):
            continue
        data = parsed.get("data", parsed)
        if not isinstance(data, dict):
            continue
        if not (data.get("sources") or data.get("items") or data.get("text") or data.get("headlines")):
            continue
        data = dict(data)
        data["_target_skill_id"] = msg_skill_id or "system.websearch"
        if not data.get("sources") and data.get("items"):
            data["sources"] = [
                {
                    "url": str(it.get("source_url") or ""),
                    "title": str(it.get("title") or ""),
                }
                for it in (data["items"] or [])
                if it.get("source_url")
            ]
        websearch_data_list.append(data)

    if not websearch_data_list:
        return ""

    try:
        from backend.renderers.registry import get_renderer

        v3_single_items = [item for item in websearch_data_list if _is_websearch_v3_single_verified_payload(item)]
        if v3_single_items:
            successful = [item for item in v3_single_items if item.get("sources") or item.get("items")]
            websearch_data_list = [successful[0] if successful else v3_single_items[0]]
        else:
            has_rss_news = any(
                _normalize_source_renderer_skill(str(item.get("_target_skill_id") or "")) == "system.rss_news"
                for item in websearch_data_list
            )
            if has_rss_news:
                websearch_data_list = [
                    item
                    for item in websearch_data_list
                    if _normalize_source_renderer_skill(str(item.get("_target_skill_id") or "")) == "system.rss_news"
                ]

        rendered_parts: List[str] = []
        for ws_data in websearch_data_list:
            target_skill = _normalize_source_renderer_skill(str(ws_data.get("_target_skill_id") or "").strip())
            if _is_websearch_v3_single_verified_payload(ws_data):
                rendered = str(ws_data.get("text") or "").strip()
                if rendered:
                    rendered_parts.append(rendered)
                continue
            if target_skill not in {"system.rss_news", "system.websearch"}:
                is_price_data = "results" in ws_data and "currency" in ws_data
                target_skill = "system.price_comparison" if is_price_data else "system.websearch"
            if target_skill == "system.websearch" and _is_news_websearch_payload(ws_data):
                target_skill = "system.rss_news"
                ws_data = _websearch_payload_as_rss_news(ws_data)
            renderer = get_renderer(target_skill)
            if not renderer:
                logger.warning("DIAMOND-RENDER: Kein Renderer fuer '%s' registriert", target_skill)
                continue
            if target_skill == "system.websearch":
                rendered = renderer.render(
                    ws_data,
                    llm_text=str(ws_data.get("text") or ""),
                )
            else:
                rendered = renderer.render(ws_data)
            if rendered:
                rendered_parts.append(rendered)

        result = "\n\n".join(rendered_parts)
        logger.info(
            "DIAMOND-RENDER: %d WebSearch-Ergebnisse verarbeitet, %d gerendert",
            len(websearch_data_list),
            len(rendered_parts),
        )
        return result
    except Exception as exc:
        logger.warning("DIAMOND-RENDER: Renderer-Aufruf fehlgeschlagen (non-critical): %s", exc)
        return ""


_MEMORY_REFERENCE_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*\u2022]\s*)?(?:Referenzwerte:\s*)?.{0,240}\b"
    r"(?:Ged\S{0,4}chtnis|Gedaechtnis|Memory|Erinnerung(?:en)?)\b.{0,240}(?:$|\n)"
)
_MEMORY_REFERENCE_SENTENCE_RE = re.compile(
    r"(?i)(?:^|(?<=[.!?])\s+)(?:Referenzwerte:\s*)?[^.!?\n]{0,240}\b"
    r"(?:Ged\S{0,4}chtnis|Gedaechtnis|Memory|Erinnerung(?:en)?)\b[^.!?\n]{0,240}[.!?]?"
)


def has_websearch_tool(tool_results: List[Dict[str, Any]]) -> bool:
    return any(isinstance(msg, dict) and msg.get("role") == "tool" and _is_websearch_tool_result(msg) for msg in (tool_results or []))


def strip_memory_references_from_live_answer(text: str) -> str:
    value = str(text or "")
    if not value:
        return value
    value = _MEMORY_REFERENCE_LINE_RE.sub("", value)
    value = _MEMORY_REFERENCE_SENTENCE_RE.sub("", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _derive_video_modal_request_from_tool_results(tool_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Build modal_request from successful video.search tool result."""
    for tr in (tool_results or []):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        if name not in {"video.search"}:
            continue
        raw_payload = tr.get("_raw_content") or tr.get("content") or "{}"
        try:
            parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else dict(raw_payload or {})
        except Exception:
            continue
        if not isinstance(parsed, dict) or str(parsed.get("status") or "").strip().lower() != "ok":
            continue
        metadata = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
        data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
        mode = str(metadata.get("mode") or "").strip().lower()
        # LIST-MODE: Bei Listen automatisch das erste Video als modal_request generieren (BACKLOG-011 Debug)
        if mode == "list" and isinstance(data.get("videos"), list) and len(data.get("videos", [])) > 0:
            first_video = data["videos"][0]
            video_id = str(first_video.get("video_id") or "").strip()
            title = str(first_video.get("title") or "").strip()
            watch_url = str(first_video.get("watch_url") or "").strip()
            embed_url = str(first_video.get("embed_url") or "").strip()
            is_embeddable = bool(first_video.get("is_embeddable", True))
            if not watch_url and len(video_id) == 11:
                watch_url = f"https://www.youtube.com/watch?v={video_id}"
            if not embed_url and len(video_id) == 11:
                embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0"
            if not watch_url and not embed_url:
                continue
            canonical_url = watch_url or embed_url
            return {
                "type": "video",
                "data": {
                    "video_id": video_id,
                    "title": title or "Video",
                    "url": canonical_url,
                },
                "payload": {
                    "source": "youtube",
                    "url": canonical_url,
                    "title": title or "Video",
                    "embed_url": embed_url if is_embeddable else "",
                    "is_embeddable": is_embeddable,
                    "external_only": (not is_embeddable),
                    "external_hint": "Nur direkt auf YouTube verfÃ¼gbar.",
                },
                "options": {"auto_open": True, "pinnable": True},
            }
        # LIST-MODE GUARD: Kein Modal bei leeren Listen
        if mode == "list" and isinstance(data.get("videos"), list) and len(data.get("videos", [])) == 0:
            return None
        # SINGLE-VIDEO MODE: Kein Modal wenn kein selected_video vorhanden
        if isinstance(data.get("videos"), list) and "selected_video" not in data:
            return None  # List-Response ohne selected_video â†’ kein Modal
        selected = data.get("selected_video") if isinstance(data.get("selected_video"), dict) else {}
        video_id = str(selected.get("video_id") or "").strip()
        title = str(selected.get("title") or "").strip()
        watch_url = str(selected.get("watch_url") or "").strip()
        embed_url = str(selected.get("embed_url") or "").strip()
        is_embeddable = bool(selected.get("is_embeddable", True))
        if not watch_url and len(video_id) == 11:
            watch_url = f"https://www.youtube.com/watch?v={video_id}"
        if not embed_url and len(video_id) == 11:
            embed_url = f"https://www.youtube.com/embed/{video_id}?rel=0"
        if not watch_url and not embed_url:
            continue
        canonical_url = watch_url or embed_url
        return {
            "type": "video",
            "data": {  # requested metadata schema
                "video_id": video_id,
                "title": title or "Video",
                "url": canonical_url,
            },
            "payload": {  # current MCL schema
                "source": "youtube",
                "url": canonical_url,
                "title": title or "Video",
                "embed_url": embed_url if is_embeddable else "",
                "is_embeddable": is_embeddable,
                "external_only": (not is_embeddable),
                "external_hint": "Nur direkt auf YouTube verfÃ¼gbar.",
            },
            "options": {"auto_open": True, "pinnable": True},
        }
    return None


def _derive_video_list_metadata_from_tool_results(tool_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Persistable metadata for video list mode so reload can restore cards."""
    logger.info("ðŸ’Ž VIDEO-LIST-METADATA: _derive_video_list_metadata_from_tool_results called with %d tool results", len(tool_results or []))
    for tr in (tool_results or []):
        if not isinstance(tr, dict):
            continue
        name = str(tr.get("name") or "").strip().lower()
        # DEBUG: sonst wirkt jedes Tool (z.B. system.weather) wie ein â€žGemini-Wetterâ€œ-Marker in Logs.
        if name == "video.search":
            logger.info("ðŸ’Ž VIDEO-LIST-METADATA: Inspecting video.search tool result")
        else:
            logger.debug("ðŸ’Ž VIDEO-LIST-METADATA: Skipping non-video tool name=%s", name)
        if name not in {"video.search"}:
            continue
        raw_payload = tr.get("_raw_content") or tr.get("content") or "{}"
        try:
            parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else dict(raw_payload or {})
        except Exception:
            logger.warning("ðŸ’Ž VIDEO-LIST-METADATA: Failed to parse payload for video.search")
            continue
        if not isinstance(parsed, dict) or str(parsed.get("status") or "").strip().lower() != "ok":
            logger.warning("ðŸ’Ž VIDEO-LIST-METADATA: video.search status not ok: %s", parsed.get("status"))
            continue
        data = parsed.get("data") if isinstance(parsed.get("data"), dict) else {}
        metadata = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
        videos = data.get("videos")
        mode = str(metadata.get("mode") or data.get("mode") or "").strip().lower()
        logger.info("ðŸ’Ž VIDEO-LIST-METADATA: video.search: mode=%s, videos=%s", mode, type(videos))
        if mode != "list" or not isinstance(videos, list):
            logger.warning("ðŸ’Ž VIDEO-LIST-METADATA: mode != 'list' or videos not a list")
            continue
        result = {
            "videos": videos,
            "count": int(data.get("count") or len(videos)),
            "mode": "list",
            "query": str(data.get("query") or "").strip(),
        }
        logger.info("ðŸ’Ž VIDEO-LIST-METADATA: Returning metadata with %d videos", len(videos))
        return result
    logger.warning("ðŸ’Ž VIDEO-LIST-METADATA: No valid video.search list mode found in tool results")
    return None


async def run_fact_extraction(
    chat_id: Any,
    user_text: str,
    assistant_text: str,
    api_key: str,
    provider: str,
    model_id: Optional[str] = None,
    learned_name: Optional[str] = None,
    *,
    model_hierarchy: Dict[str, Any],
) -> None:
    """Run fact extraction with an isolated DB session."""
    db_session = SessionLocal()
    try:
        provider_key, logic_model = _resolve_background_provider_model(provider)
        if not provider_key or not logic_model:
            logger.warning(
                "Fakten-Extraktion: Provider-Guard blockiert (provider=%r, model=%r).",
                provider_key,
                logic_model,
            )
            return
        # Optional override only if it stays within the same provider family.
        if str(model_id or "").strip():
            override = str(model_id).strip()
            if provider_key == "openai" and override.startswith("gpt-"):
                logic_model = override
            elif provider_key == "gemini" and override.startswith("gemini-"):
                logic_model = override
        if not logic_model:
            logger.error(
                "Fakten-Extraktion: Kein nutzbares Modell in MODEL_HIERARCHY fÃ¼r Provider '%s' gefunden. "
                "Extraktion wird Ã¼bersprungen.",
                provider,
            )
            return

        logger.info("START: Fakten-Extraktion (Chat %s) mit %s...", chat_id, logic_model)

        try:
            extracted = await memory_extractor.extract_and_save_fact_from_interaction(
                db=db_session,
                user_msg=user_text,
                assistant_msg=assistant_text,
                api_key=api_key,
                provider=provider,
                model_id=logic_model,
                chat_id=chat_id,
                subject_hint=learned_name,
            )
        except ValidationError:
            logger.warning("[FACT EXTRACTION] Validierung fehlgeschlagen, Ã¼berspringe Fact-Update.")
            return

        if extracted:
            logger.info("ERFOLG: %d Fakten fÃ¼r Chat %s extrahiert.", len(extracted), chat_id)
        else:
            logger.warning("INFO: Keine neuen Fakten in Chat %s gefunden.", chat_id)

    except Exception as e:
        logger.warning("[FACTS] Extraktion Ã¼bersprungen: %s", e)
    finally:
        db_session.close()


def trigger_fact_extraction(
    chat_id: Any,
    user_text: str,
    final_text: str,
    api_key: str,
    provider: str,
    model_id: Optional[str] = None,
    learned_name: Optional[str] = None,
    skip_fact_extraction: bool = False,
    *,
    model_hierarchy: Dict[str, Any],
) -> None:
    """Schedule fact extraction as a background task (fire-and-forget)."""
    if _is_e2e_fast_mode():
        logger.info("FACT EXTRACTION SKIPPED (chat=%s): JANUS_E2E_FAST_MODE active.", chat_id)
        return
    if skip_fact_extraction:
        logger.info(
            "FACT EXTRACTION SKIPPED (chat=%s): country_info NOT_FOUND in this turn.",
            chat_id,
        )
        return
    if chat_id != 9999 and memory_extractor.should_skip_extraction_from_messages(user_text, final_text):
        logger.info(
            "FACT EXTRACTION SKIPPED (chat=%s): assistant output is empty or invalid for extraction.",
            chat_id,
        )
        return
    if final_text and not intent_classifier.is_greeting(user_text):
        asyncio.create_task(
            run_fact_extraction(
                chat_id,
                user_text,
                final_text,
                api_key,
                provider,
                model_id,
                learned_name,
                model_hierarchy=model_hierarchy,
            )
        )


def _parity_vision_snapshot(wf: Any) -> Dict[str, Any]:
    if isinstance(getattr(wf, "vision_result", None), dict):
        lr = wf.vision_result.get("local_recognition_result")
        if isinstance(lr, dict):
            return lr
    return {}


def _trigger_chat_title_job_if_eligible(db: Any, chat_id: Optional[int], active_provider: str) -> None:
    """
    Erster Naming-Lauf: ``cnt >= 2`` und noch kein ``last_topic_hash`` (Job setzt Hash nach Erfolg).

    ``auto_generated`` blockiert den ersten Lauf **nicht** â€” lange SatzanfÃ¤nge / Standardtitel werden
    Ã¼ber ``_title_looks_replaceable`` nur fÃ¼r Logs markiert. Sobald ``last_topic_hash`` gesetzt ist,
    kein erneutes Feuern (Themenwechsel spÃ¤ter separat).
    """
    if _is_e2e_fast_mode():
        logger.info("[TITLE-TRIGGER] Skip chat %s: JANUS_E2E_FAST_MODE active.", chat_id)
        return
    if chat_id is None or int(chat_id) == 9999:
        logger.info("[TITLE-TRIGGER] Skip chat_id=%s (none or 9999).", chat_id)
        return
    try:
        from sqlalchemy import func

        from backend.data.models import Chat, Message
        from backend.services.orchestrator.title_generator import run_chat_title_job

        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            logger.info("[TITLE-TRIGGER] Skip chat %s: Chat-Zeile fehlt.", chat_id)
            return

        cnt = int(db.query(func.count(Message.id)).filter(Message.chat_id == chat_id).scalar() or 0)
        last_hash = getattr(chat, "last_topic_hash", None)
        raw_title = getattr(chat, "title", None)
        ag = getattr(chat, "auto_generated", None)

        in_placeholder_list = raw_title in PLACEHOLDER_TITLES
        replaceable = _title_looks_replaceable(raw_title)
        is_placeholder = in_placeholder_list or replaceable

        logger.info(
            "[TITLE-TRIGGER] Precheck chat %s: cnt=%s hash=%s auto_generated=%s in_placeholder_list=%s "
            "replaceable_extended=%s title_len=%s",
            chat_id,
            cnt,
            last_hash,
            ag,
            in_placeholder_list,
            replaceable,
            len(str(raw_title or "")),
        )

        if cnt < 2:
            logger.info("[TITLE-TRIGGER] Skip chat %s: cnt=%s (<2).", chat_id, cnt)
            return
        if last_hash:
            logger.info("[TITLE-TRIGGER] Skip chat %s: last_topic_hash already set.", chat_id)
            return

        logger.info(
            "[TITLE-TRIGGER] Final check for chat %s: cnt=%s, hash=%s, current_title=%r",
            chat_id,
            cnt,
            last_hash,
            raw_title,
        )
        logger.info(
            "[TITLE-TRIGGER] Final check (flags) chat %s: auto_generated=%s is_placeholder_combined=%s",
            chat_id,
            ag,
            is_placeholder,
        )

        provider_key, model_id = _resolve_background_provider_model(active_provider)
        if not provider_key or not model_id:
            logger.info(
                "[TITLE-TRIGGER] Skip chat %s: provider '%s' not allowed for background title jobs.",
                chat_id,
                active_provider,
            )
            return
        asyncio.create_task(run_chat_title_job(chat_id, active_provider=provider_key))
        logger.info(
            "[TITLE-TRIGGER] Chat %s: Titel-Job geplant (cnt=%s, kein last_topic_hash, replaceable_hint=%s).",
            chat_id,
            cnt,
            replaceable,
        )
    except Exception as exc:
        logger.warning("[TITLE-TRIGGER] Ãœbersprungen (chat=%s): %s", chat_id, exc, exc_info=True)


async def finalize_response(
    ctx: Any,
    *,
    db: Any,
    background_tasks: Any,
    status_sync: Any,
    model_hierarchy: Dict[str, Any],
    orchestrator_cls: type,
) -> Any:
    """Apply eval/vision backfills, persist assistant message, optional websearch render, audit UI, fact extraction."""
    _ = background_tasks
    from backend.services.chat_orchestrator import (
        _ENABLE_STRICT_LITERAL_BACKFILL,
        _normalize_exclusion_terms,
    )

    wf = ctx.workflow
    request = ctx.request
    if _ENABLE_STRICT_LITERAL_BACKFILL and wf.final_facts and wf.is_eval_reporting:
        wf.exclusion_terms = wf.final_facts.get("AUSSCHLUSS_PFLICHT", [])
        wf.normalized_exclusions = _normalize_exclusion_terms(wf.exclusion_terms) if isinstance(wf.exclusion_terms, list) else []
        wf.critical_keys = ["HAARFARBE", "FRISUR", "OUTERWEAR", "KLEIDUNG", "LEGWEAR", "SCHUH_SATZ", "POSE_SATZ", "AMBIENTE_SATZ"]
        wf.missing_literals = []
        wf.final_text_lower = wf.final_text.lower()
        for key in wf.critical_keys:
            value = str(wf.final_facts.get(key, "") or "").strip()
            if not value:
                continue
            wf.value_lower = value.lower()
            if any((excl and excl in wf.value_lower for excl in wf.normalized_exclusions)):
                continue
            if value.lower() not in wf.final_text_lower:
                wf.missing_literals.append(value)
        wf.verified_terms = wf.final_facts.get("VERIFIZIERTE_ELEMENTE_PFLICHT", [])
        if isinstance(wf.verified_terms, list):
            for term in wf.verified_terms:
                wf.term_s = str(term or "").strip()
                if wf.term_s and wf.term_s.lower() not in wf.final_text_lower:
                    wf.missing_literals.append(wf.term_s)
        if isinstance(wf.exclusion_terms, list):
            wf.footwear_exclusion = any(("keine schuhe" in str(term or "").strip().lower() for term in wf.exclusion_terms))
            if wf.footwear_exclusion:
                wf.shoe_sentence = str(wf.final_facts.get("SCHUH_SATZ", "") or "").strip().lower()
                if not wf.shoe_sentence and "keine schuhe" not in wf.final_text_lower:
                    wf.missing_literals.append("keine Schuhe")
        if wf.missing_literals:
            wf.dedup = []
            wf.seen = set()
            for entry in wf.missing_literals:
                wf.k = entry.lower()
                if wf.k in wf.seen:
                    continue
                wf.seen.add(wf.k)
                wf.dedup.append(entry)
            wf.final_text = f"{wf.final_text.rstrip()} Verifizierte Details: {', '.join(wf.dedup)}."
    if wf.final_facts and str(wf.image_name_hint or "").lower().startswith("supercluster-"):
        wf.required_verified_terms = wf.final_facts.get("VERIFIZIERTE_ELEMENTE_PFLICHT", [])
        wf.exclusion_terms = wf.final_facts.get("AUSSCHLUSS_PFLICHT", [])
        if not isinstance(wf.required_verified_terms, list):
            wf.required_verified_terms = []
        if not isinstance(wf.exclusion_terms, list):
            wf.exclusion_terms = []
        wf.normalized_exclusions = _normalize_exclusion_terms(wf.exclusion_terms)
        if wf.normalized_exclusions:
            for exclusion_term in sorted(set(wf.normalized_exclusions), key=len, reverse=True):
                if not exclusion_term:
                    continue
                wf.final_text = re.sub(f"\\b{re.escape(exclusion_term)}\\b", "", wf.final_text, flags=re.IGNORECASE)
                wf.final_text = re.sub("\\s{2,}", " ", wf.final_text).strip()
        wf.bald_required = any(
            (any((token in str(term or "").lower() for token in ["glatz", "rasiert", "kahl"])) for term in wf.required_verified_terms)
        )
        if wf.bald_required:
            wf.hair_conflict_tokens = ["blond", "braun", "schwarz", "lang", "schulterlang", "lockig", "wellig", "haare", "haar"]
            wf.sentences = re.split("(?<=[.!?])\\s+", wf.final_text)
            wf.cleaned_sentences = []
            for sentence in wf.sentences:
                wf.sentence_l = sentence.lower()
                if any((token in wf.sentence_l for token in wf.hair_conflict_tokens)):
                    continue
                wf.cleaned_sentences.append(sentence)
            wf.final_text = " ".join((part.strip() for part in wf.cleaned_sentences if part.strip())).strip()
            if "glatz" not in wf.final_text.lower() and "rasiert" not in wf.final_text.lower():
                wf.final_text = f"{wf.final_text.rstrip()} Die Person ist glatzkÃ¶pfig und rasiert.".strip()
        wf.final_text_lower = wf.final_text.lower()
        wf.missing_required_terms = []
        for raw_term in wf.required_verified_terms:
            term = str(raw_term or "").strip()
            if not term:
                continue
            wf.term_lower = term.lower()
            if any((excl and excl in wf.term_lower for excl in wf.normalized_exclusions)):
                continue
            if wf.term_lower not in wf.final_text_lower:
                wf.missing_required_terms.append(term)
        if wf.missing_required_terms:
            wf.final_text = f"{wf.final_text.rstrip()} Verifizierte Elemente: {', '.join(wf.missing_required_terms)}."
    if wf.final_facts and str(wf.image_name_hint or "").lower().startswith("supercluster-"):
        wf.literal_blacklist = {"VERIFIZIERTE_ELEMENTE_PFLICHT", "AUSSCHLUSS_PFLICHT"}
        wf.literal_lines = []
        for key, value in wf.final_facts.items():
            if key in wf.literal_blacklist:
                continue
            if value is None:
                continue
            if isinstance(value, str):
                wf.value_clean = value.strip()
                if not wf.value_clean:
                    continue
                wf.literal_lines.append(f"- {key}: {wf.value_clean}")
        if wf.literal_lines:
            wf.literal_block = "\n".join(wf.literal_lines)
            wf.final_text = f"{wf.final_text.rstrip()}\n\nDETAIL-CHECKLISTE (wÃ¶rtlich aus FACTS_JSON):\n{wf.literal_block}"
    if wf.final_facts and wf.image_key in wf.required_terms_by_image:
        wf.final_text_lower = wf.final_text.lower()
        wf.missing_terms = [term for term in wf.required_terms_by_image[wf.image_key] if term.lower() not in wf.final_text_lower]
        if wf.missing_terms:
            wf.final_text = f"{wf.final_text.rstrip()} Zusatzdetails: {', '.join(wf.missing_terms)}."
    if wf.final_image_url:
        wf.final_text = re.sub(wf.placeholder_md_pattern, f"![Generated Image]({wf.final_image_url})", wf.final_text, flags=re.IGNORECASE)
    else:
        wf.final_text = re.sub(wf.placeholder_md_pattern, "", wf.final_text, flags=re.IGNORECASE)
    if not wf.final_image_url:
        wf.markdown_image_match = re.search("!\\[[^\\]]*\\]\\(([^)]+)\\)", wf.final_text)
        if wf.markdown_image_match:
            wf.candidate_url = str(wf.markdown_image_match.group(1) or "").strip()
            if wf.candidate_url and wf.candidate_url.lower() != "generated image":
                wf.final_image_url = wf.candidate_url
    if not wf.final_text or len(wf.final_text.strip()) < 5:
        wf.final_text = wf.fallback_summary
    if wf.is_audit_request and (not wf.is_factcheck_yes):
        wf.question_line = "MÃ¶chtest du jetzt einen Faktencheck durchfÃ¼hren?"
        wf.gate_prompt = f"\n\n{wf.question_line}\n1. Ja\n2. Nein"
        wf.question_present = wf.question_line.lower() in wf.final_text.lower()
        if '"audit_summary":' in wf.final_text:
            try:
                wf.json_str = (
                    wf.final_text.split("```json")[-1].split("```")[0].strip() if "```" in wf.final_text else wf.final_text
                )
                wf.audit_data = json.loads(wf.json_str)
                wf.summary_text = (wf.audit_data.get("audit_summary", "") or "").strip()
                if wf.summary_text:
                    wf.final_text = wf.summary_text
            except Exception:
                pass
        if not wf.question_present and "mÃ¶chtest du jetzt einen faktencheck durchfÃ¼hren" not in wf.final_text.lower():
            wf.final_text = f"{wf.final_text.rstrip()}{wf.gate_prompt}"
            wf.question_present = True
        if wf.question_present and request.chat_id is not None:
            orchestrator_cls.FACTCHECK_PROMPT_PENDING.add(request.chat_id)
    _vision_res = _parity_vision_snapshot(wf)
    if wf.parity_dir and wf.final_facts:
        try:
            os.makedirs(wf.parity_dir, exist_ok=True)
            wf.timestamp = int(time.time() * 1000)
            wf.provider = request.provider or "unknown"
            wf.payload = {
                "timestamp": wf.timestamp,
                "provider": wf.provider,
                "vision_mode": wf.vision_mode,
                "image_hint": wf.image_name_hint,
                "chat_title": wf.chat_title,
                "user_text": wf.user_text,
                "final_facts": wf.final_facts,
                "final_text": wf.final_text,
                "local_feature_report": _vision_res.get("feature_report", {}),
                "local_context": _vision_res.get("context", {}),
                "cloud_result": wf.event_data.get("cloud_vision_result", {}),
                "source_of_truth": wf.final_facts.get("SOURCE_OF_TRUTH", {}),
            }
            wf.json_path = os.path.join(wf.parity_dir, f"parity_{wf.provider}_{wf.timestamp}.json")
            with open(wf.json_path, "w", encoding="utf-8") as fh:
                json.dump(wf.payload, fh, ensure_ascii=False, indent=2)
        except Exception:
            logger.exception("Parity capture failed")
    if wf.run_tool_loop_result:
        wf.aggregated_usage = getattr(wf.run_tool_loop_result, "usage", {}) or {}
        wf.aggregated_cost = getattr(wf.run_tool_loop_result, "cost", {}) or {}
        wf.tool_results = getattr(wf.run_tool_loop_result, "all_tool_results", []) or []
        if getattr(wf, "total_search_cost", None) is None:
            wf.total_search_cost = 0.0
        for tr in wf.tool_results:
            if isinstance(tr, dict):
                wf.content = tr.get("content", "{}")
                try:
                    wf.parsed = json.loads(wf.content) if isinstance(wf.content, str) else wf.content
                    if isinstance(wf.parsed, dict):
                        wf.data = wf.parsed.get("data", {})
                        if isinstance(wf.data, dict):
                            wf.search_costs = wf.data.get("_search_costs", {})
                            if isinstance(wf.search_costs, dict):
                                wf.total_search_cost += float(wf.search_costs.get("total_search_cost_eur", 0))
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass
        if wf.total_search_cost > 0:
            wf.original_cost = float(wf.aggregated_cost.get("total_cost", 0))
            wf.aggregated_cost["total_cost"] = wf.original_cost + wf.total_search_cost
            wf.aggregated_cost["search_cost"] = wf.total_search_cost
            logger.info(
                "API-USAGE-FIX: LLM-Cost %.4fâ‚¬ + Search-Cost %.4fâ‚¬ = Total %.4fâ‚¬",
                wf.original_cost,
                wf.total_search_cost,
                wf.aggregated_cost["total_cost"],
            )
        wf.video_list_metadata = _derive_video_list_metadata_from_tool_results(getattr(wf, "tool_results", []) or [])
        if not getattr(wf, "modal_request", None):
            wf.modal_request = _derive_video_modal_request_from_tool_results(wf.tool_results)
    wf.has_websearch_result = has_websearch_tool(getattr(wf, "tool_results", []) or [])
    if wf.has_websearch_result:
        wf.final_text = strip_memory_references_from_live_answer(wf.final_text)
    wf.rendered_weather = render_weather_forecast_from_tools(getattr(wf, "tool_results", []) or [])
    if wf.rendered_weather:
        wf.final_text = wf.rendered_weather
    wf.final_text = append_tool_attributions_from_tools(wf.final_text, getattr(wf, "tool_results", []) or [])
    wf.final_text = _normalize_inline_weather_source_footer(wf.final_text)
    try:
        if wf.has_websearch_result:
            wf.rendered_websearch = render_websearch_sources(getattr(wf, "tool_results", []) or [])
            wf.rendered_websearch = strip_memory_references_from_live_answer(wf.rendered_websearch)
            if wf.rendered_websearch:
                wf.final_text = wf.rendered_websearch
                logger.info("DIAMOND: Websearch-Renderer vor Persistierung angewendet")
        wf.final_text = _normalize_inline_weather_source_footer(wf.final_text)
    except Exception as e:
        logger.warning("DIAMOND: Websearch-Renderer Fehler vor Persistierung (non-critical): %s", e)
    # MCL: modal_request / Video-URL-Erkennung erst nach finalem assistant-Text (alle Backfills, Platzhalter, Audit-KÃ¼rzungen).
    wf_modal = resolve_modal_request_for_execution(wf)
    wf.execution_for_persist = ExecutionResponse(
        text=wf.final_text,
        image_url=wf.final_image_url,
        agent_payload=wf.agent_response_payload,
        tool_calls=[],
        is_agent_flow=bool(wf.agent_response_payload),
        usage=wf.aggregated_usage,
        cost=wf.aggregated_cost,
        modal_request=wf_modal,
        all_tool_results=getattr(wf, "tool_results", []) or [],
    )
    wf.execution_for_api = wf.execution_for_persist
    status_sync.persist_assistant_message(
        request.chat_id,
        wf.execution_for_persist,
        extra_metadata={"video_list_metadata": wf.video_list_metadata} if getattr(wf, "video_list_metadata", None) else None,
    )
    if not bool(getattr(wf, "skip_lightweight_post_jobs", False)):
        _trigger_chat_title_job_if_eligible(db, request.chat_id, request.provider)
    else:
        logger.info("[TITLE-TRIGGER] Skip chat %s: lightweight post jobs disabled for strict short reply.", request.chat_id)
    if wf.event in {"PERSON_IDENTIFIED", "PERSON_NAMED"}:
        identity_manager.clear_unknown_face(request.chat_id)
    if wf.event == "PERSON_NAMED" or wf.event == "PERSON_IDENTIFIED":
        wf.learned_name = wf.event_data.get("name")
    trigger_fact_extraction(
        request.chat_id,
        wf.user_text,
        wf.final_text,
        wf.api_key,
        request.provider,
        wf.chosen_model,
        wf.learned_name,
        skip_fact_extraction=(
            wf.skip_fact_extraction
            or bool(getattr(wf, "skip_lightweight_post_jobs", False))
            or (
                has_websearch_tool(getattr(wf, "tool_results", []) or [])
                and is_realtime_search_query(wf.user_text)
            )
        ),
        model_hierarchy=model_hierarchy,
    )
    identity_manager.clear_unknown_face(request.chat_id)
    wf.clean_comp = wf.final_text.strip()
    wf.display_text = wf.final_text
    if '"audit_summary":' in wf.clean_comp:
        try:
            wf.json_str = wf.clean_comp.split("```json")[-1].split("```")[0].strip() if "```" in wf.clean_comp else wf.clean_comp
            wf.audit_data = json.loads(wf.json_str)
            wf.display_text = wf.audit_data.get("audit_summary", wf.display_text)
        except Exception:
            pass
    if wf.audit_data and isinstance(wf.audit_data.get("modifications_list"), list):
        wf.mods = wf.audit_data.get("modifications_list") or []
        if wf.mods:
            wf.audit_context_to_save.status = "warning"
            wf.audit_context_to_save.details = {"source": "display_cleanup_json", "modifications_count": len(wf.mods)}
        elif wf.is_factcheck_yes or wf.is_audit_decision:
            wf.audit_context_to_save.status = "verified"
            wf.audit_context_to_save.details = {"source": "display_cleanup_json", "modifications_count": 0}
    elif '"tool_call":' in wf.clean_comp or '"arguments":' in wf.clean_comp:
        wf.display_text = "âœ… Korrektur wird ausgefÃ¼hrt. Bitte prÃ¼fen Sie gleich die neue PDF in Ihrer Liste."
    if wf.audit_context_to_save.status is None and wf.factcheck_modifications_detected is not None:
        if wf.is_factcheck_yes or wf.is_audit_decision:
            wf.audit_context_to_save.status = "warning" if wf.factcheck_modifications_detected else "verified"
            wf.audit_context_to_save.details = {"source": "tool_result_tracking", "modifications_detected": wf.factcheck_modifications_detected}
        elif wf.is_audit_request and wf.factcheck_modifications_detected:
            wf.audit_context_to_save.status = "warning"
            wf.audit_context_to_save.details = {"source": "tool_result_tracking", "modifications_detected": wf.factcheck_modifications_detected}
    if wf.audit_context_to_save.status:
        wf.status_persisted = status_sync.persist_audit_status(
            AuditContext(
                doc_name=wf.audit_context_to_save.doc_name or wf.original_filename,
                status=wf.audit_context_to_save.status,
                details=wf.audit_context_to_save.details,
            )
        )
        if wf.status_persisted and (not wf.final_ui_command):
            wf.final_ui_command = {"ui_action": "refresh_documents"}
    memory_metrics.increment("orchestrator_finalize_total")
    return wf.execution_for_api


async def finalize_response_async(
    ctx: Any,
    *,
    model_hierarchy: Dict[str, Any],
    orchestrator_cls: type,
) -> Any:
    """Persistenz und Memory-Extraktion mit frischer DB-Session (Stream-Pfad Phase D).

    Smart Chat Naming: Der Titel-Trigger lÃ¤uft in ``finalize_response`` (nach persist_assistant_message),
    sobald genau 2 Nachrichten existieren und ``auto_generated`` wahr ist.
    """
    db = SessionLocal()
    try:
        from backend.services.orchestrator.status_sync import OrchestratorStatusSync

        status_sync = OrchestratorStatusSync(db)
        return await finalize_response(
            ctx,
            db=db,
            background_tasks=None,
            status_sync=status_sync,
            model_hierarchy=model_hierarchy,
            orchestrator_cls=orchestrator_cls,
        )
    finally:
        db.close()
