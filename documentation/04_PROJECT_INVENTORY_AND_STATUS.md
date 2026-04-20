# Janus Project Inventory & Kanban Board (V1.0)
*Status-Zentrale für Janus 2.0 (Workflow-Kanban / Session-Start).*

## 🛠 1. BACKLOG (Ideen-Pool)
- [ ] **Feature:** PDF-Drop & Fact-Check Architektur.
- [ ] **Feature:** Vektor-DB Langzeit-Memory Integration.
- [ ] **UI:** Chat-Eingabe-Fenster Design-Update.
- [ ] **Refactor:** Globales Skill-Refinement (Ebene 1-8).

## 📅 2. PLANNED (Nächste Ziele)
- [ ] **Audit:** Vollständige technische Inventur (Phase 2.2 Abschluss).
- [ ] **Bug:** Bilderstellung Fix (Analyse & Stabilisierung).
- [ ] **Skill:** Websearch Diamond-Stability (V2.1 Fix).

## 🚀 3. IN PROGRESS
- [ ] **Migration:** Initialisierung des Diamond-OS (Finaler Sync).

## ✅ 4. DONE
- [x] 2026-04-19: **Task 052:** Chromium Extra Headers Fix - Aktivierung von extraHeaders Flag in onBeforeSendHeaders und onHeadersReceived zur Aufhebung der Chromium-Blockade von Referer-Manipulationen. Behebung von YouTube Error 15-4 / 153. Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-19: **Task 050:** CSP Bypass & iFrame Hardening - Header-Deletion-Pattern (radikales Entfernen von CSP-Headern), allowRunningInsecureContent, Permission Handlers (media/display-capture), Autoplay CSP Modification. Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-19: **Task 049:** YouTube Final Master Fix - YouTube-Nocookie Transition, Header-Stripping (X-Frame-Options), Cross-Domain Spoofing (googlevideo.com), PreloadMediaEngagementData Disabling. Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-19: **Task 048:** YouTube Origin & Orchestrator-Bypass Fix - YouTube Fehler 153 via Referer/Origin Header-Spoofing, Synthese-Bypass via Hard-Lock return. Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-19: **Task 047:** Beta-Ready Final Polish - Feedback-Plug-and-Play (Webhook Fallback), Video-Stability-Fix (is_final_response=True), Tiktoken-Resilience. Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-19: **Task 046:** Security Audit & Beta-Reporting System - XSS Shield (DOMPurify), RCE Prevention (IPC), JWT Vault Security, Chained Vulnerability Fix, Beta-Reporting (Discord Webhook). Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-18: **Task VID-UNDERSTAND-001:** Video Understanding V1 Epic - Lokaler Whisper-STT Fallback, Dediziertes Transkript-Modal, 100% FinOps-Transparenz, Automatische Memory V2 Injektion. Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-18: **Task FE_TRANSCRIPT_MODAL_UI_ENHANCEMENT:** Transkript-Modal UI Enhancement - Dock-Panel Design, Buttons, Drag/Resize, Taskbar-Integration. Status: 🥇 DONE.
- [x] 2026-04-16: **Task 033 MCL Video Player:** GPT-4 Purge (MOA-Hierarchy, Benchmark, Tests), Stream-Switch Pattern (UI-Karten deaktiviert, Markdown-Links als einzige Quelle), Window-Level Capture Interceptor (ultimativer Regressionsschutz gegen DOM-Changes). Status: 🥇 SEALED & COMPLETE.
- [x] 2026-04-14: **Task 033 Post-Impl Hardening:** MCL Video-Player Ende-zu-Ende stabilisiert (`modal_request` deterministic + persisted), Reopen-Link bleibt bei Stream/Chat-Wechsel/Reload verfuegbar, `openModal` fuer `video-player` idempotent, Video- und Wissensdatenbank-Modal wieder exakt an Top-Left von `chat-window-B`.
- [x] 2026-04-12: **Turbo-Flow EPIC — Task B5 (Phase 1):** Gateway-Singletons (`llm_gateway.py`) + Tool-Definitions-Cache (`tool_manager.py`, frozenset-Key). Siehe `documentation/tasks/task_019_turbo_flow_epic.md` §6 (B5 /post-impl). Vollständiger Tool-Response-API-Cache (Phase 3) ausstehend.
- [x] 2026-03-28: Diamond-OS Verfassung & Regeln (V1.6).
- [x] 2026-03-28: Automatisierungs-Skripte & Templates installiert.
- [x] 2026-03-28: Deep-Dive Audit - 5 Core Skills (websearch, price_comparison, generate_image, wikipedia_summary, weather).
- [x] 2026-04-07: Pruki Memory QA Framework Foundation (schemas_qa.py, memory_qa.py, fixtures).
- [x] 2026-04-07: Memory QA Scenarios Expansion (18 Tests, vollständige V2 Abdeckung).
- [x] 2026-04-07: Memory QA Dashboard & Skill (/test-memory, ASCII-Dashboard, Diamond-Score).
- [x] 2026-04-09: Temporal-Recall & Episodic Memory (M-MEM-V2-FINAL) — Zeitstempel, Chat-Origin, Identity-Anchor, System Clock. 🚀💎

