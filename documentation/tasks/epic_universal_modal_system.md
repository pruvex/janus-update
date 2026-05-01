# Epic: Universal Modal System (Task 029-034, 058)

**Status:** TODO (Geplant)  
**Dossier:** `UNIVERSAL_MODAL_SYSTEM_DIAMOND_DOSSIER.md`  
**Epic-Lead:** G17 (Doku/Struktur)  
**Architektur-Prinzip:** Stateless MCL (Modal Contract Layer)

---

## Zusammenfassung

Das **Universal Modal System** vereint 4 Legacy-Patterns zu einem zustandslosen Modal Contract Layer (MCL). Es ermöglicht Backend-gesteuerte Modals (`modal_request`) für Vision, Video und Interaktion, während das Frontend eine einheitliche, stateless Facade für Window-Management bereitstellt.

---

## Stateless MCL-Architekturregel

> **Core Principle:** Der MCL ist **zustandslos**. Weder Frontend noch Backend speichern Modal-Zustände persistierend. Jeder Modal-Request ist eine atomare Operation mit explizitem Contract (`type`, `payload`, `lifecycle`). Backend kann Modals remote öffnen/schließen ohne Frontend-Interaktion.

---

## Tasks (029 bis 034, 058)

## Diamond Task-Checkliste (Orchestrator UI)

- [x] 1. `task_029_mcl_core.md` (MCL Core — modal-api, window-state, Z-Stack) ✅ **DONE → ARCHIV**
- [ ] 2. `task_030_mcl_image_viewer.md` (Image-Viewer auf MCL migrieren) 🔴 **NÄCHSTER BLOCKER**
- [x] 3. `task_031_mcl_image_studio.md` (Image Studio → FloatingWindow / MCL) ✅ **DONE**
- [x] 4. `task_032_mcl_knowledge_center.md` (Knowledge Center Single Source of Truth) 🟡 **IN PROGRESS**
- [x] 5. `task_033_mcl_video_player.md`
- [x] 6. `task_034_mcl_gallery.md`
- [ ] 7. `task_058_calendar_modal_diamond_plan.md` (Janus Kalender — Agenda/Week/Day Views; siehe auch Kurzname `task_058_calendar_modal.md`)

### Task 029: MCL-Core Contract Definition
| Feld | Wert |
|------|------|
| **Ziel** | Definition der `modal_request` API-Spezifikation und Core-Contracts |
| **Phase** | M1 (Foundation) |
| **Dateien** | `backend/api/modals.py`, `frontend/js/modal-contract.js` |
| **Key Deliverables** | REST-Endpoint `/api/modal/request`, JSON-Schema für Modal-Types (image, video, confirm, input) |

### Task 030: Image-Viewer auf MCL migrieren
| Feld | Wert |
|------|------|
| **Ziel** | Legacy Image-Viewer ersetzen durch MCL-konforme Implementierung |
| **Phase** | M1 (Foundation) |
| **Dateien** | `frontend/js/modals/image-modal.js`, `frontend/css/modals.css` |
| **Key Deliverables** | Einheitliche Bild-Anzeige via MCL, Zoom/Pan Gesten, Keyboard-Navigation |

### Task 031: Image Studio auf FloatingWindow migrieren
| Feld | Wert |
|------|------|
| **Ziel** | Image Studio von Full-Screen auf MCL-FloatingWindow umstellen |
| **Phase** | M2 (Migration) |
| **Dateien** | `frontend/js/image-studio.js`, `frontend/css/image-studio.css` |
| **Key Deliverables** | Resizable/Draggable FloatingWindow, Multi-Image Support, Preset-Management |

### Task 032: Knowledge Center Single-Source-of-Truth
| Feld | Wert |
|------|------|
| **Ziel** | Knowledge Center als zentraler Wissens-Modal mit einheitlicher API |
| **Phase** | M3 (Integration) |
| **Dateien** | `frontend/js/knowledge-center.js`, `backend/services/knowledge_service.py` |
| **Key Deliverables** | Unified Search, Kategorie-Filter, Quick-Actions, Backend-Push für neue Einträge |

