import json
import logging
import re
from typing import Any, Dict, List, Optional

from backend.services.orchestrator.schemas import ToolDefinition
from backend.services.skill_router import (
    SkillNotFoundError,
    get_blocked_skills_for_query,
    is_realtime_search_query,
    skill_router,
)
from backend.services.tool_manager import tool_manager
from backend.llm_providers.shared.constants import (
    _GOOGLE_MAPS_DIR_RE,
    _WINDOWS_PDF_PATH_RE,
    _FACT_SPLIT_RE,
)
from backend.services.tool_result_renderer import (
    render_routing_segments_text,
    append_missing_pdf_facts,
    append_missing_pdf_paths,
)

logger = logging.getLogger("janus_backend")


def _extract_fact_candidates_from_pdf_content(content: str) -> List[str]:
    text = str(content or "").strip()
    if not text:
        return []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in normalized.split("\n") if line.strip()]

    facts: List[str] = []
    for line in lines:
        candidate = line
        if candidate.startswith(("#", "##", "###")):
            continue
        if candidate.startswith(("- ", "* ")):
            candidate = candidate[2:].strip()
        if candidate.lower().startswith("fakten:"):
            candidate = candidate[7:].strip()
        if not candidate:
            continue
        lower = candidate.lower()
        if any(token in lower for token in ("hauptstadt", "einwohner", "entfernung", "distanz", "route", "maps", "km")):
            facts.append(candidate)

    if facts:
        return facts

    inline = re.sub(r"\s+", " ", text).strip()
    if inline.lower().startswith("fakten:"):
        inline = inline[7:].strip()
    sentence_candidates = [part.strip(" ,") for part in _FACT_SPLIT_RE.split(inline) if part.strip(" ,")]
    return [
        sentence
        for sentence in sentence_candidates
        if any(token in sentence.lower() for token in ("hauptstadt", "einwohner", "entfernung", "distanz", "route", "maps", "km"))
    ]


def _extract_pdf_facts_from_history(messages: List[Dict[str, Any]]) -> List[str]:
    facts: List[str] = []

    def _extract_facts_from_pdf_call(tool_name: str, raw_args: Any) -> None:
        normalized_tool_name = str(tool_name or "").strip().lower()
        if normalized_tool_name not in {"system.create_pdf", "create_pdf_from_markdown", "knowledge.create_pdf"}:
            return
        parsed_args: Any = raw_args
        if isinstance(raw_args, str):
            try:
                parsed_args = json.loads(raw_args)
            except Exception:
                parsed_args = {}
        if not isinstance(parsed_args, dict):
            return
        facts.extend(_extract_fact_candidates_from_pdf_content(str(parsed_args.get("content") or "")))

    for message in messages or []:
        if not isinstance(message, dict):
            continue

        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            tool_calls = []
        for call in tool_calls:
            function = call.get("function") if isinstance(call, dict) else {}
            _extract_facts_from_pdf_call((function or {}).get("name"), (function or {}).get("arguments"))

        parts = message.get("parts")
        if not isinstance(parts, list):
            continue
        for part in parts:
            function_call = None
            if isinstance(part, dict):
                function_call = part.get("function_call")
            else:
                function_call = getattr(part, "function_call", None)
            if not function_call:
                continue

            if isinstance(function_call, dict):
                tool_name = function_call.get("name")
                raw_args = function_call.get("args")
            else:
                tool_name = getattr(function_call, "name", None)
                raw_args = getattr(function_call, "args", None)

            if not isinstance(raw_args, dict):
                try:
                    raw_args = dict(raw_args)
                except Exception:
                    raw_args = {}

            _extract_facts_from_pdf_call(tool_name, raw_args)

    deduped: List[str] = []
    seen = set()
    for fact in facts:
        key = fact.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(fact)
    return deduped


