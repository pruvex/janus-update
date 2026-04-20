# Janus Tool-Inventur (Phase A)

## Domäne: Knowledge (PDF & RAG)
| Tool-Name | Datei | Zweck | Risiko | Side Effects |
| :--- | :--- | :--- | :--- | :--- |
| `query_knowledge_base` | `backend/services/rag_manager.py` | Vektorbasierte Suche in indexierten PDFs | `read_only` | Keine (nur Antwort auf Anfrage) |
| `open_knowledge_document` | `backend/services/tool_executor.py` | Öffnet ein PDF im Knowledge Center via UI-Action | `read_only` | Trigger für PDF-Viewer (keine Datenänderung) |
| `get_full_document_text` | `backend/services/tool_executor.py` | Liefert den vollständigen Text eines Dokuments (DB/Chroma/PDF) | `read_only` | Keine (nur Lesezugriff) |
| `edit_pdf_text_in_place` | `backend/tools/pdf_editor.py` | Chirurgische Textersetzung in PDFs (zur Fact-Check-Korrektur) | `confirm_required` | Mutiert oder ersetzt gespeicherte PDFs, evtl. neue Datei/Index |
| `list_knowledge_documents` | `backend/services/tool_executor.py` | Listet verfügbare PDF-Dokumente auf | `read_only` | Keine |

## Domäne: Filesystem
| Tool-Name | Datei | Zweck | Risiko | Side Effects |
| :--- | :--- | :--- | :--- | :--- |
| `create_file` | `backend/services/filesystem_manager.py` | Erstellt eine Datei in definiertem Workspace | `confirm_required` | Schreibt neue Datei auf der Platte |
| `read_file` | `backend/services/filesystem_manager.py` | Liefert Dateiinhalt aus erlaubten Workspaces | `read_only` | Keine |
| `delete_file` | `backend/services/filesystem_manager.py` | Löscht eine Datei (nur wenn vorhanden) | `restricted` | Entfernt Datei permanent |
| `list_directory` | `backend/services/filesystem_manager.py` | Zeigt Verzeichnisinhalt (mit optionalem Pattern) | `read_only` | Keine |
| `list_allowed_workspaces` | `backend/services/filesystem_manager.py` | Gibt erlaubte Arbeitsbereiche zurück | `read_only` | Keine |
| `create_directory` | `backend/services/filesystem_manager.py` | Erzeugt neue Ordnerstruktur | `confirm_required` | Erstellt Verzeichnis |
| `delete_directory` | `backend/services/filesystem_manager.py` | Löscht Ordner rekursiv (außer Workspaces) | `restricted` | Entfernt Ordner + Inhalt |
| `move_file` / `rename_file` | `backend/services/filesystem_manager.py` | Verschiebt oder benennt Dateien um | `confirm_required` | Bewegt/benennt Datei innerhalb erlaubter Bereiche |
| `move_files` | `backend/services/filesystem_manager.py` | Batch-Verschiebung nach Pattern | `confirm_required` | Bewegt mehrere Dateien, ggf. neue Zielordner |

## Domäne: Vision
- Aktuell sind im Tool-Registry keine Vision-spezifischen Tools registriert. Die Vision-Domäne wird später mit Kamera-/Bildanalyse-Funktionen bestückt.

## Domäne: Memory
| Tool-Name | Datei | Zweck | Risiko | Side Effects |
| :--- | :--- | :--- | :--- | :--- |
| `search_past_conversation_summaries_tool` | `backend/services/memory_manager.py` | Durchsucht früher gespeicherte Memories (STM/LTM) | `read_only` | Keine |