### Task 033: Video-Player + Backend `modal_request`
| Feld | Wert |
|------|------|
| **Ziel** | Video-Player als MCL-Modal mit Backend-Initiierung |
| **Phase** | M4 (Backend Control) |
| **Dateien** | `frontend/js/modals/video-modal.js`, `backend/api/modals.py` |
| **Key Deliverables** | Backend kann Video-Modals remote öffnen (`modal_request`), Streaming-Integration, Controls |

### Task 034: Gallery Migration + Polish
| Feld | Wert |
|------|------|
| **Ziel** | Bildergalerie auf MCL migrieren + Final-Polish |
| **Phase** | M5 (Completion) |
| **Dateien** | `frontend/js/gallery.js`, `frontend/js/modals/gallery-modal.js` |
| **Key Deliverables** | Gallery als MCL-Carousel, Thumbnail-Navigation, Bulk-Actions, Performance-Optimierung |

### Task 058: Janus Calendar Modal (MCL + Dock)
| Feld | Wert |
|------|------|
| **Ziel** | Janus Kalender als MCL-Dock-Modul: zentrale UI über Google Calendar (Agenda/Week/Day), REST-Service-Layer, AI-Planung mit User-Bestätigung |
| **Phase** | M6 (Calendar / Scheduling Intelligence) |
| **Dateien** | `documentation/tasks/task_058_calendar_modal_diamond_plan.md`, `frontend/js/calendar-modal.js`, `frontend/js/modal-api.js` (Renderer `calendar`), `frontend/js/window-state.js` (Dock-Modul `calendar`), `backend/api/routers/calendar.py` (geplant), `backend/services/calendar/` (geplant) |
| **Key Deliverables** | Sidebar + optional Dock-Einstieg, `openModal({ type: "calendar" })` / `window.dockOpen("calendar")`, leeres bis MVP-gefülltes `#calendar-modal`, keine Duplikation der Logik aus `backend/tools/calendar_tools.py` (Wrap statt Fork) |

---

## Meilensteine

| Meilenstein | Tasks | Ziel |
|-------------|-------|------|
| **M1** | 029, 030 | MCL-Core + Image-Viewer Migration |
| **M2** | 031 | Image Studio auf FloatingWindow |
| **M3** | 032 | Knowledge Center Single-Source-of-Truth |
| **M4** | 033 | Video-Player + Backend `modal_request` |
| **M5** | 034 | Gallery Migration + Polish |
| **M6** | 058 | Janus Calendar Modal (MCL, API, AI-Steuerung) |

---

## Betroffene Legacy-Patterns (4→1 Vereinigung)

| Legacy Pattern | MCL-Replacement |
|---------------|-----------------|
| Full-Screen Image Studio | FloatingWindow Modal |
| Inline Video Player | MCL Video-Modal |
| Sidebar Knowledge Panel | MCL Knowledge-Modal |
| Static Gallery Grid | MCL Carousel Modal |

---

## Abhängigkeiten

- **Task 021–028 COMPLETE** (Janus AI OS UX-Linie) — MCL baut auf Window-State-System auf
- **ORCH-TRANSFORM-EPIC DONE** — Backend-Services strukturiert für `modal_request`
- **Memory V2 DONE** — Für Knowledge Center Integration

---

## Success Criteria

1. Alle 4 Legacy-Patterns durch MCL ersetzt
2. Backend kann alle Modals via `modal_request` steuern
3. Keine persistenten Modal-Zustände im Frontend
4. Einheitliche UX über alle Modal-Types
5. 100% TypeScript/JavaScript Contract Compliance

---

*Letzte Aktualisierung: 2026-05-01*  
*Epic erstellt durch: G17 (Doku/Struktur)*
