from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from backend.data import schemas
from backend.services.tool_executor import ToolExecutor
from backend.services.orchestrator.schemas import ExecutionResponse

if TYPE_CHECKING:
    from backend.services.chat_orchestrator import ChatOrchestrator

logger = logging.getLogger("janus_backend")


def build_meta_research_prompt(orchestrator: "ChatOrchestrator", prompt: str, max_tokens: int | None = None) -> str:
    truncated_prompt = orchestrator._truncate_for_token_budget(
        prompt, max_tokens or orchestrator.META_RESEARCH_PROMPT_MAX_TOKENS
    )
    logger.info(
        "Meta-Research prompt truncated to %s tokens: %s",
        orchestrator.META_RESEARCH_PROMPT_MAX_TOKENS,
        truncated_prompt,
    )
    topic_instructions = collect_meta_topic_instructions(orchestrator, prompt)
    instructions_block = " " + " ".join(topic_instructions) if topic_instructions else ""
    return (
        "Analysiere die Nutzeranfrage und recherchiere ALLE darin geforderten Fakten (z.B. Preise, Daten, Statistiken). "
        "Nutze die verfügbaren Tools für eine gründliche Recherche. "
        "WICHTIG: Erstelle in dieser Phase noch KEIN Dokument und rufe KEIN system.create_pdf auf. "
        "Sammle nur die Informationen." + instructions_block + "\n"
        f"Nutzeranfrage: {truncated_prompt}"
    )


def collect_meta_topic_instructions(orchestrator: "ChatOrchestrator", prompt_text: str) -> List[str]:
    lowered = str(prompt_text or "").lower()
    instructions = []
    for config in orchestrator.META_TOPIC_INSTRUCTION_MAP.values():
        if any(keyword in lowered for keyword in config["keywords"]):
            instructions.append(config["instruction"])
    return instructions


def build_meta_production_prompt(research_output: str) -> str:
    facts_block = str(research_output or "").strip() or "Keine belastbaren Fakten vorhanden."
    return (
        "Erstelle ein PDF-Dokument aus den folgenden Fakten. "
        "Wenn Fakten fehlen, antworte klar mit fehlenden Informationen statt ein leeres Dokument zu erzeugen.\n"
        f"Fakten:\n{facts_block}"
    )


def is_meta_phase1_facts_weak(facts: List[str]) -> bool:
    cleaned = [str(item or "").strip() for item in (facts or []) if str(item or "").strip()]
    if not cleaned:
        return True
    joined = " ".join(cleaned)
    joined_l = joined.lower()
    if len(joined.split()) < 24:
        return True
    routing_markers = ["entfernung", "distanz", "km", "route", "maps", "dauer", "travelmode", "routenuebersicht"]
    country_markers = [
        "hauptstadt",
        "einwohner",
        "bevoelkerung",
        "bevölkerung",
        "population",
        "capital",
        "region",
        "waehrung",
        "währung",
        "sprache",
        "sprachen",
        "klima",
        "handel",
        "kultur",
        "denkmal",
        "politik",
        "regierung",
    ]
    has_routing = any(marker in joined_l for marker in routing_markers)
    has_country = any(marker in joined_l for marker in country_markers)
    if has_routing and not has_country:
        return True
    weak_markers = [
        "gerne gebe ich dir informationen",
        "bitte gib mir den namen einer stadt",
        "keine belastbaren fakten",
        "hallo!",
    ]
    if any(marker in joined_l for marker in weak_markers):
        return True
    factual_markers = ["hauptstadt", "einwohner", "entfernung", "distanz", "km", "route", "capital", "population", "klima", "handel", "kultur", "politik"]
    return not any(marker in joined_l for marker in factual_markers)


