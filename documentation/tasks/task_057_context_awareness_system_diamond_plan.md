# 💎 DIAMOND TASK: Context Awareness System — Context Meter, Model-Aware Limits & Smart Compression

---
task_id: 20260429-057
status: PLANNED
assigned_to: AI-STUDIO-ORCHESTRATED / KIMI-FIRST / SWE-REVIEW
confidence_level: HIGH
created_at: 2026-04-29 19:30
updated_at: 2026-04-29 19:36
source_dossier: documentation/Planned Features/CONTEXT AWARENESS SYSTEM.md
cu_total: 12
completion_gate:
  tests: true
  audit_trail: true
  lessons_learned: true
  user_control: true
  regression_green: true
---

# 2️⃣ Impact-Analyse & Abhängigkeiten
**Beeinflusst:** Memory-Retrieval-System → Modified by task_066: Threshold-Tuning für Kontext-Relevanz (Priority 0.50 → 0.65)

# 1️⃣ Task Description

Janus soll ein Context Awareness System erhalten, das die Auslastung des aktuellen Kontextfensters jederzeit sichtbar macht, modellabhängig korrekt bewertet und dem Nutzer rechtzeitig kontrollierte Optimierungsmaßnahmen anbietet.

**Core Value:**

> Janus verhindert, dass LLMs dumm werden — bevor es passiert.

**Diamond-Ziel:**

- Kontextauslastung wird sichtbar, erklärbar und modellabhängig korrekt.
- Nutzer wird vor Qualitätsverlust aktiv gewarnt.
- Kompression ist nachvollziehbar, reversibel und user-kontrolliert.
- Kein unsichtbares Löschen von Chat-Inhalten.
- Kein Architektur-Redesign; Integration in bestehende Chat-, Memory- und Model-Catalog-Schichten.

---

# 2️⃣ Bewertung des Feature-Dossiers

## Einschätzung

Das Feature ist sehr sinnvoll und strategisch stark, weil es ein reales LLM-Problem produktseitig löst: Kontextverlust passiert heute schleichend und wird erst sichtbar, wenn Antworten schlechter werden. Eine Context-Ampel macht diesen Qualitätsverlust präventiv steuerbar.

## Diamond-Stärke

- **Hoher UX-Wert:** Nutzer sieht sofort, warum ein Chat riskant wird.
- **Hoher System-Wert:** Janus kann Context Health als Telemetrie-Signal nutzen.
- **Synergie mit TASK-056:** Prompt Caching und Context Awareness ergänzen sich: Caching spart Kosten, Context Awareness schützt Qualität.
- **Synergie mit Memory/RAG:** Komprimierte Inhalte können in Memory/RAG archiviert und bei Bedarf zurückgeholt werden.

## Haupt-Risiko

Smart Compression ist riskant, wenn sie zu früh automatisiert wird. Eine falsche Summary kann Wissen verfälschen. Deshalb muss Phase 1–2 nur messen und warnen; Phase 3 darf nur user-bestätigt komprimieren.

---

# 2️⃣b Relevante Diamond-Patterns [💎 DIAMOND UPGRADE]

- `#SavingsVisualizer`: Monetäre Ersparnis-Berechnung und UI-Anzeige — direkt wiederverwendbar für Context Compression Savings.
- `#ResilientTelemetry`: D10-Events müssen Schema-validiert, Trace-ID-kompatibel und drop-safe sein.
- `#ContractRegistry`: Neue D10-Felder (`context_*`) müssen D15-kompatibel gemeldet werden.
- `#PromptCachingClockLine`: Clock-Line invalidiert Caches jede Minute — Context Counter muss System-Prompt-Größe inklusive dynamischer Teile korrekt erfassen.
- `#AsyncLifecycleSafety`: Context State darf keine DB-Session vorzeitig schließen, wenn Compression-Proposal async läuft.
- `#UIDeduplication`: Ampel-Renderer darf bei schnellen Modelwechseln keine doppelten Warnings rendern.
- `#DeterministicSkillTesting`: Compression Candidate Selector muss deterministisch testbar sein (keine KI-Entscheidung, welche Messages kandidieren).

---

# 3️⃣ Current Architecture Reference

