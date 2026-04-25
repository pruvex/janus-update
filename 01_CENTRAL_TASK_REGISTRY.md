# Janus Central Task Registry

**Stand:** 2026-04-14  
**Zweck:** Einziges "Morgen-Radar" + **Macro-Dashboard** (V2.9 — Cache-Aware Guard). Siehe `documentation/00_AI_STUDIO_BOOTSTRAP.md`.

---

## Janus AI OS — UX-Revolution (Epic-Linie Task 021–028)

**Projektstatus: COMPLETE** (Geschlossen 2026-04-13 — für die Geschichtsbücher verzeichnet.)

| Task-ID | Thema | Status |
|---------|-------|--------|
| **021** | Smart Chat Naming | **DONE** |
| **022** | Dual-Window Core | **DONE** |
| **023** | Window Binding | **DONE** |
| **024** | Window LLM Selectors | **DONE** |
| **025** | Navigation Sync / Active State | **DONE** |
| **026** | Chat Actions (Assign A/B, Feedback) | **DONE** |
| **027** | Smart Grouping (Backend / Kategorie) | **DONE** |
| **028** | Janus Dock System | **DONE** |

**Referenzen:** `documentation/tasks/task_021_smart_chat_naming_epic.md` … `task_028_janus_dock_system.md` · Lektionen: `WHAT_I_LEARNED.md` (Layer Model, Iconographie, Dock-Patterns).

---

## Resource-Status Dashboard (V2.9)

**Quota-Stand vor jeder Task-Zuweisung prüfen:**

| Ressource | Limit | Aktuell | Status |
|-----------|-------|---------|--------|
| **Cursor Fast-Requests** | 50/Monat | [__]/50 | ⬜ OK / 🟡 Warn (45+) / 🔴 Critical (50) |
| **Windsurf Daily %** | Unlimitiert | [__]% | ⬜ Verfügbar / 🟡 Hoch (90%+) |
| **Gemini Pro (AI Studio)** | ~50/Tag | [__]/50 | ⬜ OK / 🟡 Low (<5) |

**Wenn Critical → DEFERRED Pool verwenden**

---

## Macro-Dashboard (Copy/Paste — V2.9)

*Vollständige **Master-Prompts** mit NEXT ACTION LOOP kommen aus dem **AI Studio** (Flash-Triage).*

**Aktive Übersicht:** keine offenen MCL-Zeilen mehr. Das Universal-Modal-Epic ist abgeschlossen (6/6 DONE).

| Task-ID | CU | Status | App | Modell | Prio | Cache | Tags | Meilenstein | Master-Prompt (Kurz) | Referenzen | Ergebnis |
|---------|----|--------|-----|--------|------|-------|------|-------------|---------------------|------------|----------|
| *—* | — | — | — | — | — | — | — | *Keine aktiven Tasks* | — | — | — |

**Legende (Macro):**
- **CU:** 1–10 · **Status:** TODO | IN_PROGRESS | DONE | **DEFERRED** · **Prio:** P0–P3 · **Cache:** 🧊 / 🔥

---

## ✅ Archivierte & Erledigte Epics