def collect_meta_requested_sections(orchestrator: "ChatOrchestrator", prompt_text: str) -> List[str]:
    lowered = str(prompt_text or "").lower()
    sections: List[str] = []
    default_sections = [
        "Hauptstaedte",
        "Bevoelkerung",
        "Distanzen/Routing",
    ]
    if any(keyword in lowered for keyword in ("hauptstadt", "hauptstaedte", "capital")):
        sections.append("Hauptstaedte")
    if any(keyword in lowered for keyword in ("einwohner", "bevoelker", "population")):
        sections.append("Bevoelkerung")
    if any(keyword in lowered for keyword in ("entfernung", "distanz", "route", "routing", "logistik")):
        sections.append("Distanzen/Routing")

    topic_labels = {
        "klima": "Klimazonen",
        "handel": "Handelsbeziehungen",
        "kultur": "Kulturdenkmaeler",
        "politik": "Politische Fuehrungsstruktur",
        "logistik": "Logistik-Kommentar",
    }
    for topic, config in orchestrator.META_TOPIC_INSTRUCTION_MAP.items():
        if any(keyword in lowered for keyword in config["keywords"]):
            sections.append(topic_labels[topic])

    ordered = sections or default_sections
    deduped: List[str] = []
    for section in ordered:
        if section not in deduped:
            deduped.append(section)
    return deduped


def has_meta_topic_coverage_gaps(orchestrator: "ChatOrchestrator", facts: List[str], prompt_text: str) -> bool:
    lowered_prompt = str(prompt_text or "").lower()
    if not lowered_prompt:
        return False
    lowered_facts = " ".join(str(item or "").lower() for item in (facts or []))
    if not lowered_facts:
        return True

    topic_fact_markers = {
        "klima": ["klima", "klimazon", "wetter", "temperatur"],
        "handel": ["handel", "export", "import", "wirtschaft"],
        "kultur": ["kultur", "denkmal", "museum", "bauwerk"],
        "politik": ["politik", "regierung", "praesident", "präsident", "premier", "parlament"],
        "logistik": ["logistik", "lieferkette", "transport", "hafen", "bahn", "route"],
    }

    for topic, config in orchestrator.META_TOPIC_INSTRUCTION_MAP.items():
        requested = any(keyword in lowered_prompt for keyword in config["keywords"])
        if not requested:
            continue
        if not any(marker in lowered_facts for marker in topic_fact_markers[topic]):
            return True
    return False


def extract_pdf_paths_from_text(text: str) -> List[str]:
    raw_text = str(text or "")
    if not raw_text:
        return []
    matches = re.findall(
        r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]+\.pdf",
        raw_text,
        flags=re.IGNORECASE,
    )
    deduped: List[str] = []
    for item in matches:
        path = str(item or "").strip()
        if "\\n" in path or "http://" in path.lower() or "https://" in path.lower():
            continue
        if path and path not in deduped:
            deduped.append(path)
    return deduped


def normalize_meta_facts(phase1_context: str) -> List[str]:
    lines = [str(line or "").strip() for line in str(phase1_context or "").splitlines()]
    cleaned: List[str] = []
    noise_markers = [
        "hallo!",
        "gerne teile ich informationen",
        "bitte gib mir start und ziel",
        "fuer entfernungen und routing benoetige ich",
        "für entfernungen und routing benötige ich",
        "google maps links:",
        "möchtest du wissen",
        "was möchtest du",
    ]
    for line in lines:
        if not line:
            continue
        normalized = line
        normalized = re.sub(r"^\[(?:system\.)?country_info\]\s*", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"^\[(?:system\.)?routing\]\s*", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"^fakten:\s*", "", normalized, flags=re.IGNORECASE)
        normalized = normalized.strip(" -•\t")
        lowered = normalized.lower()
        if not normalized or normalized.startswith("```"):
            continue
        if (
            normalized.startswith("{")
            and '"name"' in lowered
            and ('"parameters"' in lowered or '"arguments"' in lowered)
        ):
            continue
        if "system.route_directions" in lowered or "system.create_pdf" in lowered:
            continue
        if any(marker in lowered for marker in noise_markers):
            continue
        if normalized.endswith("?"):
            question_starts = (
                "möchtest du",
                "was möchtest",
                "was moechtest",
                "macht es sinn",
                "kannst du mir",
            )
            if lowered.startswith(question_starts):
                continue
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)
    return cleaned


