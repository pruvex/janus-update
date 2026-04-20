# AI Studio Bootstrap Protocol & Universal Routing (Diamond-OS V3.1 — Thinking-Loop Upgrade)

**Canonical:** Diese Datei ist die **Single Source of Truth** für das Bootstrapping.  
**Kopie im Repo-Root:** `00_AI_STUDIO_BOOTSTRAP.md` verweist nur hierher.

**Zweck:** **Adaptive Task-Orchestrierung** — CU-basierte Routing-Entscheidungen, Quota-sensitives Task-Pooling, und deterministische Next-Action-Loops.

---

## 0. Resource-Status Dashboard (Live-Check)

**Vor jedem Routing-Entscheid:**

| Ressource | Limit | Status | Aktion bei Erreicht |
|-----------|-------|--------|---------------------|
| **Cursor Fast-Requests** | 50/Monat | ⬜ OK / 🟡 Warn / 🔴 Critical | DEFERRED Pool |
| **Windsurf Daily %** | Unlimitiert | ⬜ 90%+ verfügbar | Standard-Routing |
| **Gemini Pro (AI Studio)** | ~50/Tag | ⬜ OK / 🟡 Low | Priorisierung nur P0-P1 |

**DEFERRED Pool:** Tasks mit Status `DEFERRED` warten auf Quota-Reset oder Ressourcen-Freigabe.

---

## 1. Editor-Routing & Adaptive Guard (V2.8)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      DIAMOND-OS V2.8 — ADAPTIVE GUARD SYSTEM                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   NUTZER-REQUEST                                                                    │
│        │                                                                            │
│        ▼                                                                            │
│   ┌──────────────────────────────────────────────┐                                 │
│   │  AI STUDIO (Gemini Flash) — TRIAGE GUARD       │                                 │
│   │  ─────────────────────────────────             │                                 │
│   │  • CU-Schätzung (1-10)                        │                                 │
│   │  • Quota-Check (Cursor/Windsurf)              │                                 │
│   │  • [TRIAGE → ANALYSE → STRATEGIE →            │                                 │
│   │     MODELL-VORGABE → HANDOVER → NEXT ACTION]  │                                 │
│   └──────────────────────┬─────────────────────────┘                                 │
│                          │                                                          │
│           ┌──────────────┼──────────────┐                                          │
│           │              │              │                                           │
│           ▼              ▼              ▼                                            │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                                      │
│   │ CU 1-3   │   │ CU 4-7   │   │ CU 8-10  │   ← Adaptive Complexity              │
│   │ Routine  │   │ Standard │   │ Complex  │                                      │
│   └────┬─────┘   └────┬─────┘   └────┬─────┘                                      │
│        │              │              │                                               │
│        ▼              ▼              ▼                                            │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                                      │
│   │ WINDSURF │   │ WINDSURF │   │ AI STUDIO│                                      │
│   │ Kimi K2.5│   │ Kimi K2.5│   │ Pro      │  ← Fallback: Cursor (2× Fail)        │
│   │ 90%      │   │ 90%      │   │ 5%       │                                      │
│   └──────────┘   └──────────┘   └──────────┘                                      │
│                                                                                     │
│   ╔══════════════════════════════════════════════════════════════════════════════╗ │
│   ║  ADAPTIVE CU ADJUSTMENT (Auto-Eskalation)                                    ║ │
│   ║  ─────────────────────────────────────────                                     ║ │
│   ║  Wenn Task in Windsurf 2× scheitert → CU +2 → Ziel-Editor wechselt zu:        ║ │
│   ║  • CU 1-3 → CU 5-7: Cursor oder Pro-Review                                     ║ │
│   ║  • CU 4-7 → CU 8-10: Gemini Pro Blueprint + Cursor-Implementierung           ║ │
│   ╚══════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                     │
│   ╔══════════════════════════════════════════════════════════════════════════════╗ │
│   ║  TASK-POOLING & QUOTA-CHECK                                                   ║ │
│   ║  ─────────────────────────                                                    ║ │
│   ║  Wenn Quota erschöpft (Cursor Fast 50/50, Windsurf Daily >90%):               ║ │
│   ║  → Task → DEFERRED Pool (Status: DEFERRED)                                    ║ │
│   ║  → Registry aktualisieren: [CU | Status: DEFERRED | App: WAITING]             ║ │
│   ╚══════════════════════════════════════════════════════════════════════════════╝ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Rollen im Detail (V2.8)

