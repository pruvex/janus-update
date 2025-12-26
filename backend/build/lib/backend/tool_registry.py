# backend/tool_registry.py
import logging
from typing import Any, Dict, Optional

import keyring

# --- IMPORTS DER LOGIK ---
# Wir importieren die Module, damit die Funktionen verfügbar sind
from backend.data import contact_schemas, schemas
from backend.services import filesystem_manager, memory_manager
from backend.services.tool_manager import tool_manager
from backend.services.websearch import perform_websearch as perform_websearch_service
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
from backend.tools.geo_service import (
    CleanGetDistanceArgs,
    find_local_business_tool,
    get_country_info_tool,
    get_distance_and_route_tool,
)

# WICHTIG: Hier wurde 'find_contact_and_send_email' ENTFERNT, da es nicht in gmail_tools existiert!
from backend.tools.gmail_tools import get_latest_emails, read_email, send_email
from backend.tools.media_tools import generate_image_tool, save_mp3_tool
from backend.tools.pdf_generator import CleanCreatePdfArgs, create_pdf_from_markdown

# Tools aus den Modulen
from backend.tools.rss_service import CleanGetLatestNewsRssToolArgs, get_latest_news_rss
from backend.tools.weather_service import CleanGetWeatherFromApiToolArgs, get_weather_from_api_tool
from backend.tools.wiki_service import CleanGetWikipediaSummaryArgs, get_wikipedia_summary

logger = logging.getLogger("janus_backend")

# --- Hilfs-Wrapper (Lokal definiert) ---


async def perform_websearch(query: str, model: Optional[str] = None) -> dict:
    """Wrapper für Websuche mit Keyring."""
    try:
        from backend.main import load_config

        cfg = load_config()
        prov = cfg.get("last_used_provider", "openai")
        key = keyring.get_password("Janus-Projekt", prov)
        if not key:
            return {"status": "error", "output": f"API Key für {prov} fehlt."}
        return await perform_websearch_service(query=query, api_key=key, provider=prov, model=model)
    except Exception as e:
        return {"status": "error", "output": str(e)}


async def find_contact_and_send_email_wrapper(name_query: str, subject: str, body: str) -> dict:
    """Sucht Kontakt in DB und sendet Mail."""
    from backend.data import crud, database

    db = next(database.get_db())
    try:
        contacts = crud.search_contacts_by_name(db, name_query=name_query)
        if not contacts:
            return {"status": "error", "message": f"Kontakt '{name_query}' nicht gefunden."}
        target_contact = contacts[0]
        if not target_contact.email:
            return {
                "status": "error",
                "message": f"Kontakt '{target_contact.name}' hat keine E-Mail.",
            }

        return send_email(to=target_contact.email, subject=subject, body=body)
    finally:
        db.close()


# --- REGISTRIERUNG ---
def register_all_tools():
    """Lädt alle Tools in den Manager."""
    if tool_manager.get_all_tools():
        return

    # 1. Info
    tool_manager.register_tool(
        get_latest_news_rss, CleanGetLatestNewsRssToolArgs, "Ruft aktuelle Schlagzeilen ab."
    )
    tool_manager.register_tool(
        get_weather_from_api_tool, CleanGetWeatherFromApiToolArgs, "Wettervorhersage."
    )
    tool_manager.register_tool(get_wikipedia_summary, CleanGetWikipediaSummaryArgs)
    tool_manager.register_tool(perform_websearch, schemas.WebsearchToolArgs)

    # 2. Geo
    tool_manager.register_tool(
        get_distance_and_route_tool, CleanGetDistanceArgs, "Distanzberechnung."
    )
    tool_manager.register_tool(find_local_business_tool, schemas.FindLocalBusinessArgs)
    tool_manager.register_tool(get_country_info_tool, schemas.GetCountryInfoToolArgs)

    # 3. Media
    tool_manager.register_tool(
        create_pdf_from_markdown, CleanCreatePdfArgs, "Erstellt PDF. WICHTIG: Nutze 'filename'."
    )
    tool_manager.register_tool(save_mp3_tool, schemas.SaveMp3Args)
    tool_manager.register_tool(generate_image_tool, schemas.GenerateImageToolArgs)

    # 4. Filesystem
    fs_tools = [
        (filesystem_manager.create_file, schemas.CreateFileArgs),
        (filesystem_manager.read_file, schemas.ReadFileArgs),
        (filesystem_manager.delete_file, schemas.DeleteFileArgs),
        (filesystem_manager.list_directory, schemas.ListDirectoryArgs),
        (filesystem_manager.list_allowed_workspaces, schemas.ListAllowedWorkspacesArgs),
        (filesystem_manager.create_directory, schemas.CreateDirectoryArgs),
        (filesystem_manager.delete_directory, schemas.DeleteDirectoryArgs),
        (filesystem_manager.rename_file, schemas.RenameFileArgs),
        (filesystem_manager.move_file, schemas.MoveFileArgs),
        (filesystem_manager.move_files, schemas.MoveFilesArgs),
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

    # 6. Kontakte & Memory
    tool_manager.register_tool(
        create_or_update_contact_tool, contact_schemas.CreateOrUpdateContactArgs
    )
    tool_manager.register_tool(list_contacts_wrapper, contact_schemas.ContactListArgs)
    tool_manager.register_tool(delete_contact_by_id_wrapper, contact_schemas.ContactDeleteArgs)
    tool_manager.register_tool(memory_manager.save_core_memory_fact, schemas.SaveCoreMemoryToolArgs)
    tool_manager.register_tool(
        memory_manager.search_past_conversation_summaries_tool, schemas.CrossChatMemoryToolArgs
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
