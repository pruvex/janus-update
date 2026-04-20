# Diamond-OS Handover Templates (V3.2)
# Location: .diamond/system/handover_templates.md

## A. Windsurf-Handover (CU 1-7)

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

**3. NEXT ACTION LOOP (Pflicht V3.1):**
```
0. THINK (MCP): Max. 3-5 Gedanken. Problem-Analyse + Hypothese.
1. IMPL: Code generieren
2. TEST: `pytest` — alle grün? ❌→Auto-Fix→Retry
3. LINTER: `ruff check .` — sauber? ❌→Auto-Fix→Retry
4. IMPORTS: Circular? Missing? Auto-fix? ❌→Report
5. DIAMOND-REPORT: Dokumentieren
```

**4. Akzeptanzkriterien**
- [ ] Feature funktioniert laut SPEC
- [ ] Tests passen zu Implementation
- [ ] Lint/Type-Check sauber

**5. Fallback-Plan**
Wenn 2× Fail → CU +2 → Eskalation zu [Cursor/Pro]
```

---

## B. Pro-Blueprint-Handover (CU 8-10)

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

---

## C. Cursor-Fallback-Handover (CU angepasst)

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

**5. DIAMOND-REPORT (mit TELEMETRIE-PFLICHT V3.3):**
- Delta-Änderungen:
- UI-Validierung: Erfolgt/Nötig?
- **TELEMETRIE-PFLICHT:**
  - Tokens verbraucht: [Anzahl]
  - API-Kosten: [X] %
  - Restguthaben: [X] %
- Lessons Learned für Kimi:
```

---

## D. Flash-Triage-Template (AI Studio)

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
- Siehe Templates in `.diamond/system/handover_templates.md`

## [NEXT ACTION] → Loop definieren
- Loop-Schritte: [THINK → IMPL → TEST → LINTER → IMPORTS → REPORT]
- Fallback bei Fail: [Editor + CU-Adjustment]
```

---

## E. Kimi-Master-Prompt (Windsurf)

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
- **REPORT-PFLICHT (V3.3):**
  - Wieviel % der Daily/Weekly Quota hat dieser Task verbraucht? (Schätzung/Anzeige in IDE)
- CU-Log: [Original] → [Current] (Adjustments)
```

---

## F. Pro-Blueprint-Prompt (AI Studio)

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

---

## G. Cursor-Fallback-Prompt

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
- **TELEMETRIE-PFLICHT (V3.3):**
  - Tokens verbraucht: [Anzahl]
  - API-Kosten: [X] %
  - Restguthaben: [X] %
- Lessons Learned für Kimi:
```