| Editor | Modell | Rolle | Einsatzanteil | CU-Range |
|--------|--------|-------|---------------|----------|
| **AI Studio** | Gemini Flash | **Triage-Guard + CU-Schätzung** | 100% aller Tasks | 1-10 (Entscheidung) |
| **AI Studio** | Gemini Pro | **CU 8-10 Blueprint** | ~5% | 8-10 |
| **Windsurf** | **Kimi K2.5** | **Primary Workhorse (CU 1-7)** | **~85%** | 1-7 |
| **Cursor** | Claude 4.6 Sonnet | **Precision + Kimi-Fallback (CU+2)** | ~10% | 3-10 (Fallback) |

---

## 2. CU — Complexity Unit Rating (1-10)

| CU | Beschreibung | Editor-Präferenz | Fallback bei 2× Fail |
|----|--------------|------------------|---------------------|
| **1-2** | Triviale Änderungen (1 Datei, Kommentare, Lint) | Windsurf/Kimi | Cursor (nur wenn blockiert) |
| **3-4** | Einfache Features (2-3 Dateien, keine Abhängigkeiten) | Windsurf/Kimi | Cursor |
| **5-6** | Standard-Features (3-5 Dateien, geringe Abhängigkeiten) | Windsurf/Kimi | Cursor oder Pro-Review |
| **7-8** | Komplexe Features (5-8 Dateien, Schema-Touch) | Windsurf/Kimi → Pro-Check | Cursor |
| **9-10** | Architektur/Schema/Sicherheit | AI Studio/Pro → Windsurf | Cursor (UI-Teile) |

**CU-Adjustments (Auto-Korrektur):**
- `+1` bei unerwarteten Abhängigkeiten während Implementierung
- `+2` bei 2× Fail im gleichen Editor
- `-1` bei erfolgreicher Wiederverwendung existierender Patterns

**CU-Schätzung durch Flash-Guard:**
```
[TRIAGE] → Dateien zählen → Abhängigkeiten checken → Schema-Touch? → CU zuweisen
```

---

## 3. Das NEXT ACTION LOOP (V3.1 — Mit Thinking-Phase)

**Jeder Master-Prompt MUSS diese Kette enthalten:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEXT ACTION LOOP (V3.1)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ 0. THINK    │───▶│ 1. IMPL     │───▶│ 2. TEST     │       │
│  │  (MCP)      │    │             │    │             │       │
│  │ Max 3-5     │    │ Code        │    │ pytest      │       │
│  │ Gedanken    │    │ generieren  │    │ läuft?      │       │
│  └─────────────┘    └─────────────┘    └──────┬──────┘       │
│       │                                         │              │
│       │                              ❌ FAIL    │              │
│       │                                         ▼              │
│       │                              ┌─────────────┐         │
│       │                              │ Auto-Fix    │         │
│       │                              │ (1 Versuch) │         │
│       │                              │             │         │
│       │                              │ Ja → TEST   │         │
│       │                              │ Nein → LOG  │         │
│       │                              └─────────────┘         │
│       │                                         │              │
│       ▼                                         ▼              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 3. LINTER                                             │    │
│  │    ruff/mypy sauber?                                  │    │
│  │    ❌ FAIL → Auto-Fix (1 Versuch) → Ja → IMPORTS      │    │
│  │                           Nein → LOG                  │    │
│  └───────────────────────────────┬───────────────────────┘    │
│                                  │                           │
│                                  ▼                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 4. IMPORTS                                          │    │
│  │    Circular? Missing? Auto-fix?                     │    │
│  │    ❌ Blocker → Diamond-Report mit Log                │    │
│  │    ✅ OK → NEXT                                     │    │
│  └───────────────────────────────┬───────────────────────┘    │
│                                  │                           │
│                                  ▼                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 5. DIAMOND-REPORT                                   │    │
│  │    • Geänderte Dateien                             │    │
│  │    • Neue Dateien                                  │    │
│  │    • Tests: X neu / Y updated                      │    │
│  │    • Breaking Changes: Ja/Nein                    │    │
│  │    • Registry-Update: CU, Status                   │    │
│  │    • CU-Adjustment-Log (falls Fail)              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Regel:** Keine Fertigmeldung ohne erfolgreichen Durchlauf des Loops.  
**Wenn Loop blockiert:** Diamond-Report mit Fehler-Log → CU +2 → Eskalation.