def extract_phase2_synopsis(text: str) -> List[str]:
    raw_text = str(text or "").strip()
    if not raw_text:
        return []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    filtered: List[str] = []
    for line in lines:
        if re.search(r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]+\.pdf", line, flags=re.IGNORECASE):
            continue
        if "Deine PDF" in line and ".pdf" in line.lower():
            continue
        filtered.append(line)
        if len(filtered) >= 5:
            break
    return filtered


def build_meta_pdf_success_message(*, phase1_context: str, phase2_text: str) -> str:
    facts = normalize_meta_facts(phase1_context)
    pdf_paths = extract_pdf_paths_from_text(phase2_text)
    filename = ""
    if pdf_paths:
        filename = os.path.basename(pdf_paths[0])
    elif ".pdf" in str(phase2_text or "").lower():
        match = re.search(r"([A-Za-z0-9_.\- ]+\.pdf)", str(phase2_text or ""), flags=re.IGNORECASE)
        if match:
            filename = str(match.group(1) or "").strip()

    lines: List[str] = []
    if facts:
        lines.append("Hier sind die recherchierten Fakten:")
        lines.extend([f"- {fact}" for fact in facts])
    else:
        lines.append("Die PDF wurde erstellt, aber es konnten keine klaren Fakten für die Chat-Ausgabe extrahiert werden.")

    if filename and pdf_paths:
        lines.append("")
        lines.append(f"Deine PDF '{filename}' wurde erstellt und liegt unter:")
        lines.extend([f"- {path}" for path in pdf_paths])
    elif filename:
        lines.append("")
        lines.append(f"Deine PDF '{filename}' wurde erfolgreich erstellt.")
    elif pdf_paths:
        lines.append("")
        lines.append("Deine PDF wurde erstellt und liegt unter:")
        lines.extend([f"- {path}" for path in pdf_paths])

    synopsis_lines = extract_phase2_synopsis(phase2_text)
    if synopsis_lines:
        lines.append("")
        lines.append("Zusätzlich hat Janus folgende Antwort zum PDF generiert:")
        lines.extend(synopsis_lines)

    return "\n".join(lines).strip()


def build_meta_pdf_failure_message(*, phase1_context: str) -> str:
    facts = normalize_meta_facts(phase1_context)
    lines: List[str] = []
    if facts:
        lines.append("Hier sind die recherchierten Fakten:")
        lines.extend([f"- {fact}" for fact in facts])
        lines.append("")
    lines.append("Die PDF konnte diesmal nicht erstellt werden.")
    lines.append("Bitte versuche es erneut (ich nenne dir danach den exakten Speicherpfad).")
    return "\n".join(lines).strip()


def build_meta_pdf_markdown_content(orchestrator: "ChatOrchestrator", *, phase1_context: str, original_user_text: str) -> str:
    facts = normalize_meta_facts(phase1_context)
    required_sections = collect_meta_requested_sections(orchestrator, original_user_text)
    topic_markers = {
        "Hauptstaedte": ["hauptstadt", "capital"],
        "Bevoelkerung": ["einwohner", "bevoelker", "bevölkerung", "population"],
        "Distanzen/Routing": ["distanz", "entfernung", "km", "route", "routing", "dauer"],
        "Klimazonen": ["klima", "temperatur", "wetter", "klimazon"],
        "Handelsbeziehungen": ["handel", "export", "import", "wirtschaft"],
        "Kulturdenkmaeler": ["kultur", "denkmal", "museum", "bauwerk", "sehens"],
        "Politische Fuehrungsstruktur": ["politik", "regierung", "praesident", "präsident", "premier", "parlament"],
        "Logistik-Kommentar": ["logistik", "lieferkette", "transport", "hafen", "bahn", "route"],
    }

    lines: List[str] = ["# Skandinavien-Analyse", ""]
    if facts:
        lines.append("## Recherchierte Kerndaten")
        lines.extend([f"- {fact}" for fact in facts])
        lines.append("")

    for section in required_sections:
        lines.append(f"## {section}")
        section_markers = topic_markers.get(section, [])
        section_facts = [
            fact
            for fact in facts
            if any(marker in str(fact or "").lower() for marker in section_markers)
        ]
        if section_facts:
            lines.extend([f"- {fact}" for fact in section_facts])
        else:
            lines.append("- Keine belastbaren Fakten aus der Recherche verfuegbar; Abschnitt auf Basis der Nutzeranforderung markiert.")
        lines.append("")

    user_requirements = orchestrator._truncate_for_token_budget(
        original_user_text,
        orchestrator.META_PHASE2_REQUIREMENTS_MAX_TOKENS,
    )
    if user_requirements:
        lines.append("## Nutzeranforderung (kompakt)")
        lines.append(user_requirements)

    return "\n".join(lines).strip()


