"""Video Understanding Tool (Task VID-UNDERSTAND-001 WO-3).

Analyzes YouTube videos via transcript retrieval and LLM processing.
Supports summarize, explain, and extract_steps tasks.
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from backend.data.schemas import VideoUnderstandingInput, VideoUnderstandingOutput
from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.services.video.transcript_service import transcript_service

logger = logging.getLogger("janus_backend")


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

_SUMMARIZE_PROMPT = """Fasse das folgende Video-Transkript zusammen.
Sprache: {language}
Detail-Level: {detail_level}

Liefere:
1. Eine Zusammenfassung (2-5 Absätze je nach Detail-Level)
2. Key Points als nummerierte Liste (5-10 Punkte)

Transkript:
{transcript_chunks}
"""

_EXPLAIN_PROMPT = """Erkläre den Inhalt des folgenden Video-Transkripts einfach und verständlich.
Sprache: {language}
Zielgruppe: Anfänger

Liefere eine klare Erklärung ohne Fachjargon.

Transkript:
{transcript_chunks}
"""

_EXTRACT_STEPS_PROMPT = """Extrahiere eine Schritt-für-Schritt-Anleitung aus dem folgenden Video-Transkript.
Sprache: {language}

Liefere:
1. Titel der Anleitung
2. Nummerierte Schritte mit kurzer Beschreibung
3. Benötigte Materialien/Voraussetzungen (falls erkennbar)

Transkript:
{transcript_chunks}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# VIDEO UNDERSTANDING TOOL
# ═══════════════════════════════════════════════════════════════════════════════

