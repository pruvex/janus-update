# Janus Development Workflow (Diamond-Standard V2.5)

**Dokument:** 05_DEVELOPMENT_WORKFLOW.md  
**Status:** Verbindliche Prozess-Regel  
**Stand:** 2026-03-29 (Zero-Inference + Token-Ökonomie)

---

## Einleitung
Dieser Workflow eliminiert KI-Fehlinterpretationen durch eine strikte Trennung von Architektur (Opus/Sonnet) und mechanischer Umsetzung (Kimi/Cursor). Ziel ist 100% Code-Integrität bei minimalen Kosten.

---

## PHASE 0: Kontext- & Request-Ökonomie (verbindlich)

**Gilt für Cursor und AI Studio.**

1. **Kein Voll-Repo-Kontext:** ` @Codebase` **nicht** standardmäßig verwenden. Stattdessen: **explizite** `@pfad/zu/datei` aus der Task-Registry oder dem Master-Prompt.
2. **Minimale Fenster:** Pro Schritt nur Dateien laden, die **direkt** geändert oder gelesen werden müssen.
3. **Macro vor Micro:** Wo möglich **ein** Agent-Durchlauf pro Meilenstein (siehe `documentation/00_AI_STUDIO_BOOTSTRAP.md` V3.1), damit nicht jeder Kleinst-Fix einen neuen Cursor-Request auslöst.
4. **First-Time-Right im Agent:** Der ausführende Agent (Cursor) **behebt** Lint-, Test- und Importfehler **selbstständig** innerhalb derselben Session, **bevor** das Ergebnis als „fertig“ gemeldet wird. Rückfragen an den Nutzer nur bei **echter** Blockade (Schema-Lock, unklare Produktentscheidung, fehlende Credentials).

---

## PHASE 1 - 3: Design & Task-Definition (AI Studio)
*   **Regel:** Jede Task-Datei (`documentation/tasks/`) muss **atomare Code-Blöcke** enthalten. 
*   **Verbot:** Es dürfen keine vagen Anweisungen wie "Optimiere den Renderer" gegeben werden. 
*   **Pflicht:** Exakte Regex-Strings, Pfade und Block-Inhalte müssen vordefiniert sein.

---

## PHASE 4: Core Implementation (Opus/Sonnet)
Das High-Tier-Modell liefert den **Referenz-Code**. Dieser Code ist das Gesetz für Phase 5.

---

## PHASE 5: Testing, Debugging & Strikte Validierung (Agent)

### 5.1 Der Modus Operandi (Zero-Inference)
Für den ausführenden Agenten (Kimi/Cursor) gelten folgende eiserne Regeln:
1.  **Schema-Integrität (Diamond-Lock):** Es ist strengstens verboten, neue Keys, Enums oder Block-Typen in Pydantic-Modellen zu erfinden. Änderungen müssen gegen `backend/data/schemas.py` und `backend/services/prompting/core/model.py` validiert werden.
2.  **Self-Correction vor Übergabe:** Syntax-, Test-, Linter- und Importfehler **selbst** in derselben Session beheben, **bevor** „Bereit für UI-Check“ gemeldet wird. Jeder zusätzliche „bitte fixen“-Chat durch den Nutzer kostet Cursor-Pro-Budget.
3.  **Kein "Silent Completion":** Ein Task darf in Sektion 6 & 7 erst dann als `[✅ Done]` markiert werden, wenn der Mensch (Product Owner) das Ergebnis im UI geprüft und mit dem Befehl **"UI-VALIDIERT"** freigegeben hat.
4.  **Fehler-Eskalation:** Wenn ein Fix nach **3 Iterationen** nicht zum Erfolg führt oder Schema-Fehler (`ValidationError`) auftreten, muss der Agent sofort stoppen und das AI Studio um einen neuen atomaren Code-Block bitten.

### 5.2 Der Validierungs-Loop
1.  **Agent:** Implementiert Code exakt nach Vorlage.
2.  **Agent:** Führt `pytest` aus.
3.  **Agent:** Meldet "Bereit für UI-Check".
4.  **Mensch:** Testet im UI.
5.  **Mensch:** Gibt "UI-VALIDIERT" oder "REJECTED" (mit Log).
6.  **Agent:** Schließt Dokumentation (Sektion 6 & 7) erst nach "UI-VALIDIERT" ab.

---

## Audit-Trail & Qualitäts-Gates

| Gate | Kriterium | Verantwortlich |
|------|-------------|----------------|
| G1 | Atomarer Umsetzungsplan (0% Interpretationsspielraum) | AI Studio |
| G2 | Code-Referenz durch High-Tier Modell (Opus/Sonnet) | Opus / Sonnet |
| G3 | Alle Unit-Tests passing | Agent (Kimi/Cursor) |
| G4 | **Menschliches UI-Sign-off ("UI-VALIDIERT")** | Mensch |
| G5 | Abschluss-Dokumentation & Inventar-Update | Agent (Kimi/Cursor) |

---

## Cascade Skills (Diamond-Flow Automation)

Die folgenden Slash-Commands in Windsurf Cascade automatisieren Routineschritte:

| Skill | Aufruf | Wann |
|-------|--------|------|
| Task erstellen | `/task-setup` | Zu Beginn jedes neuen Tasks |
| Pre-Check | `/pre-check` | Vor jeder Implementierung (Phase 4.0) |
| Post-Implementation | `/post-impl` | Nach Implementierung (füllt Audit-Trail, aktualisiert PROJECT_STATE + Inventory) |
| Session-Start | `/session-start` | Zu Beginn jeder neuen Session/Thread |
| Opus-Audit vorbereiten | `/opus-audit` | Vor jedem Claude-Audit (erstellt Scope-Block) |

**Regel:** Flash-Guard MUSS im Handover den passenden Skill-Aufruf als NEXT ACTION vorgeben (siehe AI_STUDIO_SYSTEM_PROMPT Sektion 10).

*Workflow aktualisiert am 07.04.2026. Skills-Integration hinzugefügt. Fokus: Elimination von Agenten-Halluzinationen, Token-Ökonomie, Self-Correction vor Übergabe.*