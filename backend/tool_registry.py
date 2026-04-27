# backend/tool_registry.py
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

import keyring

# --- IMPORTS DER LOGIK ---
# Wir importieren die Module, damit die Funktionen verfügbar sind
from backend.data import contact_schemas, schemas
from backend.services import filesystem_manager
from backend.tools import filesystem_tools
from backend.tools.memory_tools import (
    memory_write_tool,
    memory_read_tool,
    memory_update_tool,
    memory_history_tool,
)
from backend.services.permission_service import grant_permission, revoke_permission
from backend.services.rag_manager import query_knowledge_base
from backend.services.scraper_service import scrape_website
from backend.services.tool_executor import (
    list_knowledge_documents,
    open_knowledge_document,
    get_full_document_text,
)
from backend.services.knowledge_composite import hardened_edit_pdf
from backend.tools.pdf_editor import edit_pdf_text_in_place
from backend.services.tool_manager import tool_manager
from backend.services.websearch.websearch import execute_websearch_service
from backend.data.database import SessionLocal
from backend.tools.calendar_tools import (
    create_calendar_event,
    delete_calendar_event,
    find_address_and_update_calendar_event,
    find_and_update_calendar_event,
    find_free_time_slots,
    get_calendar_events,
    update_calendar_event,
    update_calendar_event_description,
)
from backend.tools.db_wrappers import (
    create_or_update_contact_tool,
    delete_contact_by_id_wrapper,
    list_contacts_wrapper,
)
# Geo tools return ToolResultV1 (Pydantic); tool_executor serializes via model_dump().
from backend.tools.geo_service import (
    CleanGetDistanceArgs,
    find_local_business_tool,
    get_country_info_tool,
    get_distance_and_route_tool,
)

# WICHTIG: Hier wurde 'find_contact_and_send_email' ENTFERNT, da es nicht in gmail_tools existiert!
from backend.tools.gmail_tools import get_latest_emails, read_email, send_email
from backend.tools.media_tools import generate_image_tool, save_mp3_tool
from backend.tools.pdf_generator import create_pdf_from_markdown

# Tools aus den Modulen
from backend.data.schemas import PriceComparisonOutput, VideoSearchOutput, WebSearchOutput
from backend.data.schemas_tools import ToolErrorDetails, ToolResultV1
from backend.tools.tool_contract_v1 import tool_err_v1
from backend.tools.finance_tools import PriceComparisonArgs, price_comparison_tool
from backend.tools.rss_service import CleanGetLatestNewsRssToolArgs, get_latest_news_rss
from backend.tools.weather_service import CleanGetWeatherFromApiToolArgs, get_weather_from_api_tool
from backend.tools.wiki_service import CleanGetWikipediaSummaryArgs, get_wikipedia_summary
from backend.tools.video_tools import video_search_tool
from backend.tools.video_understanding import video_understanding_tool

logger = logging.getLogger("janus_backend")

# --- Hilfs-Wrapper (Lokal definiert) ---


# ─── Websearch V2.0 Helpers ──────────────────────────────────────────────────
_PRICE_SIGNALS: frozenset = frozenset({
    "preis", "preise", "kosten", "kostet", "günstiger", "günstigsten",
    "price", "cost", "costs", "cheaper", "cheapest", "buy", "kaufen",
})
_TECH_NEWS_SIGNALS: frozenset = frozenset({
    "release", "erscheint", "launch", "leak", "ankündigung", "announce",
    "specs", "preview", "review", "news", "update", "patch", "version",
})
_PRICE_FIGURE_RE = re.compile(r'\d+[,.]\d+\s*(?:€|EUR|\$|USD)', re.IGNORECASE)


