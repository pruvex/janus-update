# Janus Projekt-Inventar & Status

**Dokument:** 04_PROJECT_INVENTORY_AND_STATUS.md  
**Stand:** 2026-03-24  
**Scope:** Code-verifizierte Übersicht aller Projekt-Bausteine (Domains, Systems, Features, Skills)

---

## Domain: Core Architecture

Die zentralen Systeme, die das Fundament von Janus bilden.

### System: LLM Gateway
- **Beschreibung:** Managed die API-Verbindungen zu OpenAI, Gemini und Ollama. Kapselt Provider-spezifische Logik (Dialekte), Tool-Schemata und Response-Normalisierung.
- **Zugehörige Dateien:**
  - `backend/services/llm_gateway.py`
  - `backend/llm_providers/openai_service.py`
  - `backend/llm_providers/gemini_service.py`
  - `backend/llm_providers/ollama_service.py`

### System: Prompting Engine
- **Beschreibung:** Baut dynamisch die Prompts für die LLMs zusammen, basierend auf Provider, Modell und Chat-Kontext. Verwaltet System-Prompts und Dialekt-Templates.
- **Zugehörige Dateien:**
  - `backend/services/prompting/`

### System: Chat Orchestrator
- **Beschreibung:** Zentrale Steuerlogik für Chat-Anfragen. Koordiniert alle Subsysteme, führt den Tool-Loop aus und synchronisiert den Zustand.
- **Zugehörige Dateien:**
  - `backend/services/chat_orchestrator.py`
  - `backend/services/orchestrator/` (ContextManager, ExecutionEngine, StatusSync)

### System: Agent Planner
- **Beschreibung:** Analysiert Anfragen und entscheidet, ob komplexe Planung erforderlich ist. Zerlegt Aufgaben in ausführbare Schritte.
- **Zugehörige Dateien:**
  - `backend/services/agent_planner.py`
  - `backend/services/planner_service.py`

### System: Tool Executor
- **Beschreibung:** Führt die vom LLM gewählten Tools aus, verwaltet Skill-Routing und rendert Tool-Ergebnisse für die LLM-Konsumtion.
- **Zugehörige Dateien:**
  - `backend/services/tool_executor.py`
  - `backend/services/tool_manager.py`
  - `backend/services/skill_router.py`
  - `backend/services/tool_result_renderer.py`

### System: Vision Pipeline
- **Beschreibung:** Verarbeitet Bildanfragen, führt Bildanalysen durch und generiert strukturierte Beschreibungen.
- **Zugehörige Dateien:**
  - `backend/services/vision/`
  - `backend/services/vision_service.py`
  - `backend/services/image_manager.py`

---

## Domain: Knowledge Management

Systeme und Features rund um Dokumente, Fakten und Wissenszugriff.

### System: RAG Manager
- **Beschreibung:** Verwaltet Vektor-basierte Dokumentensuche in indexierten PDFs und anderen Dokumenten.
- **Zugehörige Dateien:**
  - `backend/services/rag_manager.py`

### Feature: PDF Fact-Checking
- **Beschreibung:** Ermöglicht das Suchen, Verifizieren und Korrigieren von Informationen in PDF-Dokumenten. Der Nutzer kann Dokumente hochladen, Fakten prüfen und Korrekturen vornehmen.
- **Beteiligte Systeme:** `Tool Executor`, `LLM Gateway`, `RAG Manager`, `Knowledge Composite`
- **Beteiligte Skills:**
  - `knowledge.query` – Vektorbasierte Suche in Dokumenten
  - `knowledge.edit_pdf` – Chirurgische Textersetzung in PDFs
  - `knowledge.hardened_edit` – Gehärtete PDF-Bearbeitung mit zusätzlichen Checks
  - `knowledge.read_full_text` – Vollständigen Dokumenttext abrufen
  - `system.websearch` – Externe Faktenchecks via Web

### Feature: Knowledge Center (UI)
- **Beschreibung:** Die für den Nutzer sichtbare Oberfläche zum Öffnen und Betrachten von PDF-Dokumenten.
- **Beteiligte Systeme:** `Tool Executor`
- **Beteiligte Skills:**
  - `knowledge.open_document` – Öffnet ein PDF im Knowledge Center

