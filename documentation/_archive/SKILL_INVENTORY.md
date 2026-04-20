# Skill Inventory Audit (Arbeitsanweisung #12)

Stand: 2026-03-07

## Scope
- `backend/tools/`
- `backend/skills/`
- `backend/services/tool_manager.py`
- `backend/tool_registry.py`

## Executive Summary
- Gefundene Skill-Katalogeintraege (`backend/skills/**/*.json` mit `legacy_name`): **46**
- Registrierte Tools in `register_all_tools()`: **46**
- Statusverteilung:
  - 🟢 Modern/Pydantic: **44**
  - 🟡 Legacy/Dict: **1** (P1)
  - 🔴 Broken/Deprecated: **1**

## Inventar-Tabelle

| Skill ID | Legacy Name | Status | Dateipfad |
|---|---|---|---|
| calendar.create_event | create_calendar_event | 🟢 Modern/Pydantic | `backend/skills/calendar/create_event.json` |
| calendar.delete_event | delete_calendar_event | 🟢 Modern/Pydantic | `backend/skills/calendar/delete_event.json` |
| calendar.find_address_and_update_event | find_address_and_update_calendar_event | 🟢 Modern/Pydantic | `backend/skills/calendar/find_address_and_update_event.json` |
| calendar.find_and_update_event | find_and_update_calendar_event | 🟢 Modern/Pydantic | `backend/skills/calendar/find_and_update_event.json` |
| calendar.find_slots | find_free_time_slots | 🟢 Modern/Pydantic | `backend/skills/calendar/find_slots.json` |
| calendar.list_events | get_calendar_events | 🟢 Modern/Pydantic | `backend/skills/calendar/list_events.json` |
| calendar.update_event | update_calendar_event | 🟢 Modern/Pydantic | `backend/skills/calendar/update_event.json` |
| calendar.update_event_description | update_calendar_event_description | 🟢 Modern/Pydantic | `backend/skills/calendar/update_event_description.json` |
| communication.find_contact_and_email | find_contact_and_send_email_wrapper | 🟢 Modern/Pydantic | `backend/skills/communication/find_contact_and_email.json` |
| communication.list_emails | get_latest_emails | 🟢 Modern/Pydantic | `backend/skills/communication/list_emails.json` |
| communication.read_email | read_email | 🟢 Modern/Pydantic | `backend/skills/communication/read_email.json` |
| communication.send_email | send_email | 🟢 Modern/Pydantic | `backend/skills/communication/send_email.json` |
| contacts.create_or_update | create_or_update_contact_tool | 🟢 Modern/Pydantic | `backend/skills/contacts/create_or_update.json` |
| contacts.delete | delete_contact_by_id_wrapper | 🟢 Modern/Pydantic | `backend/skills/contacts/delete.json` |
| contacts.list | list_contacts_wrapper | 🟢 Modern/Pydantic | `backend/skills/contacts/list.json` |
| filesystem.create_directory | create_directory | 🟢 Modern/Pydantic | `backend/skills/filesystem/create_directory.json` |
| filesystem.create_file | create_file | 🟢 Modern/Pydantic | `backend/skills/filesystem/create_file.json` |
| filesystem.delete_directory | delete_directory | 🟢 Modern/Pydantic | `backend/skills/filesystem/delete_directory.json` |
| filesystem.delete_file | delete_file | 🟢 Modern/Pydantic | `backend/skills/filesystem/delete_file.json` |
| filesystem.list_directory | list_directory | 🟢 Modern/Pydantic | `backend/skills/filesystem/list_directory.json` |
| filesystem.list_workspaces | list_allowed_workspaces | 🟢 Modern/Pydantic | `backend/skills/filesystem/list_workspaces.json` |
| filesystem.move_file | move_file | 🟢 Modern/Pydantic | `backend/skills/filesystem/move_file.json` |
| filesystem.move_files | move_files | 🟢 Modern/Pydantic | `backend/skills/filesystem/move_files.json` |
| filesystem.read_file | read_file | 🟢 Modern/Pydantic | `backend/skills/filesystem/read_file.json` |
| filesystem.rename_file | rename_file | 🟢 Modern/Pydantic | `backend/skills/filesystem/rename_file.json` |
| knowledge.edit_pdf | edit_pdf_text_in_place | 🟢 Modern/Pydantic | `backend/skills/knowledge/edit_pdf.json` |
| knowledge.hardened_edit | hardened_edit_pdf | 🟢 Modern/Pydantic | `backend/skills/knowledge/hardened_edit.json` |
| knowledge.list_documents | list_knowledge_documents | 🔴 Broken/Deprecated | `backend/skills/knowledge/list_documents.json` |
| knowledge.open_document | open_knowledge_document | 🟢 Modern/Pydantic | `backend/skills/knowledge/open_document.json` |
| knowledge.query | query_knowledge_base | 🟢 Modern/Pydantic | `backend/skills/knowledge/query.json` |
| knowledge.read_full_text | get_full_document_text | 🟢 Modern/Pydantic | `backend/skills/knowledge/read_full_text.json` |
| memory.save_core_fact | save_core_memory_fact | 🟢 Modern/Pydantic | `backend/skills/memory/save_core_memory_fact.json` |
| memory.search_summaries | search_past_conversation_summaries_tool | 🟢 Modern/Pydantic | `backend/skills/memory/search_summaries.json` |
| system.country_info | get_country_info_tool | 🟢 Modern/Pydantic | `backend/skills/system/country_info.json` |
| system.create_pdf | create_pdf_from_markdown | 🟢 Modern/Pydantic | `backend/skills/system/create_pdf.json` |
| system.generate_image | generate_image_tool | 🟢 Modern/Pydantic | `backend/skills/system/generate_image.json` |
| system.grant_permission | system_grant_permission | 🟢 Modern/Pydantic | `backend/skills/system/grant_permission.json` |
| system.local_business | find_local_business_tool | 🟢 Modern/Pydantic | `backend/skills/system/local_business.json` |
| system.revoke_permission | system_revoke_permission | 🟢 Modern/Pydantic | `backend/skills/system/revoke_permission.json` |
| system.routing | get_distance_and_route_tool | 🟢 Modern/Pydantic | `backend/skills/system/routing.json` |
| system.rss_news | get_latest_news_rss | 🟢 Modern/Pydantic | `backend/skills/system/rss_news.json` |
| system.save_mp3 | save_mp3_tool | 🟢 Modern/Pydantic | `backend/skills/system/save_mp3.json` |
| system.scrape_website | scrape_website | 🟢 Modern/Pydantic | `backend/skills/system/scrape_website.json` |
| system.weather | get_weather_from_api_tool | 🟢 Modern/Pydantic | `backend/skills/system/weather.json` |
| system.websearch | perform_websearch | 🟡 Legacy/Dict **(P1 Refactor Priority)** | `backend/skills/system/websearch.json` |
| system.wikipedia_summary | get_wikipedia_summary | 🟢 Modern/Pydantic | `backend/skills/system/wikipedia_summary.json` |

