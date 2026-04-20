## Modell-Referenz & Kosten-Matrix

*Preise **Orientierung** gemäß Cursor-/Provider-Dokumentation; **Stand: 28.03.2026**. Abweichende oder aktualisierte Sätze im jeweiligen Dashboard (Cursor, API-Anbieter) haben Vorrang.*

| Modell | Input ($/M) | Output ($/M) | Kategorie |
| :--- | :--- | :--- | :--- |
| **Claude 4.6 Opus** | 5 | 25 | Flagship Reasoning |
| **Claude 4.6 Sonnet** | 3 | 15 | Balance (Code/Reasoning) |
| **Claude 4.5 Opus** | 5 | 25 | Flagship Reasoning |
| **Claude 4.5 Haiku** | 1 | 5 | Speed/Efficiency |
| **Gemini 3 Pro** | 2 | 12 | Large Context Reasoning |
| **Gemini 3 Flash** | 0.5 | 3 | High-Volume |
| **GPT-5.4** | 2.5 | 15 | General Coding |
| **GPT-5.4 Nano** | 0.2 | 1.25 | Ultra-Low Cost |
| **Composer 2** | 0.5 | 2.5 | Agentic Coding |
| **Kimi K2.5** | 0.6 | 3 | Specialized |

**Modell-Fallback:** Ist **Kimi K2.5** im gewählten Tool nicht verfügbar, **gleiche Aufgabe** mit **Gemini 3 Flash** ausführen (gleiche Rolle: günstig, hoher Durchsatz).

---

## Meta & Versionierung

- **Dokument-Version:** 1.4 (Stand: 28.03.2026)
- **Framework-Standard:** Diamond-Standard V2.1
- **Status:** Phase 1 & 2 Abgeschlossen.

**Versionen entwirren:** **Dokument-Version** (z. B. 1.4) zählt **Änderungen an dieser Datei** (Task 1.1–1.3, Meta). **Diamond-Standard V2.1** ist das **Framework-/Marketing-Label** für den Gesamtstand des Janus-OS (Rules, Skripte, Studio-Prompt) — nicht jede Textänderung hier erhöht automatisch V2.x.

---

## Task 1.1: Dynamischer Tages-Planungs-Workflow

## Arbeits-Standard: Diamond Standard V1.2 (Optimiert)

*Diese Vorlage enthält Escalation-Rules, Confidence-Level und differenzierte Iterationslimits. Ziel: Maximale Qualität bei minimalen Kosten und null Chaos-Iteration.*

> ### 💡 DIE DIAMOND-ELASTIZITÄTS-REGEL (V1.4)
> - **Standard:** "No Code without Plan". Jede Änderung erfordert eine Task-Datei.
> - **5-Minuten-Ausnahme:** Trivial-Änderungen (Tippfehler, Linter, < 5 Min) dürfen OHNE Task-Datei in Cursor (Mini/Composer) durchgeführt werden, sofern der Kontext bereits geladen ist.
> - **Escalation:** Schlägt der Trivial-Fix fehl oder dauert er länger als 5 Min -> SOFORTIGER STOPP -> Task-Datei via `node scripts/auto_fill_task.js` anlegen -> Strategie im AI Studio (Janus) klären.

---

### [Titel des Aufgabenbereichs]
- **Klassifizierung:** [Hard-Stop / Flow-Task]
- **Ort:** [AI Studio / Cursor]
- **Optimale Modell-Prio:** [Modell A -> Modell B -> Modell C]
- **Strategie bei Ressourcen-Engpass:** [Verschieben / Switch / Upgrade / Downgrade]
- **Confidence-Level:** [Hoch / Mittel / Niedrig]
- **Escalation-Rule:** [Max X Iterationen → STOP → Zurück ins AI Studio]
- **Dokumentations-Bedarf:** [Minimal / Mittel / Hoch]

---

## A. Planung & Architektur
*Strategische Entscheidungen – niemals kompromittieren.*

- **A1. Feature-Ideen:**  
  [Flow-Task | Ort: AI Studio | Prio: Gemini 3 Flash -> Gemini 3 Pro | Strategy: Upgrade bei guten Ideen | Conf: Mittel | Escalation: 3 Iterationen | Doku: Minimal]

