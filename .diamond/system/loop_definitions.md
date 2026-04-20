# Diamond-OS Loop Definitions (V3.2)
# Location: .diamond/system/loop_definitions.md

## Das NEXT ACTION LOOP (V3.1 - Mit Thinking-Phase)

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
│       │                              X FAIL     │              │
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
│  │    X FAIL → Auto-Fix (1 Versuch) → Ja → IMPORTS      │    │
│  │                           Nein → LOG                  │    │
│  └───────────────────────────────┬───────────────────────┘    │
│                                  │                           │
│                                  ▼                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 4. IMPORTS                                          │    │
│  │    Circular? Missing? Auto-fix?                     │    │
│  │    X Blocker → Diamond-Report mit Log                │    │
│  │    OK → NEXT                                     │    │
│  └───────────────────────────────┬───────────────────────┘    │
│                                  │                           │
│                                  ▼                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 5. DIAMOND-REPORT                                   │    │
│  │    - Geaenderte Dateien                             │    │
│  │    - Neue Dateien                                  │    │
│  │    - Tests: X neu / Y updated                      │    │
│  │    - Breaking Changes: Ja/Nein                    │    │
│  │    - Registry-Update: CU, Status                   │    │
│  │    - CU-Adjustment-Log (falls Fail)              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Regel:** Keine Fertigmeldung ohne erfolgreichen Durchlauf des Loops.  
**Wenn Loop blockiert:** Diamond-Report mit Fehler-Log → CU +2 → Eskalation.

---

## Golden Rules of Thinking (MCP Sequential Thinking)

**Regel 1: Halte Gedanken kurz & praegnant**
- Vermeidung von Sync-Hangs bei langen Thinking-Sessions
- Max. 3-5 Gedanken pro Analyse

**Regel 2: Spaetestens bei Thought 3 muss die Loesungshypothese stehen**
- Thought 1: Problem-Analyse
- Thought 2: Root-Cause oder Strategie
- Thought 3: Loesungshypothese + Umsetzungsplan

**Regel 3: Wenn ein Gedanke > 45s dauert, breche ab und starte die Umsetzung**
- Kein "Analysis Paralysis"
- Besser iterativ implementieren als endlos planen

---

## Loop-Checkpoint Status

| Status | Bedeutung | Aktion |
|--------|-----------|--------|
| LOOP_PASS | Alle 6 Schritte erfolgreich | Task DONE |
| LOOP_RETRY | Auto-Fix laeuft (max. 1 Versuch pro Schritt) | Weiter im Loop |
| LOOP_FAIL | Blockiert → Eskalation erforderlich | CU +2, Editor-Wechsel |

---

## Step Details

### 0. THINK (MCP Sequential Thinking)
**Wann:** Vor jeder Implementierung  
**Tool:** sequential_thinking (max 3-5 thoughts)  
**Output:** Problem-Analyse + Loesungshypothese  
**Abort-Condition:** >45s pro Thought → Sofort zu IMPL

### 1. IMPL (Implementation)
**Ziel:** Code generieren/aendern  
**Input:** Aufgabenstellung + Referenzen  
**Output:** Geaenderte/neue Dateien  
**Auto-Fix:** 1 Versuch bei offensichtlichen Fehlern

### 2. TEST
**Command:** pytest / npm test / etc.  
**Erfolg:** Alle Tests gruen  
**Fail:** Auto-Fix (1 Versuch) → Retry oder LOG

### 3. LINTER
**Command:** ruff check . / mypy / eslint  
**Erfolg:** Keine Fehler/Warnings  
**Fail:** Auto-Fix (1 Versuch) → Retry oder LOG

### 4. IMPORTS
**Check:** Circular imports? Missing imports?  
**Auto-Fix:** Versuch der automatischen Korrektur  
**Blocker:** Diamond-Report mit Fehler-Log

### 5. DIAMOND-REPORT
**Inhalt:**
- Geaenderte Dateien
- Neue Dateien
- Tests: X neu / Y updated
- Breaking Changes: Ja/Nein
- Registry-Update: CU, Status
- CU-Adjustment-Log (falls Fail)

---

## Migration & Quick-Check (V3.2)

- [ ] CU-Skala verstanden: 1-10 Rating fuer jeden Task
- [ ] Adaptive Logic aktiv: 2x Fail → CU +2 → Eskalation
- [ ] Quota-Check vor jedem Routing: Cursor 50/50, Pro ~50/Tag
- [ ] DEFERRED Pool eingerichtet fuer Resource-Engpaesse
- [ ] NEXT ACTION LOOP in jedem Master-Prompt: [THINK → IMPL → TEST → LINTER → IMPORTS → REPORT]
- [ ] Registry hat CU-Spalte, CU-Log, und Status DEFERRED
- [ ] Fallback-Kaskade definiert: Kimi → Cursor → Pro → Mensch
- [ ] Flash-Triage-Template verwendet: [TRIAGE → ANALYSE → STRATEGIE → MODELL-VORGABE → HANDOVER → NEXT ACTION]