## Wichtige Diskrepanzen / Risiken

1. **P1: `perform_websearch` (Legacy Name) -> `system.websearch`**
   - Legacy-Aufrufname wird weiterhin verwendet und wirft bei Legacy-Auflösung bewusst Deprecation-Warnungen.
   - Der aktuelle Wrapper in `backend/tool_registry.py` erwartet `provider`, waehrend `WebsearchToolArgs` nur `query` enthaelt.
   - Risiko: Inkonsistente Argumentquellen (teils implizit, teils vom LLM), instabile Tool-Calls ueber Provider-Grenzen.

2. **Broken: `list_knowledge_documents`**
   - In der Registrierung wird `schemas.OpenKnowledgeDocumentArgs.__class__` statt eines konkreten Pydantic-Arg-Modells uebergeben.
   - Ergebnis ist ein ungueltiger Schema-Typ (`ModelMetaclass`) statt sauberer Tool-Parameter.

## Stabilisierungsvorschlag (ohne Funktionsbruch)

### Phase 1 - Sicherheitsnetz + Kompatibilitaet (kurzfristig)
1. **Alias-Layer fuer Websearch formal einfuehren**
   - Kanonisches Tool: `system.websearch`.
   - Legacy-Namen (`perform_websearch`) nur als Alias im Router/Executor behalten.
2. **Dual-Args-Unterstuetzung fuer Websearch**
   - Neues Pydantic-Modell z. B. `WebsearchArgsV2(query, provider: Optional[str], model: Optional[str])`.
   - `provider` optional lassen; fallback auf Konfiguration (wie heute).
3. **`list_knowledge_documents` Schema fixen**
   - Registrierung auf ein echtes Args-Modell umstellen (z. B. `ListKnowledgeDocumentsArgs` ohne Pflichtfelder).

### Phase 2 - Migrationspfad (mittel)
1. Tool-Selection-Prompts auf Skill-IDs (`system.websearch`) ausrichten.
2. Deprecation-Logging fuer `perform_websearch` beibehalten, aber mit klarer Migrationsmeldung.
3. Regression-Tests:
   - Legacy-Aufruf `perform_websearch` -> funktioniert + Warnung.
   - Neuer Aufruf `system.websearch` -> funktioniert ohne Warnung.
   - `list_knowledge_documents` erzeugt gueltiges JSON-Schema.

### Phase 3 - Cleanup (spaeter)
1. Nach stabiler Telemetrie den Legacy-Primadnamen aus Prompts entfernen.
2. Alias-Weiterleitung nur noch fuer Backward-Compatibility-Pfade behalten.
3. Optional: harte Policy, dass neue Skills nur kanonische Skill-IDs verwenden.

## Referenzen
- Registrierung: `backend/tool_registry.py`
- Skill-Mapping/Katalog: `backend/skills/**/*.json`
- Deprecation-Logik: `backend/services/tool_manager.py`
- Websearch Gateway: `backend/services/websearch/websearch.py`

## Diamond Standard Review Update (2026-03-10)

- `system.routing` (`backend/skills/system/routing.json`): Version auf `1.1.1` erhöht, Beispiel-Outputs now align with runtime (`duration`/`maps_link`) und `INVALID_COORDINATES` demonstriert den realen Guardrail. Skill ist damit sauber dokumentiert und als Diamond-Ready markiert.
- `system.country_info` (`backend/skills/system/country_info.json`): Version `1.1.1`, neue Error-Beispiele für `INVALID_INPUT` und `API_ERROR` zeigen alle tatsächlichen Guardrails. Damit ist die Dokumentation vollständig und Diamond-fertig.