| Bereich | Erwartete Datei / Komponente | Rolle |
|---|---|---|
| Chat State | `frontend/js/app.js`, Chat DOM / State Store | Quelle der aktuellen Nachrichten |
| Model Selection | `frontend/js/settings.js`, `backend/config/model_catalog.json` | Aktives Modell und Context-Limit |
| Cost/Model Metadata | `backend/config/model_catalog.json` | Sollte um `context_window` / `max_context_tokens` je Modell ergänzt oder validiert werden |
| Orchestrator | `backend/services/chat_orchestrator.py`, `backend/services/orchestrator/*` | Backend-nahe Nachrichten- und Prompt-Struktur |
| Token Counting | Neu: `backend/services/context/context_counter.py` | Modell-aware Token-Schätzung und Ratio-Berechnung |
| Context API | Neu oder bestehend: `backend/api/routers/system.py` | Endpoint für Context State und Compression Actions |
| Memory/RAG | Bestehende Knowledge-/Memory-Services | Archivierung komprimierter Originalinhalte |
| UI | Neu/Erweiterung: `frontend/js/context-awareness.js`, Chat Header | Ampel, Tooltip, Warnungen, Actions |
| Telemetry | D10 Logger | Context status, compression proposals, user decisions |
| Stream Protocol | `backend/services/orchestrator/stream_protocol.py` | StreamEvent Dataclass — Context Meter kann als Event emittiert werden |

## Exakte Datei-Level Impact Analysis [💎 DIAMOND UPGRADE]

| Datei | Aktion | Beschreibung |
|---|---|---|
| `backend/config/model_catalog.json` | **MODIFY** | `max_context_tokens` Feld je Modell hinzufügen |
| `backend/services/context/__init__.py` | **CREATE** | Package-Init |
| `backend/services/context/context_counter.py` | **CREATE** | Token-Schätzung pro Message-Liste |
| `backend/services/context/context_state.py` | **CREATE** | Ratio-Berechnung, Ampel-Status, Warning-Text |
| `backend/services/context/context_compressor.py` | **CREATE** (Phase 3+) | Candidate Selection, Summary Generation, Archive |
| `backend/api/routers/context.py` | **CREATE** | Neuer Router für `/api/context/*` Endpoints |
| `backend/services/chat_orchestrator.py` | **MODIFY** (minimal) | Context State nach Message-Aufbau berechnen, als Metadaten mitgeben |
| `backend/services/orchestrator/execution_dispatcher.py` | **READ-ONLY** | System-Prompt-Größe für Token-Kalkulation lesen — kein Schreiben |
| `backend/data/models.py` | **MODIFY** (Phase 4) | `ContextCompression` + `ContextArchive` SQLAlchemy-Modelle |
| `backend/data/database.py` | **MODIFY** (Phase 4) | Auto-Migration für neue Tabellen |
| `backend/services/logging/logger_core.py` | **MODIFY** | Neue D10-Event-Typen registrieren |
| `frontend/js/context-awareness.js` | **CREATE** | Ampel-Renderer, Warning-Handler, Compression-UI |
| `frontend/index.html` | **MODIFY** | Context-Meter Element im Chat-Header |
| `frontend/src/styles.css` | **MODIFY** | Ampel-Farben und Warning-Styles |
| `backend/tests/test_context_awareness.py` | **CREATE** | Unit + Integration Tests |

## Nicht anfassen ohne expliziten Grund [💎 DIAMOND UPGRADE]

- `backend/config/model_routing.json` — Routing darf nie manuell mutiert werden.
- `backend/services/prompt_cache.py` — Prompt Cache ist unabhängig; keine Kopplung.
- `backend/llm_providers/*/service.py` — Context Awareness ist Provider-agnostisch, keine Provider-Mutation.
- Tool-Manager, Skill-Registrierung, Gemini-Name-Sanitization.

---

# 3️⃣b Provider Context Limit Matrix [💎 DIAMOND UPGRADE]

| Modell-ID | Provider | `max_context_tokens` | Output-Reserve | Effektives Input-Limit | Quelle |
|---|---|---:|---:|---:|---|
| `gpt-5.4-nano` | openai | 128.000 | 16.384 | 111.616 | OpenAI Docs |
| `gpt-5.4-mini` | openai | 128.000 | 16.384 | 111.616 | OpenAI Docs |
| `gpt-5.4` | openai | 128.000 | 16.384 | 111.616 | OpenAI Docs |
| `gpt-5.4-pro` | openai | 128.000 | 32.768 | 95.232 | OpenAI Docs |
| `gpt-5.5` | openai | 128.000 | 16.384 | 111.616 | OpenAI Docs (verifizieren) |
| `gpt-5.5-pro` | openai | 128.000 | 32.768 | 95.232 | OpenAI Docs (verifizieren) |
| `gemini-3.1-pro-preview` | gemini | 1.000.000 | 65.536 | 934.464 | Google Docs |
| `gemini-3-flash-preview` | gemini | 1.000.000 | 65.536 | 934.464 | Google Docs |
| `mistral-nemo:12b` | ollama | 128.000 | 8.192 | 119.808 | Mistral Docs |
| `qwen2.5:14b` | ollama | 32.768 | 8.192 | 24.576 | Qwen Docs |
| `gemma2:27b` | ollama | 8.192 | 4.096 | 4.096 | Gemma Docs |

