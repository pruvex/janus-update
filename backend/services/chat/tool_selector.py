from typing import List, Dict, Any, Set
from backend.tool_registry import get_all_tool_definitions

class ToolSelector:
    """
    Zuständig für die Auswahl relevanter Werkzeuge basierend auf dem User-Prompt.
    """

    # Erweiterte Keyword-Liste für bessere Trefferquote
    TOOL_CATEGORIES = {
        # E-Mail / Kommunikation
        "mail": ["get_latest_emails", "send_email", "find_contact_and_send_email"],
        "postfach": ["get_latest_emails"],
        "schreiben": ["send_email", "find_contact_and_send_email"],
        "nachricht": ["send_email", "find_contact_and_send_email"],
        
        # Kalender
        "kalender": ["get_calendar_events", "create_calendar_event", "delete_calendar_event", "update_calendar_event"],
        "termin": ["get_calendar_events", "create_calendar_event", "delete_calendar_event", "update_calendar_event"],
        "woche": ["get_calendar_events"], # "Was liegt die Woche an?"
        "heute": ["get_calendar_events", "get_weather_from_api_tool"],
        "morgen": ["get_calendar_events", "get_weather_from_api_tool"],

        # Kontakte
        "kontakt": ["create_or_update_contact_tool", "list_contacts_wrapper", "delete_contact_by_id_wrapper"],
        "adressbuch": ["create_or_update_contact_tool", "list_contacts_wrapper", "delete_contact_by_id_wrapper"],
        "nummer": ["list_contacts_wrapper"], # "Gib mir die Nummer von..."
        
        # Dateien
        "datei": ["create_file_tool", "read_file_tool", "delete_file_tool", "list_directory_tool", "create_pdf_from_markdown"],
        "ordner": ["list_directory_tool", "create_directory", "delete_directory"],
        "pdf": ["create_pdf_from_markdown"],
        "speichern": ["create_file_tool", "create_pdf_from_markdown"],

        # Wetter
        "wetter": ["get_weather_from_api_tool"],
        "temperatur": ["get_weather_from_api_tool"],
        "regen": ["get_weather_from_api_tool"],
        "sonne": ["get_weather_from_api_tool"],
        "grad": ["get_weather_from_api_tool"],

        # Geo / Route
        "route": ["get_distance_and_route_tool"],
        "entfernung": ["get_distance_and_route_tool"],
        "distanz": ["get_distance_and_route_tool"],
        "wie weit": ["get_distance_and_route_tool"],
        "km": ["get_distance_and_route_tool"],
        "kilometer": ["get_distance_and_route_tool"],
        "auto": ["get_distance_and_route_tool"],
        "fahrt": ["get_distance_and_route_tool"],
        "nach": ["get_distance_and_route_tool"], # "München nach Hamburg"

        # News
        "nachrichten": ["get_latest_news_rss"],
        "news": ["get_latest_news_rss"],
        "schlagzeilen": ["get_latest_news_rss"],
        "aktuell": ["get_latest_news_rss", "perform_websearch"],
        "feed": ["get_latest_news_rss"],
        "spiegel": ["get_latest_news_rss"],
        "tagesschau": ["get_latest_news_rss"],

        # Medien
        "bild": ["generate_image_tool"],
        "foto": ["generate_image_tool"],
        "zeichnen": ["generate_image_tool"],
        "malen": ["generate_image_tool"],
        "audio": ["save_mp3_tool"],
        "mp3": ["save_mp3_tool"],
        "sprechen": ["save_mp3_tool"],
        "vorlesen": ["save_mp3_tool"],
        "sagen": ["save_mp3_tool"],
    }

    # Basis-Tools, die immer verfügbar sein sollten
    CORE_TOOLS = {
        "perform_websearch",
        "get_wikipedia_summary",
        "read_email",
        "save_core_memory_fact",
        "find_local_business_tool",
        "save_mp3_tool",
    }

    @classmethod
    def select_tools(cls, user_prompt: str, email_context: List[Any] = None) -> List[Dict]:
        prompt_lower = user_prompt.lower()
        selected_names: Set[str] = set(cls.CORE_TOOLS)

        # 1. Kategorie-Matching
        for keyword, tools in cls.TOOL_CATEGORIES.items():
            # Einfaches Substring-Matching
            if keyword in prompt_lower:
                selected_names.update(tools)

        # 2. Kontext-Guardrails (E-Mail Kontext)
        if email_context:
            nav_keywords = ["lies", "öffne", "erste", "zweite", "nummer", "inhalt"]
            if any(kw in prompt_lower for kw in nav_keywords):
                # Fokus auf E-Mail Interaktion
                return [
                    t for t in get_all_tool_definitions()
                    if t["function"]["name"] in ["read_email", "perform_websearch"]
                ]

        # 3. Definitionen zurückgeben
        all_tools = get_all_tool_definitions()
        
        # Extrahiere die passenden Tools
        filtered = []
        for tool in all_tools:
            name = tool.get("function", {}).get("name")
            if name in selected_names:
                filtered.append(tool)
        
        return filtered if filtered else all_tools