---

## Domain: Memory & Context

Systeme für langfristige Speicherung und Kontexterhaltung.

### System: Memory Manager
- **Beschreibung:** Verwaltet Kurz- und Langzeitgedächtnis (STM/LTM), speichert Gesprächszusammenfassungen und core facts.
- **Zugehörige Dateien:**
  - `backend/services/memory_manager.py`
  - `backend/services/memory_extractor.py`

### System: Vector Service
- **Beschreibung:** Bietet semantische Vektor-Suche für Memory-Recall und ähnliche Gespräche.
- **Zugehörige Dateien:**
  - `backend/services/vector_service.py`

### Feature: Long-Term Memory
- **Beschreibung:** Gibt Janus die Fähigkeit, sich an frühere Gespräche und wichtige Fakten über den Nutzer zu erinnern.
- **Beteiligte Systeme:** `Memory Manager`, `Vector Service`, `Chat Summarizer`
- **Beteiligte Skills:**
  - `memory.search_summaries` – Durchsucht frühere Gespräche
  - `memory.save_core_fact` – Speichert wichtige Nutzer-Fakten

### Feature: Calendar Memory Mirror
- **Beschreibung:** Spiegelt die nächsten Kalendertermine als kompakten, nicht-autoritativen Snapshot in `memories.category = "calendar_snapshot"` und injiziert daraus bei Kalender-/Planungsfragen einen begrenzten Chat-Kontext.
- **Beteiligte Systeme:** `Calendar Service`, `Memory Manager`, `Chat Orchestrator`
- **Zugehörige Dateien:**
  - `backend/services/calendar/calendar_memory.py`
  - `backend/api/routers/calendar.py`
  - `backend/services/chat_orchestrator.py`
  - `backend/tests/test_calendar_memory.py`
- **Betriebsflags:** `JANUS_CALENDAR_MIRROR_ENABLED` (default on), `JANUS_CALENDAR_PROACTIVE_HINTS` (default off).

---

## Domain: Communication

Features für E-Mail, Kontakte und externe Kommunikation.

### System: Contact Manager
- **Beschreibung:** Verwaltet das Adressbuch des Nutzers mit CRUD-Operationen.
- **Zugehörige Dateien:**
  - `backend/services/contact_manager.py`

### Feature: E-Mail Integration
- **Beschreibung:** Ermöglicht Lesen, Senden und Verwalten von E-Mails über verknüpfte Accounts.
- **Beteiligte Systeme:** `Tool Executor`, `Contact Manager`
- **Beteiligte Skills:**
  - `communication.list_emails` – Liste kürzlich eingegangener E-Mails
  - `communication.read_email` – Einzelne E-Mail lesen
  - `communication.send_email` – E-Mail versenden
  - `communication.find_contact_and_email` – Kombiniert Kontakt-Suche + E-Mail

### Feature: Kontaktverwaltung
- **Beschreibung:** Erstellen, Aktualisieren und Löschen von Kontakten im Adressbuch.
- **Beteiligte Systeme:** `Contact Manager`
- **Beteiligte Skills:**
  - `contacts.create_or_update` – Kontakt anlegen/aktualisieren
  - `contacts.list` – Kontakte auflisten
  - `contacts.delete` – Kontakt löschen

---

## Domain: Calendar & Scheduling

Kalender-Funktionen und Terminmanagement.

### UI: Tages-Panel (Diamond Rail)
- **Beschreibung:** Eingebetteter rechter Rail am Chat (`calendar-day-widget`): Tages-Kennzahlen, nächster Termin, Schnellaktionen, KI-Zeile (Delegation Vollkalender). Produktions-UI aus **`frontend/dist`** nach `vite build`; Gate: `scripts/verify-frontend-dist.cjs`.
- **Zugehörige Dateien:** `frontend/js/calendar-day-widget.js`, `frontend/js/calendar-day-stats.js`, `frontend/css/calendar-day-widget.css`, `frontend/index.html`; Release-Doku: `documentation/tasks/task_calendar_day_widget_rail_diamond.md`.

### System: Calendar Tools
- **Beschreibung:** Integration mit Kalender-APIs zum Lesen, Erstellen und Aktualisieren von Terminen.
- **Zugehörige Dateien:**
  - `backend/tools/calendar_tools.py`

