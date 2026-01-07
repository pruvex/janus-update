from typing import List, Dict, Any, Set
from backend.tool_registry import get_all_tool_definitions

class ToolSelector:
    """
    Zuständig für die Auswahl relevanter Werkzeuge basierend auf dem User-Prompt.
    OPTIMIERTE VERSION mit Candidate Retrieval.
    """

    # Liste gefährlicher Tools, die eine Bestätigung erfordern
    RISKY_TOOLS = {
        "delete_file_tool",
        "delete_directory",
        "delete_calendar_event",
        "send_email",
    }
    
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

    # Kritische Aktionen, die eine Bestätigung erfordern
    RISKY_TOOLS = {
        "delete_file_tool",
        "delete_directory",
        "delete_calendar_event",
        "send_email",
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
    def retrieve_candidates(cls, user_prompt: str) -> List[Dict[str, Any]]:
        """
        Identifiziert eine Liste von wahrscheinlichen Tool-Namen mit Konfidenzwerten.
        
        Returns:
            List[Dict]: Liste von Dictionaries mit 'tool_name' und 'confidence' für jedes Tool
        """
        prompt_lower = user_prompt.lower()
        candidates = []
        
        # 1. Core-Tools mit hoher Konfidenz (0.95) hinzufügen
        for tool_name in cls.CORE_TOOLS:
            candidates.append({
                "tool_name": tool_name,
                "confidence": 0.95
            })
        
        # 2. Keyword-basierte Kandidaten mit mittlerer Konfidenz (0.65) hinzufügen
        for keyword, tools in cls.TOOL_CATEGORIES.items():
            if keyword in prompt_lower:
                for tool_name in tools:
                    # Nur hinzufügen, wenn nicht bereits in der Liste (vermeide Duplikate)
                    if not any(c["tool_name"] == tool_name for c in candidates):
                        candidates.append({
                            "tool_name": tool_name,
                            "confidence": 0.65
                        })
        
        return candidates

    @classmethod
    def is_risky(cls, tool_name: str) -> bool:
        """Prüft, ob ein Tool als risikoreich eingestuft ist und eine Bestätigung erfordert.
        
        Args:
            tool_name: Name des zu prüfenden Tools
            
        Returns:
            bool: True, wenn das Tool risikoreich ist, sonst False
        """
        return tool_name in cls.RISKY_TOOLS

    @classmethod
    def select_tools(cls, user_prompt: str, email_context: List[Any] = None) -> List[Dict]:
        """
        Wählt die finalen Tool-Definitionen basierend auf den Kandidaten aus.
        Behält die alte Signatur bei, nutzt aber intern die neue Logik.
        """
        # Kontext-Guardrails (E-Mail Kontext) hat Vorrang
        if email_context:
            prompt_lower = user_prompt.lower()
            nav_keywords = ["lies", "öffne", "erste", "zweite", "nummer", "inhalt"]
            if any(kw in prompt_lower for kw in nav_keywords):
                # Fokus auf E-Mail Interaktion
                return [
                    t for t in get_all_tool_definitions()
                    if t["function"]["name"] in ["read_email", "perform_websearch"]
                ]

        # Schritt 1: Kandidaten finden
        candidates = cls.retrieve_candidates(user_prompt)
        
        # Extrahiere die Namen aus den Dictionaries
        # Wir nutzen ein Set für schnelleren Zugriff
        candidate_names = {c["tool_name"] for c in candidates}

        # Schritt 2: Definitionen aus dem Katalog filtern
        all_tools = get_all_tool_definitions()
        
        filtered_tools = []
        for tool in all_tools:
            name = tool.get("function", {}).get("name")
            if name in candidate_names:
                filtered_tools.append(tool)
        
        # Wenn keine Kandidaten gefunden wurden, bieten wir sicherheitshalber alle an.
        # Dies können wir später durch einen LLM-Router-Call ersetzen.
        return filtered_tools if filtered_tools else all_tools
