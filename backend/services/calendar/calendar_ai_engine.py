# backend/services/calendar/calendar_ai_engine.py
"""
AI Calendar Engine — Natural Language → strukturierter CalendarAIPlan (TASK-058 Phase 4).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import keyring

from backend.data.schemas_calendar import (
    CalendarAIPlan,
    CalendarAIAction,
    JanusCalendarEvent,
)
from backend.services import llm_gateway
from backend.utils.config_loader import load_config_data

logger = logging.getLogger("janus_backend.calendar_ai")

# §10 task_058_calendar_modal_diamond_plan.md — System Prompt (Production Grade)
CALENDAR_AI_SYSTEM_PROMPT = """You are Janus Calendar AI, a deterministic scheduling engine.

Your task:
- Optimize user schedules
- Reduce fragmentation
- Maximize deep work blocks
- Minimize context switching
- Answer calendar usage questions with concrete strategies

Rules:
1. Never create overlapping events.
2. Respect existing confirmed events unless explicitly told otherwise.
3. Prefer grouping meetings into contiguous blocks.
4. Preserve at least 2-hour uninterrupted focus blocks where possible.
5. Do not hallucinate events. Only reference events from the provided context.
6. Output ONLY structured JSON actions for scheduling requests.

Calendar Usage Strategies (for general questions):
When users ask "Wie nutze ich den Kalender effizient?" or similar, provide concrete strategies:

Time-Blocking:
- Reserve 2-4 hours at a stretch for focused work without interruptions
- Group meetings into contiguous blocks to minimize context switching
- Schedule 15-30 minute buffers between blocks for transitions and emergencies
- Match block sizes to natural energy cycles (e.g., 2h mornings, 1h afternoons)

Deep Work:
- Block your most productive hours (often 9-12am) for most difficult tasks
- Morning blocks: Reserve for challenging work requiring peak concentration
- Meeting clusters: Group meetings to reduce fragmentation
- Energy management: Adapt block sizes to your energy patterns

Dashboard Features:
- Prioritäten prüfen: Checks if today's events align with long-term projects/goals in Janus
- Fokusblock schützen: Reserves 2-4 hours for focused work without meetings; AI detects gaps automatically
- Offene Termine bestätigen: Shows events with 'tentative' status or needing clarification

Natural Language Commands:
- "Optimiere meinen Tag für Deep Work"
- "Gruppiere meine Meetings morgen"
- "Finde einen 3-Stunden-Block für das Projekt X"
- "Zeig mir Konflikte diese Woche"

Action payload shape:
- create: payload includes "title", "start" (ISO 8601), "end" (ISO 8601); optional "location", "description", "timezone" (default Europe/Berlin).
- update: payload may include partial fields ("title", "start", "end", "location", "description", "is_all_day"); "event_id" must be set at the action root.
- move: same fields as update — new "start" / "end" in payload; "event_id" required.
- delete: "event_id" required; payload may be {}.