### System: Calendar Memory Mirror
- **Beschreibung:** Nicht-autoritatives Spiegel-System für kommende Kalendertermine im Memory-Kontext. Erzeugt Snapshot v1 (`derived` + `events[]`), limitiert die Prompt-Injection auf relevante Kalender-/Planungsfragen und hält proaktive Hinweise per Flag deaktivierbar.
- **Zugehörige Dateien:**
  - `backend/services/calendar/calendar_memory.py`
  - `backend/api/routers/calendar.py`
  - `backend/services/chat_orchestrator.py`
- **Endpoint:** `POST /api/calendar/sync/memory`
- **Tests:** `backend/tests/test_calendar_memory.py`

### Feature: Terminmanagement
- **Beschreibung:** Vollständige Kalender-Funktionalität inkl. Terminsuche, Erstellung, Update und Freizeitsuche.
- **Beteiligte Systeme:** `Calendar Tools`, `Tool Executor`
- **Beteiligte Skills:**
  - `calendar.list_events` – Termine auflisten
  - `calendar.create_event` – Termin erstellen
  - `calendar.update_event` – Termin aktualisieren
  - `calendar.update_event_description` – Termin-Beschreibung anpassen
  - `calendar.delete_event` – Termin löschen
  - `calendar.find_slots` – Freie Terminslots finden
  - `calendar.find_and_update_event` – Suche + Update kombiniert
  - `calendar.find_address_and_update_event` – Adress-Suche + Event-Update

---

## Domain: Content Generation

Features zur Erzeugung von Medien und Dokumenten.

### System: Image Engine
- **Beschreibung:** Verwaltet Bildgenerierung via externer Provider (OpenAI, Gemini).
- **Zugehörige Dateien:**
  - `backend/services/image_manager.py`
  - `backend/tools/media_tools.py`

### Feature: Image Studio
- **Beschreibung:** Die für den Nutzer sichtbare Funktion "Erstelle ein Bild" via KI.
- **Beteiligte Systeme:** `LLM Gateway`, `Image Engine`
- **Beteiligte Skills:**
  - `system.generate_image` – Bild via LLM-Provider erzeugen

### Feature: Audio Generation (TTS)
- **Beschreibung:** Text-to-Speech Funktionalität zur Erzeugung von MP3-Dateien.
- **Beteiligte Systeme:** `TTS Service`
- **Beteiligte Skills:**
  - `system.save_mp3` – Text zu MP3 synthetisieren und speichern

### Feature: PDF Generation
- **Beschreibung:** Erzeugung von PDF-Dokumenten aus Markdown-Content.
- **Beteiligte Systeme:** `PDF Generator`
- **Beteiligte Skills:**
  - `system.create_pdf` – PDF aus Markdown erzeugen

---

## Domain: Finance & Commerce

Preisvergleich und Finanzdaten.

### System: Price Comparison Service
- **Beschreibung:** Führt Preisvergleiche über idealo.de/geizhals.de (DE) und amazon.com/bestbuy.com (US) durch. Unterstützt Refurbished-Vergleiche mit 20%-Ersparnis-Regel.
- **Zugehörige Dateien:**
  - `backend/tools/finance_tools.py`

### Feature: Price Lookup
- **Beschreibung:** Produktpreise inkl. Versandkosten vergleichen, mit optionaler Refurbished-Alternative.
- **Beteiligte Systeme:** `Price Comparison Service`, `Websearch Service`
- **Beteiligte Skills:**
  - `system.price_comparison` – Preisvergleich mit Total-Cost-Berechnung

---

## Domain: Web & Research

Web-Suche, Scraping und Recherche-Funktionen.

### System: Websearch Service
- **Beschreibung:** Abstrahiert Websuche über verschiedene Provider (OpenAI, Gemini, DuckDuckGo-Fallback).
- **Zugehörige Dateien:**
  - `backend/services/websearch/`

### System: Scraper Service
- **Beschreibung:** Liest und parst Webseiteninhalte für LLM-Verarbeitung.
- **Zugehörige Dateien:**
  - `backend/services/scraper_service.py`