### Golden Rules of Thinking (MCP Sequential Thinking)

**Regel 1: Halte Gedanken kurz & prägnant**
- Vermeidung von Sync-Hangs bei langen Thinking-Sessions
- Max. 3-5 Gedanken pro Analyse

**Regel 2: Spätestens bei Thought 3 muss die Lösungshypothese stehen**
- Thought 1: Problem-Analyse
- Thought 2: Root-Cause oder Strategie
- Thought 3: Lösungshypothese + Umsetzungsplan

**Regel 3: Wenn ein Gedanke > 45s dauert, breche ab und starte die Umsetzung**
- Kein „Analysis Paralysis"
- Besser iterativ implementieren als endlos planen

**Loop-Checkpoint Status:**
- 🟢 `LOOP_PASS` — Alle 5 Schritte erfolgreich
- 🟡 `LOOP_RETRY` — Auto-Fix läuft (max. 1 Versuch pro Schritt)
- 🔴 `LOOP_FAIL` — Blockiert → Eskalation erforderlich

---

## 4. Task-Pooling & Quota-Management (V2.8)

### 4.1 Active Pool (Standard-Verarbeitung)

Tasks mit Status: `TODO` → `IN_PROGRESS` → `DONE`

**Flow mit NEXT ACTION LOOP:**
```
Task-Creation → CU-Schätzung → Quota-Check → Editor-Zuweisung → NEXT ACTION LOOP → DONE
```

### 4.2 DEFERRED Pool (Quota-Warteschlange)

Wenn Ressourcen erschöpft:

| Trigger | Task-Status | Aktion |
|---------|-------------|--------|
| Cursor Fast 45+/50 | `DEFERRED` | Wartet auf Reset |
| Gemini Pro <3/Tag verfügbar | `DEFERRED` | Nur P0-P1 erlaubt |
| Windsurf unlimitiert | N/A | Immer verfügbar |

**DEFERRED Pool Management:**
```markdown
### DEFERRED Pool (Warteschlange)

| Task-ID | CU | Ursprünglicher Editor | Grund | Seit | Priorität |
|---------|----|----------------------|-------|------|-----------|
| M-UI-05 | 4 | Cursor | Fast-Quota 50/50 | 2026-03-31 | P2 |
| M-ARCH-03 | 9 | Pro | Pro-Quota <2/Tag | 2026-03-31 | P1 |
```

### 4.3 Adaptive CU Adjustment (Auto-Eskalation)

**Trigger:** Task scheitert 2× im selben Editor

| Original CU | Nach 2× Fail | Neuer Editor | Eskalations-Pfad |
|-------------|--------------|--------------|------------------|
| 1-3 | 3-5 | Cursor | Kimi → Cursor |
| 4-6 | 6-8 | Cursor oder Pro | Kimi → Pro-Check → Cursor |
| 7-8 | 9-10 | Pro → Cursor | Kimi → Pro-Blueprint → Cursor-UI |

**Registry-Update bei CU-Adjustment:**
```markdown
| Task-ID | CU | CU-Log | Status | App |
|---------|----|--------|--------|-----|
| M-FEAT-12 | 6 | 4→6 (+2 nach Fail#2) | IN_PROGRESS | Cursor |
```

---

## 5. Eskalations-Matrix V2.8 (Adaptive)

| CU | Initial-Routing | Bei 1× Fail | Bei 2× Fail (CU +2) |
|----|-----------------|-------------|---------------------|
| **1-3** | Windsurf/Kimi | Auto-Fix, retry | Cursor |
| **4-6** | Windsurf/Kimi | Auto-Fix, retry | Cursor oder Pro-Check |
| **7-8** | Windsurf/Kimi | Cursor-Check | Gemini Pro + Cursor |
| **9-10** | Gemini Pro → Windsurf | Cursor für UI-Teile | Menschliche Review |