| Epic | Status | Zertifizierung | Referenz |
|------|--------|----------------|----------|
| **Janus Dock System** | 🏆 DONE (2026-04-13) | — | `documentation/tasks/task_028_janus_dock_system.md` |
| **Memory System V2** | ✅ DONE 🚀💎 (2026-04-08) | **DIAMOND CERTIFIED V2.1.0** | `documentation/features/epic_memory_v2.md` |
| **Diamond Task Orchestrator UI** | ✅ Completed | — | `documentation/features/epic_orchestrator_ui.md` |
| **ChatOrchestrator Transformation** | 🏆 **EPIC COMPLETE** 🥇 SEALED | **DIAMOND GOLD** | `documentation/tasks` (6 Module unter `backend/services/orchestrator/`) |
| **Turbo-Flow — Streaming & Caching (B5)** | 🟡 **B5 Phase-1 hot-path DONE** (2026-04-12) | SSE + Gateway-Cache | `documentation/tasks/task_019_turbo_flow_epic.md` |
| **Memory Core Refactor** | ✅ DONE (2026-04-12) | **Opus Sign-off** | `documentation/tasks/task_020_memory_core_refactor_epic.md` |
| **Smart Chat Naming** | ✅ DONE (2026-04-13) | UX-Linie komplett | `documentation/tasks/task_021_smart_chat_naming_epic.md` |
| **Proactive Suggestion Engine** | 🏆 **LEGENDARY** 🥇 SEALED | **GRADE 1+** | `WHAT_I_LEARNED.md` |
| **Sidebar Overhaul & Project Dashboard** | 🥇 **DONE & SEALED** | **GRADE 1** | `WHAT_I_LEARNED.md` (V4.7.6 / V4.7.7) |
| **Universal Modal System (Task 029-034)** | 🥇 **SEALED & COMPLETE** | **DIAMOND-OS EPIC SEALED** | `documentation/architecture/JANUS_MCL_SPECIFICATION.md` |
| **MCL Video Player (Task 033)** | 🥇 **SEALED & COMPLETE** (2026-04-16) | **GPT-4 Purge + Stream-Switch + Window-Interceptor** | `documentation/tasks/task_033_mcl_video_player.md` |
| **FE Transcript Modal UI Enhancement** | ✅ **DONE** (2026-04-18) | **Dock-Panel Design, Buttons, Drag/Resize, Taskbar-Integration** | `documentation/tasks/task_FE_TRANSCRIPT_MODAL_UI_ENHANCEMENT.md` |
| **Video Understanding V1 (VID-UNDERSTAND-001)** | 🥇 **SEALED & COMPLETE** (2026-04-18) | **Whisper-STT Fallback, Transkript-Modal, FinOps-Transparenz, Memory V2 Injektion** | `documentation/tasks/task_VID-UNDERSTAND-001_video_understanding_skill.md` |
| **Stability Arc (Tasks 037-045)** | 🥇 **SEALED & COMPLETE** (2026-04-18) | **Upload-Audit, Forced Tool-Calls, Naming-Shims, Workspace-Unification** | `PROJECT_STATE.md`, `WHAT_I_LEARNED.md` |
| **BUG-ORCH-002 — Audit-Loop Forced-Tool-Args** | 🥇 **SEALED & COMPLETE** (2026-04-18) | **Pre-filled Tool Injection, Initial-Loop-State Pattern, OpenAI 400 Fix** | `documentation/tasks/task_BUG-ORCH-002_audit_loop_forced_tool_args.md` |
| **D10 — Logging Pipeline Phase 1** | 🥇 **SEALED & COMPLETE** (2026-04-25) | **Metadata Injection Pattern — Provider/Model in additional_context** | `documentation/tasks/D10_logging_pipeline_phase_1.md` |

> **Turbo-Flow (B5) Detail:** `documentation/tasks/task_019_turbo_flow_epic.md` — 🟡 B5 Phase-1 hot-path DONE; offen: D11 Prompt-Cache, Tool-Response-Store; Blocker: `OllamaCompiler` bei vollem `pytest backend/tests`.

---

## DEFERRED Pool (Warteschlange — V2.9)

*Tasks, die auf Ressourcen-Freigabe warten (Quota erschöpft oder Loop-Fail mit Eskalation)*