### Feature: Web Research
- **Beschreibung:** Recherche-Funktionen für aktuelle Informationen, Wikipedia-Zusammenfassungen und Webseiten-Analyse.
- **Beteiligte Systeme:** `Websearch Service`, `Scraper Service`, `LLM Gateway`
- **Beteiligte Skills:**
  - `system.websearch` – Allgemeine Websuche
  - `system.wikipedia_summary` – Wikipedia-Artikel zusammenfassen
  - `system.scrape_website` – Webseiteninhalt scrapen
  - `system.rss_news` – Nachrichten via RSS abrufen

---

## Domain: Location & Geo

Standort-basierte Features und geografische Dienste.

### System: Geo Service
- **Beschreibung:** Berechnet Routen, findet lokale Geschäfte und liefert Länderinformationen.
- **Zugehörige Dateien:**
  - `backend/tools/geo_service.py`

### Feature: Routing & Navigation
- **Beschreibung:** Streckenberechnung mit Distanz, Fahrzeit und Google-Maps-Links.
- **Beteiligte Systeme:** `Geo Service`
- **Beteiligte Skills:**
  - `system.routing` – Strecke + Fahrzeit berechnen

### Feature: Local Business Search
- **Beschreibung:** Findet lokale Geschäfte und extrahiert visuelle/ergänzende Informationen.
- **Beteiligte Systeme:** `Geo Service`, `Websearch Service`
- **Beteiligte Skills:**
  - `system.local_business` – Lokale Geschäfte finden

### Feature: Country Information
- **Beschreibung:** Liefert Basisinformationen zu Ländern (Hauptstadt, Währung, etc.).
- **Beteiligte Systeme:** `Geo Service`
- **Beteiligte Skills:**
  - `system.country_info` – Länderbasisinfos abrufen

### Feature: Weather Lookup
- **Beschreibung:** Wetterdaten zu Ort und Zeitraum abrufen.
- **Beteiligte Systeme:** `Weather Service`
- **Beteiligte Skills:**
  - `system.weather` – Wetterdaten abrufen

---

## Domain: File Operations

Dateisystem-Zugriffe und Workspace-Management.

### System: Filesystem Manager
- **Beschreibung:** Verwaltet Dateioperationen innerhalb definierter Workspaces mit Security-Checks.
- **Zugehörige Dateien:**
  - `backend/services/filesystem_manager.py`

### Feature: File Management
- **Beschreibung:** CRUD-Operationen für Dateien und Verzeichnisse im erlaubten Workspace.
- **Beteiligte Systeme:** `Filesystem Manager`, `Tool Executor`
- **Beteiligte Skills:**
  - `filesystem.create_file` – Datei erstellen
  - `filesystem.read_file` – Datei lesen
  - `filesystem.delete_file` – Datei löschen
  - `filesystem.move_file` – Datei verschieben
  - `filesystem.rename_file` – Datei umbenennen
  - `filesystem.move_files` – Batch-Datei-Verschiebung
  - `filesystem.list_directory` – Verzeichnisinhalt listen
  - `filesystem.create_directory` – Verzeichnis erstellen
  - `filesystem.delete_directory` – Verzeichnis löschen
  - `filesystem.list_workspaces` – Erlaubte Workspaces auflisten

---

## Domain: Security & Policy

Berechtigungen, Consent-Management und Sicherheitsfeatures.

### System: Policy Engine
- **Beschreibung:** Zentrale Berechtigungsverwaltung und Consent-Tracking für sicherheitskritische Operationen.
- **Zugehörige Dateien:**
  - `backend/services/policy_engine.py`
  - `backend/services/permission_service.py`

### System: Tool Argument Sanitizer
- **Beschreibung:** Bereinigt und validiert Tool-Argumente vor der Ausführung (Security-Layer).
- **Zugehörige Dateien:**
  - `backend/services/tool_argument_sanitizer.py`

### Feature: Permission Management
- **Beschreibung:** Vergabe und Entzug von Berechtigungen für sicherheitskritische Skills.
- **Beteiligte Systeme:** `Policy Engine`, `Permission Service`
- **Beteiligte Skills:**
  - `system.grant_permission` – Berechtigung erteilen (Meta-Skill)
  - `system.revoke_permission` – Berechtigung entziehen (Meta-Skill)

