# Codex Handoff: Block 2 Kalender+Wikipedia + Diamond-Routine-UX

**Date:** 2026-07-10 (Abend, nach Live-Tests ~21:32–21:48)  
**Source:** Cursor-Session (GPT/Gemini Live-Validierung Block 2)  
**Status:** READY FOR CODEX  
**Vorgänger:** `documentation/codex/model-routing/HANDOFF_ROADMAP_STATUS_TO_CODEX_2026-07-10.md`

---

## 1. Executive Summary

Block 2 (**Kalender + Wikipedia**, passive Lernen, semantic reuse, GPT + Gemini) ist **live validiert und produktionsreif** im Sinne von M3-Erweiterung. Cursor hat in dieser Session mehrere Bugs gefixt, Diamond-UX für Wikipedia-Routinen implementiert und mit echten Janus-Läufen verifiziert.

**Roadmap-Freigabe:** M3 bleibt **EXIT PASS**. Codex kann **weiter mit M4 Memory C** — nach einem bounded `janus-documentation-update` für diese Session.

**Nicht fertig / bewusst offen:**
- Routinen-UI (Löschen/Verwalten in Settings) — nur DB-Zugriff
- Formaler Final-Audit-Task für Block-2-Slice (noch kein `TASK-*` im Registry)
- Git-Checkpoint dieser Session (uncommitted lokal)

---

## 2. Was in dieser Cursor-Session erreicht wurde

### 2.1 Block 2 Funktionsziele (alle LIVE PASS)

| Ziel | Ergebnis |
|------|----------|
| Combo Kalender + Wikipedia (erster LLM-Lauf) | GPT formuliert natürlich; Gemini nutzt Tool-Kurzfassung + Quelle |
| Passive Lernkette | 1. Lauf Kandidat, 2. Lauf Promotion mit Hinweis |
| Semantic Routine-Reuse | „Ich habe deine passende gespeicherte Routine genutzt.“ |
| Rebind (Berlin → München) | Frische Wikipedia-Daten, kein Berlin-Snapshot |
| Keine leere Gemini-Bubble | Behoben (Forced-Tools + Stream-Fallback) |
| Kein `No module named 'wikipedia'` | `wiki_service.py` auf stdlib MediaWiki-API umgestellt |

### 2.2 Live-Test-Protokoll (Operator, 2026-07-10)

**Vorher (Routine ohne Snapshot):**
- Routine reuse ✅, aber rohe Tool-Ausgabe (`events: []`, langer Wiki-Text mit `(Auszug)`)

**Nach Diamond-UX-Fixes:**
- Formatierung lesbar ✅
- Wikipedia: 4-Satz-Kurzfassung statt 2000-Zeichen-Hardcut ✅

**Rebind-Test München (Gemini):** PASS — München-Text, Routine reuse

**Neu-Lernen nach DB-Löschung:**
1. **GPT 21:47** — schöne LLM-Synthese (Kalender + kurze Wikipedia + Quelle + Vorschläge)
2. **Gemini 21:47** — Tool-Combo + „Ich habe dafuer eine passende Routine gespeichert.“
3. **GPT 21:48** — Routine reuse mit gespeichertem Snapshot (489 Zeichen, `snapshot_query: Berlin`)

**Bekannte Nuance:** Snapshot stammt vom **Gemini-Promotion-Lauf**, nicht von GPTs schönerer Formulierung in Lauf 1 — weil Promotion cross-chat/cross-provider erfolgte. Kein Bug; optionaler Follow-up: Snapshot aus bestem LLM-Lauf oder gleicher Provider für beide Lernläufe.

### 2.3 Operator-DB-Eingriff (Cursor)

Routine **„Routine Kalender Wikipedia“** (ID 3) und **4 aktive Kandidaten** aus `janus.db` gelöscht, damit Neu-Lernen möglich war.  
Pfad: `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`

Aktuell wieder vorhanden: neue Routine ID 3 nach Gemini-Promotion. Kalender+Wetter-Routinen (ID 1, 2) unberührt.

---

## 3. Technische Änderungen (Code)

### 3.1 Neue Datei

| Datei | Zweck |
|-------|-------|
| `backend/services/workflow/calendar_wikipedia_presenter.py` | Diamond-Policy: LLM-Antwort erhalten vs. Combo-Fallback; Wikipedia-Snapshot beim Speichern; Snapshot vs. Rebind in Routines |

### 3.2 Geänderte Kern-Dateien