**Wichtig:** Diese Werte müssen bei Modell-Updates verifiziert und in `model_catalog.json` eingepflegt werden.

**Fallback-Defaults (wenn Feld fehlt):**

| Provider | Fallback `max_context_tokens` | Fallback Output-Reserve |
|---|---:|---:|
| openai | 128.000 | 16.384 |
| gemini | 1.000.000 | 65.536 |
| ollama | 8.192 | 2.048 |
| unknown | 4.096 | 1.024 |

---

# 4️⃣ Architekturprinzipien

- **Visibility first:** Janus zeigt Context Health, bevor er eingreift.
- **User control always:** Keine automatische Kompression ohne explizite Zustimmung, außer späterer Opt-in Auto-Modus.
- **Reversible compression:** Originale werden nicht gelöscht, sondern archiviert und referenzierbar gemacht.
- **Model-aware truth:** Context Ratio basiert auf aktivem Modell und dessen Kontextfenster.
- **No hidden quality loss:** Jede Kompression erzeugt sichtbare UI-Spuren und Audit-Daten.
- **Incremental by default:** Token-Zählung soll nicht bei jeder UI-Änderung komplett neu rechnen.
- **Safety over compactness:** Lieber weniger aggressiv komprimieren als wichtige Informationen verlieren.

---

# 5️⃣ Zielarchitektur

```text
Chat Messages / Prompt State
  ↓
Context Token Counter
  ↓
Model Context Limit Resolver
  ↓
Context State Calculator
  ↓
Context Ampel UI
  ↓
User Decision Layer
  ↓
Smart Compression Engine
  ↓
Compressed Summary Block + Archived Originals
  ↓
Memory/RAG Retrieval on Demand
```

---

# 6️⃣ Technical Contract

## Input Contract

```python
class ContextStateInput(BaseModel):
    chat_id: str
    model: str
    messages: list[dict]
    include_system_prompt: bool = True
```

## Output Contract

```python
class ContextStateOutput(BaseModel):
    chat_id: str
    model: str
    total_tokens: int
    max_context_tokens: int
    usage_ratio: float
    usage_percent: float
    status: Literal["green", "yellow", "orange", "red", "overflow"]
    remaining_tokens: int
    warning: str | None = None
    recommended_actions: list[str] = []
```

## Compression Proposal Contract

```python
class CompressionProposal(BaseModel):
    chat_id: str
    candidate_message_ids: list[str]
    estimated_tokens_before: int
    estimated_tokens_after: int
    estimated_tokens_saved: int
    risk_level: Literal["low", "medium", "high"]
    summary_preview: str
    requires_user_confirmation: bool = True
```

## Compression Result Contract

```python
class CompressionResult(BaseModel):
    chat_id: str
    compression_id: str
    archived_message_ids: list[str]
    summary_message_id: str
    tokens_before: int
    tokens_after: int
    tokens_saved: int
    reversible: bool = True
```

---

# 7️⃣ Ampel-Logik

| Status | Ratio | Bedeutung | UI-Verhalten |
|---|---:|---|---|
| 🟢 green | 0–50% | Kontext gesund | Prozentanzeige, kein Prompt |
| 🟡 yellow | 50–70% | Leichte Einschränkung möglich | Tooltip mit Resttokens |
| 🟠 orange | 70–85% | Qualitätsrisiko steigt | Inline-Hinweis + Kompression vorschlagen |
| 🔴 red | 85–100% | Akuter Qualitätsverlust möglich | Warnbox + Actions: Modell behalten, komprimieren, neuer Chat |
| ⚫ overflow | >100% | Modell-Kontext überschritten | Blockierende Warnung vor Modellwechsel/Sendung |

**Formel:**

```text
usage_ratio = total_tokens / max_context_tokens
usage_percent = round(usage_ratio * 100, 1)
```