def build_meta_phase2_json_only_prompt(
    orchestrator: "ChatOrchestrator",
    phase1_context: str,
    requested_filename: str = "",
    original_user_text: str = "",
    meta_profile: Optional[Dict[str, Any]] = None,
) -> str:
    normalized_facts = normalize_meta_facts(phase1_context)
    has_topic_gaps = has_meta_topic_coverage_gaps(orchestrator, normalized_facts, original_user_text)
    use_request_fallback = is_meta_phase1_facts_weak(normalized_facts) or has_topic_gaps
    facts_block = " ".join(normalized_facts).strip() or "Keine belastbaren Fakten vorhanden."
    profile = meta_profile or orchestrator.META_PROVIDER_PROFILE_DEFAULT
    facts_block = orchestrator._truncate_for_token_budget(
        facts_block, profile.get("phase2_facts_max_tokens", orchestrator.META_PHASE2_FACTS_MAX_TOKENS)
    )
    logger.info(
        "Meta-Phase2 facts truncated to %s tokens: %s",
        profile.get("phase2_facts_max_tokens", orchestrator.META_PHASE2_FACTS_MAX_TOKENS),
        facts_block,
    )
    request_fallback_block = orchestrator._truncate_for_token_budget(
        original_user_text,
        profile.get(
            "phase2_request_fallback_max_tokens",
            orchestrator.META_PHASE2_REQUEST_FALLBACK_MAX_TOKENS,
        ),
    )
    request_requirements_block = orchestrator._truncate_for_token_budget(
        original_user_text,
        profile.get(
            "phase2_requirements_max_tokens",
            orchestrator.META_PHASE2_REQUIREMENTS_MAX_TOKENS,
        ),
    )
    if use_request_fallback and request_fallback_block:
        logger.warning(
            "META-AGENT PHASE2 FALLBACK: Phase-1-Fakten sind duenn oder thematisch unvollstaendig. Nutze Nutzeranfrage als Zusatzkontext (%s Tokens).",
            orchestrator.META_PHASE2_REQUEST_FALLBACK_MAX_TOKENS,
        )
    filename_hint = str(requested_filename or "").strip()
    system_prompt_override = (
        "JSON-ONLY-OVR:\n"
        "Du bist im Produktions-Modus. Deine einzige Aufgabe ist es, den PDF-Erstellungs-Tool-Call "
        "als exaktes JSON-Objekt zurueckzugeben. "
        "SCHREIBE KEINEN TEXT! NUR DAS JSON!\n"
        "Erlaubte Ausgabe: ein einziges JSON-Objekt im Format "
        "{\"name\": \"system.create_pdf\", \"parameters\": {\"content\": \"...\", \"filename\": \"...\"}}\n"
        "VERBOTEN: Erklaerungen, Markdown, Codeblock-Fences, Vor- oder Nachtext.\n"
        "WENN Fakten unvollstaendig sind, erstelle trotzdem ein inhaltlich nuetzliches PDF auf Basis der Nutzeranfrage. "
        "Stelle KEINE Rueckfragen an den Nutzer. "
        "Bilde alle recherchierten Informationen als klare, logische Abschnitte im PDF-Dokument ab. "
        "Falls einzelne Fakten nicht belastbar sind, kennzeichne das im jeweiligen Abschnitt transparent statt den Abschnitt wegzulassen."
    )
    if filename_hint:
        system_prompt_override += (
            f"\nWICHTIG: Verwende fuer parameter.filename EXAKT '{filename_hint}'. "
            "Kein Ersatzname erlaubt."
        )
    user_content = f"Fakten: {facts_block}. "
    if request_requirements_block:
        user_content += f"Nutzeranfrage (Pflichtanforderungen): {request_requirements_block}. "
    if use_request_fallback and request_fallback_block:
        user_content += f"Nutzeranfrage (Fallback-Kontext): {request_fallback_block}. "
    user_content += f"Erstelle das PDF{(' mit Dateiname ' + filename_hint) if filename_hint else ''}."
    return (
        f"{system_prompt_override}\n\n"
        f"{{\"role\": \"user\", \"content\": \"{user_content}\"}}"
    )


