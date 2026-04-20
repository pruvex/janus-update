"""
Storybook (Kinderbuch-Macro) pipeline extracted from ChatOrchestrator.

Phase 1a orchestrator refactor: logic unchanged from original module-level helpers + _run_storybook_macro.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend.data import schemas
from backend.services.llm_gateway import get_provider
from backend.tools.media_tools import generate_image_tool
from backend.tools.pdf_generator import create_pdf_from_markdown
from backend.services.orchestrator.schemas import ExecutionResponse
from backend.utils.story_constraints import extract_story_constraints

logger = logging.getLogger("janus_backend")


def _extract_json_payload(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    fence_match = re.search(r"```json\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    generic_match = re.search(r"```\s*(.*?)```", raw, flags=re.DOTALL)
    if generic_match:
        return generic_match.group(1).strip()
    return raw


def _build_storybook_image_prompt_rules(text_above: str, text_below: str, user_prompt: str) -> List[str]:
    context = " ".join(part for part in [text_above, text_below, user_prompt] if part).lower()
    animal_markers = [
        "hase",
        "häschen",
        "kaninchen",
        "rabbit",
        "bunny",
        "igel",
        "hedgehog",
        "fuchs",
        "fox",
        "bär",
        "baer",
        "bear",
        "maus",
        "mouse",
        "eule",
        "owl",
        "ente",
        "duck",
        "hund",
        "dog",
        "katze",
        "cat",
    ]
    if not any(marker in context for marker in animal_markers):
        return []

    return [
        "Keep the recurring protagonists as the same animal characters in this scene.",
        "They may be cute and expressive, but they must still clearly be animals with fur, paws, snouts, ears, and animal faces.",
        "Do not depict them as human children, toddlers, babies, dolls, or children in animal costumes.",
        "Do not change their species, age group, or core visual identity between illustrations.",
    ]


def _stabilize_storybook_image_prompt(image_prompt: str, text_above: str, text_below: str, user_prompt: str) -> str:
    prompt = str(image_prompt or "").strip()
    if not prompt:
        return prompt

    rules = _build_storybook_image_prompt_rules(text_above, text_below, user_prompt)
    if not rules:
        return prompt

    prompt_lower = prompt.lower()
    additions: List[str] = []
    if "consistent style" not in prompt_lower and "same characters" not in prompt_lower:
        additions.append("Maintain the same recurring protagonists and the same children's-book illustration style as in the other images.")
    for rule in rules:
        if rule.lower() not in prompt_lower:
            additions.append(rule)

    if not additions:
        return prompt
    return f"{prompt.rstrip('.')} . {' '.join(additions)}".replace(" .", ".")


def _split_storybook_sentences_local(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", str(text or "")).strip()) if part.strip()]


def _is_generic_storybook_title(title: str) -> bool:
    normalized = re.sub(r"[^a-zA-ZäöüÄÖÜß]+", "", str(title or "").strip().lower())
    return normalized in {"", "kinder", "kinderbuch", "geschichte", "maerchen", "märchen", "story", "buch"}


def _extract_storybook_visual_keywords(text: str) -> List[str]:
    lowered = str(text or "").lower()
    keyword_map = [
        (("erdbeer", "erdbeeren"), "red strawberries"),
        (("blaubeer", "blaubeeren"), "blueberries"),
        (("beeren",), "berries"),
        (("nest",), "a cozy nest made of grass and moss"),
        (("moos",), "soft moss"),
        (("wurzel", "wurzeln"), "tree roots"),
        (("bach", "fluss", "wasser"), "a small stream"),
        (("garten",), "a hidden garden"),
        (("abend", "sonnenuntergang", "himmel", "mond", "sterne"), "a warm evening sky"),
    ]
    matches: List[str] = []
    for markers, label in keyword_map:
        if any(marker in lowered for marker in markers) and label not in matches:
            matches.append(label)
    return matches


def _extract_storybook_scene_subjects(text: str) -> List[str]:
    lowered = str(text or "").lower()
    subject_map = [
        (("apfel", "äpfel", "apples"), "a red apple"),
        (("beeren", "erdbeer", "erdbeeren", "blaubeer", "blaubeeren"), "ripe berries"),
        (("bach", "fluss", "wasser"), "a small stream"),
        (("nest",), "a cozy nest"),
        (("moos",), "soft moss"),
        (("wurzel", "wurzeln"), "tree roots"),
        (("blumen", "waldblumen"), "wildflowers"),
        (("garten",), "a hidden garden"),
    ]
    matches: List[str] = []
    for markers, label in subject_map:
        if any(marker in lowered for marker in markers) and label not in matches:
            matches.append(label)
    return matches


def _build_gemini_storybook_scene_prompt(image_prompt: str, chapter_title: str, text_above: str, text_below: str, user_prompt: str) -> str:
    scene_text = " ".join(part.strip() for part in [text_above, text_below] if str(part or "").strip())
    visual_keywords = _extract_storybook_visual_keywords(scene_text)
    scene_subjects = _extract_storybook_scene_subjects(scene_text)
    prompt_parts = [
        "Create a warm children's-book illustration with the same recurring rabbit and hedgehog protagonists.",
        "Important: the illustration must contain no visible text whatsoever.",
        "No letters, words, captions, subtitles, chapter text, labels, handwriting, speech bubbles, signs, watermarks, or typography anywhere in the image.",
    ]
    if scene_subjects:
        prompt_parts.append(f"Depict the protagonists interacting with these visible scene elements: {', '.join(scene_subjects)}.")
    if visual_keywords:
        prompt_parts.append(f"Visible details that must clearly appear in the image: {', '.join(visual_keywords)}.")
    if image_prompt:
        prompt_parts.append(f"Use this as supporting style/context only: {image_prompt.strip()}")
    prompt_parts.append(
        "Depict only the scene content and environment from the chapter, but do not render any written text from the narrative. No alternative scene composition."
    )
    prompt = " ".join(part.strip() for part in prompt_parts if part.strip())
    return _stabilize_storybook_image_prompt(prompt, text_above, text_below, user_prompt)


def _extract_requested_storybook_title(user_prompt: str) -> str:
    # Lazy import avoids circular dependency with chat_orchestrator at module load time.
    from backend.services.chat_orchestrator import ChatOrchestrator

    prompt = str(user_prompt or "").strip()
    if not prompt:
        return ""

    filename = ChatOrchestrator._extract_requested_pdf_filename(prompt)
    if filename:
        stem = re.sub(r"\.pdf$", "", filename, flags=re.IGNORECASE).strip()
        if stem:
            return stem.replace("_", " ").strip()

    patterns = [
        r"(?:mit|unter)\s+dem\s+titel\s*['\"]([^'\"]+)['\"]",
        r"(?:mit|unter)\s+dem\s+namen\s*['\"]([^'\"]+)['\"]",
        r"(?:den\s+)?(?:titel|namen)\s*['\"]([^'\"]+)['\"]\s*(?:tragen|geben)",
        r"(?:titel|name)\s*(?:des\s*(?:buchs|kinderbuchs|maerchens|märchens|pdfs))?\s*(?:soll|sollte|muss)\s*([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9\-]+(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9\-]+){0,5})\s*(?:sein|lauten|hei(?:ss|ß)en)",
        r"(?:geschichte|kinderbuch|märchen|maerchen)\s+namens\s*['\"]([^'\"]+)['\"]",
        r"(?:geschichte|kinderbuch|märchen|maerchen)\s+hei(?:ss|ß)t\s*['\"]([^'\"]+)['\"]",
        r"(?:geschichte|buch|kinderbuch|märchen|maerchen)\s+soll\s+(?:den\s+)?(?:titel|namen)\s*['\"]([^'\"]+)['\"]\s*tragen",
        r"(?:titel|name)\s*(?:des\s*(?:buchs|kinderbuchs|maerchens|märchens|pdfs))?\s*(?:ist|wäre|waere)\s*['\"]([^'\"]+)['\"]",
        r"(?:soll|sollte|muss)\s+(?:der\s+)?(?:titel|name)\s*(?:des\s*(?:buchs|kinderbuchs|märchens|maerchens|pdfs))?\s*(?:sein|lauten|hei(?:ss|ß)en)\s*['\"]([^'\"]+)['\"]",
        r"(?:nenn|nenne|benenne)\s+(?:mir\s+)?(?:die\s+)?(?:geschichte|das\s+buch|das\s+kinderbuch|das\s+märchen|das\s+maerchen)\s*['\"]([^'\"]+)['\"]",
        r"(?:titel|name)\s*(?:des\s*(?:buchs|kinderbuchs|maerchens|märchens|pdfs))?\s*(?:soll|sollte|muss)\s*['\"]([^'\"]+)['\"]\s*(?:sein|hei(?:ss|ß)en|lauten)",
        r"(?:titel|name)\s*(?:des\s*(?:buchs|kinderbuchs|maerchens|märchens|pdfs))?\s*(?:soll|sollte|muss)?\s*(?:lauten|sein|hei(?:ss|ß)en)\s*[:=]?\s*['\"]([^'\"]+)['\"]",
        r"(?:titel|name)\s*(?:des\s*(?:buchs|kinderbuchs|maerchens|märchens|pdfs))?\s*[:=]\s*['\"]?([^'\"\n.,!?]+(?:\s+[^'\"\n.,!?]+)*)",
        r"(?:nenne|benenne)\s+(?:das\s+)?(?:buch|kinderbuch|märchen|maerchen|pdf)\s+['\"]([^'\"]+)['\"]",
        r"(?:kinderbuch|buch|geschichte|märchen|maerchen)\s+['\"]([^'\"]{3,80})['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, flags=re.IGNORECASE)
        if match:
            candidate = str(match.group(1) or "").strip(" .,:;!?\n\r\t'\"")
            if candidate:
                return candidate

    standalone_quotes = re.findall(r"['\"]([^'\"]{3,80})['\"]", prompt)
    for candidate in standalone_quotes:
        cleaned = str(candidate or "").strip(" .,:;!?\n\r\t'\"")
        lowered = cleaned.lower()
        if cleaned and lowered not in {"pdf", "kinderbuch", "geschichte", "märchen", "maerchen"}:
            return cleaned

    title_case_match = re.search(r"\b([A-ZÄÖÜ][\wäöüÄÖÜß\-]+(?:\s+[A-ZÄÖÜ][\wäöüÄÖÜß\-]+){1,5})\b", prompt)
    if title_case_match:
        candidate = str(title_case_match.group(1) or "").strip()
        if candidate and candidate.lower() not in {"bitte", "kinderbuch", "geschichte", "märchen", "maerchen", "der name", "der titel", "das buch", "die geschichte"}:
            return candidate

    unquoted_match = re.search(
        r"(?:(?:mit|unter)\s+dem\s+(?:titel|namen)|(?:titel|name)\s+des\s+(?:buchs|kinderbuchs|märchens|maerchens)|(?:die|das)\s+(?:geschichte|buch|kinderbuch|märchen|maerchen)\s+(?:soll|sollte|muss)?\s*(?:sein|hei(?:ss|ß)en|lauten|tragen)?\s*[:=]?)\s*([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9\-]+(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9\-]+){0,5})",
        prompt,
        flags=re.IGNORECASE,
    )
    if unquoted_match:
        candidate = str(unquoted_match.group(1) or "").strip(" .,:;!?\n\r\t'\"")
        if candidate and not _is_generic_storybook_title(candidate):
            return candidate
    return ""


def _compact_storybook_text(text: str, max_sentences: int = 2, max_chars: int | None = None) -> str:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip()
    if not normalized:
        return ""

    sentences = _split_storybook_sentences_local(normalized)
    if len(sentences) <= max_sentences and (not max_chars or len(normalized) <= max_chars):
        return normalized

    kept: List[str] = []
    for sentence in sentences[:max_sentences]:
        candidate = " ".join(kept + [sentence]).strip()
        if max_chars and kept and len(candidate) > max_chars:
            break
        kept.append(sentence)
        if max_chars and len(candidate) >= max_chars:
            break

    if not kept:
        kept = [sentences[0]]

    while len(kept) > 1 and max_chars and len(" ".join(kept).strip()) > max_chars:
        kept.pop()

    if len(kept) >= 2 and (len(kept[-1]) < 48 or (max_chars and len(" ".join(kept).strip()) > max_chars)):
        kept[-2] = f"{kept[-2].rstrip()} {kept[-1].lstrip()}".strip()
        kept.pop()

    compacted = " ".join(kept).strip()
    if max_chars and len(compacted) > max_chars:
        compacted = kept[0].strip()
    return compacted if compacted.endswith((".", "!", "?", ":", "…")) else f"{compacted}."


def _normalize_storybook_chapter_block(chapter: Any, idx: int, user_prompt: str, provider: str, min_sentences_per_chapter: int) -> Dict[str, str]:
    chapter_block = chapter if isinstance(chapter, dict) else {}
    chapter_title = str(chapter_block.get("chapter_title") or f"Kapitel {idx}").strip() or f"Kapitel {idx}"
    text_above = re.sub(r"\s+", " ", str(chapter_block.get("text_above") or "")).strip()
    text_below = re.sub(r"\s+", " ", str(chapter_block.get("text_below") or "")).strip()
    image_prompt = str(chapter_block.get("image_prompt") or "").strip()

    if provider == "gemini":
        above_sentences = _split_storybook_sentences_local(text_above)
        below_sentences = _split_storybook_sentences_local(text_below)
        all_sentences = above_sentences + below_sentences
        target_total = max(2, min_sentences_per_chapter)
        if idx >= 3:
            target_total = max(target_total, 3)
        if len(all_sentences) > target_total:
            if above_sentences and below_sentences and target_total >= 3:
                kept_above = above_sentences[:1]
                kept_below = below_sentences[: max(1, target_total - len(kept_above))]
                if len(kept_above) + len(kept_below) < target_total:
                    remaining_from_above = above_sentences[len(kept_above):]
                    needed = target_total - len(kept_above) - len(kept_below)
                    kept_above.extend(remaining_from_above[:needed])
                text_above = " ".join(kept_above).strip()
                text_below = " ".join(kept_below).strip()
            else:
                all_sentences = all_sentences[:target_total]
                if all_sentences:
                    above_count = 1 if len(all_sentences) > 1 else len(all_sentences)
                    if len(all_sentences) >= 4:
                        above_count = 2
                    text_above = " ".join(all_sentences[:above_count]).strip()
                    text_below = " ".join(all_sentences[above_count:]).strip()

        text_above = _compact_storybook_text(
            text_above,
            max_sentences=max(1, min(2, len(_split_storybook_sentences_local(text_above)) or 1)),
            max_chars=260 if min_sentences_per_chapter >= 3 else 190,
        )
        below_sentences = _split_storybook_sentences_local(text_below)
        allowed_below_sentences = max(1, target_total - len(_split_storybook_sentences_local(text_above)))
        text_below = _compact_storybook_text(
            text_below,
            max_sentences=max(1, allowed_below_sentences),
            max_chars=(260 if min_sentences_per_chapter >= 3 else (165 if idx >= 3 else 185)),
        )
        if len(_split_storybook_sentences_local(f"{text_above} {text_below}".strip())) < min_sentences_per_chapter and below_sentences:
            text_below = " ".join(below_sentences[: max(1, min_sentences_per_chapter - len(_split_storybook_sentences_local(text_above)))]).strip()

        image_prompt = _build_gemini_storybook_scene_prompt(image_prompt, chapter_title, text_above, text_below, user_prompt)
    else:
        image_prompt = _stabilize_storybook_image_prompt(image_prompt, text_above, text_below, user_prompt)

    return {
        "chapter_title": chapter_title,
        "text_above": text_above,
        "text_below": text_below,
        "image_prompt": image_prompt,
    }


def _normalize_storybook_payload(story_data: Dict[str, Any], user_prompt: str, provider: str) -> tuple[str, List[Dict[str, str]]]:
    from backend.services.chat_orchestrator import ChatOrchestrator

    effective_prompt = str(user_prompt or "").strip()
    constraints = extract_story_constraints(effective_prompt)
    requested_title = _extract_requested_storybook_title(effective_prompt)
    raw_title = str((story_data or {}).get("title") or "").strip()
    fallback_prompt_title = requested_title or ChatOrchestrator._extract_requested_pdf_filename(effective_prompt).removesuffix(".pdf").replace("_", " ").strip()
    if provider == "gemini":
        title = fallback_prompt_title or ("" if _is_generic_storybook_title(raw_title) else raw_title) or "Kinderbuch"
    else:
        title = raw_title or fallback_prompt_title or "Kinderbuch"
    if provider == "gemini" and _is_generic_storybook_title(title):
        fallback_title = requested_title or ChatOrchestrator._extract_requested_pdf_filename(effective_prompt).removesuffix(".pdf").replace("_", " ").strip()
        if fallback_title and not _is_generic_storybook_title(fallback_title):
            title = fallback_title
    chapters = (story_data or {}).get("chapters")
    normalized_chapters = [
        _normalize_storybook_chapter_block(chapter, idx, effective_prompt, provider, max(2, constraints.min_sentences_per_chapter))
        for idx, chapter in enumerate(chapters if isinstance(chapters, list) else [], start=1)
    ]
    return title, normalized_chapters


async def run_storybook_macro(
    db: Session,
    user_prompt: str,
    request: schemas.ChatRequest,
    api_key: str,
) -> ExecutionResponse:
    logger.info("DIAMOND-MACRO: Starte Storybook-Generator.")
    provider_service = get_provider(request.provider)
    effective_prompt = str(user_prompt or request.prompt or (request.content[0].text if request.content and request.content[0].type == "text" else "")).strip()
    constraints = extract_story_constraints(effective_prompt)
    requested_title = _extract_requested_storybook_title(effective_prompt)
    min_sentences = max(2, constraints.min_sentences_per_chapter)

    system_msg = (
        "Du bist ein professioneller Autor von Kinderbüchern. Deine Aufgabe ist es, eine kurze Geschichte zu schreiben "
        "und passende Bild-Prompts für den Illustrator zu entwerfen.\n\n"
        "REGELN:\n"
        "1. Die Geschichte muss 3 bis 4 Kapitel haben.\n"
        "2. Jedes Kapitel hat zwingend einen Text OBERHALB der Illustration, einen Bild-Prompt und einen Text UNTERHALB.\n"
        f"3. Jedes Kapitel muss insgesamt MINDESTENS {min_sentences} vollständige Sätze enthalten.\n"
        "4. Der 'image_prompt' MUSS auf Englisch sein und die Szene detailliert beschreiben und alle wichtigen sichtbaren Requisiten/Orte aus dem Kapitel zeigen (z.B. Beeren, Bach, Nest, Moos).\n"
        f"5. Verwende als Titel EXAKT '{requested_title}' .\n" if requested_title else "5. Behalte den gewünschten Nutzertitel exakt bei, wenn einer genannt wird.\n"
    ) + (
        "6. Antworte AUSSCHLIESSLICH in folgendem JSON-Format (kein Text drumherum):\n\n"
        "{\n"
        '  "title": "Der kleine Hase",\n'
        '  "chapters": [\n'
        '    {\n'
        '      "chapter_title": "Kapitel 1",\n'
        '      "text_above": "An einem warmen Morgen begegneten sich ein Häschen und ein Igel.",\n'
        '      "image_prompt": "A cute small rabbit meeting a hedgehog in a sunny meadow, children book style",\n'
        '      "text_below": "Sie beschlossen, Freunde zu werden."\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    try:
        logger.info("Storybook-Macro: Generiere Geschichte via LLM...")
        resp = await provider_service.generate_response(
            api_key=api_key,
            model=request.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Schreibe eine Kindergeschichte basierend auf: {effective_prompt}"},
            ],
        )
        raw_text = resp.get("text", "") if isinstance(resp, dict) else str(resp)
        story_payload = _extract_json_payload(raw_text)
        story_data = json.loads(story_payload.strip())
    except Exception as exc:
        logger.error("Storybook-Macro: Fehler beim Parsen der Story-JSON", exc_info=True)
        return ExecutionResponse(
            text=(
                "Fehler: Das Modell konnte die Geschichte nicht im benötigten Format entwerfen. "
                "Bitte versuche es erneut."
            ),
            tool_calls=[],
            is_agent_flow=False,
            error={"code": "STORYBOOK_PARSE_ERROR", "message": str(exc)},
        )

    title, chapters = _normalize_storybook_payload(story_data, effective_prompt, str(request.provider or "").strip().lower())
    if not chapters:
        logger.error("Storybook-Macro: JSON enthält keine Kapitel")
        return ExecutionResponse(
            text="Fehler: Die erzeugte Geschichte enthielt keine Kapitel.",
            tool_calls=[],
            is_agent_flow=False,
            error={"code": "STORYBOOK_NO_CHAPTERS"},
        )

    markdown_lines = [f"# {title}", ""]
    generated_image_paths: List[str] = []

    for idx, chapter in enumerate(chapters, start=1):
        chapter_block = chapter if isinstance(chapter, dict) else {}
        chapter_title = str(chapter_block.get("chapter_title") or f"Kapitel {idx}")
        text_above = str(chapter_block.get("text_above") or "").strip()
        text_below = str(chapter_block.get("text_below") or "").strip()
        image_prompt = str(chapter_block.get("image_prompt") or "").strip()

        markdown_lines.append(f"## {chapter_title}")
        if text_above:
            markdown_lines.append(text_above)
            if not text_above.endswith("\n"):
                markdown_lines.append("")

        if image_prompt:
            try:
                logger.info("Storybook-Macro: Generiere Bild %s...", idx)
                img_result = await generate_image_tool(
                    prompt=image_prompt,
                    size="1024x1024",
                    quality="low",
                    db=db,
                )
                if hasattr(img_result, "model_dump"):
                    img_result = img_result.model_dump()
            except Exception:
                logger.exception("Storybook-Macro: Bildgenerierung für Kapitel %s fehlgeschlagen", idx)
                img_result = {"status": "error", "error": {"message": "unexpected exception"}}

            if img_result.get("status") == "ok":
                data_block = img_result.get("data") if isinstance(img_result.get("data"), dict) else {}
                markdown_image = str(data_block.get("markdown_image") or "").strip()
                local_path = str(data_block.get("local_image_path") or "").strip()
                if markdown_image:
                    markdown_lines.append(markdown_image)
                elif local_path:
                    markdown_lines.append(f"![Illustration]({local_path})")
                if local_path:
                    generated_image_paths.append(local_path)
                markdown_lines.append("")
            else:
                error_msg = (img_result.get("error") or {}).get("message") if isinstance(img_result.get("error"), dict) else None
                markdown_lines.append(
                    f"> Hinweis: Illustration für Kapitel {idx} konnte nicht erstellt werden ({error_msg or 'unbekannter Fehler'})."
                )
                markdown_lines.append("")

        if text_below:
            markdown_lines.append(text_below)
            markdown_lines.append("")

    final_markdown = "\n".join(markdown_lines).strip()
    if str(request.provider or "").strip().lower() == "gemini":
        enforced_title = _extract_requested_storybook_title(effective_prompt)
        if enforced_title and not _is_generic_storybook_title(enforced_title):
            title = enforced_title
            if markdown_lines and markdown_lines[0].startswith("# "):
                markdown_lines[0] = f"# {title}"
                final_markdown = "\n".join(markdown_lines).strip()
    safe_title = "".join(ch if ch.isalnum() else "_" for ch in title).strip("_") or "kinderbuch_story"
    pdf_filename = f"{safe_title[:40]}.pdf"

    logger.info("Storybook-Macro: Erstelle PDF '%s'...", pdf_filename)
    pdf_res = create_pdf_from_markdown(
        content=final_markdown,
        filename=pdf_filename,
        location="Documents",
        layout_profile="bilderbuch",
        image_path=generated_image_paths[-1] if generated_image_paths else None,
        source_prompt=effective_prompt,
        db=db,
    )

    if hasattr(pdf_res, "model_dump"):
        pdf_payload = pdf_res.model_dump()
    elif isinstance(pdf_res, dict):
        pdf_payload = pdf_res
    else:
        pdf_payload = {}

    if pdf_payload.get("status") == "ok":
        pdf_path = str((pdf_payload.get("data") or {}).get("file_path") or "")
        final_text = (
            "✅ **Dein Kinderbuch ist fertig!**\n\n"
            "Ich habe die Geschichte geschrieben, die Illustrationen generiert und alles in ein Bilderbuch-Layout verpackt."
        )
        if pdf_path:
            final_text += f"\n\nDu findest die PDF hier: `{pdf_path}`"
        ui_command = {"ui_action": "refresh_documents"}
    else:
        error_msg = str(((pdf_payload.get("error") or {}).get("message")) or "Unbekannter Fehler")
        final_text = (
            "Die Geschichte und Illustrationen wurden erzeugt, aber der PDF-Export ist fehlgeschlagen: "
            f"{error_msg}"
        )
        ui_command = None

    return ExecutionResponse(text=final_text, tool_calls=[], is_agent_flow=False, ui_command=ui_command)
