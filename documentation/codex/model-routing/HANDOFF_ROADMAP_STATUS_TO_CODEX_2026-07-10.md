# Codex Handoff: Roadmap-Stand → M3.4 Audit → M4

**Date:** 2026-07-10  
**Source:** Cursor Roadmap-Review + `ROADMAP_EPIC_ORDER.md` v1.2.2 Sync  
**Status:** READY FOR CODEX

---

## 1. Was Cursor geändert hat

In `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md` (v1.2.1 → **v1.2.2**):

| Bereich | Änderung |
|---------|----------|
| **§0.1 Aktueller Auftrag** | `JETZT` von M1 auf **M3.4 `janus-final-audit`** gesetzt; danach M4 → M6 → Epic 5/6 |
| **§0.1** | Block **ABGESCHLOSSEN** (M0, M1.1–M1.3, MA/MB, M2.1, M3.1–M3.3, Delegation) ergänzt |
| **§0.1** | Block **OFFENE CAVEATS** (Recall +0 pp, M2.2 optional) ergänzt |
| **§0.7 Operator-Prioritäten** | Prio 1 = M3.4 Audit; Prio 2 = M4 MC; Prio 3 = Recall Follow-up |
| **§4 M0** | Marker `← JETZT` entfernt → `EXIT PASS` |
| **§14 Schnellreferenz** | Normal-Pfad auf M3.4 Audit → M4 aktualisiert |
| **§16 Tracker** | Fortschritts-Tabelle (~55–65 % gesamt, ~75–80 % Kern-MVP) ergänzt |
| **§16** | M3.4/M3 Zeilen auf 2026-07-10 und §0.1 JETZT synchronisiert |
| **§17 Entscheidungslog** | Einträge 2026-07-10 für Roadmap-Sync + dieses Handoff |

**Nicht geändert:** Produktcode, Flags, Task-Artefakte, `CURRENT_STATE.md` (bleibt Codex-Verantwortung nach Audit).

---

## 2. Current Truth (verbindlich)

### EXIT PASS

| Block | Evidence |
|-------|----------|
| M0 Intent Benchmark | `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md` |
| Codex Delegation 4-Choice | `HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md` |
| M1.1 / M1.2 / M1.3 | Task + Final-Audit-Artefakte unter `documentation/tasks/` |
| MA/MB Memory A+B | `TASK-MEM-M1.1` EXIT PASS |
| M2.1 Confidence Routing | `TASK-INTENT-M2.1` EXIT PASS |
| M3.1 Routine Store + Detector | `TASK-WORKFLOW-M3.1` EXIT PASS |
| M3.2 Proactive Offer | `TASK-WORKFLOW-M3.2` EXIT PASS |
| M3.3 Routine Runner | `TASK-WORKFLOW-M3.3` EXIT PASS |
| BACKLOG-124 GPT-5.6 Matrix | `CURRENT_STATE` 2026-07-10 17:15 — DONE, final audit PASS |

### IN ARBEIT / HANDOFF

| Block | Status | Nächster Schritt |
|-------|--------|------------------|
| **M3.4 Semantic Routine Reuse** | HANDOFF FINAL AUDIT | `janus-final-audit` auf bestehendem Audit-Package |
| **M3 gesamt** | IN ARBEIT | Nach M3.4 Audit → M3 EXIT PASS deklarieren |

### OFFEN

| Block | Hinweis |
|-------|---------|
| M4 Memory C (Session-Search FTS5) | Nächster großer Roadmap-Meilenstein nach M3.4 |
| M2.2 Regex-Freeze | Optional, niedrige Prio |
| M6 Transport, Epic 5/6 | Nach M4 (Standard-Pfad) |

### CAVEATS (dokumentiert)

- **M1 Recall:** `80.0% → 80.0%` (+0 pp) — kein „Recall solved“-Claim; Staging-Enablement nur mit Caveat
- **M3 trotz Recall-Caveat:** Pragmatisch fortgeschritten; Gate in Roadmap war strenger — bewusst dokumentiert
- **Cursor Composer Timeouts:** Operatives Risiko bei ≤2-File-Slices; siehe `HANDOFF_CURSOR_COMPOSER_TIMEOUT_ANALYSIS_2026-07-10.md`
- **Git:** Kein Commit/Push in Cursor-Session — lokaler Stand kann remote fehlen

---

## 3. Fortschritt (geschätzt)