- **A2. Architektur:**  
  [Hard-Stop | Ort: AI Studio | Prio: Claude 4.6 Sonnet -> Gemini 3 Pro | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

- **A3. Architektur-Review:**  
  [Hard-Stop | Ort: AI Studio | Prio: Gemini 3 Pro -> Claude 4.6 Opus | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Mittel]

---

## B. Struktur & Spezifikation
*Bindeglied zwischen Idee und Code.*

- **B4. Umsetzungsplan:**  
  [Flow-Task | Ort: AI Studio | Prio: Gemini 3 Pro -> Gemini 3 Flash | Strategy: Switch | Conf: Mittel | Escalation: 3 Iterationen | Doku: Mittel]

- **B5. Skill-Spezifikation:**  
  [Flow-Task | Ort: AI Studio | Prio: Gemini 3 Pro -> Gemini 3 Flash | Strategy: Switch | Conf: Hoch | Escalation: 3 Iterationen | Doku: Hoch]

- **B6. Schema-Design:**  
  [Hard-Stop | Ort: AI Studio (Design) -> Cursor (Implementierung) | Prio: Claude 4.6 Sonnet | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

---

## C. Implementierung
*Operative Phase – kontrollierte Ausführung.*

- **C7. Code-Generierung:**  
  [Flow-Task | Ort: Cursor | Prio: Composer 2 -> Claude 4.6 Sonnet | Strategy: Upgrade bei Komplexität | Conf: Mittel | Escalation: 3 Iterationen | Doku: Minimal]

- **C8. Code-Refactoring:**  
  [Hard-Stop | Ort: Cursor | Prio: Claude 4.6 Sonnet | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

- **C9. Boilerplate-Code:**  
  [Flow-Task | Ort: Cursor | Prio: GPT-5.4 Nano -> Composer 2 | Strategy: Switch | Conf: Niedrig | Escalation: 5 Iterationen | Doku: Keiner]

---

## D. Debugging & Fehleranalyse
*Strikte Trennung: Denken vs. Ausführen.*

- **D10. Log-Analyse:**  
  [Hard-Stop | Ort: AI Studio | Prio: Gemini 3 Pro -> Claude 4.6 Opus | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

- **D11. Bugfix-Strategie:**  
  [Hard-Stop | Ort: AI Studio | Prio: Gemini 3 Pro | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

- **D12. Fix-Anweisung:**  
  [Flow-Task | Ort: AI Studio | Prio: Gemini 3 Flash -> Gemini 3 Pro | Strategy: Upgrade bei kritischen Bugs | Conf: Mittel | Escalation: 3 Iterationen | Doku: Mittel]

---

## E. Testing & Qualität
*Stabilität absichern – nicht unterschätzen.*

- **E13. Testfälle:**  
  [Flow-Task | Ort: Cursor | Prio: GPT-5.4 Nano -> Composer 2 -> Gemini 3 Pro (Review) | Strategy: Upgrade bei kritischen Tests | Conf: Mittel | Escalation: 5 Iterationen | Doku: Minimal]

- **E14. Testauswertung:**  
  [Flow-Task | Ort: AI Studio | Prio: Gemini 3 Flash -> Kimi K2.5 (Fallback: Gemini 3 Flash) | Strategy: Switch | Conf: Mittel | Escalation: 3 Iterationen | Doku: Mittel]

---

## F. Integration & Orchestrierung
*System zusammenführen – hohe Sensibilität.*

- **F15. Skill-Integration:**  
  [Hard-Stop | Ort: Cursor | Prio: Claude 4.6 Sonnet | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

- **F16. Abhängigkeitsanalyse:**  
  [Hard-Stop | Ort: AI Studio | Prio: Gemini 3 Pro | Strategy: Verschieben | Conf: Hoch | Escalation: 2 Iterationen | Doku: Hoch]

---

## G. Dokumentation & Optimierung
*Wissen sichern und skalierbar machen.*

- **G17. Wissen & Logs:**  
  [Flow-Task | Ort: AI Studio | Prio: Gemini 3 Flash -> Kimi K2.5 (Fallback: Gemini 3 Flash) | Strategy: Switch | Conf: Mittel | Escalation: 5 Iterationen | Doku: Mittel]

---

## Task 1.2: Pacing-Logik & Kontingent-Management (Audit V1.3)
*Systematische Ressourcen-Steuerung zur Vermeidung von Stillstand. Gehört zur **Dokumentversion 1.4** (siehe Abschnitt „Meta & Versionierung“).*

### 1. Morning Briefing
- Analyse der geplanten Tasks (A-G).
- Prio-Klassifizierung: A (Kritisch/Architektur), B (Wichtig/Spec), C (Optional/Tests/Doku).
- Kalkulation des Pro-Bedarfs.
- Auswahl eines realistischen Tages-Scope basierend auf Budget und Priorität.

---

### 2. Daily Budget Control
- **Hard Cap:** Maximal 70% des Pro-Kontingents pro Tag verplanen.
- **Reserve:** 30% zwingend für ungeplante Debugging-Tasks (Hard-Stops) freihalten.

**Definition „Pro-Kontingent“ (Cursor Pro):** Bezug ist der im **[Cursor Usage-Dashboard](https://cursor.com/dashboard/usage)** sichtbare Verbrauch bzw. Rest im **laufenden Abrechnungszeitraum** (typisch monatlich; Reset-Datum unter „Manage Subscription“ / Billing prüfen). Die **70 %-Tagesplanung** bezieht sich auf den **für geplante Arbeit** vorgesehenen Anteil der **in Cursor Pro inkludierten** Nutzung (insb. API-Pool und realistisch eingeplante Auto-/Composer-Nutzung), **nicht** auf kostenlose AI-Studio-Nutzung oder andere Tools. Die **30 %-Reserve** ist für **ungeplante** Hard-Stops, Eskalationen und Debugging reserviert.

---

### 3. Pacing & Slicing
- Hard-Stops über den Arbeitstag verteilen (keine Bündelung morgens).
- **Micro-Slicing:** Nur bei logisch trennbaren Tasks, sofern Architektur-Integrität (Schema-Design) gewahrt bleibt.

---

### 4. Pro Usage Trigger (Wann darf Pro genutzt werden?)
- Nur wenn Task = Hard-Stop.
- Oder bei hoher Confidence-Anforderung.
- Oder als Escalation nach 3 fehlgeschlagenen Iterationen (Fix-Versuchen).
- Nach Escalation: Übergabe an AI Studio zur Analyse und Neu-Strategie.
- Keine wiederholten Versuche mit demselben Modell nach Fehlschlag (immer eskalieren).

---
## Task 1.3: Diamond Documentation & Automation Protocol (Audit V1.4)
*Die technische Infrastruktur zur Durchsetzung des Workflows (Enforced by Cursor Rules 01-04).*

### 1. Das Task-Container-Prinzip
- Jede Arbeitseinheit benötigt zwingend eine Datei in `documentation/tasks/task_XXX.md`.
- **Audit-Trail:** Jede Task-Datei führt einen tabellarischen Log (Datum, Status, Änderung). Cursor-Rule `01_task_protection` überwacht dies.

### 2. Die Automatisierungs-Werkbank
- **Creation-Script:** `node scripts/auto_fill_task.js "[Taskname]"` (Erzeugt Task-Dateien aus `.cursor/templates/diamond_task_template.mdc`).
- **Integrity-Checker:** `bash scripts/diamond_check.sh` (Prüft vor Abschluss die Existenz von Tasks, Audit-Trails und Lessons Learned).

### 3. Der Lern-Loop (Rule: 02_learning_loop)
- Wissen wird atomar in `docs/lessons_learned.md` gesichert.
- Janus (AI Studio) extrahiert Lessons; Cursor integriert sie proaktiv via `@-Referenz`.

### 4. Definition of Done (Rule: 04_completion_gate)
Vollständige Kriterien siehe `.cursor/rules/04_completion_gate.mdc`. Kurzfassung — ein Task gilt erst als „Done“, wenn:
1. Tests grün sind (Linter/Units).
2. Dokumentation aktuell: Task-Audit-Trail und **Haupt-README.md** (siehe Regel 04).
3. Relevante Lessons in `docs/lessons_learned.md` eingetragen.
4. Der `diamond_check.sh` fehlerfrei durchläuft (wo vorgesehen; Windows: Git Bash/WSL).