## Output-Token-Reserve [💎 DIAMOND UPGRADE]

**Kritischer Punkt:** Das Kontextfenster enthält Input UND erwarteten Output. Wenn ein Modell 128k Kontext hat und 16k Output-Reserve braucht, stehen effektiv nur 112k für Input zur Verfügung.

**Korrigierte Formel:**

```text
effective_input_limit = max_context_tokens - output_reserve
usage_ratio = total_tokens / effective_input_limit
```

**Output-Reserve pro Provider:**

- OpenAI: `max_tokens` aus Request oder Default 16.384.
- Gemini: `maxOutputTokens` aus Request oder Default 65.536.
- Ollama: `num_predict` aus Config oder Default 8.192.

**Diamond-Regel:** Ampel muss die Output-Reserve berücksichtigen. Sonst zeigt sie Grün bei 80%, obwohl der LLM-Call bereits abgeschnitten wird.

---

# 8️⃣ Model Context Limit Resolver

## Anforderungen

- Context-Limits dürfen nicht hardcoded in der UI liegen.
- Primäre Quelle soll `backend/config/model_catalog.json` sein.
- Jedes Modell braucht ein Feld wie `context_window` oder `max_context_tokens`.
- Falls Feld fehlt: konservativer Fallback pro Provider plus Warnlog.

## Beispiel-Erweiterung

```json
{
  "gpt-5.4-mini": {
    "provider": "openai",
    "max_context_tokens": 128000
  },
  "gemini-3.1-pro-preview": {
    "provider": "gemini",
    "max_context_tokens": 1000000
  }
}
```

## Model Switch Handling

Beim Modellwechsel:

1. Frontend sendet `chat_id`, neues `model` an Context State Endpoint.
2. Backend berechnet neue Ratio.
3. UI aktualisiert Ampel sofort.
4. Wenn Status `red` oder `overflow`: Warnung anzeigen.
5. Nutzer entscheidet: Modellwechsel bestätigen, Chat komprimieren oder abbrechen.

---

# 8️⃣b Token Counting Strategie [💎 DIAMOND UPGRADE]

## Ansatz: Heuristik-first, Tokenizer-second

Ein genauer Tokenizer (tiktoken für OpenAI, SentencePiece für Gemini) ist wünschenswert, darf aber kein Blocker für Phase 1 sein.

### Phase 1 — Heuristik (MVP)

```python
def estimate_tokens(text: str) -> int:
    """Konservative Schätzung: ~4 Zeichen pro Token, aufgerundet."""
    return max(1, -(-len(text) // 4))  # ceil division
```

**Safety Margin:** Heuristik überschätzt leicht (Faktor 1.1), damit die Ampel eher zu früh als zu spät warnt.

### Phase 2 — tiktoken (optional, nur OpenAI)

```python
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4o")  # aktuellster Tokenizer
tokens = len(enc.encode(text))
```

**Bedingung:** tiktoken wird nur genutzt, wenn bereits im Projekt installiert. Kein neuer Dependency-Zwang für Phase 1.

### Incremental Counting

- Jede Message bekommt ein `_token_estimate` Feld beim Erstellen/Empfangen.
- Context State addiert die Einzelwerte, statt die gesamte History neu zu tokenisieren.
- Nur bei Compression/Archive wird der Count für betroffene Messages neu berechnet.

---

# 9️⃣ Smart Compression Design

## Nicht sofort automatisieren

Phase 1 darf nur messen. Phase 2 darf nur warnen. Phase 3 darf Kompressionsvorschläge erzeugen, aber nicht automatisch anwenden.

## Compression Candidate Selection

Kandidaten sollten sein:

- Alte Nachrichten außerhalb der letzten N Turns.
- Nachrichten ohne aktive Tool-Call-Abhängigkeiten.
- Keine System-/Developer-/Policy-Blöcke.
- Keine aktuell referenzierten Dateien/Bilder/Tool-Outputs ohne Archivverweis.

## Summary Requirements

Eine Summary muss enthalten:

- Ziele und Entscheidungen des Nutzers.
- Wichtige Fakten, Dateien, Pfade, IDs, APIs, Fehlermeldungen.
- Offene TODOs und Constraints.
- Explizite User-Präferenzen.
- Referenz auf archivierte Originale.

## Reversibilität

- Originale werden in Memory/RAG oder Archiv-Tabelle gespeichert.
- UI zeigt komprimierten Block als „Zusammengefasst / Archiviert“.
- Nutzer kann Details anzeigen oder Originale wiederherstellen.