def _sources_to_items(sources: List[Dict[str, Any]]) -> List:
    """Konvertiert WebSearchResult.sources zu WebSearchItem-Liste."""
    from backend.data.schemas import WebSearchItem
    items = []
    for s in (sources or []):
        url = str(s.get("url") or "").strip()
        if not url:
            continue
        items.append(WebSearchItem(
            title=str(s.get("title") or url),
            description=str(s.get("snippet") or "") or None,
            date=None,
            source_url=url,
            thumbnail_url=None,
        ))
    return items


def _detect_price_query(query: str, text: str) -> bool:
    """True wenn Query Preis-Signale hat UND Text konkrete Preiszahlen enthält."""
    if not any(sig in query.lower() for sig in _PRICE_SIGNALS):
        return False
    return bool(_PRICE_FIGURE_RE.search(text))


def _detect_global_fallback_needed(query: str, items: list) -> bool:
    """True wenn Ergebnis-Items leer/wenig sind UND Query ein Tech/News-Thema andeutet."""
    if len(items) >= 2:
        return False
    return any(sig in query.lower() for sig in _TECH_NEWS_SIGNALS)


async def _enrich_with_price_comparison(query: str, locale: str) -> Optional[dict]:
    """Ruft price_comparison_tool intern auf (Soft-Fail bei Fehler)."""
    try:
        currency = "USD" if locale.startswith("en") else "EUR"
        args = PriceComparisonArgs(
            product_name=query,
            condition_filter="new",
            locale=locale,
            currency=currency,
        )
        result = await price_comparison_tool(args)
        if hasattr(result, "model_dump"):
            result = result.model_dump()
        if isinstance(result, dict) and result.get("status") == "ok":
            return result.get("data")
        return None
    except Exception as exc:
        logger.warning("WEBSEARCH-V2: price enrichment soft-fail: %s", exc)
        return None


def _normalize_websearch_query(query: str) -> str:
    normalized = str(query or "").strip()
    if not normalized:
        return normalized
    lowered = normalized.lower()
    current_markers = ("aktuell", "aktuelle", "heute", "derzeit", "current", "latest")
    price_markers = ("preis", "preise", "gold", "feinunze", "kosten", "kurs", "wert")
    if any(marker in lowered for marker in current_markers):
        current_year = str(datetime.utcnow().year)
        for year in ("2024", "2025", "2026", "2027"):
            if year in normalized and year != current_year:
                normalized = normalized.replace(year, current_year)
                lowered = normalized.lower()
    if any(marker in lowered for marker in price_markers) and not any(token in lowered for token in (" euro", " eur", "€", " usd", "dollar")):
        normalized = f"{normalized} in Euro"
    return normalized


