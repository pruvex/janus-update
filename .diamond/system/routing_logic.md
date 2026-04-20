# Diamond-OS Routing Logic (V3.2)
# Location: .diamond/system/routing_logic.md

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

## 3. Task-Pooling & Quota-Management

### 3.1 Active Pool (Standard-Verarbeitung)

Tasks mit Status: `TODO` → `IN_PROGRESS` → `DONE`

**Flow mit NEXT ACTION LOOP:**
```
Task-Creation → CU-Schätzung → Quota-Check → Editor-Zuweisung → NEXT ACTION LOOP → DONE
```

### 3.2 DEFERRED Pool (Quota-Warteschlange)

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

### 3.3 Adaptive CU Adjustment (Auto-Eskalation)

**Trigger:** Task scheitert 2× im selben Editor

| Original CU | Datum | Task-ID | CU | Editor | Tokens | %-Kosten | Est. € | Notiz |
|-------|---------|----|--------|--------|----------|--------|-------|
| 2026-03-31 | SYS-V3.3-HEALTH-CHECK | 5 | Cursor | 2,5M | 4% | 0,80 € | Baseline fuer Audit |
| 6-8 | Cursor oder Pro | Kimi → Pro-Check → Cursor |
| 7-8 | 9-10 | Pro → Cursor | Kimi → Pro-Blueprint → Cursor-UI |

**Registry-Update bei CU-Adjustment:**
```markdown
| Task-ID | CU | CU-Log | Status | App |
|---------|----|--------|--------|-----|
| M-FEAT-12 | 6 | 4→6 (+2 nach Fail#2) | IN_PROGRESS | Cursor |
```

---

## 4. Eskalations-Matrix V2.8 (Adaptive)

| CU | Initial-Routing | Bei 1× Fail | Bei 2× Fail (CU +2) |
|----|-----------------|-------------|---------------------|
| **1-3** | Windsurf/Kimi | Auto-Fix, retry | Cursor |
| **4-6** | Windsurf/Kimi | Auto-Fix, retry | Cursor oder Pro-Check |
| **7-8** | Windsurf/Kimi | Cursor-Check | Gemini Pro + Cursor |
| **9-10** | Gemini Pro → Windsurf | Cursor für UI-Teile | Menschliche Review |

**Wichtig:** Adaptive CU-Logik aktiviert sich **automatisch** bei wiederholtem Fail.

---

## [COST_PREDICTION_MATRIX] (V3.3 - Prädiktiv)
**Basis:** Audit-Daten (CU 5 = 4% Cursor-Budget / 2.5M Tokens)

| CU-Range | Geschätzter Verbrauch | Impact-Level | Empfohlene Reserve |
|----------|----------------------|--------------|-------------------|
| **CU 1-3** | ~0.1% - 0.5% Cursor-Budget | Low Impact | 1% |
| **CU 4-6** | ~1% - 5% Cursor-Budget | Standard Impact | 5-10% |
| **CU 7-8** | ~5% - 10% Cursor-Budget | High Impact | 15% |
| **CU 9-10** | > 10% Cursor-Budget | Architektur-Deep-Dive | 20%+ |

**Berechnungsformel:**
```
Predicted % = (CU / 5) × 4% × Komplexitäts-Faktor(1.0-2.0)
```

**Beispiele:**
- CU 2 (Simple Task): (2/5) × 4% × 0.5 = ~0.8%
- CU 5 (Audit-Referenz): (5/5) × 4% × 1.0 = 4% ✓
- CU 8 (Complex): (8/5) × 4% × 1.5 = ~9.6%

---

## [FINANCIAL_DECISION_MATRIX] (V3.3 - Euro-Basiert)
**Budget-Basis:** Windsurf (€ 15/Monat) | Cursor (€ 20/Monat)

### TCT-Formel (Total Cost of Task)
```
TCT = (Modell-Kosten in €) + (Risiko-Aufschlag bei CU > 6)
Risiko-Aufschlag = 20% der Modell-Kosten (nur wenn CU > 6)
```

### Euro-Kalkulation (Flash-Guard Ready)
| Einheit | Cursor (€20/Monat) | Windsurf (€15/Monat) |
|---------|-------------------|---------------------|
| **1% Monthly** | 0,20 € | 0,15 € |
| **1% Daily** | 0,0067 € | 0,005 € |
| **1% Weekly** | 0,05 € | 0,0375 € |

### Quick-Calc für Triage
```
Cursor:    %-Wert × 0,20 € = €-Kosten
Windsurf:  Daily% × 0,005 € = €-Kosten
           Weekly% × 0,0375 € = €-Kosten
```