---

# 🔟 Database / Persistence Proposal

## Option A — Minimal Phase 1

Keine DB-Änderung. Context State wird live berechnet.

## Option B — Diamond Phase 3+

Neue Tabellen oder bestehende Message-Metadaten erweitern:

```text
context_compressions
- id
- chat_id
- created_at
- model
- tokens_before
- tokens_after
- tokens_saved
- summary_text
- archived_ref
- reversible
- user_confirmed
```

```text
context_archives
- id
- chat_id
- compression_id
- original_message_ids
- original_payload_json
- embedding_ref
- created_at
```

---

# 1️⃣1️⃣ API Proposal

## Read Context State

```http
POST /api/context/state
```

Body:

```json
{
  "chat_id": "abc",
  "model": "gpt-5.4-mini",
  "messages": []
}
```

## Create Compression Proposal

```http
POST /api/context/compression/propose
```

## Apply Compression

```http
POST /api/context/compression/apply
```

## Restore / Expand Archive

```http
POST /api/context/compression/{compression_id}/restore
```

---

# 1️⃣2️⃣ Frontend UX Plan

## Context Meter Placement

- Oben im Chat-Header neben Modell-Auswahl.
- Kompakt: `🟢 Kontext 42%`.
- Tooltip: `53.200 / 128.000 Tokens · 74.800 verbleibend`.

## Warning UX

Bei Orange:

> Kontext wird voll. Antworten können ungenauer werden. Möchtest du ältere Teile zusammenfassen?

Bei Rot:

> Kritisch: Dieses Modell nähert sich seinem Kontextlimit. Du kannst beim aktuellen Modell bleiben, den Chat komprimieren oder einen neuen Chat starten.

Buttons:

- `Beim Modell bleiben`
- `Chat komprimieren`
- `Neuen Chat starten`
- `Größeres Modell wählen` falls verfügbar

## Archived Block UI

```text
📦 Zusammengefasst: 42 Nachrichten archiviert · 18.400 Tokens gespart
[Details anzeigen] [Wiederherstellen] [In Memory suchen]
```

---

# 1️⃣3️⃣ Telemetry / D10 Events

Neue Events:

- `context_state_calculated`
- `context_warning_shown`
- `context_model_switch_risk`
- `context_compression_proposed`
- `context_compression_applied`
- `context_archive_restored`

Payload-Mindestfelder:

```json
{
  "chat_id": "...",
  "model": "...",
  "total_tokens": 12345,
  "max_context_tokens": 128000,
  "usage_ratio": 0.42,
  "status": "green",
  "trace_id": "..."
}
```

---

# 1️⃣4️⃣ Implementation Phases

## Phase 1 — Context Meter MVP

**Ziel:** Sichtbarkeit ohne Mutation.

- [ ] `model_catalog.json` um `max_context_tokens` und `output_reserve` je Modell ergänzen.
- [ ] `backend/services/context/context_counter.py` — Heuristik Token-Schätzung (4 chars/token, Safety Margin 1.1).
- [ ] `backend/services/context/context_state.py` — Ratio + Status + Warning-Text + recommended_actions.
- [ ] `backend/api/routers/context.py` — Endpoint `POST /api/context/state`.
- [ ] `frontend/js/context-awareness.js` — Ampel im Chat-Header.
- [ ] `frontend/index.html` — Context-Meter Element einfügen.
- [ ] Modelwechsel triggert Neuberechnung mit korrekter Output-Reserve.
- [ ] `backend/tests/test_context_awareness.py` — Tests für Status-Schwellen, Fallback-Limits, Output-Reserve.

**Completion Gate:** Ampel zeigt korrekt green/yellow/orange/red für unterschiedliche Modelle. Output-Reserve wird berücksichtigt.

**CU:** 4 [💎 DIAMOND UPGRADE]

## Phase 2 — Warning & Decision Layer

**Ziel:** Nutzer wird aktiv, aber nicht invasiv gewarnt.

- [ ] Inline-Warnings bei Orange/Rot.
- [ ] Blocking Warning bei Overflow.
- [ ] Model-Switch-Warnung bei kleinerem Kontextfenster.
- [ ] D10 Events für Warnungen.
- [ ] UI-Actions vorbereitet, Compression noch disabled oder Preview-only.

**Completion Gate:** Wechsel von großem Modell auf kleines Modell erzeugt korrekt Rot/Overflow-Warnung.