def meta_phase1_missing_research_skills(execution: Optional[ExecutionResponse]) -> bool:
    if not isinstance(execution, ExecutionResponse):
        return True
    payload = execution.agent_payload if isinstance(execution.agent_payload, dict) else {}
    completed_skills = {
        str(skill).strip()
        for skill in (payload.get("required_skills") or [])
        if str(skill).strip()
    }
    return not {"system.country_info", "system.routing"}.issubset(completed_skills)


def extract_requested_pdf_filename(prompt: str) -> str:
    raw_prompt = str(prompt or "")
    if not raw_prompt:
        return ""
    named_match = re.search(
        r"(?:hei(?:ss|ß)t|hei(?:ss|ß)en|genannt\s+werden)\s*[:=]?\s*['\"]?([A-Za-z0-9_.\-]+\.pdf)",
        raw_prompt,
        flags=re.IGNORECASE,
    )
    if named_match:
        return str(named_match.group(1) or "").strip()

    token_matches = re.findall(r"\b([A-Za-z0-9_.\-]+\.pdf)\b", raw_prompt, flags=re.IGNORECASE)
    for match in reversed(token_matches):
        candidate = os.path.basename(str(match or "").strip().strip("'\""))
        if candidate.lower().endswith(".pdf"):
            return candidate

    prompt_lower = raw_prompt.lower()
    if not any(keyword in prompt_lower for keyword in ("pdf", "dokument")):
        return ""

    country_match = re.search(
        r"\b(?:ueber|über|zu|von|fuer|für)\s+(?:das|die|der|den|dem\s+)?([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]{2,})",
        raw_prompt,
        flags=re.IGNORECASE,
    )
    if country_match:
        country = str(country_match.group(1) or "").strip(" .,:;!?\n\r\t")
        if country:
            slug = (
                country.lower()
                .replace("ä", "ae")
                .replace("ö", "oe")
                .replace("ü", "ue")
                .replace("ß", "ss")
            )
            slug = re.sub(r"[^a-z0-9\-_]+", "_", slug).strip("_-")
            if slug:
                return f"{slug}.pdf"
    return ""