**Test-Rechnung:**
- 10% Daily Windsurf = 10 × 0,005 € = **0,05 €** ✓
- 4% Monthly Cursor = 4 × 0,20 € = **0,80 €** (Audit-Baseline) ✓
- CU 8 + Risiko-Aufschlag: 9,6% Cursor = 9,6 × 0,20 € × 1,2 = **2,30 €**

---

### Dynamische Kostenformeln (Modell-unabhängig)

**Cursor (Monthly Subscription $20 / ~18 €):**
```
€-Kosten = (Used_% / 100) × 18 €
Beispiel: 4% verwendet = 0,04 × 18 € = 0,72 €
```

**Windsurf (Monthly Subscription $15 / ~13,50 €):**
```
Daily:  €-Kosten = (Daily_% / 100) × (13,50 € / 30 Tage)
        = (Daily_% / 100) × 0,45 €
        
Weekly: €-Kosten = (Weekly_% / 100) × (13,50 € / 4 Wochen)
        = (Weekly_% / 100) × 3,375 €
```

**Vergleichs-Baseline:**
- 10% Daily Windsurf = 0,045 €
- 4% Monthly Cursor = 0,72 €

---

## [MODEL_EFFICIENCY_RATINGS]
**Zweck:** Dokumentation, welches Modell (GPT vs. Claude vs. Kimi) in welcher IDE (Cursor vs. Windsurf) für welche Tags die höchste Effizienz (Erfolg/Kosten) aufweist.

| Tag | Bestes Modell | Beste IDE | Effizienz-Score | Begründung |
|-----|---------------|-----------|-----------------|------------|
| #Setup | [TBD] | [TBD] | [TBD] | [Ergebnis aus Benchmark] |
| #UI | [TBD] | [TBD] | [TBD] | [Ergebnis aus Benchmark] |
| #Logic | [TBD] | [TBD] | [TBD] | [Ergebnis aus Benchmark] |
| #API | [TBD] | [TBD] | [TBD] | [Ergebnis aus Benchmark] |
| #SequentialThinking | [TBD] | [TBD] | [TBD] | [Ergebnis aus Benchmark] |

**Effizienz-Score-Berechnung:**
```
Score = Success_Rate / €-Kosten_pro_Task
```

**Legend:**
- [TBD] = To Be Determined (nach ausreichend Benchmark-Daten)
- Baseline-Aufnahme pro Tag: Min. 3 Tasks mit gleichem Tag für statistische Signifikanz

---

## [BENCHMARK_PRIORITY_RULE] (V3.3 - Autonomes A/B)
**Regel:** Solange ein Tag in der GAP-Matrix als [FEHLT] markiert ist, hat das Schließen der Datenlücke Vorrang vor der Standard-Editor-Wahl (A/B-Testing Modus), sofern die Quota dies zulässt.

**Prioritäts-Logik:**
1. Prüfe Gap-Analysis Matrix auf "FEHLT"-Einträge
2. Wenn aktueller Task-Tag = FEHLT → Priorisiere alternativen Editor
3. Nur wenn Quota < 10% → Fallback auf Standard-Präferenz

**Beispiel:**
- Task mit Tag #UI kommt rein
- Gap-Analysis: #UI bei Windsurf = FEHLT
- Cursor-Quota: OK (> 10%)
→ **Routing: Windsurf** (Lücken-Schließung priorisiert)

---

## 5. Status-Keywords (Registry / Dashboard)

| Status | Bedeutung | Verwendung |
|--------|-----------|------------|
| **TODO** | Wartet auf Flash-Triage | Initial nach Task-Creation |
| **IN_PROGRESS** | Bearbeitung läuft | Nach Editor-Zuweisung |
| **DONE** | Loop erfolgreich | Nach DIAMOND-REPORT |
| **DEFERRED** | Quota-Block / Resource-Engpass | Wartet auf Freigabe |
| **UI-VALIDIERT** | Menschliche UI-Abnahme | Nach Cursor-UI-Work |
| **LOOP_FAIL** | NEXT ACTION LOOP blockiert | CU +2, Eskalation |

---

## 6. Registry-Integration

Jeder Task MUSS in `PROJECT_STATE.md` (Registry-Section) mit:
- **CU:** [1-10] — Initial vom Flash geschätzt
- **CU-Log:** [Verlauf bei Adjustments, z.B. "4→6 (+2 nach Fail#2)"]
- **Status:** TODO | IN_PROGRESS | DONE | **DEFERRED** | UI-VALIDIERT
- **App:** Windsurf | Cursor | AI Studio | **WAITING**
- **Loop-Status:** LOOP_PASS | LOOP_RETRY | **LOOP_FAIL** (bei Eskalation)