**CU:** 2 [💎 DIAMOND UPGRADE]

## Phase 3 — Smart Compression Proposal

**Ziel:** Vorschläge ohne automatische Anwendung.

- [ ] Candidate Selector für ältere Chat-Segmente.
- [ ] Summary Prompt Template mit Fakten-/TODO-/Constraint-Erhaltung.
- [ ] Preview Endpoint `POST /api/context/compression/propose`.
- [ ] UI zeigt Summary Preview und erwartete Token-Ersparnis.
- [ ] Nutzer muss bestätigen.
- [ ] Tests für Candidate Exclusion: System, Tool Schemas, aktuelle Turns.

**Completion Gate:** Proposal ist nachvollziehbar, user-confirmed und verändert den Chat noch nicht ohne Apply.

**CU:** 4 [💎 DIAMOND UPGRADE]

## Phase 4 — Apply Compression + Archive

**Ziel:** Reversible Chat-Bereinigung.

- [ ] Persistence für `context_compressions` / Archiv-Referenzen.
- [ ] Apply Endpoint ersetzt alte Messages durch Summary Block.
- [ ] Originale werden archiviert.
- [ ] UI zeigt „Zusammengefasst / Archiviert“ Block.
- [ ] Restore/Expand Funktion.
- [ ] D10 Events für applied/restored.

**Completion Gate:** Kompression spart Tokens, Summary bleibt im Kontext, Originale sind wiederherstellbar.

**CU:** 5 [💎 DIAMOND UPGRADE]

## Phase 5 — RAG Hybrid Retrieval

**Ziel:** Archiviertes Wissen bleibt nutzbar.

- [ ] Archivierte Originale optional embeddieren.
- [ ] Retrieval bei Fragen zu alten Inhalten.
- [ ] UI-Hinweis: „Antwort nutzt archivierten Kontext“.
- [ ] Tests für Retrieval aus komprimierten Segmenten.

**Completion Gate:** Nutzer kann alte Informationen trotz Kompression zuverlässig abrufen.

**CU:** 3 [💎 DIAMOND UPGRADE]

## Phase 6 — Opt-in Automation

**Ziel:** Automatisierung nur kontrolliert.

- [ ] Setting: Auto-Propose bei Orange/Rot.
- [ ] Optional: Auto-Compress nur bei explizitem Opt-in.
- [ ] Konservative Limits und Undo-Prompt.
- [ ] Audit Trail verpflichtend.

**Completion Gate:** Automatik ist deaktiviert per Default und vollständig rückgängig machbar.

**CU:** 2 [💎 DIAMOND UPGRADE]

---

# 1️⃣5️⃣ Acceptance Criteria

## Must-have

- [ ] Context Ratio wird modellabhängig korrekt berechnet.
- [ ] Ampel aktualisiert sich beim Chat- und Modellwechsel.
- [ ] UI zeigt Prozent, Token-Nutzung und Resttokens.
- [ ] Orange/Rot-Warnungen erscheinen rechtzeitig.
- [ ] Keine automatische Kompression ohne Nutzerbestätigung.
- [ ] Komprimierte Inhalte sind als solche sichtbar.
- [ ] Originale sind archiviert und wiederherstellbar.
- [ ] D10 Telemetrie erfasst Context Health und User Decisions.

## Should-have

- [ ] Incremental Token Counting für Performance.
- [ ] Summary Preview vor Apply.
- [ ] RAG-Restore für archivierte Inhalte.
- [ ] Model-Switch-Empfehlung auf größeres Kontextmodell.
- [ ] Tests für sehr lange Chats und mehrere Kompressionsblöcke.

## Won't-have in MVP

- [ ] Vollautomatische unsichtbare Kompression.
- [ ] Löschung von Originalnachrichten ohne Archiv.
- [ ] Provider-spezifische Tokenizer-Pflicht als Blocker.
- [ ] Aggressive Kontext-Kürzung ohne Review.

## Forbidden Actions (Must-not) [💎 DIAMOND UPGRADE]