**Wichtig:** Adaptive CU-Logik aktiviert sich **automatisch** bei wiederholtem Fail.

---

## 6. Handover-Pakete V2.8 (Next-Action-kompatibel)

### A. Windsurf-Handover (CU 1-7)

```markdown
## Windsurf-Handover: [TASK-ID] | CU: [1-7]

**Ziel-Editor:** Windsurf (Kimi K2.5)  
**CU:** [Initial | Nach 2× Fail: CU+2]  
**Kategorie:** [Bugfix / Feature / Routine]

**1. Aufgabenstellung**
[Präzise Beschreibung des zu lösenden Problems]

**2. Betroffene Dateien (max. 5)**
- @backend/services/...
- @backend/tests/...

**3. NEXT ACTION LOOP (Pflicht-Reihenfolge V3.1):**
```
0. THINK (MCP): Max. 3-5 Gedanken. Problem-Analyse + Hypothese.
1. IMPL: Code generieren
2. TEST: `pytest` — alle grün? ❌→Auto-Fix→Retry
3. LINTER: `ruff check .` — sauber? ❌→Auto-Fix→Retry
4. IMPORTS: Circular? Missing? Auto-fix? ❌→Report
5. DIAMOND-REPORT: Dokumentieren

**4. Akzeptanzkriterien**
- [ ] Feature funktioniert laut SPEC
- [ ] Tests passen zu Implementation
- [ ] Lint/Type-Check sauber

**5. Fallback-Plan**
Wenn 2× Fail → CU +2 → Eskalation zu [Cursor/Pro]
```

### B. Pro-Blueprint-Handover (CU 8-10)

```markdown
## Pro-Blueprint: [TASK-ID] | CU: [8-10]

**Ziel-Editor:** AI Studio (Gemini Pro)  
**CU:** [8-10]  
**Kategorie:** Architektur / Komplex

**1. Problemstellung**
Warum ist Kimi allein überfordert?

**2. Komplexitäts-Analyse**
- [ ] Schema-Änderungen erforderlich
- [ ] Neue Architektur-Patterns nötig
- [ ] Breaking Changes zu managen

**3. NEXT ACTION LOOP für Pro**
- [ ] 1. ANALYSE: Kontext vollständig?
- [ ] 2. STRATEGIE: Lösungsansatz definiert
- [ ] 3. BLUEPRINT: Technische Spezifikation
- [ ] 4. HANDOVER: Windsurf/Cursor übergeben
- [ ] 5. DIAMOND-REPORT: Dokumentation

**4. Output für Windsurf/Cursor**
- Blueprint-Dokument
- Implementierungs-Plan mit CU-Bewertung
- Test-Strategie
```

### C. Cursor-Fallback-Handover (CU angepasst)

```markdown
## Cursor-Fallback: [TASK-ID] | CU: [Original+2]

**Ziel-Editor:** Cursor (Claude Sonnet)  
**CU:** [Nach 2× Kimi-Fail: Original +2]  
**Kategorie:** [UI-Feinschliff / Kimi-Fallback]

**1. Vorgeschichte**
- Editor: Windsurf (Kimi K2.5)
- Versuche: 2×
- CU-Adjustment: +2 (von [X] auf [Y])

**2. Fehler-Log / Blocker**
1. [Beschreibung des ersten Fehlers]
2. [Beschreibung des zweiten Fehlers]

**3. NEXT ACTION LOOP (Präzision)**
- [ ] 1. IMPLEMENTATION: Feinschliff / Korrektur
- [ ] 2. TEST: Spezifische Tests für gefailte Bereiche
- [ ] 3. LINTER/TYPE: Strikte Checks
- [ ] 4. UI-VALIDIERUNG: Screenshot/Vergleich
- [ ] 5. DIAMOND-REPORT: Delta-Dokumentation