async def websearch_wrapper(websearch_args: schemas.WebsearchArgsV2) -> ToolResultV1:
    """Websuche V2.0 (Diamond): Strukturierter Output + Smart Global Fallback + Seamless Price Integration."""
    import time as _time
    started_at = _time.perf_counter()
    skill_name = "system.websearch"

    def _elapsed_ms() -> int:
        return int((_time.perf_counter() - started_at) * 1000)

    def _persist_websearch_cost(raw: Dict[str, Any], provider_name: str, model_name: Optional[str]) -> None:
        if not isinstance(raw, dict):
            return
        cost = raw.get("cost") if isinstance(raw.get("cost"), dict) else {}
        total_cost = cost.get("total_cost")
        if not isinstance(total_cost, (int, float)) or total_cost <= 0:
            return
        usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
        db = SessionLocal()
        try:
            from backend.services.cost_service import create_cost_entry
            create_cost_entry(
                db=db,
                amount=float(total_cost),
                model=str(model_name or provider_name or "websearch"),
                provider=str(provider_name or "unknown"),
                source_type="websearch",
                input_tokens=int(usage.get("query_count") or 0),
                output_tokens=0,
                context_details=f"query_count={int(usage.get('query_count') or 1)}",
            )
        finally:
            db.close()

    try:
        payload = schemas.WebsearchArgsV2.model_validate(websearch_args)
        provider = str(payload.provider or "").strip().lower()
        normalized_query = _normalize_websearch_query(payload.query)
        key = (keyring.get_password("Janus-Projekt", provider) or "") if provider else ""

        # ── Execute primary search ──────────────────────────────────────────
        raw = await execute_websearch_service(
            query=normalized_query,
            api_key=key,
            provider=provider,
            model=payload.model,
        )
        _persist_websearch_cost(raw, provider or "default", payload.model)

        text = str(raw.get("text") or "")
        sources = raw.get("sources") if isinstance(raw.get("sources"), list) else []
        meta = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        source_provider = str(meta.get("provider") or provider or "unknown")

        # ── Build structured items from sources ────────────────────────────
        items = _sources_to_items(sources)

        # ── Ebene 5: Smart Global Fallback (Tech/News ohne ausreichend Ergebnisse) ──
        if _detect_global_fallback_needed(normalized_query, items):
            en_query = f"{normalized_query} latest news"
            logger.info("WEBSEARCH-V2: Smart Global Fallback → '%s'", en_query)
            try:
                raw_en = await execute_websearch_service(
                    query=en_query, api_key=key, provider=provider, model=payload.model,
                )
                en_sources = raw_en.get("sources") if isinstance(raw_en.get("sources"), list) else []
                fallback_items = _sources_to_items(en_sources)
                if fallback_items:
                    items = fallback_items
                if raw_en.get("text"):
                    text = (text + "\n\n[Global Research]\n" + raw_en["text"]) if text else raw_en["text"]
            except Exception as fb_exc:
                logger.warning("WEBSEARCH-V2: Global Fallback soft-fail: %s", fb_exc)

        # ── Ebene 8: Seamless Integration – Preis-Signal → interne price_comparison ──
        # TASK 002 (STANDALONE VALIDATION): Deaktiviert — Keine Skill-Kopplung erlaubt.
        price_enrichment = None
        # if _detect_price_query(normalized_query, text):
        #     logger.info("WEBSEARCH-V2: Preis-Signal detektiert → interne price_comparison für '%s'", normalized_query)
        #     price_enrichment = await _enrich_with_price_comparison(normalized_query, "de_DE")

        # ── Build structured WebSearchOutput ─────────────────────────────────
        output = WebSearchOutput(
            query=normalized_query,
            locale="de_DE",
            items=[i.model_dump() for i in items] if items else [],
            text=text,
            price_enrichment=price_enrichment,
            source=source_provider,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.info(
            "skill=%s status=ok provider=%s items=%s enriched=%s ms=%s",
            skill_name, source_provider, len(items), price_enrichment is not None, _elapsed_ms(),
        )
        # Include raw sources alongside WebSearchOutput so _render_websearch_sources
        # can always find them regardless of whether items is populated.
        output_dict = output.model_dump()
        output_dict["sources"] = sources
        return ToolResultV1(
            status="ok",
            data=output_dict,
            metadata={"execution_time_ms": _elapsed_ms()},
        )

    except Exception as e:
        logger.error("skill=%s status=error code=WEBSEARCH_FAILED error=%s ms=%s", skill_name, e, _elapsed_ms())
        return ToolResultV1(
            status="error",
            data={},
            error=ToolErrorDetails(code="WEBSEARCH_FAILED", message=str(e)),
            metadata={"execution_time_ms": _elapsed_ms()},
        )


async def find_contact_and_send_email_wrapper(name_query: str, subject: str, body: str) -> ToolResultV1:
    """Sucht Kontakt in DB und sendet Mail."""
    import time

    from backend.data import crud, database

    t0 = time.perf_counter()
    try:
        db = next(database.get_db_sync())
        try:
            contacts = crud.search_contacts_by_name(db, name_query=name_query)
            if not contacts:
                return tool_err_v1(
                    "CONTACT_NOT_FOUND",
                    f"Kontakt '{name_query}' nicht gefunden.",
                    details={"name_query": name_query},
                    started_at=t0,
                    tags=["communication"],
                )
            target_contact = contacts[0]
            if not target_contact.email:
                return tool_err_v1(
                    "NO_EMAIL",
                    f"Kontakt '{target_contact.name}' hat keine E-Mail.",
                    details={"name_query": name_query, "contact_id": target_contact.id},
                    started_at=t0,
                    tags=["communication"],
                )

            return send_email(to=target_contact.email, subject=subject, body=body)
        finally:
            db.close()
    except Exception as e:
        logger.error("find_contact_and_send_email_wrapper failed", exc_info=True)
        return tool_err_v1(
            "FIND_CONTACT_EMAIL_FAILED",
            str(e),
            details={"name_query": name_query},
            started_at=t0,
            tags=["communication"],
        )


def system_grant_permission(skill_id: str, tool_name: Optional[str] = None, db: Session = None):
    return grant_permission(skill_id=skill_id, tool_name=tool_name, db=db)


def system_revoke_permission(skill_id: str, tool_name: Optional[str] = None, db: Session = None):
    return revoke_permission(skill_id=skill_id, tool_name=tool_name, db=db)


# --- REGISTRIERUNG ---
def register_all_tools():
    """Lädt alle Tools in den Manager."""
    if len(tool_manager.get_all_tools()) > 0:
        # Tools already registered
        return

    # WebSearch V2.0: ALS ERSTES registrieren für korrektes Mapping
    tool_manager.register_tool(
        websearch_wrapper, 
        schemas.WebsearchArgsV2, 
        name="system.websearch"
    )
    tool_manager.set_output_schema("system.websearch", WebSearchOutput)
    tool_manager.register_tool(
        video_search_tool,
        schemas.VideoSearchInput,
        name="video.search",
    )
    tool_manager.set_output_schema("video.search", VideoSearchOutput)

    # Video Understanding Skill (VID-UNDERSTAND-001)
    from backend.data.schemas import VideoUnderstandingInput, VideoUnderstandingOutput
    tool_manager.register_tool(
        video_understanding_tool,
        VideoUnderstandingInput,
        name="system.video_understanding",
    )
    tool_manager.set_output_schema("system.video_understanding", VideoUnderstandingOutput)

    # 1. Info
    tool_manager.register_tool(
        get_latest_news_rss, CleanGetLatestNewsRssToolArgs, "Ruft aktuelle Schlagzeilen ab."
    )
    tool_manager.register_tool(
        scrape_website, schemas.ReadUrlContentArgs, "Liest den Textinhalt einer Webseite."
    )
    tool_manager.register_tool(
        get_weather_from_api_tool, CleanGetWeatherFromApiToolArgs, "Wettervorhersage."
    )
    tool_manager.register_tool(get_wikipedia_summary, CleanGetWikipediaSummaryArgs)
    tool_manager.register_tool(
        price_comparison_tool,
        PriceComparisonArgs,
        "Preisvergleich für Produkte. Vergleicht idealo.de vs. geizhals.de (DE) oder amazon.com vs. bestbuy.com (USA). Liefert den günstigsten Preis inkl. optionalem Refurbished-Spar-Tipp (>= 20% Ersparnis).",
    )
    tool_manager.set_output_schema("system.price_comparison", PriceComparisonOutput)

    # 2. Geo
    tool_manager.register_tool(
        get_distance_and_route_tool, CleanGetDistanceArgs, "system.routing"
    )
    tool_manager.register_tool(
        find_local_business_tool,
        schemas.FindLocalBusinessArgs,
        (
            "PFLICHT-TOOL für lokale Empfehlungen! Wenn der Nutzer nach Restaurants, Geschäften oder POIs sucht, "
            "FRAGE NIEMALS NACH ERLAUBNIS, sondern FÜHRE DIESES TOOL SOFORT AUS. "
            "UX-REGEL: Sei intelligent! Wenn der Nutzer z.B. 4 Restaurants sucht, nutze die Ergebnisse, um proaktiv "
            "eine diverse Auswahl zu präsentieren (z.B. 1x Budget/Locker, 1x Fine Dining, 1x Vegan/Spezial, 1x Geheimtipp). "
            "Erfinde keine Orte, nutze immer diese Live-Daten."
        ),
    )
    tool_manager.register_tool(get_country_info_tool, schemas.CountryInfoArgs)

    # 3. Media
    tool_manager.register_tool(
        create_pdf_from_markdown,
        schemas.CreatePdfFromMarkdownArgs,
        "Erstellt PDF. WICHTIG: Nutze 'filename'.",
    )
    tool_manager.register_tool(save_mp3_tool, schemas.SaveMp3Args)
    tool_manager.register_tool(generate_image_tool, schemas.GenerateImageToolArgs)

    # 4. Filesystem
    fs_tools = [
        (filesystem_tools.create_file, schemas.CreateFileArgs),
        (filesystem_tools.read_file, schemas.ReadFileArgs),
        (filesystem_tools.delete_file, schemas.DeleteFileArgs),
        (filesystem_tools.list_directory, schemas.ListDirectoryArgs),
        (filesystem_manager.list_allowed_workspaces, schemas.ListAllowedWorkspacesArgs),
        (filesystem_manager.create_directory, schemas.CreateDirectoryArgs),
        (filesystem_manager.delete_directory, schemas.DeleteDirectoryArgs),
        (filesystem_manager.rename_file, schemas.RenameFileArgs),
        (filesystem_tools.move_file, schemas.MoveFileArgs),
        (filesystem_manager.move_files, schemas.MoveFilesArgs),
        (filesystem_manager.find_files, schemas.FindFilesArgs),
    ]
    for func, schema in fs_tools:
        tool_manager.register_tool(func, schema)

    # 5. Kalender & Mail
    cal_tools = [
        (get_calendar_events, schemas.GetCalendarEventsArgs),
        (create_calendar_event, schemas.CreateCalendarEventArgs),
        (delete_calendar_event, schemas.DeleteCalendarEventArgs),
        (update_calendar_event, schemas.UpdateCalendarEventArgs),
        (find_free_time_slots, schemas.FindFreeTimeSlotsArgs),
        (update_calendar_event_description, schemas.UpdateCalendarEventDescriptionArgs),
        (find_and_update_calendar_event, schemas.FindAndUpdateCalendarEventArgs),
        (find_address_and_update_calendar_event, schemas.FindAddressAndUpdateCalendarEventArgs),
        (get_latest_emails, schemas.GetLatestEmailsArgs),
        (send_email, schemas.SendEmailArgs),
        (read_email, schemas.ReadEmailArgs),
    ]
    for func, schema in cal_tools:
        tool_manager.register_tool(func, schema)

    # Mail Wrapper manuell registrieren
    tool_manager.register_tool(
        find_contact_and_send_email_wrapper, schemas.FindContactAndSendEmailArgs
    )

    # 6. Kontakte & Memory (V2.1 Gold Standard)
    # Neue Memory Tools - V2.1 Gold Standard (memory_write, memory_read, memory_update, memory_history)
    tool_manager.register_tool(
        memory_write_tool,
        schemas.MemoryWriteArgs,
        name="memory.write",
        description="Speichert einen Fakt oder eine Information im Langzeitgedächtnis. Wird aufgerufen wenn der User etwas Wichtiges erwähnt (Vorlieben, Fakten über Personen). NICHT für Smalltalk oder Begrüßungen.",
    )
    tool_manager.register_tool(
        memory_read_tool,
        schemas.MemoryReadArgs,
        name="memory.read",
        description="Durchsucht das Gedächtnis nach relevanten Informationen. NUR aufrufen wenn der User explizit nach vergangenen Informationen fragt (z.B. 'Was weiß ich über X?', 'Erzähle mir von Y'). NIEMALS für Smalltalk oder 'Wer bist du?'.",
    )
    tool_manager.register_tool(
        memory_update_tool,
        schemas.MemoryUpdateArgs,
        name="memory.update",
        description="Aktualisiert oder korrigiert eine bestehende Erinnerung. Nur für user_editable=true Memories.",
    )
    tool_manager.register_tool(
        memory_history_tool,
        schemas.MemoryHistoryArgs,
        name="memory.history",
        description="Zeigt den Änderungsverlauf (Audit-Trail) einer Erinnerung an.",
    )

    tool_manager.register_tool(
        create_or_update_contact_tool, contact_schemas.CreateOrUpdateContactArgs
    )
    tool_manager.register_tool(list_contacts_wrapper, contact_schemas.ContactListArgs)
    tool_manager.register_tool(delete_contact_by_id_wrapper, contact_schemas.ContactDeleteArgs)

    tool_manager.register_tool(
        query_knowledge_base,
        schemas.QueryKnowledgeBaseArgs,
        "WISSENS-TOOL: Nutze dieses Tool für PDFs. Suche nach Stichworten (z.B. 'Hauptstadt', "
        "'Einwohner'), NICHT nach ganzen Sätzen. Der Parameter 'filename' ist optional."
    )

    tool_manager.register_tool(
        open_knowledge_document,
        schemas.OpenKnowledgeDocumentArgs,
        "Öffnet ein Dokument in der Wissensdatenbank (PDF-Viewer) per Dateiname. Nutze es bei 'Zeig mir...', 'Öffne...' oder ähnlichen Anfragen.",
    )

    tool_manager.register_tool(
        get_full_document_text,
        schemas.GetFullDocumentTextArgs,
        "Liefert den vollständigen Text eines Dokuments, ohne ihn vorher zu kürzen oder zu suchen."
    )

    tool_manager.register_tool(
        edit_pdf_text_in_place,
        schemas.EditPdfTextInPlaceArgs,
        "Überarbeitet eine PDF chirurgisch, indem gezielt Textstellen ersetzt werden."
    )

    tool_manager.register_tool(
        hardened_edit_pdf,
        schemas.HardenedEditPdfArgs,
        "Sicherer Composite-PDF-Edit mit Backup (Makro ueber interne Skills).",
    )

    tool_manager.register_tool(
        list_knowledge_documents,
        schemas.ListKnowledgeDocumentsArgs,
        "Gibt eine Liste aller aktuell in der Wissensdatenbank vorhandenen Dokumente zurück. Nutze dieses Tool, wenn der User fragt 'Welche Dokumente hast du?', 'Was ist in der Wissensbasis?' oder 'Welche PDFs kennst du?'.",
    )

    tool_manager.register_tool(
        system_grant_permission,
        schemas.GrantPermissionArgs,
        "Ermöglicht dem System, auf Basis einer User-Zustimmung ein Tool dauerhaft zu erlauben.",
    )

    tool_manager.register_tool(
        system_revoke_permission,
        schemas.RevokePermissionArgs,
        "Widerruft eine zuvor erteilte dauerhafte Erlaubnis für ein Tool und verlangt erneut Consent.",
    )


# --- PUBLIC API / LEGACY SUPPORT ---

# Alias für direkten Zugriff (damit alter Code nicht bricht)
TOOL_REGISTRY = tool_manager.tools


def get_all_tool_definitions():
    if not tool_manager.get_all_tools():
        register_all_tools()
    return tool_manager.get_tool_definitions()


def get_all_tools() -> Dict[str, Any]:
    if not tool_manager.get_all_tools():
        register_all_tools()
    # Da Legacy-Code ein 'Tool'-Objekt mit .func erwartet, und ToolDefinition.func existiert,
    # ist ToolDefinition kompatibel zum alten Tool-Objekt.
    return tool_manager.get_all_tools()