- [ ] Keine Kompression ohne User-Confirmation in Phase 1–3.
- [ ] Keine Löschung von Originalnachrichten — nur Archivierung.
- [ ] Keine Mutation von `model_routing.json`.
- [ ] Keine Provider-spezifische Logik im Context State Service (provider-agnostisch).
- [ ] Keine KI-basierte Entscheidung über Compression Candidates — nur regelbasiert.
- [ ] Kein Chat-Fail oder Chat-Blockade wegen Telemetrie-Fehler.
- [ ] Keine Token-Zählung, die den Chat verlangsamt (>50ms für Berechnung = Bug).
- [ ] Keine Kompression von System-Prompt, Tool-Schemas, Developer-Messages oder aktuellem Turn.
- [ ] Kein Overflow-Status ohne Möglichkeit für den User, fortzufahren (immer "trotzdem senden" Option).

---

# 1️⃣6️⃣ Test Plan

## Unit Tests

- `test_context_status_thresholds()`
- `test_context_ratio_uses_model_limit()`
- `test_missing_model_limit_uses_safe_fallback()`
- `test_model_switch_recalculates_ratio()`
- `test_compression_candidates_exclude_recent_messages()`
- `test_compression_candidates_exclude_system_and_tool_messages()`

## Integration Tests

- Long chat → Ampel rot.
- Same chat, larger model → Ampel gelb/grün.
- Smaller model switch → overflow warning.
- Compression proposal → preview generated, no mutation.
- Compression apply → summary block inserted, originals archived.
- Restore → original content recoverable.

## UI Tests / Manual Verification

- Ampel im Chat-Header sichtbar.
- Tooltip zeigt total/max/remaining Tokens.
- Warning popups erscheinen nicht mehrfach pro Turn.
- Komprimierter Block ist eindeutig markiert.
- Restore/Details Buttons funktionieren.

---

# 1️⃣7️⃣ Risk Register

| Risiko | Severity | Mitigation |
|---|---:|---|
| Token-Schätzung ungenau | Medium | Modell-spezifische Tokenizer später, MVP konservativ + Safety Margin |
| Summary verliert wichtige Details | High | Preview, User Confirmation, Restore, Fakten-Checklist im Summary Prompt |
| Kompression verändert Tool-/System-Kontext | High | Exclusion Rules für System/Tool/aktuelle Turns |
| UI warnt zu oft | Medium | Debounce + warn_once_per_threshold |
| Sehr lange Chats langsam | Medium | Incremental Counting + cached per-message token counts |
| RAG Restore findet Inhalte nicht | Medium | Archiv-ID-basierte Wiederherstellung zusätzlich zu Embeddings |

---

# 1️⃣8️⃣ Diamond Guardrails

- Kein Löschen ohne Archiv.
- Keine unsichtbare Kompression.
- Kein Summary-Apply ohne User-Confirmation in MVP.
- Keine Kompression von System-, Developer-, Tool-Schema- oder aktueller Turn-Struktur.
- Jede Compression braucht `compression_id`, `tokens_saved`, `archived_ref`, `reversible=true`.
- Model-Limits müssen aus zentraler Quelle kommen.
- D10 Events müssen Schema-kompatibel und optional sein, kein Chat-Fail wegen Telemetrie.
- [💎 DIAMOND UPGRADE] Context State Berechnung muss Output-Reserve berücksichtigen.
- [💎 DIAMOND UPGRADE] Token-Schätzung darf MVP nicht blocken — Heuristik mit Safety Margin ist ausreichend.
- [💎 DIAMOND UPGRADE] Overflow-Warning darf Chat nie blockieren — User muss immer "trotzdem senden" können.
- [💎 DIAMOND UPGRADE] Frontend-Ampel muss Debounce haben: maximal 1 Update pro 500ms, nicht pro Keystroke.

---

# 1️⃣9️⃣ Recommended Implementation Order

1. **Model Context Limits zentralisieren** in `model_catalog.json` + Resolver mit Fallback-Defaults.
2. **Context State Backend** als reine Read-only Berechnung mit Output-Reserve.
3. **Ampel UI** in Chat Header mit Tooltip.
4. **Model Switch Warning** integrieren.
5. **D10 Telemetrie** für Context Health Events.
6. **Compression Proposal** ohne Mutation.
7. **Compression Apply + Archive** reversibel.
8. **RAG Hybrid Restore**.
9. **Opt-in Automation** erst nach stabiler Telemetrie.

---

# 2️⃣0️⃣ AI Studio Orchestration Plan [💎 DIAMOND UPGRADE]

## Triage-Einschätzung