| Datei | Änderung |
|-------|----------|
| `backend/tools/wiki_service.py` | MediaWiki/stdlib; `_condense_wikipedia_summary()` — max. 4 Sätze / ~900 Zeichen |
| `backend/services/workflow/routine_schema.py` | `RoutineStep.output_snapshot`, `RoutineStep.snapshot_query` |
| `backend/services/workflow/routine_runner.py` | `_build_calendar_wikipedia_success_summary()`; Snapshot-Reuse + Rebind-Fallback |
| `backend/services/workflow/workflow_offer_service.py` | `enrich_steps_with_wikipedia_snapshot()` bei Kandidat/Promotion/Offer-Accept |
| `backend/services/workflow/routine_store.py` | `promote_candidate_to_routine(..., steps=)` Override |
| `backend/services/orchestrator/response_finalizer.py` | `resolve_calendar_wikipedia_final_text()` — LLM nicht mehr blind überschreiben |
| `backend/services/orchestrator/execution_engine.py` | Gleiche LLM-Preserve-Logik in Tool-Loop-Return + Stream-Pfad |
| `backend/services/orchestrator/execution_dispatcher.py` | Calendar+Wikipedia Combo-Routing, Forced-Tools, Guards (frühere Session-Fixes) |
| `backend/services/orchestrator/intent_engine.py` | Combo nicht mehr von `video_understanding` / `personal_recall` blockiert |

### 3.3 Tests (neu/erweitert, lokal grün)

| Test |
|------|
| `backend/tests/test_calendar_wikipedia_presenter.py` (neu) |
| `backend/tests/test_routine_runner.py` — Wikipedia-Format, Snapshot, Rebind |
| `backend/tests/tools/test_system_skills_diamond.py` — `test_wikipedia_condenses_long_lead_to_opening_sentences` |
| `backend/tests/test_execution_dispatcher_wikipedia_guard.py` |
| `backend/tests/test_agent_factory_runtime.py` — combo response |

---

## 4. Diamond-UX-Modell (verbindlich für Codex)

```
Stufe 1 — Tool (immer):     Wikipedia 4-Satz-Kurzfassung aus Lead
Stufe 2 — Erster LLM-Lauf:  Modell formuliert, wenn substantiell → behalten
Stufe 3 — Speichern:        output_snapshot + snapshot_query auf Wikipedia-Step
Stufe 4 — Routine-Reuse:    Kalender live; Wikipedia = Snapshot bei gleichem Query,
                            sonst frische Tool-Kurzfassung (Rebind)
```

**Nicht implementiert (Backlog):**
- Routinen-UI in Settings
- LLM-Snapshot-Backfill bei bestehenden Routinen ohne Snapshot
- „Bester“ Snapshot bei cross-provider Promotion

---

## 5. Current Truth Roadmap

### EXIT PASS (unverändert gültig)

- M0, M1 (mit Recall-Caveat), M2.1, MA/MB, **M3.1–M3.4**, Spec 29.1/29.2 (passive learning), Spec 31.1/31.2 (semantic reuse Weather/Routing)

### Diese Session ergänzt (noch ohne formalen Task-Abschluss)

- **Block 2: Calendar + Wikipedia** — Live PASS, Code + Tests in Repo (teilweise uncommitted)
- Erweitert M3 semantic reuse auf **`calendar.list_events + system.wikipedia_summary`**

### JETZT laut Roadmap v1.2.2

**M4 Memory C** — nächster großer Meilenstein

### OFFEN / Optional

| Item | Prio |
|------|------|
| `janus-documentation-update` für Block-2-Session | Prio 1 (bounded) |
| Routinen-UI (Settings CRUD) | Backlog / Spec-29-Slice |
| Cross-provider Snapshot-Polish | Backlog |
| M2.2 Regex-Freeze | Niedrig |
| Git-Checkpoint develop | Nur nach Operator-OK |

---

## 6. Was Codex zuerst lesen soll

1. `documentation/codex/HANDOFF_BLOCK2_CALENDAR_WIKIPEDIA_TO_CODEX_2026-07-10.md` (dieses Dokument)
2. `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md` (§0.1, §16 — M3 EXIT PASS, JETZT M4)
3. `documentation/codex/model-routing/HANDOFF_ROADMAP_STATUS_TO_CODEX_2026-07-10.md`
4. `documentation/ai/CURRENT_STATE.md` (nach Doku-Update aktualisieren)
5. `backend/services/workflow/calendar_wikipedia_presenter.py`
6. Relevante Tests: `test_calendar_wikipedia_presenter.py`, `test_routine_runner.py` (wikipedia tests)

---

## 7. Aufgaben für Codex (Priorität)

### Prio 1 — Bounded Documentation Sync