async def run_meta_agent_direct_pdf_generation(
    orchestrator: "ChatOrchestrator",
    *,
    phase1_context: str,
    requested_filename: str,
    original_user_text: str,
    request: schemas.ChatRequest,
    api_key: str,
) -> ExecutionResponse:
    logger.warning(
        "META-AGENT PHASE 2: Starte deterministischen create_pdf-Fallback ohne zusaetzlichen LLM-Schritt."
    )
    filename = (
        str(requested_filename or "").strip()
        or extract_requested_pdf_filename(original_user_text)
        or "die.pdf"
    )
    markdown_content = build_meta_pdf_markdown_content(
        orchestrator,
        phase1_context=phase1_context,
        original_user_text=original_user_text,
    )
    executor = ToolExecutor(
        db=orchestrator.db,
        api_key=api_key,
        provider=request.provider,
        model=request.model,
        additional_context={
            "chat_id": request.chat_id,
            "trace_id": str(uuid.uuid4()),
            "allowed_skill_ids": ["system.create_pdf"],
        },
    )
    tool_call = {
        "id": f"meta-phase2-direct-pdf-{uuid.uuid4().hex[:12]}",
        "function": {
            "name": "system.create_pdf",
            "arguments": json.dumps(
                {
                    "content": markdown_content,
                    "filename": filename,
                    "location": "Documents",
                    "include_image": False,
                    "font_size": 11,
                    "image_width": 0,
                    "dry_run": False,
                },
                ensure_ascii=False,
            ),
        },
    }
    try:
        results = await executor.execute_tool_calls([tool_call])
    except Exception:
        logger.error("META-AGENT PHASE 2: Deterministischer create_pdf-Fallback fehlgeschlagen.", exc_info=True)
        return ExecutionResponse(
            text="",
            raw_response={},
            tool_calls=[],
            is_agent_flow=False,
            agent_payload=None,
            error={
                "code": "META_AGENT_PHASE2_DIRECT_PDF_FAILED",
                "message": "Deterministische PDF-Erstellung ist fehlgeschlagen.",
            },
        )

    raw_content = str(((results or [{}])[0] or {}).get("content") or "")
    extracted_paths = extract_pdf_paths_from_text(raw_content)
    payload: Dict[str, Any] = {}
    try:
        payload = json.loads(raw_content)
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        data_block = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        data_path = str(data_block.get("file_path") or "").strip()
        if data_path and data_path not in extracted_paths:
            extracted_paths.append(data_path)

    if not extracted_paths:
        return ExecutionResponse(
            text=raw_content,
            raw_response={"tool_results": results},
            tool_calls=[],
            is_agent_flow=False,
            agent_payload=None,
            error={
                "code": "META_AGENT_PHASE2_DIRECT_PDF_NO_PATH",
                "message": "Deterministische PDF-Erstellung lieferte keinen Dateipfad.",
            },
        )

    text = "\n".join(["Deterministische PDF-Erstellung erfolgreich:", *[f"- {path}" for path in extracted_paths]])
    return ExecutionResponse(
        text=text,
        raw_response={"tool_results": results},
        tool_calls=[],
        is_agent_flow=True,
        agent_payload={
            "trace_id": str(uuid.uuid4()),
            "trace_ids": [],
            "required_skills": ["system.create_pdf"],
            "mode": "meta_production_direct_pdf_fallback",
        },
    )