Output format (JSON object only — no markdown fences, no commentary):
{
  "summary": "string describing changes",
  "actions": [
    {"type": "create|update|delete|move", "event_id": "string or null", "payload": {}}
  ],
  "risk_level": "low|medium|high"
}
"""


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


def _extract_text_from_llm_result(result: Any) -> str:
    if not isinstance(result, dict):
        return ""
    if str(result.get("type") or "").strip().lower() == "tool_code":
        logger.warning("[calendar_ai] LLM response is tool_code without user text")
        return ""
    text = result.get("text") or result.get("content")
    if text is None and isinstance(result.get("raw_assistant_response"), dict):
        text = (result["raw_assistant_response"] or {}).get("content")
    return str(text or "").strip()


def _resolve_provider_model_key() -> Tuple[str, str, str]:
    config = load_config_data()
    catalog = llm_gateway.get_cached_model_catalog()
    model_id = str(config.get("last_used_model") or "").strip() or "gpt-5-mini"
    if model_id in catalog:
        provider = str(catalog[model_id].get("provider") or "openai").lower()
    else:
        provider = "openai"
        model_id = "gpt-5-mini"
    api_key = (keyring.get_password("Janus-Projekt", provider) or "").strip()
    return provider, model_id, api_key


def _parse_calendar_plan(raw_llm_text: str) -> CalendarAIPlan:
    frag = _extract_json_object_fragment(raw_llm_text)
    if not frag:
        raise ValueError("No JSON object in LLM response")
    data = json.loads(frag)
    if not isinstance(data, dict):
        raise ValueError("LLM JSON root must be an object")
    return CalendarAIPlan.model_validate(data)


class CalendarAIEngine:
    """AI Engine für Kalender-Planung (NL → strukturierte Aktionen)."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("janus_backend.calendar_ai_engine")

    async def generate_plan(
        self,
        command: str,
        events: List[JanusCalendarEvent],
        date: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> CalendarAIPlan:
        """
        Erzeugt einen CalendarAIPlan per LLM (Janus Gateway).
        Ohne API-Key oder bei Parse-Fehler: sicherer Fallback-Plan (keine Mutation).
        """
        extra_context = dict(extra_context) if isinstance(extra_context, dict) else {}

        provider, model_id, api_key = _resolve_provider_model_key()
        if not api_key:
            self.logger.warning("Calendar AI: no API key for provider=%s — returning empty plan", provider)
            return CalendarAIPlan(
                summary=(
                    "Kalender-KI ist nicht bereit (kein API-Schlüssel im Schlüsselbund für diesen Provider). "
                    "Bitte Anmeldedaten unter Einstellungen hinterlegen."
                ),
                actions=[],
                risk_level="low",
            )

        context_block = {
            "target_date": date,
            "events": [e.model_dump(mode="json") for e in events],
            **extra_context,
        }
        user_content = (
            f"User command:\n{command.strip()}\n\n"
            f"Scheduling context (JSON):\n{json.dumps(context_block, ensure_ascii=False, indent=2)}\n\n"
            "Respond with a single JSON object matching the schema in your system instructions."
        )
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": CALENDAR_AI_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            result = await llm_gateway.call_llm(
                provider=provider,
                model_id=model_id,
                api_key=api_key,
                messages=messages,
                force_no_tools=True,
                temperature=0.2,
                max_completion_tokens=4096,
            )
        except Exception as exc:
            self.logger.exception("Calendar AI LLM call failed: %s", exc)
            return CalendarAIPlan(
                summary=f"LLM-Anfrage fehlgeschlagen: {exc!s}",
                actions=[],
                risk_level="high",
            )

        raw_text = _extract_text_from_llm_result(result)
        if not raw_text:
            msg = result.get("message") if isinstance(result, dict) else None
            detail = str(msg or result.get("error") or "empty response")
            self.logger.warning("Calendar AI: empty assistant text (%s)", detail[:200])
            return CalendarAIPlan(
                summary="Die KI hat keinen gültigen Plan zurückgegeben.",
                actions=[],
                risk_level="high",
            )

        try:
            plan = _parse_calendar_plan(raw_text)
        except Exception as exc:
            self.logger.warning("Calendar AI: parse failed: %s | raw snippet=%r", exc, raw_text[:400])
            return CalendarAIPlan(
                summary=f"Konnte den KI-Plan nicht verarbeiten: {exc!s}",
                actions=[],
                risk_level="high",
            )

        self.logger.info(
            "Calendar AI plan OK: summary_len=%s actions=%s risk=%s",
            len(plan.summary),
            len(plan.actions),
            plan.risk_level,
        )
        return plan

    async def suggest_optimization(
        self,
        events: List[JanusCalendarEvent],
    ) -> List[CalendarAIAction]:
        self.logger.info("Optimization suggestion requested (delegates to generate_plan)")
        plan = await self.generate_plan(
            "Suggest schedule optimizations without deleting user events.", events, extra_context={"mode": "suggest"}
        )
        return list(plan.actions)

    async def resolve_conflict(
        self,
        event_a: JanusCalendarEvent,
        event_b: JanusCalendarEvent,
    ) -> Optional[CalendarAIAction]:
        self.logger.info("Conflict resolution suggestion requested")
        plan = await self.generate_plan(
            f"Resolve overlap between '{event_a.title}' and '{event_b.title}'. Prefer minimal moves.",
            [event_a, event_b],
            extra_context={
                "conflict_pair": {"a": event_a.id, "b": event_b.id},
            },
        )
        return plan.actions[0] if plan.actions else None