def _extract_pdf_paths_from_history(messages: List[Dict[str, Any]]) -> List[str]:
    paths: List[str] = []

    def _add_path(candidate: Any) -> None:
        value = str(candidate or "").strip()
        if not value:
            return
        if value.lower().endswith(".pdf") and value not in paths:
            paths.append(value)

    for message in messages or []:
        if str(message.get("role") or "") != "tool":
            continue
        content = message.get("content")
        raw_text = str(content or "")
        for found in _WINDOWS_PDF_PATH_RE.findall(raw_text):
            _add_path(found)
        try:
            payload = json.loads(raw_text)
        except Exception:
            payload = None
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            continue
        data = payload.get("data")
        if not isinstance(data, dict):
            continue
        _add_path(data.get("file_path"))

    return paths


def _extract_google_maps_links_from_history(messages: List[Dict[str, Any]]) -> List[str]:
    links: List[str] = []

    def _add_link(candidate: Any) -> None:
        value = str(candidate or "").strip()
        if not value:
            return
        if _GOOGLE_MAPS_DIR_RE.search(value) and value not in links:
            links.append(value)

    def _collect_from_payload(payload: Any) -> None:
        if isinstance(payload, dict):
            for nested in payload.values():
                _collect_from_payload(nested)
            return
        if isinstance(payload, list):
            for nested in payload:
                _collect_from_payload(nested)
            return
        if isinstance(payload, str):
            for found in _GOOGLE_MAPS_DIR_RE.findall(payload):
                _add_link(found)

    for message in messages or []:
        if str(message.get("role") or "") != "tool":
            continue
        content = message.get("content")
        _collect_from_payload(content)
        try:
            parsed = json.loads(str(content or ""))
        except Exception:
            parsed = None
        if parsed is not None:
            _collect_from_payload(parsed)

    return links


def _extract_route_segments_from_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    segments: List[Dict[str, str]] = []

    for message in messages or []:
        if str(message.get("role") or "") != "tool":
            continue
        content = message.get("content")
        try:
            payload = json.loads(str(content or ""))
        except Exception:
            continue
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            continue
        data = payload.get("data")
        if not isinstance(data, dict):
            continue

        origin = str(data.get("origin") or "").strip()
        destination = str(data.get("destination") or "").strip()
        distance_km = data.get("distance_km")
        duration = str(data.get("duration") or data.get("duration_text") or "").strip()
        maps_link = str(data.get("maps_link") or data.get("map_link") or "").strip()

        if not origin or not destination:
            continue

        segment = {
            "origin": origin,
            "destination": destination,
            "distance_km": str(distance_km) if distance_km is not None else "",
            "duration": duration,
            "maps_link": maps_link,
        }
        if segment not in segments:
            segments.append(segment)

    return segments


def _build_deterministic_routing_text(segments: List[Dict[str, str]]) -> str:
    return render_routing_segments_text(segments)


