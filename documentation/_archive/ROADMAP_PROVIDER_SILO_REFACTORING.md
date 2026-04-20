# Janus Provider-Silo Refactoring Roadmap

## 1. Executive Summary
Der aktuelle `llm_gateway.py` bündelt sämtliche Provider-Weichen und Nachbearbeitungen in einer Datei. Jede Optimierung für Gemini oder GPT kann daher unbeabsichtigte Seiteneffekte auslösen. Die Provider-Silo-Architektur isoliert jeden LLM-Anbieter in einem eigenen Gateway-Service mit definierten Contracts. Das schafft:

- **Isolation:** Änderungen an Gemini können GPT/Ollama nicht regressieren.
- **Wartbarkeit:** Klare Verantwortlichkeiten, fokussierte Tests und Dokumentation.
- **Diamond-Standard-Konformität:** Jeder Provider kann eigenständig alle Guardrails (z.B. Link-Reparatur, Strukturierungsregeln) durchsetzen.

## 2. Ziel-Architektur
```
backend/
└── llm_providers/
    ├── shared/
    │   ├── base_gateway.py            # BaseProviderGateway-Interface, gemeinsame Utilities
    │   ├── tool_payloads.py           # Gemeinsame Parser/Validatoren für Tool-Responses
    │   └── docs/                      # Cross-Provider Guidelines (Routing, Cost, Logging)
    ├── gemini/
    │   ├── gateway.py                 # Extrahierte Orchestrierungs-/Postprocessing-Logik
    │   ├── service.py                 # API-Aufrufe, Websearch, Cost-Tracking
    │   ├── dialect.py                 # Ehemaliger Compiler (Prompts, Constraints)
    │   └── docs/gemini_websearch.md   # Provider-spezifische Handbücher
    ├── openai/
    │   ├── gateway.py
    │   ├── service.py
    │   ├── dialect.py
    │   └── docs/openai_guardrails.md
    └── ollama/
        ├── gateway.py
        ├── service.py
        ├── dialect.py
        └── docs/ollama_local_ops.md
```
`llm_gateway.py` verbleibt als schlanker Router, der anhand des Providers das passende Gateway instanziiert.

## 3. Implementierungs-Phasen
### Phase 1 – BaseProviderGateway definieren
- Datei: `backend/llm_providers/shared/base_gateway.py`
- Interface: `prepare_request`, `route_tools`, `reason_and_respond`, `postprocess_response`.
- Gemeinsame Hilfen (Logging, Cost-Annotation, Tool-Payload-Parsing) nach `shared/` verschieben.

### Phase 2 – Gemini-Silo
- Bestehende Gemini-spezifische Logik aus `llm_gateway.py`, `prompting/compilers/gemini.py`, `services/websearch/gemini_provider.py` in `llm_providers/gemini/gateway.py` konsolidieren.
- Sicherstellen, dass Diamond-Standard-Guards (Link-Reparatur, Überblick/Liste) nur noch dort leben.
- Unit-Tests: `tests/gateway/gemini/test_gateway_flow.py`.

### Phase 3 – OpenAI-Silo
- Aktuellen „perfekten GPT-Stand“ einfrieren.
- Migration analog zu Gemini, jedoch mit Fokus auf `openai_provider` (native Websearch) und `prompting/compilers/openai.py`.
- Regressionstests: bestehende GPT-E2E-Suiten gegen neues Gateway laufen lassen.

### Phase 4 – Ollama-Silo
- Besonderheiten: lokale Ressourcenverwaltung, Meta-Agent Flow (Phase 1/2), Tool-Rate-Limits.
- Gateway kapselt lokale Node-Verfügbarkeit und Fallbacks.

### Phase 5 – `llm_gateway.py` zum Router umbauen
- Enthält nur noch:
  - Provider-Dispatch (Factory für Gateways)
  - Gemeinsame Telemetrie-Hooks
  - Fallback-Fehlerbehandlung
- Entfernt sämtliche Provider-spezifischen Branches.

## 4. Definition of Done (pro Silo)
Ein Provider-Silo gilt als **Diamond-Ready**, wenn:
1. **Testabdeckung:**
   - Unit-Tests für Gateway, Service, Dialect.
   - Integrationstests (tool execution, link repair) grün.
   - Provider-spezifische E2E-Szenarien dokumentiert.
2. **Typisierung:** `mypy`-saubere Typen in Gateway/Service/Dialect.
3. **Dokumentation:**
   - `docs/<provider>/*.md` erklärt Flows, Guardrails, bekannte Constraints.
   - README-Abschnitt beschreibt Integration in Orchestrator.
4. **Monitoring:** Provider-Gateway meldet Usage, Errors, Diamond-Guards in konsistenter Struktur.
5. **Contract-Stabilität:** Öffentliche Interfaces (`BaseProviderGateway`) unverändert, automatisierte Contract-Tests laufen.

## 5. Risiko-Matrix & Gegenmaßnahmen
| Risiko | Auswirkung | Gegenmaßnahme |
| --- | --- | --- |
| Duplizierung von gemeinsamen Utilities in jedem Silo | Pflegeaufwand, Divergenz | `backend/llm_providers/shared/` beherbergt Parser, Logging, Tool-Contracts. Code-Review-Regel: kein Copy/Paste ohne Shared-Abstraktion. |
| Uneinheitliche Tests | Scheinbar grüne Provider, aber Live-Parity leidet | Test-Harness pro Silo plus gemeinsames Template (`tests/gateway/shared`). CI-Gates verlangen sowohl Provider- als auch Shared-Tests. |
| Router/Factory bleibt „Gott-Objekt“ | Alte Probleme bleiben bestehen | Nach Phase 5: `llm_gateway.py` enthält nur noch Provider-Wahl + Telemetrie. Regel: keine Provider-spezifischen `if` mehr dort. |
| Wissensverlust bei Teamwechsel | Fehlende Provider-Dokumentation führt zu Regressionen | Pflicht: docs/<provider>/* vor Merge aktualisieren. Architektur-Review checkt Vollständigkeit. |
| Shared-Abstraktionen verwässern Provider-Freiheit | Silos können besondere Anforderungen nicht mehr erfüllen | Shared-Layer nur für wirklich generische Funktionen (Payload-Parsing, Logging). Guardrails bleiben im jeweiligen Silo. |

---
**Nächste Schritte:** Phase 1 implementieren (`base_gateway.py` + Shared-Utilities) und in einem Architektur-Review absegnen, bevor Gemini-Migration startet.