| Feld | Wert |
|---|---|
| Geschätzte Dateien | 12–16 |
| Schema-Touch | Ja (Phase 4: neue Tabellen) |
| Provider-Touch | Nein (provider-agnostisch) |
| Breaking-Change-Risiko | Niedrig (Phase 1–2 sind read-only) |
| CU Gesamt | 12 |
| Empfehlung | AI Studio Blueprint → Kimi-First Phase 1–2 → Review → Phase 3–4 → Phase 5–6 |

## Modell-/Agenten-Rollen

### AI Studio / Gemini Pro — Blueprint Controller

**Aufgabe:**

- Kontext lesen (PROJECT_STATE.md + diesen Task-Plan).
- Phase-by-Phase Handover erzeugen.
- CU feinjustieren nach Phase-1-Ergebnis.
- D15/D10-Kontrakte prüfen.

### Kimi K2.6 / Cascade — Primary Implementation Engine

**Aufgabe:**

- Phase 1–2 implementieren (Context State + Ampel UI).
- Tests schreiben.
- model_catalog.json erweitern.
- Minimal-invasive Codeänderungen.

### SWE 1.6 — Review / Hardening

**Aufgabe:**

- Token-Counting-Genauigkeit prüfen.
- Edge Cases: sehr lange Chats, leere Chats, fehlende Modelle.
- Ampel-UX-Review.
- Compression Candidate Exclusion Rules validieren.

---

# 2️⃣1️⃣ Ready-to-Copy AI Studio Master Prompt [💎 DIAMOND UPGRADE]

```markdown
# Pro-Blueprint: Context Awareness System | Status: BLUEPRINT_READY | CU: 12

**Ziel-Editor:** AI Studio orchestriert Kimi K2.6 + SWE 1.6  
**Kategorie:** UX / Quality Protection Feature  
**Projekt:** Diamond-OS / Janus

## AUSGANGSLAGE

Janus soll das Feature aus `documentation/Planned Features/CONTEXT AWARENESS SYSTEM.md` im Diamondstandard implementieren. Ziel ist ein Context Awareness System, das die Kontextfenster-Auslastung modellabhängig sichtbar macht, den Nutzer bei Qualitätsrisiko warnt und reversible Smart Compression anbietet.

## REFERENZEN

- Diamond-Plan: `documentation/tasks/task_057_context_awareness_system_diamond_plan.md`
- Feature-Dossier: `documentation/Planned Features/CONTEXT AWARENESS SYSTEM.md`
- PROJECT_STATE.md für aktuellen Systemstatus
- WHAT_I_LEARNED.md für Patterns #SavingsVisualizer, #ResilientTelemetry, #PromptCachingClockLine

## KONTEXT-REGELN

1. Lies `documentation/tasks/task_057_context_awareness_system_diamond_plan.md` VOLLSTÄNDIG.
2. Lies `backend/config/model_catalog.json` für aktuelle Modell-Struktur.
3. Lies `backend/services/chat_orchestrator.py` für Message-Pipeline.
4. Folge dem 6-Phasen-Plan strikt.
5. Phase 1–2 sind READ-ONLY (keine Chat-Mutation, keine DB-Änderung).
6. Keine Provider-Mutation. Context Awareness ist provider-agnostisch.
7. Token-Heuristik (4 chars/token) ist für Phase 1 ausreichend.
8. Output-Reserve MUSS in der Ampel-Formel berücksichtigt werden.

## PHASE 1 HANDOVER (Kimi-First)

Implementiere Phase 1 — Context Meter MVP:
1. Erweitere `model_catalog.json` um `max_context_tokens` und `output_reserve`.
2. Erstelle `backend/services/context/context_counter.py` und `context_state.py`.
3. Erstelle `backend/api/routers/context.py` mit `POST /api/context/state`.
4. Erstelle `frontend/js/context-awareness.js` mit Ampel im Chat-Header.
5. Erstelle Tests in `backend/tests/test_context_awareness.py`.
6. Completion Gate: Ampel zeigt korrekt für verschiedene Modelle, Output-Reserve berücksichtigt.
```

---

# 2️⃣2️⃣ Success Definition

TASK-057 ist Diamond-fertig, wenn Janus in jedem Chat sichtbar anzeigen kann:

- Wie voll der Kontext ist (inkl. Output-Reserve).
- Ob das aktuelle Modell gefährdet ist.
- Was beim Modellwechsel passiert.
- Wie viele Tokens durch Kompression gespart werden könnten.
- Welche Inhalte archiviert wurden.
- Wie sie wiederhergestellt werden können.

**Final Claim:**

> Janus hält den Kontext schlank — und das Wissen vollständig.
