# Ollama Goldstandard Implementation Plan

## Ziel

Eine universelle, robuste Ollama-Schnittstelle schaffen, damit neue Skills nicht mehr einzeln mit provider-spezifischen Sonderfixes stabilisiert werden müssen.

## Kernprinzipien

- Ein interner Janus-Contract fuer LLM-Ergebnisse statt loser provider-spezifischer Spezialfaelle
- Capability-basierte Behandlung pro Modell und Knoten statt globaler Annahmen ueber alle Ollama-Modelle
- Zentrale Tool-Argument-Sanitization statt skillweiser Ad-hoc-Reparaturen
- Deterministische Result-Renderer fuer tool-lastige Skills statt fragiler freier Endsynthese
- Harte Budget- und Degrade-Regeln pro Request statt mehrfacher unkoordinierter Timeouts

## Problemklassen

### 1. Tool-Contract-Instabilitaet

Ollama liefert je nach Modell native Tool-Calls, pseudo-JSON oder Freitext. Dadurch ist der Vertrag fuer den Rest des Systems zu weich.

### 2. Argument-Drift

Pseudo-Toolcalls schreiben Nutzerargumente um, uebersetzen sie oder abstrahieren sie. Das fuehrt zu schlechter Tool-Ausfuehrung.

### 3. Synthesis-Fragilitaet

Selbst nach erfolgreicher Tool-Ausfuehrung kann die finale freie Textphase timeouten oder Tool-Ergebnisse verlieren.

### 4. Verteilte Sonderlogik

Heute leben Ollama-Spezialfaelle in Provider, Gateway, Executor und einzelnen Skills. Das macht neue Skills teuer.

## Zielarchitektur

### A. Ollama Adapter Contract

Ein zentrales Modul kapselt:

- capability negotiation
- native-tool vs pseudo-tool routing
- outcome normalization
- degrade strategy
- timeout/budget profile

### B. Generic Tool Argument Sanitizer

Ein zentrales Modul bereinigt Tool-Argumente anhand von:

- provider
- tool_name
- original_user_text
- schema-/intent-Heuristiken

Es enthaelt allgemeine Hooks und tool-spezifische Validatoren.

### C. Deterministic Result Renderer

Tool-lastige Skills sollen nach erfolgreicher Tool-Ausfuehrung bevorzugt deterministisch gerendert werden, bevor eine freie Ollama-Synthese versucht wird.

### D. Capability Cache

Capabilities werden pro `model + base_url` gecacht.

Beispiele:

- supports_native_tools
- supports_streaming
- supports_json_mode
- prefers_text_only_synthesis
- tool_blind

## Umsetzungsphasen

### Phase 1

- Einfuehrung `backend/llm_providers/ollama_adapter.py`
- Einfuehrung `backend/services/tool_argument_sanitizer.py`
- Migration des bestehenden Local-Business-Schutzes in den Sanitizer

### Phase 2

- Outcome-Normalisierung im Ollama-Provider auf zentrale Adapter-Helfer umstellen
- Capability-Ermittlung und Caching zentralisieren

### Phase 3

- Deterministische Renderer fuer `system.local_business`, `system.routing`, `system.create_pdf`
- Gateway bevorzugt Renderer statt freier Synthesis

### Phase 4

- Request-Budget-Manager fuer Plan, Tool-Phase und Synthese
- harte Degrade-Pfade bei langsamen Modellen
- zentrale Budget-Policy statt verteilter Magic Numbers im Gateway
- freie Ollama-Synthese wird bei niedrigem Restbudget bewusst uebersprungen oder reduziert

## Migrationsstrategie

- Vorhandene Behaviour-Fixes bleiben zunaechst erhalten
- neue zentrale Schicht wird zuerst parallel eingefuehrt
- bestehende Skill-Sonderfaelle werden schrittweise in generische Module gezogen
- erst nach Testabdeckung werden alte Pfade entfernt

## Akzeptanzkriterien

- Neue Ollama-Fixes landen primaer im Adapter oder Sanitizer, nicht in einzelnen Skills
- Tool-Argumente duerfen nicht mehr semantisch vom User-Intent wegdriften
- Erfolgreiche Tool-Outputs muessen ohne fragile Endsynthese sauber auslieferbar sein
- Timeouts duerfen nicht mehr in unkontrollierte Doppel- oder Dreifach-Loops fuehren

## Sofortige erste Umsetzung

1. Sanitizer-Modul erstellen und `system.local_business` darauf migrieren
2. Ollama-Adapter-Basis fuer Capabilities und normalized outcomes erstellen
3. Bestehende Tests auf die zentrale Sanitizer-Schicht ausrichten
4. Danach Gateway und Renderer schrittweise umstellen