---

## Domain: Quality & Monitoring

Qualitätskontrolle und Monitoring-Systeme.

### System: Quality Gate
- **Beschreibung:** Validiert Responses auf Qualität und Vollständigkeit vor der Auslieferung.
- **Zugehörige Dateien:**
  - `backend/services/quality_gate.py`

### System: Cost Calculator
- **Beschreibung:** Schätzt und trackt Token-Kosten pro Anfrage.
- **Zugehörige Dateien:**
  - `backend/services/cost_calculator.py`
  - `backend/services/cost_service.py`

---

## Anhang A: Vollständige Skill-Liste (46 Skills)

| Skill ID | Legacy Name | Status | Domain | Capabilities |
|----------|-------------|--------|--------|--------------|
| **system.country_info** | get_country_info_tool | ✅ Diamond | Location & Geo | country_lookup, reference_lookup |
| **system.create_pdf** | create_pdf_from_markdown | ✅ Diamond | Content Generation | document_generation, file_write |
| **system.generate_image** | generate_image_tool | ✅ Diamond | Content Generation | image_generation, media_generation |
| **system.grant_permission** | system_grant_permission | ✅ Diamond | Security & Policy | policy_write, security_override |
| **system.local_business** | find_local_business_tool | ✅ Diamond | Location & Geo | local_search, location_lookup |
| **system.price_comparison** | price_comparison_tool | ✅ Diamond | Finance & Commerce | price_comparison, refurbished_check, realtime |
| **system.revoke_permission** | system_revoke_permission | ✅ Diamond | Security & Policy | policy_write, security_override |
| **system.routing** | get_distance_and_route_tool | ✅ Diamond | Location & Geo | routing, location_lookup |
| **system.rss_news** | get_latest_news_rss | ✅ Diamond | Web & Research | news_fetch, web_read |
| **system.save_mp3** | save_mp3_tool | ✅ Diamond | Content Generation | audio_generation, file_write |
| **system.scrape_website** | scrape_website | ✅ Diamond | Web & Research | web_scrape, web_read |
| **system.weather** | get_weather_from_api_tool | ✅ Diamond | Location & Geo | weather_lookup, api_read |
| **system.websearch** | perform_websearch | ✅ Diamond | Web & Research | web_search, research, id_anchor_rendering, pricing_protocol_v2 |
| **system.wikipedia_summary** | get_wikipedia_summary | ✅ Diamond | Web & Research | reference_lookup, web_read |
| calendar.create_event | create_calendar_event | 🔍 Audit | Calendar & Scheduling | calendar_write, schedule_mutation |
| calendar.delete_event | delete_calendar_event | 🔍 Audit | Calendar & Scheduling | calendar_write, schedule_mutation |
| calendar.find_address_and_update_event | find_address_and_update_calendar_event | 🔍 Audit | Calendar & Scheduling | calendar_write, schedule_mutation |
| calendar.find_and_update_event | find_and_update_calendar_event | 🔍 Audit | Calendar & Scheduling | calendar_write, schedule_mutation |
| calendar.find_slots | find_free_time_slots | 🔍 Audit | Calendar & Scheduling | calendar_read, availability_lookup |
| calendar.list_events | get_calendar_events | 🔍 Audit | Calendar & Scheduling | calendar_read, schedule_lookup |
| calendar.update_event | update_calendar_event | 🔍 Audit | Calendar & Scheduling | calendar_write, schedule_mutation |
| calendar.update_event_description | update_calendar_event_description | 🔍 Audit | Calendar & Scheduling | calendar_write, schedule_mutation |
| communication.find_contact_and_email | find_contact_and_send_email_wrapper | 🔍 Audit | Communication | mail_write, contact_lookup |
| communication.list_emails | get_latest_emails | 🔍 Audit | Communication | mail_read, inbox_lookup |
| communication.read_email | read_email | 🔍 Audit | Communication | mail_read, inbox_lookup |
| communication.send_email | send_email | 🔍 Audit | Communication | mail_write, external_send |
| contacts.create_or_update | create_or_update_contact_tool | 🔍 Audit | Communication | contact_write, addressbook_mutation |
| contacts.delete | delete_contact_by_id_wrapper | 🔍 Audit | Communication | contact_write, addressbook_mutation |
| contacts.list | list_contacts_wrapper | 🔍 Audit | Communication | contact_read, addressbook_lookup |
| filesystem.create_directory | create_directory | 🔍 Audit | File Operations | directory_create, workspace_mutation |
| filesystem.create_file | create_file | 🔍 Audit | File Operations | file_write, workspace_mutation |
| filesystem.delete_directory | delete_directory | 🔍 Audit | File Operations | directory_delete, workspace_mutation |
| filesystem.delete_file | delete_file | 🔍 Audit | File Operations | file_delete, workspace_mutation |
| filesystem.list_directory | list_directory | 🔍 Audit | File Operations | file_read, workspace_discovery |
| filesystem.list_workspaces | list_allowed_workspaces | 🔍 Audit | File Operations | workspace_discovery, policy_scope_read |
| filesystem.move_file | move_file | 🔍 Audit | File Operations | file_move, workspace_mutation |
| filesystem.move_files | move_files | 🔍 Audit | File Operations | file_move, bulk_operation |
| filesystem.read_file | read_file | 🔍 Audit | File Operations | file_read, workspace_inspection |
| filesystem.rename_file | rename_file | 🔍 Audit | File Operations | file_rename, workspace_mutation |
| knowledge.edit_pdf | edit_pdf_text_in_place | 🔍 Audit | Knowledge Management | document_edit, correction_batch |
| knowledge.hardened_edit | hardened_edit_pdf | 🔍 Audit | Knowledge Management | document_edit, hardened |
| knowledge.list_documents | list_knowledge_documents | 🔴 Broken | Knowledge Management | document_inventory, knowledge_discovery |
| knowledge.open_document | open_knowledge_document | 🔍 Audit | Knowledge Management | document_navigation, ui_open |
| knowledge.query | query_knowledge_base | 🔍 Audit | Knowledge Management | document_analysis, semantic_search, fact_lookup |
| knowledge.read_full_text | get_full_document_text | 🔍 Audit | Knowledge Management | document_read, fulltext_extraction |
| memory.save_core_fact | save_core_memory_fact | 🔍 Audit | Memory & Context | memory_write, fact_persistence |
| memory.search_summaries | search_past_conversation_summaries_tool | 🔍 Audit | Memory & Context | memory_read, history_lookup |