async def collect_scandinavia_country_facts(
    orchestrator: "ChatOrchestrator",
    *,
    request: schemas.ChatRequest,
    api_key: str,
) -> List[str]:
    facts: List[str] = []
    for country, expected_capital in orchestrator.META_SCANDINAVIA_COUNTRY_TARGETS:
        resolved_line = ""
        for query_country in orchestrator._country_query_candidates(country):
            executor = ToolExecutor(
                db=orchestrator.db,
                api_key=api_key,
                provider=request.provider,
                model=request.model,
                additional_context={
                    "chat_id": request.chat_id,
                    "trace_id": str(uuid.uuid4()),
                    "allowed_skill_ids": ["system.country_info"],
                },
            )
            tool_call = {
                "id": f"meta-country-{orchestrator._normalize_geo_name(country)}-{orchestrator._normalize_geo_name(query_country)}",
                "function": {
                    "name": "system.country_info",
                    "arguments": json.dumps({"country": query_country, "language": "de"}, ensure_ascii=False),
                },
            }
            try:
                results = await executor.execute_tool_calls([tool_call])
            except Exception:
                logger.warning(
                    "META-AGENT PHASE 1: Deterministischer country_info-Aufruf fehlgeschlagen (%s).",
                    query_country,
                    exc_info=True,
                )
                continue
            if not results:
                continue
            raw_content = str((results[0] or {}).get("content") or "")
            try:
                payload = json.loads(raw_content)
            except Exception:
                payload = {}
            if not isinstance(payload, dict) or payload.get("status") != "ok":
                continue
            data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
            country_name = str(data.get("name") or country)
            capital = str(data.get("capital") or expected_capital or "n/a")
            if not orchestrator._capital_matches_expected(actual_capital=capital, expected_capital=expected_capital):
                logger.warning(
                    "META-AGENT PHASE 1: country_info-Mismatch fuer %s (query=%s, capital=%s).",
                    country,
                    query_country,
                    capital,
                )
                continue
            population = orchestrator._format_population(data.get("population"))
            region = str(data.get("region") or "n/a")
            resolved_line = (
                f"[system.country_info] {country_name}: Hauptstadt {capital}, "
                f"Einwohner ca. {population}, Region {region}."
            )
            break
        if resolved_line and resolved_line not in facts:
            facts.append(resolved_line)
        elif not resolved_line:
            logger.warning(
                "META-AGENT PHASE 1: Keine belastbaren country_info-Daten fuer %s gefunden.",
                country,
            )
    if facts:
        logger.info(
            "META-AGENT PHASE 1: Deterministische country_info-Anreicherung aktiv (facts=%s).",
            len(facts),
        )
    return facts