```
Gesamt-Roadmap (bis Epic 6):     ~55–65 %
Kern-MVP (ohne M4):              ~75–80 %
Intent (M0–M2):                  ~85 %
Workflows (M3):                  ~90 %
Memory C (M4):                     0 %
```

---

## 4. Files to Trust (konzentriert)

**Roadmap / Planning:**
- `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md` (v1.2.2)
- `documentation/ai/CURRENT_STATE.md` (oberster Snapshot)

**M3.4 Audit:**
- `documentation/tasks/TASK-WORKFLOW-M3.4_*.md` (precheck, execution, audit package)
- `documentation/Cursor specs/LEARNED_WORKFLOWS_SPEC.md`

**Delegation (bei live Cursor):**
- `documentation/codex/model-routing/HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md`
- `documentation/codex/model-routing/HANDOFF_CURSOR_COMPOSER_TIMEOUT_ANALYSIS_2026-07-10.md`

**M4 Vorbereitung (nach Audit):**
- `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md` §6
- `ROADMAP_EPIC_ORDER.md` §15.7

---

## 5. Verbindliche No-Go-Regeln

- Kein Transport / OAuth / OpenRouter-Produkt vor M4 (Standard-Pfad)
- Keine Delegation-Härtung auf Critical Path (Track B only, max. 1 Slice/Woche)
- Kein Prod-Flag-Flip ohne Live-Retest + Audit
- Multi-File-Backend-Slices → **Codex lokal**, nicht live Cursor
- Nach M3.4 Audit: genau **ein** nächster Slice — entweder M4 MC starten oder bounded Recall-Follow-up (Operator-Entscheidung)

---

## 6. Aufgabe für Codex (Priorität)

### Prio 1 — JETZT

**`janus-final-audit` für TASK-WORKFLOW-M3.4** (Semantic Routine Reuse)

- Live-Evidence bereits PASS (beide Provider)
- Bei PASS: M3.4 + M3 in §16 auf EXIT PASS setzen, `CURRENT_STATE` + Doku aktualisieren
- Modell: `5.6 Terra` medium; `5.6 Sol` nur bei Audit-Eskalation

### Prio 2 — DANACH

**M4 Memory C (Session-Search FTS5)** — `ROADMAP_EPIC_ORDER.md` §15.7

- `janus-preimplementation-check` vor Code
- Flag `MEMORY_SESSION_SEARCH_ENABLED=false` default

### Prio 3 — Parallel oder nach M3.4 (Operator)

Bounded Recall-Follow-up oder explizite Entscheidung, Recall-Caveat für Staging zu akzeptieren

### Optional — Git

`janus-git-governance` nur nach explizitem Operator-OK (uncommitted State)

---

## 7. Copy-paste Prompt für Codex

```text
Du arbeitest am Janus-Projekt (Branch: develop).

STANDARD: M3.4 janus-final-audit abschließen, dann M4 Memory C vorbereiten.

Binding constraints (verbindlich):
- Roadmap v1.2.2: JETZT = M3.4 Final Audit → DANN M4 MC
- M3.1–M3.3 EXIT PASS; M3.4 live PASS, formaler Audit offen
- M1 Recall-Caveat (+0 pp) dokumentiert — kein „Recall solved“ claim
- Track A wins: Produkt-Roadmap vor Delegation-Härtung (Operating Model beachten)
- Multi-File-Backend → Codex lokal; Cursor nur ≤2 allowlistete Dateien
- No-Go: kein Transport/OAuth/OR-Produkt vor M4

Trust files zuerst:
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md (§0.1, §16)
- documentation/codex/model-routing/HANDOFF_ROADMAP_STATUS_TO_CODEX_2026-07-10.md
- documentation/ai/CURRENT_STATE.md
- documentation/tasks/TASK-WORKFLOW-M3.4_* (precheck, execution, audit package)
- documentation/codex/model-routing/HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md

Aufgabe Prio 1:
- Führe janus-final-audit für TASK-WORKFLOW-M3.4 durch
- Bei PASS: §16 M3.4 + M3 auf EXIT PASS, CURRENT_STATE + SKILL_USAGE_LOG aktualisieren

Aufgabe Prio 2 (nach PASS):
- janus-preimplementation-check für M4 MC (Session-Search FTS5) vorbereiten — noch nicht implementieren ohne PASS

Stop:
- Nach M3.4 Audit PASS/Blocked mit Evidence
- Git-Checkpoint nur nach explizitem Operator-OK
```

---

**END OF CODEX HANDOFF**
