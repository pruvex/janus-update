JANUS FEATURE SPEC – DIAMANTSTANDARD v2
1. FEATURE NAME

Capability Overview Response

2. CORE IDEA

Dieses Feature ermöglicht es Janus, auf explizite Nutzeranfragen wie „Was kannst du?“ eine vollständige, strukturierte und verständliche Übersicht aller aktuell verfügbaren Fähigkeiten auszugeben.
Die Ausgabe basiert ausschließlich auf der validierten Capability Registry und zeigt nur verifizierte, stabile Fähigkeiten.
Die Darstellung ist kategorisiert, deterministisch sortiert und enthält pro Fähigkeit eine kurze, nutzerverständliche Erklärung.

3. USER PROBLEM & VALUE

Problem:
Nutzer wissen nicht, welche Fähigkeiten Janus aktuell besitzt oder wie sie diese nutzen können.

Value:

Klare Transparenz über Systemfähigkeiten
Reduzierte Unsicherheit und Fehlbedienung
Schnellere Einarbeitung neuer Nutzer
Höheres Vertrauen durch konsistente und verlässliche Aussagen
4. FUNCTIONAL CORE
Erkennung von Nutzeranfragen nach Systemfähigkeiten („Was kannst du?“)
Laden der Capability Registry als Single Source of Truth
Filtern von Capabilities nach:
status = verified
confidence ≥ 0.7
Gruppierung der Capabilities nach Kategorie
Sortierung in fester, deterministischer Reihenfolge
Generierung einer strukturierten Antwort:
Kategorieüberschriften
Capability + kurze Erklärung
Ausgabe an den Nutzer
Fallback-Antwort, wenn keine gültigen Capabilities vorhanden sind
5. SYSTEM BEHAVIOR
Trigger
Nutzer stellt explizite Anfrage nach Fähigkeiten
Flow
Input wird analysiert (Intent: Capability Overview)
System lädt capability_registry.json
Filter:
nur verified
nur confidence ≥ 0.7
Falls Ergebnis leer:
→ Fallback-Antwort ausgeben
Sonst:
Gruppieren nach Kategorien
Sortieren nach definierter Reihenfolge

Formatieren:

Kategorie:
- Fähigkeit: Erklärung
Ausgabe an Nutzer
6. EDGE CASES / FAILURE BEHAVIOR
Registry fehlt → Fehler + sichere Fallback-Antwort
Registry leer → Fallback-Antwort
Capabilities ohne Beschreibung → werden übersprungen
Ungültige Datenstruktur → defensive Validierung + Fallback
Keine Capabilities nach Filter → definierter Hinweistext
Doppelte Einträge → deduplizieren nach ID
Unbekannte Kategorien → in „Sonstiges“ einsortieren
7. CONSTRAINTS / LIMITS
Keine Anzeige von:
nicht verifizierten Capabilities
Capabilities mit confidence < 0.7
Keine technischen Details (Tasks, IPC, Dateien etc.) in UX
Keine dynamische Sortierung
Keine Interpretation außerhalb der Registry
Output muss deterministisch sein
Keine Seiteneffekte im System
8. INTEGRATION CONTEXT

Interne Module:

Capability Registry (backend/data/capability_registry.json)
Capability Trust Layer
Intent Detection / Input Parser
Response Generator / UI Layer

Datenfluss:
User Input → Intent Detection → Registry → Filter → Format → Output

9. COMPLEXITY LEVEL

medium

10. TEST STRATEGY REQUIREMENT
Unit Tests
Filterlogik (status + confidence)
Gruppierung
Sortierung
Deduplication
Integration Tests
Registry Laden + Parsing
End-to-End Datenfluss (Input → Output Struktur)
E2E Tests (MANDATORY)
User fragt: „Was kannst du?“
System gibt korrekt strukturierte Liste aus
Fallback-Szenario testen
State / Consistency Tests
Registry Änderungen → Output korrekt reflektiert
Trust Layer wirkt korrekt auf Output
AI / Behavior Tests
Intent wird korrekt erkannt
Output entspricht UX-Vorgaben
HARTE TESTREGELN
Mindestens 1 echter E2E Flow
Kein vollständiges Mocking der Registry
Tests validieren Output-Struktur und Inhalt
11. DEFINITION OF DONE
Capability Output ist korrekt strukturiert
Nur valide Capabilities werden angezeigt
Fallback funktioniert deterministisch
E2E Test besteht stabil
Keine inkonsistenten oder falschen Aussagen
12. OPEN QUESTIONS

None

13. IMPLEMENTATION CONTRACT
13.1 TASK GENERATION RULES
Jede Funktion wird als eigener Task modelliert
Kein Task enthält mehrere Ziele
Keine impliziten Entscheidungen
13.2 TASK STRUKTUR

Alle Tasks folgen strikt:

eindeutiges Ziel
klarer Input
deterministischer Output
konkrete Steps
feste Dateien
klare Tests
13.3 AGENT RULES
Keine Interpretation erlaubt
Keine Erweiterung des Features
Nur Umsetzung der Spec
13.4 EXECUTION GUARANTEE
Tasks sind vollständig abgeleitet
Keine offenen Entscheidungen
Deterministische Ausführung möglich
14. IMPLEMENTATION OUTPUT REQUIREMENT

Dieser Spec ermöglicht:

GPT-5.5 → vollständige Planung
Windsurf → deterministische Task-Generierung
SWE/Kimi → direkte Implementierung
Orchestrator → saubere Ausführung
15. SYSTEM GOAL

Maximale Transparenz der Systemfähigkeiten bei vollständiger Wahrheitskonsistenz.

🧠 EIN-SATZ-DEFINITION

Dieses Feature ist die deterministische, vertrauensbasierte Selbstdarstellung der Fähigkeiten von Janus.

---

**→ Modified by** `documentation/tasks/task_069_capability_overview_response_diamond_plan.md` **(TASK-069):** Umsetzung abgeschlossen — Help Fast-Path, Registry-Filter (`verified` / `confidence ≥ 0.7`), deterministischer Markdown-Output, Playwright E2E; Final Audit: PASS WITH FIXES.