async def run_meta_agent_research_fallback(
    orchestrator: "ChatOrchestrator",
    *,
    user_text: str,
    request: schemas.ChatRequest,
    api_key: str,
    skip_final_synthesis: bool = False,
    meta_profile: Optional[Dict[str, Any]] = None,
) -> ExecutionResponse:
    logger.warning(
        "META-AGENT PHASE 1: Planner lieferte keinen belastbaren Recherche-Plan. "
        "Starte erzwungenen Skill-Lauf mit dynamischer Werkzeugliste."
    )

    dynamic_skills = []
    try:
        dynamic_skills = orchestrator.skill_selector.get_relevant_skills(user_text)
    except Exception as exc:
        logger.warning("META-AGENT Fallback: SkillSelector fehlgeschlagen (%s)", exc)

    fallback_skills: List[str] = []
    seen: Set[str] = set()
    for skill in dynamic_skills or []:
        normalized = str(skill or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        fallback_skills.append(normalized)
    if not fallback_skills:
        fallback_skills = ["system.websearch", "system.country_info", "system.routing"]

    forced_spec = schemas.AgentSpec(
        name="Meta-Research-Agent",
        goal="Recherchiere alle Fakten aus der Nutzeranfrage als Grundlage fuer die PDF-Erstellung.",
        required_skills=fallback_skills,
        instructions=(
            "Arbeite die folgenden Skills der Reihe nach ab: "
            f"{', '.join(fallback_skills)}. Ohne diese Tool-Aufrufe gilt die Recherche als unvollstaendig."
        ),
        max_iterations=max(2, len(fallback_skills)),
    )
    try:
        run_result = await orchestrator.agent_runtime.run(
            spec=forced_spec,
            user_prompt=build_meta_research_prompt(
                orchestrator,
                user_text,
                max_tokens=(meta_profile or {}).get(
                    "phase1_max_tokens", orchestrator.META_RESEARCH_PROMPT_MAX_TOKENS
                ),
            ),
            provider=request.provider,
            model=request.model,
            api_key=api_key or "",
            chat_id=request.chat_id,
            skip_final_synthesis=skip_final_synthesis,
        )
        phase_outputs = [str(item or "").strip() for item in (run_result.get("phase_outputs") or []) if str(item or "").strip()]
        phase_text = str(run_result.get("text") or "").strip()
        if skip_final_synthesis and phase_outputs:
            phase_text = "\n".join(phase_outputs)
        if orchestrator._should_force_scandinavia_country_coverage(user_text):
            deterministic_country_facts = await collect_scandinavia_country_facts(
                orchestrator,
                request=request,
                api_key=api_key or "",
            )
            if deterministic_country_facts:
                existing_lines = [
                    str(line or "").strip()
                    for line in phase_text.splitlines()
                    if str(line or "").strip()
                ]
                for line in deterministic_country_facts:
                    if line not in existing_lines:
                        existing_lines.append(line)
                phase_text = "\n".join(existing_lines)
        return ExecutionResponse(
            text=phase_text,
            raw_response=run_result.get("raw_response"),
            tool_calls=[],
            is_agent_flow=True,
            agent_payload={
                "trace_id": run_result.get("trace_id"),
                "trace_ids": run_result.get("trace_ids") or [],
                "required_skills": fallback_skills,
                "mode": "meta_research_forced",
            },
        )
    except Exception:
        logger.error("META-AGENT PHASE 1 FORCED RUN fehlgeschlagen.", exc_info=True)
        return ExecutionResponse(
            text="",
            raw_response={},
            tool_calls=[],
            is_agent_flow=False,
            agent_payload=None,
            error={
                "code": "META_AGENT_PHASE1_FORCED_FAILED",
                "message": "Erzwungene Recherchephase konnte nicht abgeschlossen werden.",
            },
        )


async def run_meta_agent_production_fallback(
    orchestrator: "ChatOrchestrator",
    *,
    phase1_context: str,
    requested_filename: str,
    original_user_text: str,
    request: schemas.ChatRequest,
    api_key: str,
    meta_profile: Optional[Dict[str, Any]] = None,
) -> ExecutionResponse:
    logger.warning(
        "META-AGENT PHASE 2: Planner wird im Fast-Path uebersprungen. "
        "Starte erzwungenen system.create_pdf Lauf."
    )
    forced_spec = schemas.AgentSpec(
        name="Meta-Production-Agent",
        goal="Erstelle ein PDF mit den recherchierten Fakten.",
        required_skills=["system.create_pdf"],
        instructions=(
            "Nutze ausschliesslich system.create_pdf. "
            "Die Ausgabe muss ein valider PDF-Tool-Call sein."
        ),
        max_iterations=1,
    )
    try:
        run_result = await orchestrator.agent_runtime.run(
            spec=forced_spec,
            user_prompt=build_meta_phase2_json_only_prompt(
                orchestrator,
                phase1_context,
                requested_filename=requested_filename,
                original_user_text=original_user_text,
                meta_profile=meta_profile,
            ),
            provider=request.provider,
            model=request.model,
            api_key=api_key or "",
            chat_id=request.chat_id,
            skip_final_synthesis=True,
        )
        phase2_text = str(run_result.get("text") or "")
        if not extract_pdf_paths_from_text(phase2_text):
            logger.warning(
                "META-AGENT PHASE 2 FORCED RUN: Kein bestaetigter PDF-Pfad gefunden. "
                "Wechsle auf deterministischen create_pdf-Fallback."
            )
            return await run_meta_agent_direct_pdf_generation(
                orchestrator,
                phase1_context=phase1_context,
                requested_filename=requested_filename,
                original_user_text=original_user_text,
                request=request,
                api_key=api_key,
            )
        return ExecutionResponse(
            text=phase2_text,
            raw_response=run_result.get("raw_response"),
            tool_calls=[],
            is_agent_flow=True,
            agent_payload={
                "trace_id": run_result.get("trace_id"),
                "trace_ids": run_result.get("trace_ids") or [],
                "required_skills": ["system.create_pdf"],
                "mode": "meta_production_forced",
            },
        )
    except Exception:
        logger.error("META-AGENT PHASE 2 FORCED RUN fehlgeschlagen.", exc_info=True)
        return await run_meta_agent_direct_pdf_generation(
            orchestrator,
            phase1_context=phase1_context,
            requested_filename=requested_filename,
            original_user_text=original_user_text,
            request=request,
            api_key=api_key,
        )

