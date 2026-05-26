# Janus Skill Inventory

**Erstellt:** 2026-04-13  
**Aktualisiert:** 2026-04-22 — Diamond-Standard RAG V2 + knowledge.code_search registriert
**Quelle:** Backend Tool-Registry & Skill-Katalog (`backend/skills/`)

---

## Übersicht nach Kategorien

### 1. Web & Information (6 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tool_registry.py` | `system.websearch` | Web | [x] Diamond Certified |
| `tools/rss_service.py` | `system.rss_news` | Web | [x] Diamond Certified |
| `services/scraper_service.py` | `system.scrape_website` | Web | [x] Diamond Certified |
| `tools/weather_service.py` | `system.weather` | Web/API | [x] Diamond Certified |
| `tools/wiki_service.py` | `system.wikipedia_summary` | Web | [x] Diamond Certified |
| `tools/finance_tools.py` | `system.price_comparison` | Web | [x] Diamond Certified |

### 2. Geo & Routing (3 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/geo_service.py` | `system.routing` | Geo | [x] Diamond Certified |
| `tools/geo_service.py` | `system.local_business` | Geo | [x] Diamond Certified |
| `tools/geo_service.py` | `system.country_info` | Geo | [x] Diamond Certified |

### 3. Media & Dokumente (4 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/pdf_generator.py` | `system.create_pdf` | Media | [x] Diamond Certified |
| `tools/media_tools.py` | `system.save_mp3` | Media | [x] Diamond Certified |
| `tools/media_tools.py` | `system.generate_image` | Media | [x] Diamond Certified |
| `tools/pdf_editor.py` | `knowledge.edit_pdf` | Document | [x] Diamond Certified |

### 4. Filesystem (10 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `services/filesystem_manager.py` | `filesystem.create_file` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.read_file` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.delete_file` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.list_directory` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.list_workspaces` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.create_directory` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.delete_directory` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.rename_file` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.move_file` | File-IO | [x] Diamond Certified |
| `services/filesystem_manager.py` | `filesystem.move_files` | File-IO | [x] Diamond Certified |

### 5. Kalender (8 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/calendar_tools.py` | `calendar.list_events` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.create_event` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.delete_event` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.update_event` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.find_slots` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.update_event_description` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.find_and_update_event` | Calendar | [x] Diamond Certified |
| `tools/calendar_tools.py` | `calendar.find_address_and_update_event` | Calendar | [x] Diamond Certified |

### 6. Kommunikation & Email (4 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/gmail_tools.py` | `communication.list_emails` | Communication | [x] Diamond Certified |
| `tools/gmail_tools.py` | `communication.read_email` | Communication | [x] Diamond Certified |
| `tools/gmail_tools.py` | `communication.send_email` | Communication | [x] Diamond Certified |
| `tool_registry.py` | `communication.find_contact_and_email` | Communication | [x] Diamond Certified |

### 7. Kontakte (3 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/db_wrappers.py` | `contacts.create_or_update` | Contacts | [x] Diamond Certified |
| `tools/db_wrappers.py` | `contacts.list` | Contacts | [x] Diamond Certified |
| `tools/db_wrappers.py` | `contacts.delete` | Contacts | [x] Diamond Certified |

### 8. Wissensbasis & Dokumente (7 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `services/rag_manager.py` | `knowledge.query` | Knowledge | [x] Diamond Certified |
| `services/rag/api_adapter.py` | `knowledge.code_search` | Knowledge | [x] Diamond Certified — RAG V2 Code-Aware Search |
| `services/tool_executor.py` | `knowledge.open_document` | Knowledge | [x] Diamond Certified |
| `services/tool_executor.py` | `knowledge.read_full_text` | Knowledge | [x] Diamond Certified |
| `services/tool_executor.py` | `knowledge.list_documents` | Knowledge | [x] Diamond Certified |
| `services/knowledge_composite.py` | `knowledge.hardened_edit` | Knowledge | [x] Diamond Certified |
| `tools/pdf_editor.py` | `knowledge.edit_pdf` | Knowledge | [x] Diamond Certified |