def _ensure_routing_summary_in_text_response(response: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if str(response.get("type") or "") != "text":
        return response

    segments = _extract_route_segments_from_history(history)
    if not segments:
        return response

    text = str(response.get("text") or "")
    lowered = text.lower()
    has_rate_limit_or_apology = (
        ("system.routing" in lowered and "überschritten" in lowered)
        or "pro turn maximal" in lowered
        or "ich entschuldige" in lowered
    )

    def _segment_is_covered(seg: Dict[str, str]) -> bool:
        origin = str(seg.get("origin") or "")
        destination = str(seg.get("destination") or "")
        distance_raw = str(seg.get("distance_km") or "").strip()
        distance_alt = distance_raw.replace(".", ",") if distance_raw else ""
        duration = str(seg.get("duration") or "").strip()

        has_od = bool(origin and destination and origin in text and destination in text)
        if not has_od:
            return False

        has_distance_or_duration = False
        if distance_raw and (distance_raw in text or distance_alt in text):
            has_distance_or_duration = True
        if duration and duration.lower() in lowered:
            has_distance_or_duration = True

        if distance_raw or duration:
            return has_distance_or_duration
        return True

    missing_segments = [seg for seg in segments if not _segment_is_covered(seg)]

    if not has_rate_limit_or_apology and not missing_segments:
        return response

    updated_response = dict(response)
    updated_response["text"] = _build_deterministic_routing_text(segments)
    logger.info(
        "ROUTING-QUALITY-GUARD: Deterministische Routenantwort gesetzt (segmente=%s, missing=%s, apology=%s).",
        len(segments),
        len(missing_segments),
        has_rate_limit_or_apology,
    )
    return updated_response


def _ensure_google_maps_links_in_text_response(response: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if str(response.get("type") or "") != "text":
        return response
    for message in history or []:
        if str(message.get("role") or "") != "tool":
            continue
        skill_name = str(message.get("_skill_id") or message.get("name") or "").strip()
        if skill_name in {"system.local_business", "find_local_business_tool", "system_local_business"}:
            return response
    links = _extract_google_maps_links_from_history(history)
    if not links:
        return response

    text = str(response.get("text") or "")
    existing_links = set(_GOOGLE_MAPS_DIR_RE.findall(text))
    missing_links = [link for link in links if link not in existing_links]
    if not missing_links:
        return response

    suffix = "\n".join(f"- {link}" for link in missing_links)
    updated_response = dict(response)
    updated_response["text"] = f"{text.rstrip()}\n\nGoogle Maps Links:\n{suffix}" if text.strip() else f"Google Maps Links:\n{suffix}"
    logger.info("ROUTING-LINK-GUARD: %s fehlende Google-Maps-Links an finale Antwort angehängt.", len(missing_links))
    return updated_response


def _ensure_pdf_paths_in_text_response(response: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if str(response.get("type") or "") != "text":
        return response
    pdf_paths = _extract_pdf_paths_from_history(history)
    if not pdf_paths:
        return response

    text = str(response.get("text") or "")
    existing_paths = set(_WINDOWS_PDF_PATH_RE.findall(text))
    missing_paths = [path for path in pdf_paths if path not in existing_paths]
    if not missing_paths:
        return response

    updated_response = dict(response)
    updated_response["text"] = append_missing_pdf_paths(text, missing_paths)
    logger.info("PDF-PATH-GUARD: %s PDF-Pfad(e) an finale Antwort angehängt.", len(missing_paths))
    return updated_response


def _ensure_pdf_facts_in_text_response(response: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if str(response.get("type") or "") != "text":
        return response

    facts = _extract_pdf_facts_from_history(history)
    if not facts:
        return response

    text = str(response.get("text") or "")
    text_lower = text.lower()
    missing_facts = [fact for fact in facts if fact.lower() not in text_lower]
    if not missing_facts:
        return response

    updated_response = dict(response)
    updated_response["text"] = append_missing_pdf_facts(text, missing_facts)
    logger.info("PDF-FACTS-GUARD: %s Fakten aus create_pdf-Argumenten an finale Antwort angehängt.", len(missing_facts))
    return updated_response


def _apply_routing_quality_guards(
    response: Dict[str, Any],
    history: List[Dict[str, Any]],
    *,
    allow_pdf_enrichment: bool = False,
) -> Dict[str, Any]:
    updated = _ensure_routing_summary_in_text_response(response, history)
    updated = _ensure_google_maps_links_in_text_response(updated, history)
    if allow_pdf_enrichment:
        updated = _ensure_pdf_facts_in_text_response(updated, history)
        updated = _ensure_pdf_paths_in_text_response(updated, history)
    return updated


def _extract_tool_payload(tool_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(tool_result, dict):
        return None
    try:
        payload = json.loads(tool_result.get("content", "{}"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _normalize_match_key(value: str) -> str:
    lowered = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9äöüß]+", " ", str(value or "").lower()))
    return lowered.strip()


def _tokenize_name(name: str) -> List[str]:
    return [tok for tok in re.split(r"[._\-]", str(name or "").lower()) if tok]


def _hallucination_repair_candidates() -> List[str]:
    tools = set(tool_manager.get_all_tools().keys())
    tools.update(tool_manager.get_skill_mapping().values())
    return sorted(str(name) for name in tools if name)


def _repair_hallucinated_name(requested_name: str) -> Optional[str]:
    requested_tokens = sorted(_tokenize_name(requested_name))
    if not requested_tokens:
        return None

    for candidate in _hallucination_repair_candidates():
        if requested_name == candidate:
            return candidate
        if sorted(_tokenize_name(candidate)) == requested_tokens:
            return candidate
    return None


def _normalize_requested_tool_name(requested_name: str) -> str:
    normalized = str(requested_name or "").strip()
    if not normalized or "." in normalized or "_" not in normalized:
        return normalized

    for skill_id in tool_manager.get_skill_mapping().values():
        sid = str(skill_id or "").strip()
        if sid and sid.replace(".", "_") == normalized:
            return sid
    return normalized


def _build_skill_error_response(
    code: str,
    message: str,
    requested_name: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": {"requested": requested_name, **(details or {})},
        },
    }


def _is_websearch_tool_result(tool_result: Dict[str, Any]) -> bool:
    if not isinstance(tool_result, dict):
        return False
    skill_name = str(
        tool_result.get("_skill_id") or tool_result.get("skill_id") or tool_result.get("name") or ""
    ).strip().lower()
    return skill_name in {"system.websearch", "websearch_wrapper"}


def _extract_websearch_sources_for_compaction(raw_sources: Any, max_items: int = 4) -> List[Dict[str, str]]:
    compact_sources: List[Dict[str, str]] = []
    seen_urls: set[str] = set()
    for src in raw_sources or []:
        if not isinstance(src, dict):
            continue
        url = str(src.get("url") or src.get("uri") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        item: Dict[str, str] = {"url": url}
        title = str(src.get("title") or src.get("name") or "").strip()
        snippet = str(src.get("snippet") or src.get("text") or "").strip()
        if title:
            item["title"] = title[:120]
        if snippet:
            item["snippet"] = snippet[:180]
        compact_sources.append(item)
        if len(compact_sources) >= max_items:
            break
    return compact_sources


def _extract_release_line_title(line: str) -> str:
    bold_match = re.search(r"\*\*([^*]+)\*\*", line)
    if bold_match:
        return str(bold_match.group(1) or "").strip()
    cleaned = re.sub(r"^\s*[-*+]\s*", "", str(line or "").strip())
    first_segment = re.split(r"\s+[—–-]\s+", cleaned, maxsplit=1)[0]
    return first_segment.strip()


def _find_best_source_for_release_title(title: str, sources: List[Dict[str, str]]) -> Optional[str]:
    normalized_title = _normalize_match_key(title)
    if not normalized_title:
        return None

    title_tokens = {token for token in normalized_title.split() if len(token) >= 3}
    if not title_tokens:
        return None

    best_url: Optional[str] = None
    best_score = 0
    for source in sources or []:
        if not isinstance(source, dict):
            continue
        url = str(source.get("url") or "").strip()
        if not url:
            continue
        haystack = " ".join(
            [
                _normalize_match_key(str(source.get("title") or "")),
                _normalize_match_key(str(source.get("snippet") or "")),
            ]
        ).strip()
        if not haystack:
            continue

        score = 0
        if normalized_title in haystack:
            score += 10
        score += sum(1 for token in title_tokens if token in haystack)
        if any(domain in url for domain in (".de", ".at", ".ch")):
            score += 2
        if score > best_score:
            best_score = score
            best_url = url
    return best_url if best_score > 2 else None


def _extract_websearch_sources_for_link_repair(tool_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    all_sources: List[Dict[str, str]] = []
    seen_urls: set[str] = set()

    for result in tool_results or []:
        payload = _extract_tool_payload(result)
        if not payload or payload.get("status") != "ok":
            continue

        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        sources = data.get("sources") if isinstance(data.get("sources"), list) else []

        for source in sources:
            if not isinstance(source, dict):
                continue
            url = str(source.get("uri") or source.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            all_sources.append(
                {
                    "url": url,
                    "title": str(source.get("title") or ""),
                    "snippet": str(source.get("snippet") or source.get("text") or ""),
                }
            )
            seen_urls.add(url)

    return all_sources


def _trim_tool_results(tool_results: List[Dict[str, Any]], provider: str = "openai") -> List[Dict[str, Any]]:
    trimmed_results: List[Dict[str, Any]] = []
    for result in tool_results or []:
        trimmed_result = dict(result)
        content_str = str(trimmed_result.get("content", "") or "")
        is_successful_websearch = False
        if _is_websearch_tool_result(trimmed_result):
            payload = _extract_tool_payload(trimmed_result)
            is_successful_websearch = bool(payload and payload.get("status") == "ok")
        if str(provider).lower() == "gemini":
            max_content_chars = 40000 if is_successful_websearch else 15000
            max_text_chars = 38000 if is_successful_websearch else 14000
        else:
            max_content_chars = 7000 if is_successful_websearch else 2200
            max_text_chars = 3200 if is_successful_websearch else 1400
        if len(content_str) > max_content_chars:
            try:
                content_data = json.loads(content_str)
                if isinstance(content_data, dict):
                    data = content_data.get("data") if isinstance(content_data.get("data"), dict) else None
                    if data:
                        text_value = str(data.get("text") or "")
                        if len(text_value) > max_text_chars:
                            data["text"] = text_value[:max_text_chars].rstrip() + "... (gekürzt)"
                    trimmed_result["content"] = json.dumps(content_data, ensure_ascii=False)
                else:
                    trimmed_result["content"] = content_str[:max_content_chars] + "... (gekürzt)"
            except (json.JSONDecodeError, TypeError):
                trimmed_result["content"] = content_str[:max_content_chars] + "... (gekürzt für LLM-Kontext)"
        trimmed_results.append(trimmed_result)
    return trimmed_results


def _filter_tools_by_skill_ids(allowed_skill_ids: Optional[List[str]]) -> List[Any]:
    all_tools = list(tool_manager.get_all_tools().values())
    allowed = {
        str(skill_id).strip()
        for skill_id in (allowed_skill_ids or [])
        if str(skill_id).strip()
    }
    if not allowed:
        return all_tools

    filtered: List[Any] = []
    for tool_def in all_tools:
        tool_name = str(getattr(tool_def, "name", "") or "").strip()
        if not tool_name:
            continue
        skill_id = str(tool_manager.get_skill_id(tool_name) or "").strip()
        if skill_id in allowed:
            filtered.append(tool_def)

    if filtered:
        logger.debug(
            "SKILL-DISCOVERY: Eingeschraenkte Toolliste aktiv (%s/%s).",
            len(filtered),
            len(all_tools),
        )
        return filtered

    logger.warning(
        "STRICT-PAYLOAD-CLAMP: allowed_skill_ids gesetzt, aber keine Tool-Matches gefunden (%s). Sende leere Toolliste.",
        sorted(allowed),
    )
    return []


def _build_tool_definitions_for_llm(tools: List[Any]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for tool in tools or []:
        try:
            if isinstance(tool, dict):
                candidate = ToolDefinition.model_validate(tool)
            else:
                args_schema_model = getattr(tool, "args_schema", None)
                schema = {"type": "object", "properties": {}}
                if args_schema_model:
                    if hasattr(args_schema_model, "model_json_schema"):
                        schema = args_schema_model.model_json_schema()
                    elif hasattr(args_schema_model, "schema"):
                        schema = args_schema_model.schema()
                candidate = ToolDefinition.model_validate(
                    {
                        "name": str(getattr(tool, "name", "") or ""),
                        "description": str(getattr(tool, "description", "") or ""),
                        "parameters": schema if isinstance(schema, dict) else {"type": "object", "properties": {}},
                    }
                )
            candidate_payload = candidate.model_dump()
            candidate_name = str(candidate_payload.get("name") or "")
            if candidate_name:
                candidate_skill_id = str(tool_manager.get_skill_id(candidate_name) or "")
                if candidate_skill_id:
                    candidate_payload["name"] = candidate_skill_id
            normalized.append(candidate_payload)
        except Exception as exc:
            logger.error("Tool schema validation failed and tool was skipped: %s", exc)
    return normalized


def _dedupe_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen_signatures = set()
    for call in tool_calls or []:
        function = call.get("function") if isinstance(call, dict) else {}
        name = str((function or {}).get("name") or "").strip()
        raw_args = (function or {}).get("arguments", "{}")
        try:
            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except Exception:
            parsed_args = str(raw_args)
        if isinstance(parsed_args, dict):
            normalized_args = json.dumps(parsed_args, sort_keys=True, ensure_ascii=False)
        else:
            normalized_args = str(parsed_args)
        signature = f"{name}::{normalized_args}"
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        deduped.append(call)
    return deduped


def _prevalidate_tool_calls(tool_calls: List[Dict[str, Any]], user_prompt: str = "") -> Dict[str, Any]:
    valid_calls: List[Dict[str, Any]] = []
    immediate_results: Dict[int, Dict[str, Any]] = {}
    system_hints: List[str] = []
    invalid_signatures: List[str] = []
    websearch_call_kept = False

    for idx, tool_call in enumerate(tool_calls):
        function = tool_call.get("function") or {}
        requested_name_raw = str(function.get("name") or "").strip()
        requested_name = _normalize_requested_tool_name(requested_name_raw)
        raw_args = function.get("arguments", "{}")

        if not requested_name:
            immediate_results[idx] = {
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": requested_name,
                "content": json.dumps(
                    _build_skill_error_response(
                        code="MALFORMED_REQUEST",
                        message="Tool-Call enthält keinen Funktionsnamen.",
                        requested_name=requested_name,
                    ),
                    ensure_ascii=False,
                ),
            }
            invalid_signatures.append("MALFORMED_REQUEST:<empty_name>")
            continue

        resolved_legacy = None
        corrected_request_name = requested_name
        try:
            resolved_legacy = skill_router.resolve_tool_name(requested_name)
        except SkillNotFoundError:
            repaired_name = _repair_hallucinated_name(requested_name)
            if repaired_name and repaired_name != requested_name:
                corrected_request_name = repaired_name
                try:
                    resolved_legacy = skill_router.resolve_tool_name(repaired_name)
                    system_hints.append(
                        "Naming-Hinweis: Du hast den Legacy-/Skill-Namen inkorrekt verwendet "
                        f"('{requested_name}'). Nutze künftig bevorzugt domain.action Namen "
                        f"(z.B. '{tool_manager.get_skill_mapping().get(resolved_legacy, resolved_legacy)}')."
                    )
                except SkillNotFoundError:
                    resolved_legacy = None

        if not resolved_legacy:
            immediate_results[idx] = {
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": requested_name_raw,
                "content": json.dumps(
                    _build_skill_error_response(
                        code="SKILL_NOT_FOUND",
                        message=f"Skill/Tool '{requested_name_raw}' ist nicht registriert.",
                        requested_name=requested_name_raw,
                    ),
                    ensure_ascii=False,
                ),
            }
            invalid_signatures.append(f"SKILL_NOT_FOUND:{requested_name_raw}")
            continue

        try:
            parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except Exception as exc:
            immediate_results[idx] = {
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": requested_name,
                "content": json.dumps(
                    _build_skill_error_response(
                        code="MALFORMED_REQUEST",
                        message="Tool-Argumente sind kein valides JSON-Objekt.",
                        requested_name=requested_name,
                        details={"reason": str(exc)},
                    ),
                    ensure_ascii=False,
                ),
            }
            invalid_signatures.append(f"MALFORMED_REQUEST:{requested_name}")
            continue

        if not isinstance(parsed_args, dict):
            immediate_results[idx] = {
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": requested_name,
                "content": json.dumps(
                    _build_skill_error_response(
                        code="MALFORMED_REQUEST",
                        message="Tool-Argumente müssen ein JSON-Objekt sein.",
                        requested_name=requested_name,
                        details={"received_type": type(parsed_args).__name__},
                    ),
                    ensure_ascii=False,
                ),
            }
            invalid_signatures.append(f"MALFORMED_REQUEST:{requested_name}")
            continue

        resolved_skill_id = str(tool_manager.get_skill_id(resolved_legacy) or "").strip()
        blocked_skills = get_blocked_skills_for_query(user_prompt)
        if is_realtime_search_query(user_prompt) and resolved_skill_id in blocked_skills:
            immediate_results[idx] = {
                "tool_call_id": tool_call.get("id"),
                "role": "tool",
                "name": requested_name,
                "content": json.dumps(
                    _build_skill_error_response(
                        code="TOOL_NOT_ALLOWED_FOR_REALTIME_QUERY",
                        message=(
                            f"Tool '{resolved_skill_id}' ist fuer aktuelle Preise, Kurse oder Marktdaten blockiert. "
                            "Nutze stattdessen system.websearch."
                        ),
                        requested_name=requested_name,
                        details={
                            "blocked_skill": resolved_skill_id,
                            "required_skill": "system.websearch",
                        },
                    ),
                    ensure_ascii=False,
                ),
            }
            system_hints.append(
                "Routing-Hinweis: Bei aktuellen Preisen, Kursen oder Marktdaten ist system.websearch verpflichtend. "
                "system.wikipedia_summary und system.rss_news sind hier unzulässig."
            )
            invalid_signatures.append(f"TOOL_NOT_ALLOWED_FOR_REALTIME_QUERY:{resolved_skill_id}")
            continue

        tool_def = tool_manager.get_tool(resolved_legacy)
        if tool_def and tool_def.args_schema and hasattr(tool_def.args_schema, "model_json_schema"):
            try:
                schema = tool_def.args_schema.model_json_schema()
            except Exception:
                schema = {}
            if resolved_skill_id == "system.websearch":
                query_value = str(parsed_args.get("query") or "").strip()
                if not query_value and str(user_prompt or "").strip():
                    parsed_args["query"] = str(user_prompt or "").strip()
            required_fields = schema.get("required", []) if isinstance(schema, dict) else []
            missing_fields = [field for field in required_fields if field not in parsed_args]
            if missing_fields:
                immediate_results[idx] = {
                    "tool_call_id": tool_call.get("id"),
                    "role": "tool",
                    "name": requested_name,
                    "content": json.dumps(
                        _build_skill_error_response(
                            code="MALFORMED_REQUEST",
                            message="Pflichtparameter fehlen im Tool-Call.",
                            requested_name=requested_name,
                            details={"missing_fields": missing_fields},
                        ),
                        ensure_ascii=False,
                    ),
                }
                invalid_signatures.append(f"MALFORMED_REQUEST:{requested_name}:{','.join(sorted(missing_fields))}")
                continue

        canonical_skill_id = str(tool_manager.get_skill_id(resolved_legacy) or "").strip()
        if canonical_skill_id == "system.websearch":
            query_value = str(parsed_args.get("query") or "").strip()
            if not query_value and str(user_prompt or "").strip():
                parsed_args["query"] = str(user_prompt or "").strip()
                query_value = parsed_args["query"]
            if not query_value:
                immediate_results[idx] = {
                    "tool_call_id": tool_call.get("id"),
                    "role": "tool",
                    "name": requested_name,
                    "content": json.dumps(
                        _build_skill_error_response(
                            code="MALFORMED_REQUEST",
                            message="Pflichtparameter fehlen im Tool-Call.",
                            requested_name=requested_name,
                            details={"missing_fields": ["query"]},
                        ),
                        ensure_ascii=False,
                    ),
                }
                invalid_signatures.append(f"MALFORMED_REQUEST:{requested_name}:query")
                continue
            if websearch_call_kept:
                system_hints.append(
                    "Websearch-Hinweis: In einer Runde ist nur ein system.websearch-Aufruf erlaubt. "
                    "Nutze einen einzigen, präzisen Query statt mehrerer konkurrierender Suchen."
                )
                continue
            websearch_call_kept = True
        target_name = canonical_skill_id or corrected_request_name

        prepared_call = dict(tool_call)
        prepared_function = dict(function)
        prepared_function["name"] = target_name
        prepared_function["arguments"] = json.dumps(parsed_args, ensure_ascii=False)
        prepared_call["function"] = prepared_function
        valid_calls.append(prepared_call)

    signature = "|".join(sorted(invalid_signatures)) if invalid_signatures else None
    return {
        "valid_calls": valid_calls,
        "immediate_results": immediate_results,
        "system_hints": system_hints,
        "invalid_signature": signature,
    }