---

## Anhang B: Status-Legende

| Status | Bedeutung |
|--------|-----------|
| ✅ **Diamond** | Vollständig gehärtet: Striktes Pydantic-Schema, SkillResponse-Contract, Deterministic Renderer (wo anwendbar), E2E-Validiert |
| 🔍 **Audit** | Funktional, aber nicht auf Diamond-Standard gehoben |
| 🔴 **Broken** | Bekannte Probleme, erfordert Fix |

---

## Anhang C: Domain-Übersicht

| Domain | Anzahl Skills | Anzahl Diamond | Kernsysteme |
|--------|---------------|----------------|-------------|
| Core Architecture | – | – | LLM Gateway, Prompting Engine, Chat Orchestrator, Agent Planner, Tool Executor, Vision Pipeline |
| Knowledge Management | 6 | 0 🔍 5, 🔴 1 | RAG Manager, Knowledge Composite |
| Memory & Context | 2 | 0 🔍 2 | Memory Manager, Vector Service |
| Communication | 7 | 0 🔍 7 | Contact Manager |
| Calendar & Scheduling | 8 | 0 🔍 8 | Calendar Tools |
| Content Generation | 3 | 3 ✅ | Image Engine, TTS Service, PDF Generator |
| Web & Research | 4 | 4 ✅ | Websearch Service, Scraper Service |
| Location & Geo | 4 | 4 ✅ | Geo Service, Weather Service |
| File Operations | 10 | 0 🔍 10 | Filesystem Manager |
| Security & Policy | 2 | 2 ✅ | Policy Engine, Permission Service |
| Quality & Monitoring | – | – | Quality Gate, Cost Calculator |

---

*Dokument generiert nach Domain-Struktur – Code-verifiziert gegen backend/skills/ und backend/services/*