### 9. Memory (4 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/memory_tools.py` | `memory.write` | Memory | [x] Diamond Certified |
| `tools/memory_tools.py` | `memory.read` | Memory | [x] Diamond Certified |
| `tools/memory_tools.py` | `memory.update` | Memory | [x] Diamond Certified |
| `tools/memory_tools.py` | `memory.history` | Memory | [x] Diamond Certified |

### 10. Video & Media (2 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tools/video_tools.py` | `video.search` | Video | [x] Diamond Certified |
| `tools/video_understanding.py` | `video.understand` | Video | [x] Diamond Certified |

### 11. System & Permissions (2 Skills)

| Modul / Datei | Skill Name | Kategorie | Status |
|---------------|------------|-----------|--------|
| `tool_registry.py` | `system.grant_permission` | System | [x] Diamond Certified |
| `tool_registry.py` | `system.revoke_permission` | System | [x] Diamond Certified |

---

## Vollständige Liste (Alphabetisch)

| # | Skill Name | Modul | Kategorie |
|---|------------|-------|-----------|
| 1 | `calendar.create_event` | `calendar_tools.py` | Calendar |
| 2 | `calendar.delete_event` | `calendar_tools.py` | Calendar |
| 3 | `calendar.find_address_and_update_event` | `calendar_tools.py` | Calendar |
| 4 | `calendar.find_and_update_event` | `calendar_tools.py` | Calendar |
| 5 | `calendar.find_slots` | `calendar_tools.py` | Calendar |
| 6 | `calendar.list_events` | `calendar_tools.py` | Calendar |
| 7 | `calendar.update_event` | `calendar_tools.py` | Calendar |
| 8 | `calendar.update_event_description` | `calendar_tools.py` | Calendar |
| 9 | `communication.find_contact_and_email` | `tool_registry.py` | Communication |
| 10 | `communication.list_emails` | `gmail_tools.py` | Communication |
| 11 | `communication.read_email` | `gmail_tools.py` | Communication |
| 12 | `communication.send_email` | `gmail_tools.py` | Communication |
| 13 | `contacts.create_or_update` | `db_wrappers.py` | Contacts |
| 14 | `contacts.delete` | `db_wrappers.py` | Contacts |
| 15 | `contacts.list` | `db_wrappers.py` | Contacts |
| 16 | `filesystem.create_directory` | `filesystem_manager.py` | File-IO |
| 17 | `filesystem.create_file` | `filesystem_manager.py` | File-IO |
| 18 | `filesystem.delete_directory` | `filesystem_manager.py` | File-IO |
| 19 | `filesystem.delete_file` | `filesystem_manager.py` | File-IO |
| 20 | `filesystem.list_directory` | `filesystem_manager.py` | File-IO |
| 21 | `filesystem.list_workspaces` | `filesystem_manager.py` | File-IO |
| 22 | `filesystem.move_file` | `filesystem_manager.py` | File-IO |
| 23 | `filesystem.move_files` | `filesystem_manager.py` | File-IO |
| 24 | `filesystem.read_file` | `filesystem_manager.py` | File-IO |
| 25 | `filesystem.rename_file` | `filesystem_manager.py` | File-IO |
| 26 | `knowledge.code_search` | `rag/api_adapter.py` | Knowledge |
| 27 | `knowledge.edit_pdf` | `pdf_editor.py` | Knowledge |
| 28 | `knowledge.hardened_edit` | `knowledge_composite.py` | Knowledge |
| 29 | `knowledge.list_documents` | `tool_executor.py` | Knowledge |
| 30 | `knowledge.open_document` | `tool_executor.py` | Knowledge |
| 31 | `knowledge.query` | `rag_manager.py` | Knowledge |
| 32 | `knowledge.read_full_text` | `tool_executor.py` | Knowledge |
| 33 | `memory.history` | `memory_tools.py` | Memory |
| 34 | `memory.read` | `memory_tools.py` | Memory |
| 35 | `memory.update` | `memory_tools.py` | Memory |
| 36 | `memory.write` | `memory_tools.py` | Memory |
| 37 | `system.country_info` | `geo_service.py` | Geo |
| 38 | `system.create_pdf` | `pdf_generator.py` | Media |
| 39 | `system.generate_image` | `media_tools.py` | Media |
| 40 | `system.grant_permission` | `tool_registry.py` | System |
| 41 | `system.local_business` | `geo_service.py` | Geo |
| 42 | `system.price_comparison` | `finance_tools.py` | Web |
| 43 | `system.revoke_permission` | `tool_registry.py` | System |
| 44 | `system.routing` | `geo_service.py` | Geo |
| 45 | `system.rss_news` | `rss_service.py` | Web |
| 46 | `system.save_mp3` | `media_tools.py` | Media |
| 47 | `system.scrape_website` | `scraper_service.py` | Web |
| 48 | `system.weather` | `weather_service.py` | Web/API |
| 49 | `system.websearch` | `tool_registry.py` | Web |
| 50 | `system.wikipedia_summary` | `wiki_service.py` | Web |
| 51 | `video.search` | `video_tools.py` | Video |
| 52 | `video.understand` | `video_understanding.py` | Video |