**4. Erfolgskriterien**
[Was muss Cursor besser machen als Kimi?]
```

---

## 7. Registry-Integration (V2.8)

Jeder Task MUSS in `01_CENTRAL_TASK_REGISTRY.md` mit:
- **CU:** [1-10] — Initial vom Flash geschätzt
- **CU-Log:** [Verlauf bei Adjustments, z.B. "4→6 (+2 nach Fail#2)"]
- **Status:** TODO | IN_PROGRESS | DONE | **DEFERRED** | UI-VALIDIERT
- **App:** Windsurf | Cursor | AI Studio | **WAITING**
- **Loop-Status:** LOOP_PASS | LOOP_RETRY | **LOOP_FAIL** (bei Eskalation)

---

## 8. Status-Keywords (Registry / Dashboard)

| Status | Bedeutung | Verwendung |
|--------|-----------|------------|
| **TODO** | Wartet auf Flash-Triage | Initial nach Task-Creation |
| **IN_PROGRESS** | Bearbeitung läuft | Nach Editor-Zuweisung |
| **DONE** | Loop erfolgreich | Nach DIAMOND-REPORT |
| **DEFERRED** | Quota-Block / Resource-Engpass | Wartet auf Freigabe |
| **UI-VALIDIERT** | Menschliche UI-Abnahme | Nach Cursor-UI-Work |
| **LOOP_FAIL** | NEXT ACTION LOOP blockiert | CU +2, Eskalation |

---

## 9. Master-Prompt Templates (V2.8 — Mit NEXT ACTION LOOP)

### A. Flash-Triage-Template (AI Studio)

```markdown
# Flash-Triage: [TASK-ID] | Input: [Nutzer-Request]

**Ziel:** CU-Schätzung + Routing-Entscheidung

## [TRIAGE] → Dateien zählen
- Geschätzte Dateien: [X]
- Schema-Touch: [Ja/Nein]
- Breaking Changes: [Ja/Nein]

## [ANALYSE] → Abhängigkeiten checken
- Externe APIs: [Liste]
- Interne Services: [Liste]
- Test-Abdeckung nötig: [Ja/Nein]

## [STRATEGIE] → Lösungsansatz
- Direkt umsetzbar: [Ja/Nein]
- Blueprint nötig: [Ja/Nein]

## [MODELL-VORGABE] → CU + Editor
- **CU:** [1-10]
- **Editor:** [Windsurf / Cursor / AI Studio]
- **Begründung:** [Kurze Begründung]

## [HANDOVER] → Paket erstellen
- Siehe Templates in `00_AI_STUDIO_BOOTSTRAP.md`

## [NEXT ACTION] → Loop definieren
- Loop-Schritte: [IMPL → TEST → LINTER → IMPORTS → REPORT]
- Fallback bei Fail: [Editor + CU-Adjustment]
```

### B. Kimi-Master-Prompt (Windsurf)

```markdown
# Kimi-Task: [NAME] | Status: IN_PROGRESS | CU: [1-7]

**Ziel-Editor:** Windsurf (Kimi K2.5)
**CU:** [Initial | Nach 2× Fail: CU+2]
**Kategorie:** [Bugfix / Feature / Routine]

**REFERENZEN (konkrete Pfade):**
- @backend/...
- @backend/tests/...

**AUFGABE:**
[Vollständige Modul-Lieferung: Logik + Tests + Error-Handling]

**NEXT ACTION LOOP (Pflicht V3.1):**
```
0. THINK (MCP): Max 3-5 Gedanken. Problem-Analyse + Hypothese.
1. IMPLEMENTATION: Code generieren
2. TEST: `pytest` — alle grün? ❌→Auto-Fix→Retry
3. LINTER: `ruff check .` — sauber? ❌→Auto-Fix→Retry
4. IMPORTS: Circular? Missing? Auto-fix? ❌→Report
5. DIAMOND-REPORT: Dokumentieren
```

**Wenn Fehler autonom lösbar:** Fixen, NICHT Nutzer fragen.
**Wenn 2× Fail:** CU +2 → Eskalation.

**DIAMOND-REPORT:**
- Geänderte Dateien:
- Neue Dateien:
- Tests: [Anzahl] neu / [Anzahl] updated
- Breaking Changes: Ja/Nein
- **Ressourcen-Verbrauch:**
  - Einheiten verbraucht: [X] (Cursor Fast: [XX]/50 → [XX]/50 | Pro: [XX]/50 → [XX]/50)
  - Rest-Bestand: Cursor [XX]/50 | Pro [XX]/~50 | Windsurf: Unlimitiert