**Skill:** `janus-documentation-update`

- `CURRENT_STATE.md`: Block 2 Calendar+Wikipedia LIVE PASS, Diamond-UX, Snapshot-Modell
- `SKILL_USAGE_LOG.md`: Eintrag Cursor-Session 2026-07-10 Abend
- Optional: kurzer Eintrag `01_CENTRAL_TASK_REGISTRY.md` als „Block 2 validation“ oder kleines `TASK-BLOCK2-*` nur wenn Diamond-Pipeline es verlangt — **nicht** over-engineeren

### Prio 2 — M4 Memory C starten

**Skill:** `janus-skill-router` → `janus-preimplementation-check`

- `ROADMAP_EPIC_ORDER.md` §15.7
- `MEMORY_SESSION_SEARCH_ENABLED=false` default
- Kein Transport/OAuth/OpenRouter vor M4

### Prio 3 — Optional Git

**Skill:** `janus-git-governance` — nur nach explizitem Operator-OK

- Viele lokale Änderungen; scoped commit für Block-2-Cluster sinnvoll:
  - `calendar_wikipedia_presenter.py`
  - `wiki_service.py`
  - workflow + orchestrator Änderungen
  - Tests

### Nicht jetzt

- Kein Rewrite der gesamten Wikipedia/LLM-Pipeline
- Keine Routinen-UI ohne eigenen Spec/Task
- Kein erneutes M3.4-Audit (bereits PASS)

---

## 8. Verifikation für Codex (schnell)

```powershell
cd C:\KI\Janus-Projekt
python -m pytest backend/tests/test_calendar_wikipedia_presenter.py -q
python -m pytest backend/tests/test_routine_runner.py -k "wikipedia" -q
python -m pytest backend/tests/tools/test_system_skills_diamond.py::TestWikipediaService -q
python -m pytest backend/tests/test_execution_dispatcher_wikipedia_guard.py -q
```

Erwartung: alles grün.

---

## 9. Copy-Paste Prompt für Codex

```text
Du arbeitest am Janus-Projekt (Branch: develop).

KONTEXT: Cursor hat am 2026-07-10 Abend Block 2 (Kalender + Wikipedia) live validiert und Diamond-UX implementiert. Lies zuerst:
- documentation/codex/HANDOFF_BLOCK2_CALENDAR_WIKIPEDIA_TO_CODEX_2026-07-10.md
- documentation/codex/model-routing/HANDOFF_ROADMAP_STATUS_TO_CODEX_2026-07-10.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md (§0.1, §16)

BINDING TRUTH:
- M3 (M3.1–M3.4) = EXIT PASS
- Block 2 Calendar+Wikipedia = LIVE PASS (GPT/Gemini, Routine, Rebind München, Snapshot)
- Nächster Roadmap-Meilenstein = M4 Memory C
- Routinen-UI fehlt noch — Löschen ging per DB, kein Produkt-UI
- Recall-Caveat M1 unverändert (+0 pp)
- Viele Block-2-Codeänderungen sind lokal, ggf. uncommitted — nicht blind „fertig“ annehmen ohne git status

AUFGABE PRIO 1:
- janus-documentation-update: CURRENT_STATE + SKILL_USAGE_LOG für Block-2-Session und Diamond-UX (calendar_wikipedia_presenter, wiki 4-Satz-Kurzfassung, Snapshot)
- Kein neuer Feature-Scope

AUFGABE PRIO 2:
- janus-skill-router → janus-preimplementation-check für M4 Memory C (Session-Search FTS5)
- Noch nicht implementieren ohne PASS

CONSTRAINTS:
- Track A: Produkt-Roadmap vor Delegation-Härtung
- Multi-File-Backend → Codex lokal
- Kein Transport/OAuth/OpenRouter-Produkt vor M4
- Git nur nach explizitem Operator-OK

STOP:
- Nach Doku-Sync + M4-Precheck-Handoff mit Evidence
```

---

## 10. CAVEATS für ehrliche Kommunikation

1. **„Diamond“ für Block 2** = funktional + UX-Pfad definiert und live belegt — **nicht** jeder Roadmap-Slice ist auditiert/dokumentiert.
2. **Snapshot-Qualität** hängt vom Promotion-Lauf ab (Provider/Chat). GPT-Schönheit ≠ automatisch gespeicherter Snapshot.
3. **Operator musste Routine per DB löschen** — bis Routinen-UI kommt, ist das der Workaround.
4. **`CURRENT_STATE.md` ist noch nicht von dieser Session aktualisiert** — Codex-Aufgabe Prio 1.

---

**END OF CODEX HANDOFF**