---

## Zusammenfassung

| Kategorie | Anzahl |
|-----------|--------|
| Web & Information | 6 |
| Geo & Routing | 3 |
| Media & Dokumente | 4 |
| Video & Media | 2 |
| Filesystem | 10 |
| Kalender | 8 |
| Kommunikation & Email | 4 |
| Kontakte | 3 |
| Wissensbasis & Dokumente | 7 |
| Memory | 4 |
| System & Permissions | 2 |
| **GESAMT** | **52 Skills** |

---

## Quelldateien

### Tool-Module (`backend/tools/`)
- `calendar_tools.py` - 8 Calendar-Funktionen
- `contact_tools.py` / `contacts_tools.py` - Kontakt-Hilfsfunktionen
- `db_wrappers.py` - DB-Wrapper für Kontakte
- `finance_tools.py` - Preisvergleich
- `geo_service.py` - Routing, Local-Business, Country-Info
- `gmail_tools.py` - Email-Funktionen
- `media_tools.py` - Bildgenerierung, MP3-Speicherung
- `memory_tools.py` - Memory V2.1 Gold Standard (4 Tools)
- `pdf_editor.py` - PDF-Text-Editing
- `pdf_generator.py` - PDF-Erzeugung
- `rss_service.py` - RSS-News
- `video_tools.py` - YouTube Video-Suche
- `video_understanding.py` - Video-Understanding (Transkript-Analyse)
- `weather_service.py` - Wetter-API
- `wiki_service.py` - Wikipedia-Zusammenfassungen

### Service-Module mit Tools
- `services/filesystem_manager.py` - 10 Filesystem-Operationen
- `services/rag_manager.py` - Knowledge-Query
- `services/scraper_service.py` - Website-Scraping
- `services/tool_executor.py` - Knowledge-Dokument-Operationen
- `services/knowledge_composite.py` - Hardened PDF-Edit
- `services/video/transcript_service.py` - YouTube Transcript-Service für Video-Understanding

### Registry
- `tool_registry.py` - Zentrale Registrierung aller 52 Skills

### Skill-Katalog (`backend/skills/`)
JSON-Definitionen für alle Skills nach Namespace organisiert:
- `calendar/` - 8 Skills
- `communication/` - 4 Skills
- `contacts/` - 3 Skills
- `filesystem/` - 10 Skills
- `knowledge/` - 7 Skills (inkl. `knowledge.code_search` — RAG V2 Diamond-Standard)
- `system/` - 18 Skills
- `video/` - 2 Skills (video.search, video.understand)
