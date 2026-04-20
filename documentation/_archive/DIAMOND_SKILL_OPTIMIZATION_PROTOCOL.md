# Protokoll: Diamond Skill Optimization (Janus V0.5.0)

Dieses Dokument definiert den verbindlichen Workflow zur Optimierung eines Skills auf Diamond-Niveau. Ein Skill gilt erst dann als "Diamond-Ready", wenn alle drei Säulen (Contract, Logik, Prompting) erfüllt sind.

## Säule 1: Der technische Contract (Pydantic & Schema)
- **Input-Modell:** Existiert ein striktes Pydantic-Modell in `backend/data/schemas.py`? (Nutzung von `Field(..., description="...")`, `ge`, `le`, `Literal`).
- **Output-Modell:** Liefert der Handler eine konsistente `SkillResponse`?
- **Error-Codes:** Sind alle Fehlerzustände (z.B. `NOT_FOUND`, `API_ERROR`) über stabile Fehler-Codes definiert?

## Säule 2: Die Implementierungs-Härtung
- **Telemetry:** Wird die `execution_time_ms` gemessen? Werden alle Argumente und Antworten über den `ToolExecutor` getraced?
- **Sandbox:** Ist das `sandbox_level` im Katalog korrekt gesetzt (z.B. `workspace_only`)?
- **Policy:** Ist das Risiko-Level (`read_only`, `confirm_required`) in der Policy Engine hinterlegt?
- **Renderer:** Wurde geprüft, ob ein Deterministic Renderer (`backend/renderers/`) die LLM-Synthese ersetzen oder unterstützen kann?
- **Context Compaction:** Werden große Tool-Ergebnisse vor der finalen Synthese in ein kompaktes, faktenorientiertes Zwischenformat reduziert, ohne Quellen und Kernfakten zu verlieren?

## Säule 3: Die Prompt-Direktive (Engine V2)
Dies ist der wichtigste Schritt für die Antwortqualität. Für jeden Skill muss geprüft werden, welche "Befehle" das Modell braucht, um das Ergebnis perfekt zu verarbeiten.

### Schritt A: Direktive definieren
Lege im OpenAICompiler (oder im künftigen Handbuch) fest:
- **Nano-Regel:** Was muss das schwächste Modell wissen, um nicht zu halluzinieren? (z.B. "Extrahiere nur die Zahl, ignoriere den Text").
- **Standard-Regel:** Wie nutzt das stärkste Modell die Daten am besten? (z.B. "Analysiere Trends in den Daten").

### Schritt B: Grounding & Output
- Hat der Skill eine `StrictGroundingDirective`?
- Ist das gewünschte Ausgabeformat (Liste, Tabelle, Prosa) im `OutputContract` definiert?

### Schritt C: Synthesis-Budget absichern
- Für Recherche-Skills wie `system.websearch` muss geprüft werden, ob der erste Tool-Dispatch mit kompaktem Kontext ausgeführt werden kann.
- Vor der zweiten LLM-Runde sollen Websearch-Ergebnisse in ein kompaktes Faktenobjekt normalisiert werden (z.B. `facts`, `urls`, `sources`, `source_count`), damit die Synthese auf belastbaren Kerndaten statt auf vollem Rohtext arbeitet.
- Die Kompaktierung darf nur den LLM-Kontext reduzieren; der öffentliche Skill-Contract selbst bleibt unverändert.
- Bei Listen- oder Release-Anfragen gilt Diamond-Standard nur dann als erfüllt, wenn pro Listeneintrag ein passender Quellen-Link ausgegeben wird, sofern das Material eine belastbare Zuordnung erlaubt.

## Der "Definition of Done" (DoD) Testlauf
Ein Skill ist erst fertig, wenn:
1. **Nano-Test:** Ein komplexes Prompt mit Nano-Modell erzeugt ein valides JSON-Planning.
2. **Standard-Test:** Die finale Antwort (Synthese) ist faktisch korrekt und nutzt die Daten des Tools vollständig.
3. **Kosten-Check:** Der Orchestrierungs-Overhead liegt dank Engine V2 und Kontext-Kompaktierung für reine Websearch-Turns grob im Bereich von ~1.5k Input-Tokens gesamt oder besser.