async def video_understanding_tool(args: VideoUnderstandingInput, db=None, **kwargs) -> ToolResultV1:
    """
    Analyze a YouTube video based on its transcript.

    Pipeline:
    1. Retrieve transcript via TranscriptService
    2. Build task-specific prompt
    3. Call LLM via gateway.complete
    4. Extract and persist costs (FinOps)
    5. Store summary in memory on success
    6. Return structured VideoUnderstandingOutput

    Args:
        args: VideoUnderstandingInput with video_id, task, language, detail_level
        db: Optional database session for cost persistence
        **kwargs: Additional context (provider, model, etc.)

    Returns:
        ToolResultV1 with VideoUnderstandingOutput data or error
    """
    started_at = time.perf_counter()
    video_id = args.video_id
    task = args.task
    language = args.language or "de"
    detail_level = args.detail_level or "medium"
    source = args.source or "chat"

    # ─────────────────────────────────────────────────────────────────────────
    # Button-First UX Enforcement
    # ─────────────────────────────────────────────────────────────────────────
    if source != "ui_button":
        logger.info("VIDEO-UNDERSTANDING: Chat-based analysis denied (source=%s), directing to UI button", source)
        return ToolResultV1(
            status="ok",
            data={
                "video_id": video_id,
                "task": task,
                "transcript_source": "ui_required",
            },
            message="Um eine Zusammenfassung oder Analyse dieses Videos zu erhalten, öffne bitte das Video und klicke auf den 🧠 (Brain) Button oben links im Video-Player.",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Retrieve transcript
    # ─────────────────────────────────────────────────────────────────────────
    logger.info("VIDEO-UNDERSTANDING: Starting analysis for video_id=%s task=%s", video_id, task)

    try:
        transcript_result = await transcript_service.get_transcript(video_id)
    except Exception as exc:
        logger.error("VIDEO-UNDERSTANDING: Transcript retrieval failed: %s", exc, exc_info=True)
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="TRANSCRIPT_RETRIEVAL_FAILED",
                message=f"Failed to retrieve transcript: {str(exc)}",
            ),
        )

    # Check if transcript is unavailable
    if transcript_result.source == "unavailable" or not transcript_result.text:
        logger.warning("VIDEO-UNDERSTANDING: Transcript unavailable for video_id=%s", video_id)
        return ToolResultV1(
            status="error",
            data={
                "video_id": video_id,
                "task": task,
                "transcript_source": "unavailable",
            },
            error=ToolErrorDetails(
                code="TRANSCRIPT_UNAVAILABLE",
                message="Kein Transkript für dieses Video verfügbar. Bitte versuche ein anderes Video.",
            ),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Build prompt based on task
    # ─────────────────────────────────────────────────────────────────────────
    transcript_chunks = "\n\n".join(transcript_result.chunks)

    if task == "summarize":
        prompt = _SUMMARIZE_PROMPT.format(
            language=language,
            detail_level=detail_level,
            transcript_chunks=transcript_chunks,
        )
    elif task == "explain":
        prompt = _EXPLAIN_PROMPT.format(
            language=language,
            transcript_chunks=transcript_chunks,
        )
    elif task == "extract_steps":
        prompt = _EXTRACT_STEPS_PROMPT.format(
            language=language,
            transcript_chunks=transcript_chunks,
        )
    else:
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="INVALID_TASK",
                message=f"Unknown task: {task}. Allowed: summarize, explain, extract_steps.",
            ),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Call LLM via gateway
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Simple single-turn with direct provider call
        # Use OpenAI for reliable text analysis
        from backend.llm_providers.openai.service import OpenAIServiceProvider

        service = OpenAIServiceProvider()

        # Simple messages for analysis
        messages = [
            {"role": "system", "content": "Du bist ein Video-Analyst. Analysiere das gegebene Transkript präzise und strukturiert."},
            {"role": "user", "content": prompt},
        ]

        # Direct completion call
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("VIDEO-UNDERSTANDING: No OPENAI_API_KEY found, trying keyring")
            import keyring
            api_key = keyring.get_password("Janus-Projekt", "openai") or ""

        response = await service.generate_response(
            api_key=api_key,
            model="gpt-4o-mini",  # Fast and cost-effective
            messages=messages,
            temperature=0.3,
        )

        analysis_text = response.get("text", "")

        if not analysis_text:
            raise RuntimeError("Empty response from LLM")

        # ─────────────────────────────────────────────────────────────────────────
        # Step 3.5: Extract and persist costs (FinOps)
        # ─────────────────────────────────────────────────────────────────────────
        total_cost = 0.0
        usage_data = {}
        cost_data = {}

        try:
            # Extract usage and cost from response
            usage_data = response.get("usage", {})
            cost_data = response.get("cost", {})
            total_cost = cost_data.get("total_cost", 0.0) or 0.0

            # Persist costs to database if db session is available
            if db is not None and total_cost > 0:
                from backend.services.cost_service import create_cost_entry

                input_tokens = usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0) or 0
                output_tokens = usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0) or 0

                create_cost_entry(
                    db=db,
                    amount=float(total_cost),
                    model="gpt-4o-mini",
                    provider="openai",
                    source_type="skill",
                    input_tokens=int(input_tokens),
                    output_tokens=int(output_tokens),
                    context_details=f"video.understand (video_id={video_id}, task={task})",
                )

                logger.info(
                    "VIDEO-UNDERSTANDING: Cost persisted - %.6f€ (input=%d, output=%d)",
                    total_cost, input_tokens, output_tokens
                )
        except Exception as exc:
            logger.warning("VIDEO-UNDERSTANDING: Failed to persist costs: %s", exc)
            # Don't fail the tool if cost tracking fails

    except Exception as exc:
        logger.error("VIDEO-UNDERSTANDING: LLM call failed: %s", exc, exc_info=True)
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(
                code="LLM_ANALYSIS_FAILED",
                message=f"Analysis failed: {str(exc)}",
            ),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Parse result and store in memory
    # ─────────────────────────────────────────────────────────────────────────
    execution_time_ms = int((time.perf_counter() - started_at) * 1000)

    # Extract key points from analysis (simple heuristic)
    key_points = _extract_key_points(analysis_text)

    # Store summary in memory (V2 Bridge)
    memory_stored = transcript_service.store_summary_in_memory(
        video_id=video_id,
        title=transcript_result.video_title or f"Video {video_id}",
        summary=analysis_text,
    )

    # Build structured output
    output = VideoUnderstandingOutput(
        video_id=video_id,
        task=task,
        title=transcript_result.video_title or "",
        summary=analysis_text,
        key_points=key_points,
        structured_notes=_build_structured_notes(task, analysis_text) if task == "extract_steps" else None,
        transcript_source=transcript_result.source,
        transcript_language=transcript_result.language,
        chunk_count=len(transcript_result.chunks),
    )

    logger.info(
        "VIDEO-UNDERSTANDING: Completed video_id=%s task=%s source=%s memory_stored=%s time_ms=%d",
        video_id, task, transcript_result.source, memory_stored, execution_time_ms
    )

    # Build metadata with cost information
    metadata = {
        "execution_time_ms": execution_time_ms,
        "transcript_source": transcript_result.source,
        "memory_stored": memory_stored,
    }

    # Add cost metadata for sidebar display
    if total_cost > 0:
        metadata["_tool_cost_eur"] = float(total_cost)
        metadata["_tool_usage"] = {
            "input_tokens": usage_data.get("prompt_tokens", 0) or usage_data.get("input_tokens", 0) or 0,
            "output_tokens": usage_data.get("completion_tokens", 0) or usage_data.get("output_tokens", 0) or 0,
        }

    return ToolResultV1(
        status="ok",
        data=output.model_dump(),
        message=f"Video analysiert ({task}). Transkript-Quelle: {transcript_result.source}",
        metadata=metadata,
    )


def _extract_key_points(text: str) -> List[str]:
    """Extract key points from analysis text (heuristic)."""
    points = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        # Match numbered lists: "1. Point", "- Point", "* Point"
        if re.match(r'^[\d\-\*•]\.?\s+', line):
            points.append(line)
        # Limit to reasonable number
        if len(points) >= 10:
            break

    return points


def _build_structured_notes(task: str, text: str) -> Optional[Dict[str, Any]]:
    """Build structured notes for extract_steps task."""
    if task != "extract_steps":
        return None

    steps = []
    materials = []
    title = ""

    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract title (first non-empty line that looks like a title)
        if not title and not line.startswith(("1.", "2.", "-", "*", "Schritt")):
            title = line
            continue

        # Extract steps
        step_match = re.match(r'^[\d]+\.\s*(.+)$', line)
        if step_match:
            steps.append({
                "step_number": len(steps) + 1,
                "description": step_match.group(1),
            })

        # Extract materials (heuristic)
        if any(keyword in line.lower() for keyword in ["material", "benötigt", "voraussetzung", "werkzeug"]):
            materials.append(line)

    return {
        "title": title,
        "steps": steps,
        "materials": materials if materials else None,
    }