- CU-Log: [Original] → [Current] (Adjustments)
```

### C. Pro-Blueprint-Prompt (AI Studio)

```markdown
# Pro-Blueprint: [NAME] | Status: IN_PROGRESS | CU: [8-10]

**Ziel-Editor:** AI Studio (Gemini Pro)
**CU:** [8-10]
**Kategorie:** Architektur

**AUSGANGSLAGE:**
[Komplexer Task, CU 8-10, Blueprint nötig]

**REFERENZEN:**
- @documentation/features/epic_...
- @backend/...

**ZIEL:**
Architektur-Blueprint erstellen für:
1. Schema-Design (Pydantic)
2. Schnittstellen-Definition
3. Implementierungs-Plan mit CU-Neubewertung

**NEXT ACTION LOOP für Pro:**
```
1. ANALYSE: Kontext vollständig?
2. STRATEGIE: Lösungsansatz definiert?
3. BLUEPRINT: Technische Spezifikation erstellt?
4. HANDOVER: Windsurf/Cursor Paket bereit?
5. DIAMOND-REPORT: Dokumentation vollständig?
```

**OUTPUT:**
- Markdown-Blueprint
- Windsurf-Handover (CU anpassen: 8-10 → 5-7 für Umsetzung)
- Cursor-Handover für UI-Teile (falls nötig)
- Registry-Update mit CU-Log
```

### D. Cursor-Fallback-Prompt

```markdown
# Cursor-Fallback: [NAME] | Status: IN_PROGRESS | CU: [Adjusted+2]

**Ziel-Editor:** Cursor (Claude Sonnet)
**CU:** [Original +2 nach 2× Kimi-Fail]
**Kategorie:** [UI-Feinschliff / Kimi-Fallback]

**VORGESCHICHTE:**
- Editor: Windsurf (Kimi K2.5)
- Versuche: 2×
- CU: [X] → [Y] (+2)

**FEHLER-LOG / BLOCKER:**
1. [Erster Fehler]
2. [Zweiter Fehler]

**PRÄZISIONS-AUFGABE:**
[Was muss Cursor anders/besser machen?]

**NEXT ACTION LOOP (Präzision):**
```
1. IMPLEMENTATION: Feinschliff / Korrektur
2. TEST: Spezifische Tests für gefailte Bereiche
3. LINTER/TYPE: Strikte Checks (keine Toleranz)
4. UI-VALIDIERUNG: Visueller Vergleich/Screenshot
5. DIAMOND-REPORT: Delta-Dokumentation
```

**DIAMOND-REPORT:**
- Delta-Änderungen:
- UI-Validierung: Erfolgt/Nötig?
- **Ressourcen-Verbrauch:**
  - Einheiten verbraucht: [X] (Cursor Fast: [XX]/50 → [XX]/50)
  - Rest-Bestand: Cursor [XX]/50 | Pro [XX]/~50 | Windsurf: Unlimitiert
- Lessons Learned für Kimi:
```

---

## 10. Migration & Quick-Check (V2.8)

- [ ] **CU-Skala** verstanden: 1-10 Rating für jeden Task
- [ ] **Adaptive Logic** aktiv: 2× Fail → CU +2 → Eskalation
- [ ] **Quota-Check** vor jedem Routing: Cursor 50/50, Pro ~50/Tag
- [ ] **DEFERRED Pool** eingerichtet für Resource-Engpässe
- [ ] **NEXT ACTION LOOP** in jedem Master-Prompt: [THINK → IMPL → TEST → LINTER → IMPORTS → REPORT]
- [ ] **Registry** hat CU-Spalte, CU-Log, und Status DEFERRED
- [ ] **Fallback-Kaskade** definiert: Kimi → Cursor → Pro → Mensch
- [ ] **Flash-Triage-Template** verwendet: [TRIAGE → ANALYSE → STRATEGIE → MODELL-VORGABE → HANDOVER → NEXT ACTION]

---

**Version:** 3.1 — Thinking-Loop Upgrade (MCP Sequential Thinking, Golden Rules, 6-Step Loop).
**Motto:** *„Think first, then build — CU decides the route, quotas manage the flow, loops ensure the quality."*
