JANUS FEATURE SPEC – DIAMANTSTANDARD v2

(FINAL, EXECUTION-GRADE – COPY-PASTE READY)

1. FEATURE NAME

Janus Source Routing Engine

2. CORE IDEA

Das Feature definiert ein deterministisches Informations-Routing-System für Janus, das jede Nutzeranfrage über eine strikt regelbasierte Pipeline verarbeitet. Informationen werden dabei abhängig von Datentyp und Kontext aus fest definierten Quellen (APIs, Websearch, RSS etc.) bezogen. Ziel ist maximale Konsistenz, Nachvollziehbarkeit und Testbarkeit aller Antworten durch eine zentral gesteuerte Source Policy mit kontrollierten Fallbacks und Transparenzpflicht.

3. USER PROBLEM & VALUE

Problem:
Informationsquellen werden aktuell inkonsistent gewählt (API, Wiki, Websearch gemischt ohne klare Priorität).

Value:

reproduzierbare Antworten
klare Herkunft jeder Information
reduzierte Halluzinationen
testbare AI-Entscheidungen (QA/E2E-fähig)
kontrollierbare Datenqualität im gesamten System
4. FUNCTIONAL CORE
Klassifikation jeder Anfrage in feste Intent-Kategorien
Mapping von Datentyp → primäre Datenquelle
Anwendung einer zentralen Source Policy
Kontextbasierte Priorisierung bei Konflikten
Ausführung einer strikt linearen Pipeline
automatisierter Fallback bei fehlenden Daten (regelbasiert)
vollständige Quellenanzeige pro Antwort
synthetisierte Antwort mit separatem Quellenblock
deterministische Fehlerbehandlung (kein Best-Effort-Modus)
5. SYSTEM BEHAVIOR
Execution Pipeline (strict linear)
Input Parsing
Intent Classification (fixed categories)
Datentyp Mapping
Context Assignment
Source Selection (Source Policy Engine)
Data Retrieval (API / Web / RSS etc.)
Conflict Resolution (context-based priority rules)
Fallback Execution (if required)
Response Composition (synthetic answer)
Source Logging & Output
Kontextverhalten
Kontext beeinflusst Priorität, aber nur regelbasiert
keine freien LLM-Entscheidungen erlaubt
nur definierte Kategorien (z. B. statisch / aktuell / lokal / zeitkritisch)
6. EDGE CASES / FAILURE BEHAVIOR
API failure → Fallback-Quelle gemäß Regelwerk
Websearch failure → nächste definierte Quelle
keine Quelle verfügbar → HARD FAIL
Ausgabe: „Keine verlässlichen Daten verfügbar“
widersprüchliche Daten:
Auflösung via kontextbasierter Prioritätsregel
ungültige Anfrage:
kein synthetischer Ersatz erlaubt
7. CONSTRAINTS / LIMITS
jede Antwort MUSS Quellen enthalten
jede Anfrage MUSS durch Pipeline laufen
keine LLM-basierte freie Quellenwahl
keine impliziten Entscheidungen im System erlaubt
Overrides nur über explizite Regeln
keine Änderung bestehender Regeln (nur additive Erweiterung)
keine Best-Effort Antworten bei fehlenden Daten
8. INTEGRATION CONTEXT
Interne Module
system.weather (Open-Meteo)
system.routing (OSRM)
system.country_info (REST Countries API)
system.websearch
RSS Feed Aggregator
Wikipedia Skill Layer
OpenStreetMap Service Layer
Externe APIs
REST Countries API
Open-Meteo API
OSRM Routing API
Wikipedia API
RSS Feeds (Spiegel, Tagesschau, Reuters etc.)
Websearch Provider (Gemini / Web Layer)
9. COMPLEXITY LEVEL

system-critical

10. TEST STRATEGY REQUIREMENT (MANDATORY)

Dieses Feature MUSS vollständig testbar sein.

Pflicht-Testebenen:
Unit Tests
Intent Classification
Datentyp Mapping
Policy Rule Evaluation
Integration Tests
API → Policy Engine
Fallback Logic
Context-based Priority Resolution
E2E Tests (MANDATORY)
reale User Queries
vollständige Pipeline-Ausführung
mindestens 1 Flow ohne Mock kritischer Quellen
State / Consistency Tests
Quellenkonsistenz über gleiche Anfrage
UI ↔ Backend Quellenidentität
AI / Behavior Tests
erwartete Routing-Entscheidungen bei definierten Inputs
HARTE TESTREGELN
Tests prüfen Verhalten, nicht Code
kein „Green Test ohne echte Systemvalidierung“
keine vollständige Mocking-Kette für kritische Pfade
Produktionsverhalten MUSS simuliert werden
11. DEFINITION OF DONE

Ein Feature gilt nur als fertig, wenn:

alle Tests erfolgreich sind
E2E Flow stabil läuft
keine offenen Edge Cases existieren
Output exakt Spec-konform ist
keine impliziten Entscheidungen im System verbleiben
12. OPEN QUESTIONS

Alle offenen Punkte müssen explizit als:

Entscheidungsbedarf
oder fehlende Regel

markiert werden.

NICHT erlaubt:

implizite Annahmen
stille Default-Entscheidungen
13. IMPLEMENTATION CONTRACT (EXECUTION LAYER – KRITISCH)
13.1 TASK GENERATION RULES
1 Task = 1 Verhaltenseinheit
keine kombinierten Ziele
keine Architektur-Interpretation erlaubt
keine freien Designentscheidungen
13.2 TASK STRUCTURE

TASK ID

Goal (STRICT)
ein einziges überprüfbares Ziel

Context
Systembereich

Input
Dateien / Module

Output (STRICT)
konkrete Systemänderung

Implementation Steps

Schritt 1
Schritt 2
Schritt 3

Files
exakte Pfade

Dependencies
Abhängige Tasks

Acceptance Criteria

binär prüfbar
pass/fail

Test Mapping
Unit / Integration / E2E

13.3 AGENT RULES
keine Interpretation erlaubt
keine Architekturentscheidungen im Task
keine Optimierungsideen
nur Spec-Ausführung
13.4 EXECUTION GUARANTEE

Ein System ist nur korrekt implementiert, wenn:

alle Tasks deterministisch ausführbar sind
keine impliziten Entscheidungen existieren
alle Acceptance Criteria erfüllt sind
14. IMPLEMENTATION OUTPUT REQUIREMENT

Dieses Spec MUSS ermöglichen:

GPT-5.5 → Architekturentscheidung
Windsurf Skill → Task Compilation
SWE/Kimi → Code ohne Interpretation
Gemini Orchestrator → Routing + Execution Order
15. SYSTEM GOAL

Maximale Deterministik bei minimaler Interpretation.

🧠 EIN-SATZ-DEFINITION

Dieser Spec ist kein Dokument.

Er ist ein ausführbarer Vertrag zwischen Feature-Idee und Code-Ausführung.