## Domäne: System
| Tool-Name | Datei | Zweck | Risiko | Side Effects |
| :--- | :--- | :--- | :--- | :--- |
| `get_latest_news_rss` | `backend/tools/rss_service.py` | Ruft Nachrichten per RSS ab | `read_only` | Keine |
| `scrape_website` | `backend/services/scraper_service.py` | Liest Webseiteninhalt für LLM-Antworten | `read_only` | Keine (nur Parsing) |
| `get_weather_from_api_tool` | `backend/tools/weather_service.py` | Holt Wetterdaten zu Ort/Zeitraum | `read_only` | Keine |
| `get_wikipedia_summary` | `backend/tools/wiki_service.py` | Liefert gekürzte Wikipedia-Zusammenfassung | `read_only` | Keine |
| `perform_websearch` | `backend/tool_registry.py` (Wrapper) | Startet Gateway-Websuche über `websearch_service` | `read_only` | Keine |
| `get_distance_and_route_tool` | `backend/tools/geo_service.py` | Berechnet Strecke + Fahrzeit via OSRM | `read_only` | Keine |
| `find_local_business_tool` | `backend/tools/geo_service.py` | Extrahiert visuelle Angaben zu lokalen Geschäften | `read_only` | Keine |
| `get_country_info_tool` | `backend/tools/geo_service.py` | Gibt Länderbasisinfos zurück | `read_only` | Keine |
| `create_pdf_from_markdown` | `backend/tools/pdf_generator.py` | Erzeugt PDF aus Markdown-Dateien | `confirm_required` | Schreibt PDF und triggert Indexierung |
| `save_mp3_tool` | `backend/tools/media_tools.py` | Synthesisiert Text zu MP3 und speichert auf Desktop | `confirm_required` | Schreibt MP3-Datei auf Desktop |
| `generate_image_tool` | `backend/tools/media_tools.py` | Erzeugt Bild via LLM-Provider (z.B. OpenAI/Gemini) | `confirm_required` | Ruft Remote-API, liefert URL zu erzeugtem Bild |
| `get_calendar_events` | `backend/tools/calendar_tools.py` | Listet bestehende Termine | `read_only` | Keine |
| `create_calendar_event` | `backend/tools/calendar_tools.py` | Erstellt Termine via Kalender-API | `confirm_required` | Fügt Ereignis hinzu |
| `delete_calendar_event` | `backend/tools/calendar_tools.py` | Löscht Termin | `restricted` | Entfernt Ereignis |
| `update_calendar_event` | `backend/tools/calendar_tools.py` | Aktualisiert Termin | `confirm_required` | Ändert bestehendes Ereignis |
| `find_free_time_slots` | `backend/tools/calendar_tools.py` | Sucht freie Terminslots | `read_only` | Keine |
| `update_calendar_event_description` | `backend/tools/calendar_tools.py` | Passt Beschreibung an | `confirm_required` | Schreibt neue Beschreibung |
| `find_and_update_calendar_event` | `backend/tools/calendar_tools.py` | Kombiniert Suche + Update | `confirm_required` | Ändert Termin und ggf. Beschreibung |
| `find_address_and_update_calendar_event` | `backend/tools/calendar_tools.py` | Sucht Adresse und passt Event an | `confirm_required` | Ergänzt/ändert Termindaten |
| `get_latest_emails` | `backend/tools/gmail_tools.py` | Holt kürzlich eingegangene E-Mails | `read_only` | Keine |
| `read_email` | `backend/tools/gmail_tools.py` | Liest einzelne E-Mail (Body + Anhänge) | `read_only` | Keine |
| `send_email` | `backend/tools/gmail_tools.py` | Versendet Mail über verknüpften Account | `confirm_required` | Sendet E-Mail, Log-Eintrag im Postausgang |
| `create_or_update_contact_tool` | `backend/tools/db_wrappers.py` | Legt Kontakt an oder aktualisiert ihn | `confirm_required` | Schreibt in Kontakt-DB |
| `list_contacts_wrapper` | `backend/tools/db_wrappers.py` | Listet gespeicherte Kontakte | `read_only` | Keine |
| `delete_contact_by_id_wrapper` | `backend/tools/db_wrappers.py` | Entfernt Kontakt anhand ID | `restricted` | Löscht Datenbankeintrag |
| `find_contact_and_send_email_wrapper` | `backend/tool_registry.py` | Kombiniert Kontakt-Suche + E-Mail | `confirm_required` | Sendet Mail + Log, potenziell DB-Reads |

## Fehler-Taxonomie
1. **Tool-Executor (LLM-Schnittstelle)**: `{"role":"tool","name":"...","content":"Error: Tool 'NAME' not found."}` oder `{"content":"Error executing tool: <message>"}` tritt bei Alias-/Registrierungsproblemen oder Laufzeitfehlern auf.
2. **Filesystem-Manager**: `{"output":"Fehler: <Exception-Message>"}` (z. B. `Fehler bei create_file`, `Fehler: '<path>' existiert nicht.`) bei Pfad-/Zugriffsproblemen.
3. **Knowledge/Memory**: `{"error":"Datei '<name>' nicht gefunden."}`, `{"error":"Die Datei enthält keinen direkt abrufbaren Text."}` (z. B. `get_full_document_text`).
4. **API-Wrapper (Media/Geo/Calendar/etc.)** erzeugen `{"status":"error","message":"<Text>"}` oder `{"status":"error","output":"<Text>"}` z. B. `Geocoding nicht gefunden`, `OpenAI API Key fehlt`, `Kein Text zum Speichern gefunden.`
5. **Tool-Executor JSON-Protokoll**: `{"tool_call_id": ..., "role":"tool", "content":"<JSON-string>"}` und als Fallback `Error executing tool: <Exception>` wenn die Ziel-Logik eine Exception wirft.