| Task-ID | CU | CU-Log | Ursprünglicher Editor | Grund | Seit | Prio | Entblockung |
|---------|----|--------|----------------------|-------|------|------|-------------|
| M-UI-05 | 4 | 2→4 (+2 nach Fail#2) | Cursor | Fast-Quota 50/50 | 2026-03-31 | P2 | Wartet auf Reset (1. nächsten Monat) |
| M-ARCH-08 | 8 | 6→8 (+2 nach Fail#2) | Pro | Pro-Quota <2/Tag | 2026-03-31 | P1 | Wartet auf Pro-Quota |

**DEFERRED → ACTIVE Transition:**
- Wenn Quota wieder verfügbar → Status: TODO → Editor-Zuweisung
- Wenn CU-Adjusted → Neuer Editor entsprechend V2.8 Matrix

---

## Epics in Entwicklung (Übersicht)

### Epic: Keine aktiven Epics (Ref: `documentation/architecture/JANUS_MCL_SPECIFICATION.md`)

**Status:** 🥇 **SEALED & COMPLETE**  
**Progress:** Alle MCL-Epics abgeschlossen. Das Universal Modal System ist archiviert.

---

## 🏛️ Refactoring Roadmap 2026 (Geplant)

**Referenz:** `documentation/Planned Features/Refactoring_Roadmap_2026.md`

| Target | Zeilen | CU | Prio | Pattern |
|--------|--------|----|------|---------|
| Vision Fusion Engine | ~6.500 | 8 | P1 | Service-Agnostic Dispatcher |
| Memory Core Manager | ~1.600 | 7 | P1 | Separation of Concerns |
| Geo-Intelligence Service | ~2.300 | 6 | P2 | Registry-Pattern |
| PDF Generation Engine | ~1.800 | 5 | P2 | Engine + Adapter |
| Link-Rendering Framework | ~900 | 4 | P3 | Strategy + Registry |

---

## Isolierte Bugfixes & Audits

- **Task:** `task_bug_websearch_xml` (Ref: `system.websearch`) → **Macro-Zeile M-WS-01** (CU: 3)
- **Status:** ✅ Completed
- **Priorität:** Hoch (P0)

---

## Adaptive CU Log (V2.9)

*Historie der CU-Adjustments (2× Fail → CU +2)*

| Datum | Task-ID | Von | Nach | Grund | Neuer Editor |
|-------|---------|-----|------|-------|--------------|
| — | — | — | — | — | — |

---

## Bundel-Regel & NEXT ACTION LOOP (V2.9)

**Macro-Tasking:** Lieber ein Macro-Prompt mit NEXT ACTION LOOP:
```
[IMPL → TEST → LINTER → IMPORTS → DIAMOND-REPORT]
```
als drei „Mini-Apply"-Klicks.

**Ausnahmen:**
- Schema-Lock (CU 8-10) → Pro-Blueprint
- Security (CU 9-10) → Menschliche Review
- LOOP_FAIL nach 2× → CU +2 → Eskalation

---

**Version:** 2.9 — Cache-Aware Guard | **Motto:** *„CU decides the route, quotas manage the flow, caching cuts the cost."*

---

### Verzeichnis-Hygiene (Diamond-Clean)

- Dossier-/Duplikat-MD aus dem **Repo-Root** archiviert unter **`documentation/archive/dossiers/`** (siehe dort `README.md`).
- Kanonische Projekt-Doku bleibt unter **`documentation/`** (z. B. `04_PROJECT_INVENTORY_AND_STATUS.md`).

---

## Macro-Dashboard Archiv (DONE / SEALED)

*Historische Macro-Zeilen (Status DONE / SEALED / EPIC COMPLETE). Aktive Planung: `## Macro-Dashboard (Copy/Paste — V2.9)`.*

| Task-ID | CU | Status | App | Modell | Prio | Cache | Tags | Meilenstein | Master-Prompt (Kurz) | Referenzen | Ergebnis |
|---------|----|--------|-----|--------|------|-------|------|-------------|---------------------|------------|----------|
| **FEAT-PROACTIVE-SUGGEST** | 6 | 🏆 LEGENDARY | Cursor | — | P1 | 🧊 | #Suggestion #Elite | Elite Engine | [ARCHIV] Elite Suggestion Engine — siehe Doku | WHAT_I_LEARNED.md | GRADE 1+ SEALED |
| **M-MEM-01** | 4 | DONE | Windsurf | Kimi | P0 | 🧊 | #DB #Setup | P1 Foundation | [ARCHIV] Phase 1 Alembic & Models | memory_v2.md | DONE |
| **M-MEM-02** | 5 | DONE | Windsurf | Kimi | P0 | 🧊 | #RAM #Performance | P2 Cache & TTL | [ARCHIV] RAMCache & cleanup job | memory_v2.md | DONE |
| **M-MEM-03** | 6 | DONE | Windsurf | Kimi | P0 | 🧊 | #Logic #Resilience | P3 Enricher | [ARCHIV] Priority guard & circuit breaker | memory_v2.md | DONE |
| **M-MEM-04** | 5 | DONE | Windsurf | Kimi | P0 | 🧊 | #Context | P4 Knapsack | [ARCHIV] build_final_context_v2 | memory_v2.md | DONE |
| **M-MEM-05** | 6 | DONE | Windsurf | Kimi | P0 | 🧊 | #Tools #API | P5 Unified tools | [ARCHIV] memory tool JSONs | memory_v2.md | DONE |
| **M-MEM-06** | 4 | DONE | Windsurf | Opus | P0 | 🔥 | #Test #Release | P6 Regression | [ARCHIV] E2E & benchmarks | memory_v2.md | V2.1.0 |
| **003** | 5 | DONE | Windsurf | Kimi | P1 | 🧊 | #QA #Framework | QA Foundation | [ARCHIV] Memory QA runner | task_003_memory_qa_framework.md | DONE |
| **004** | 4 | DONE | Windsurf | Kimi | P1 | 🧊 | #QA | QA Expansion | [ARCHIV] 18 scenarios | task_004_memory_qa_scenarios.md | 18/18 |
| **005** | 3 | DONE | Windsurf | Kimi | P1 | 🧊 | #QA #Dashboard | QA Dashboard | [ARCHIV] Health dashboard | task_005_memory_qa_dashboard.md | DONE |
| **007** | 2 | DONE | Windsurf | Kimi | P1 | 🧊 | #QA #LogCapture | QA Stabilization | [ARCHIV] LogCapture root logger | task_007_regex_glue_patch.md | DONE |
| **008** | 4 | DONE | Windsurf | Kimi | P1 | 🧊 | #QA #Cognitive | QA Diamond | [ARCHIV] Cognitive bridge | task_008_cognitive_bridge.md | DIAMOND |
| **009** | 3 | DONE | Windsurf | Kimi | P0 | 🧊 | #Critical | Tool mapping | [ARCHIV] register_all_tools | task_009_memory_tool_mapping.md | DONE |
| **010** | 2 | DONE | Windsurf | Kimi | P0 | 🧊 | #Critical | Naming | [ARCHIV] Registry naming | task_010_memory_naming_mismatch.md | DONE |
| **011** | 2 | DONE | Windsurf | Kimi | P0 | 🧊 | #Critical | Signature | [ARCHIV] memory_tools signatures | task_011_memory_tool_signature.md | DONE |
| **012** | 3 | DONE | Windsurf | Sonnet | P1 | 🔥 | #Enhancement | Pre-Pass | [ARCHIV] Pre-pass physis | task_012_memory_pre_pass_physis.md | DONE |
| **BUG-MEM-034** | 2 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Strategic routing | [ARCHIV] Gemini bypass recall | task_bug_mem_034_strategic_routing.md | DONE |
| **BUG-MEM-033** | 2 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Fact field | [ARCHIV] Fact grammar | task_bug_mem_033_fact_field_warning.md | DONE |
| **BUG-MEM-032** | 3 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | List guard | [ARCHIV] List-request guard | task_bug_mem_032_list_request_guard.md | DONE |
| **BUG-MEM-031** | 3 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Semantic expansion | [ARCHIV] Query expansion | task_bug_mem_031_semantic_query_expansion.md | DONE |
| **BUG-MEM-030** | 2 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Recall pronouns | [ARCHIV] Pronoun guard | task_bug_mem_030_recall_guard_pronouns.md | DONE |
| **BUG-MEM-029** | 3 | DONE | Windsurf | Kimi | P0 | 🧊 | #Bug #Medical | Medical nano | [ARCHIV] Allergen reasoning | task_bug_mem_029_medical_nano_reasoning.md | DONE |
| **BUG-MEM-028** | 2 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Adverb guard | [ARCHIV] Identity adverb | task_bug_mem_028_identity_adverb_guard.md | DONE |
| **BUG-MEM-023** | 2 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Top-K | [ARCHIV] Top-K starvation | task_bug_mem_023_topk_starvation.md | DONE |
| **BUG-MEM-022** | 2 | DONE | Windsurf | Kimi | P0 | 🧊 | #Bug | Health starvation | [ARCHIV] HEALTH threshold | task_bug_mem_022_health_starvation.md | DONE |
| **BUG-MEM-021** | 4 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Context commander | [ARCHIV] Search guard V3 | task_bug_mem_021_context_commander_search_guard.md | DONE |
| **BUG-MEM-020** | 4 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Density | [ARCHIV] Memory density | task_bug_mem_020_memory_density_priority_upgrade.md | DONE |
| **BUG-SYS-019-V2** | 4 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Proactivity | [ARCHIV] Fact-telling guard | task_bug_sys_019_memory_fact_proactivity_guard.md | DONE |
| **BUG-MEM-018** | 4 | DONE | Windsurf | Kimi | P1 | 🧊 | #Bug | Relations | [ARCHIV] Identity mapping | task_bug_mem_018_relationship_identity_mapping.md | DONE |
| **BUG-MEM-017** | 4 | DONE | Windsurf | Kimi | P0 | 🧊 | #Bug | Rolf fix | [ARCHIV] Identity hard lock | task_bug_mem_017_identity_hard_lock_fix.md | DONE |
| **ORCH-DIAMOND-FINAL** | 5 | 🥇 DONE & SEALED | Windsurf | Kimi | P1 | 🧊 | #Refactor | Diamond cleanup | [ARCHIV] Service-agnostic dispatcher | intent_engine.py | SEALED |
| **ORCH-TRANSFORM-EPIC** | 8 | 🏆 EPIC COMPLETE | Windsurf | Kimi | P1 | 🧊 | #Epic | ChatOrchestrator | [ARCHIV] 6 service modules | orchestrator/ | SEALED |
| **EPIC-MEM-V2** | — | 🚀 DONE | Windsurf | Kimi | P0 | 🧊 | #Epic | Memory V2 | [ARCHIV] Diamond certified | task_008_cognitive_bridge.md | Production |
| **EPIC-MEMORY-CORE-REFACTOR** | 7 | DONE | Cursor | Cursor | P1 | 🧊 | #Epic | Memory split | [ARCHIV] crud + retrieval | task_020_memory_core_refactor_epic.md | DONE 2026-04-12 |
| **FEAT-10-SMART-CHAT-NAMING** | 6 | DONE | Cursor | — | P2 | 🧊 | #Epic #UX | Semantic titles | [ARCHIV] Task 021 epic | task_021_smart_chat_naming_epic.md | DONE 2026-04-13 |
| **029** | 5 | DONE | Cursor | Sonnet | P1 | 🔥 | #Arch #MCL #Core | MCL-Phase M1 | MCL Core: `modal-api.js`, `window-state` MCL-Felder, Z-Stack Basis 100 | Epic MCL §M1 | `documentation/archive/dossiers/task_029_mcl_core.md` |
| **030** | 3 | DONE | Windsurf | Kimi | P1 | 🧊 | #Refactor #UI | MCL-Phase M1 | Image Viewer MCL-Migration | Epic MCL §M1 | `documentation/archive/dossiers/task_030_mcl_image_viewer.md` |
| **031** | 4 | DONE | Windsurf | Kimi | P2 | 🧊 | #MUI #UI | MCL-Phase M2 | Image Studio Z-Stack-Integration | Epic MCL §M2 | `documentation/archive/dossiers/task_031_mcl_image_studio.md` |
| **032** | 4 | DONE | Windsurf | Kimi | P2 | 🧊 | #State #Cleanup | MCL-Phase M3 | Knowledge Center Single-Source-of-Truth | Epic MCL §M3 | `documentation/archive/dossiers/task_032_mcl_knowledge_center.md` |
| **033** | 6 | DONE | Cursor | Sonnet | P1 | 🔥 | #NewFeature #API | MCL-Phase M4 | Video-Player Backend→Frontend | Epic MCL §M4 | `documentation/archive/dossiers/task_033_mcl_video_player.md` |
| **034** | 3 | DONE | Windsurf | Kimi | P3 | 🧊 | #Migration #UI | MCL-Phase M5 | Gallery MCL-Migration + Max-Modals-Limit | Epic MCL §M5 | `documentation/archive/dossiers/task_034_mcl_gallery.md` |

**Legende (Archiv):** wie Macro-Dashboard V2.9; Zeilen sind nur zur Nachvollziehbarkeit archiviert.
