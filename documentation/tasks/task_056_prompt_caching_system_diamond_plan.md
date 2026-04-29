# 💎 DIAMOND TASK: Prompt Caching System — Provider-Agnostic Cost Optimization Engine

---
task_id: 20260429-056
status: BLUEPRINT_READY
assigned_to: AI-STUDIO-ORCHESTRATED / KIMI-K2.6 / SWE-1.6
confidence_level: HIGH
created_at: 2026-04-29 15:09
updated_at: 2026-04-29 15:09
completion_gate:
  tests: false
  audit_trail: false
  lessons_learned: false
---

# 1️⃣ Task Description

Janus soll ein provider-agnostisches Prompt-Caching-System erhalten, das stabile Prompt-Anteile deterministisch erkennt, cachebar segmentiert, provider-spezifische Native-Caching-Features optimal nutzt und Kosten-/Token-Einsparungen sauber in der vorhandenen Telemetrie sichtbar macht.

**Core Value:**

> Janus zahlt nie zweimal für denselben stabilen Kontext.

**Quelle / Feature-Dossier:**

- `documentation/Planned Features/PROMPT CACHING SYSTEM.md`

**Diamond-Ziel:**

- Kein Architektur-Redesign.
- Minimal-invasive Integration in vorhandene Orchestrator-/Provider-Pipeline.
- Provider-agnostischer Janus-Cache als SSOT.
- Provider-native Caches nur als Adapter-Optimierung.
- Vollständige Kosten-, Token- und Cache-Metriken über D10/D13/D15-kompatible Telemetrie.

---

# 2️⃣ Current Architecture Reference

## Relevante bestehende Dateien

| Bereich | Datei | Rolle |
|---|---|---|
| Chat-Orchestrierung | `backend/services/chat_orchestrator.py` | Hauptpipeline `handle_chat_request()` → `_execute_generation()` |
| Prompt-Aufbau / Gateway-Kwargs | `backend/services/orchestrator/execution_dispatcher.py` | Baut `wf.final_system_prompt`, `wf.messages`, `wf.gateway_kwargs` |
| Provider Interface | `backend/llm_providers/shared/base_provider.py` | Gemeinsames Provider-Interface |
| OpenAI Adapter | `backend/llm_providers/openai/service.py` | OpenAI Chat-Completions, Tool-Calls, Usage |
| Gemini Adapter | `backend/llm_providers/gemini/service.py` | Gemini-Adapter, Tool-Konvertierung, Kosten |
| Cost Calculator | `backend/services/cost_calculator.py` | Unterstützt bereits `cached_tokens` / `prompt_tokens_cached` |
| Model Catalog | `backend/config/model_catalog.json` | Preise, inklusive cached input pricing bei unterstützten Modellen |
| Telemetrie | `backend/services/logging/logger_core.py` | D10 Events, Trace-ID, UPSERT, Queue-Hardening |
| Logging Schemas | `backend/data/schemas_logging.py` | D10 Payload-Kontrakte |
| Integrity Engine | `backend/services/logging/integrity_engine.py` | D15 Contract Registry / Allowed Actions |
| Prompt Registry | `backend/services/orchestrator/prompt_registry.py` | Globale Direktiven, muss injiziert werden, sonst Dead Code |

## Relevante Diamond-Patterns

- `#ResilientTelemetry`: Trace-ID, UPSERT, Drop-Oldest, schema-validierte Payloads.
- `#ContractRegistry`: Neue Payload-Felder müssen D15-kompatibel bleiben.
- `#DeadCode #Prompting`: Neue Prompt-Direktiven nur wirksam, wenn sie tatsächlich injiziert werden.
- `#AsyncLifecycleSafety`: Cache-/DB-Ressourcen dürfen nicht vor Abschluss async laufender Provider-Calls geschlossen werden.
- `#GeminiNameSanitization`: Gemini hat eigene Provider-Anforderungen; Adapterlogik strikt kapseln.
- `#StatisticalRoutingBaseline`: Einsparungen müssen über mehrere Runs validiert werden, nicht über Einzelfälle.

---

# 3️⃣ Zielbild / Architektur

## Ziel-Pipeline

```text
User Request
  ↓
ChatOrchestrator
  ↓
Prompt Builder / execution_dispatcher.py
  ↓
Prompt Segmenter
  ↓
Janus Prompt Cache Layer
  ↓
Provider Cache Adapter
  ↓
LLM Provider Call
  ↓
Usage + Cache Metrics
  ↓
D10 Telemetry + Cost Calculator + UI Metrics
```

## Architekturprinzipien

- **Janus-first:** Janus entscheidet deterministisch, welche Segmente stabil/cachebar sind.
- **Provider-second:** Provider-native Features werden genutzt, aber ersetzen nicht die Janus-Logik.
- **Hash-truth:** Wiederverwendung ausschließlich über Content-/Metadata-Hash, niemals über Ähnlichkeit.
- **No wrong reuse:** Ein falscher Cache-Hit ist schlimmer als ein Cache-Miss.
- **No tool suppression:** Prompt-Caching darf Tool-Calls, Tool-Schemas, Tool-Results und Gemini-Thought-Signatures nicht beschädigen.
- **Observable by default:** Jeder Request liefert Cache-Metriken, auch bei `disabled` / `unsupported`.

---

# 4️⃣ Functional Requirements / Acceptance Criteria

## Must-have

- [ ] Stabile Prompt-Segmente werden deterministisch erkannt.
- [ ] Cache-Keys enthalten mindestens `provider`, `model`, `segment_type`, `content_hash`, `prompt_version`, `tool_schema_hash` optional.
- [ ] Cache invalidiert automatisch bei Content-, Modell-, Provider-, Prompt-Version- oder Tool-Schema-Änderung.
- [ ] OpenAI-Calls erhalten unveränderte semantische Message-Reihenfolge.
- [ ] Gemini-Calls behalten Tool-/Function-Call-Speziallogik vollständig intakt.
- [ ] Ollama/local Provider laufen ohne externe Provider-Cache-Annahme weiter.
- [ ] Kostenrechner verarbeitet `cached_tokens` weiterhin korrekt.
- [ ] D10-Events enthalten Cache-Metriken pro LLM-Call.
- [ ] Tests decken Segmentierung, Key-Stabilität, Invalidation und Provider-Fallback ab.

## Should-have

- [ ] Provider-Fähigkeiten werden zentral konfiguriert statt hardcoded.
- [ ] Persistent Cache ist optional aktivierbar.
- [ ] UI kann `cache_hit_rate`, `cached_tokens`, `estimated_tokens_saved` anzeigen.
- [ ] Cache kann per Config/Env deaktiviert werden.

## Must-not

- [ ] Keine Antwort aus einem alten Prompt-Kontext wiederverwenden.
- [ ] Keine User-Eingabe cachebar markieren.
- [ ] Keine Tool-Results ohne Tool-Call-ID / Turn-Kontext wiederverwenden.
- [ ] Keine manuellen Änderungen an `model_routing.json`.
- [ ] Keine KI-basierte Validierung der Cache-Korrektheit.

---

# 5️⃣ Provider Capability Matrix

| Provider | Janus Segment Cache | Native Prompt Cache | Strategie |
|---|---:|---:|---|
| OpenAI | Ja | Teilweise / modellabhängig über cached input accounting | Stabilen Prefix erhalten; `cached_tokens` aus Usage auswerten; keine API-spezifische Mutation ohne Modellfreigabe. |
| Gemini | Ja | Ja, modell-/API-abhängig über cached content möglich | Phase 1 nur Janus-Metrik + stabile Messages; Phase 2 expliziter Gemini Cache Adapter. Thought-Signature-/Tool-Call-Logik nicht anfassen ohne Spezialtests. |
| Anthropic | Ja | Ja, über prompt caching / cache-control bei passenden SDKs | Adapter erst implementieren, wenn Anthropic-Service im Repo eindeutig vorhanden ist. |
| Ollama | Ja | Nein / lokal nicht abrechnungsrelevant | Nur Segment-Metrik und lokale Wiederverwendungsanalyse; keine Kostenersparnis behaupten. |
| Websearch/Image/Audio | Nein für Prompt-Segmente | Provider-spezifisch | Nur Usage/Cost unverändert lassen; nicht in Phase 1 einbeziehen. |

**Diamond-Regel:** Native Cache-Features sind Optimierungen. Der Janus-Kontrakt funktioniert auch, wenn ein Provider kein natives Caching unterstützt.

---

# 6️⃣ Technical Contract

## Neue Pydantic-/Dataclass-Modelle

Empfohlene Datei:

- `backend/services/prompt_cache.py`

Alternativ bei größerem Umfang:

- `backend/services/prompt_cache/models.py`
- `backend/services/prompt_cache/segmenter.py`
- `backend/services/prompt_cache/cache_store.py`
- `backend/services/prompt_cache/provider_adapters.py`

## Datenmodelle

```python
class PromptSegment(BaseModel):
    segment_id: str
    segment_type: Literal["system", "directive", "skill_directive", "history_summary", "document", "tool_schema", "recent_history", "user_input"]
    content: str
    cacheable: bool
    stability_reason: str
    content_hash: str
    token_estimate: int = 0

class PromptCacheKey(BaseModel):
    provider: str
    model: str
    segment_type: str
    content_hash: str
    prompt_version: str
    tool_schema_hash: str | None = None

class PromptCacheDecision(BaseModel):
    enabled: bool
    provider: str
    model: str
    cache_hits: int
    cache_misses: int
    cache_bypassed: int
    estimated_tokens_saved: int
    native_cache_supported: bool
    native_cache_applied: bool
    reason: str | None = None
```

## Segment-Typen

| Segment | Cachebar | Grund |
|---|---:|---|
| `system` | Ja | Stabiler Basisprompt |
| `directive` | Ja | Registry-Direktiven, versionsabhängig |
| `skill_directive` | Ja | Stabil pro Skill + Schema-Version |
| `history_summary` | Ja | Stabil, wenn Summary-Hash gleich bleibt |
| `document` | Ja | Stabil bei unverändertem Dokument-Hash |
| `tool_schema` | Ja, providerabhängig | Stabil, aber bei Schema-Änderung invalidieren |
| `recent_history` | Nein in Phase 1 | Hohe Drift / Turn-Abhängigkeit |
| `user_input` | Nein | Immer dynamisch |
| `tool_result` | Nein in Phase 1 | Turn-/Tool-ID-abhängig |

---

# 7️⃣ Cache-Key Design

## Deterministischer Key

```text
sha256(
  provider + "|" +
  model + "|" +
  segment_type + "|" +
  prompt_version + "|" +
  tool_schema_hash + "|" +
  normalized_content_hash
)
```

## Normalisierung

- Unicode stabilisieren: NFC.
- Whitespace nur konservativ normalisieren.
- Keine semantische Umformulierung.
- JSON-Schemas mit sortierten Keys serialisieren.
- Windows-Pfade bei Dokumentsegmenten normalisieren, siehe `#WindowsPaths` Pattern.

## Invalidation

Ein Cache-Miss muss automatisch entstehen bei:

- Providerwechsel.
- Modellwechsel.
- Systemprompt-Änderung.
- Skill-Direktiven-Änderung.
- Tool-Schema-Änderung.
- Dokumentinhalt-Änderung.
- Prompt-Cache-Version-Bump.

Empfohlene globale Version:

```python
PROMPT_CACHE_VERSION = "v1"
```

---

# 8️⃣ Implementation Phases

## Phase 0 — Discovery & Guardrails

**Ziel:** Implementierungspfad bestätigen, ohne Funktionalität zu ändern.

**Aufgaben:**

- [ ] `execution_dispatcher.py` Prompt-Aufbau exakt kartieren.
- [ ] Provider-Liste aus realem Code bestätigen: OpenAI, Gemini, Ollama, ggf. Anthropic.
- [ ] Prüfen, ob Anthropic-Service existiert; wenn nein: nur Capability-Platzhalter.
- [ ] D15-Kontrakte für neue `cache_*` Telemetrie-Felder prüfen.
- [ ] Feature Flag definieren: `PROMPT_CACHE_ENABLED` default `false` für erste Integration.

**Output:**

- Mini-Audit im Task-Dokument / Audit Trail.

**CU:** 2

---

## Phase 1 — Segmenter + Deterministic Cache Keys

**Ziel:** Keine Provider-Mutation, nur Segmentierung und Metrik.

**Neue Datei:**

- `backend/services/prompt_cache.py`

**Aufgaben:**

- [ ] `PromptSegment`, `PromptCacheKey`, `PromptCacheDecision` definieren.
- [ ] `segment_messages(messages, provider, model, metadata)` implementieren.
- [ ] Cachebare Segmente erkennen: system prompt, skill directives, stable directives.
- [ ] `build_cache_key()` mit SHA-256 und Versionierung implementieren.
- [ ] In-Memory Store mit TTL/FIFO-Limit implementieren.
- [ ] Keine Änderung an `messages` in Phase 1.

**Integration:**

- In `execution_dispatcher.py` nach `wf.messages` Aufbau und vor `wf.gateway_kwargs`:
  - Segmenter aufrufen.
  - Decision an `wf.gateway_kwargs["prompt_cache_decision"]` hängen.

**Tests:**

- `tests/test_prompt_cache.py`
  - gleicher Content → gleicher Key.
  - anderes Modell → anderer Key.
  - andere Prompt-Version → anderer Key.
  - User Input nicht cachebar.
  - System Prompt cachebar.

**CU:** 4

---

## Phase 2 — Telemetry + Cost Accounting Integration

**Ziel:** Cache-Metriken sichtbar machen, ohne Provider-Risiko.

**Betroffene Dateien:**

- `backend/services/logging/logger_core.py`
- `backend/data/schemas_logging.py`
- `backend/services/cost_calculator.py`
- `backend/services/chat_orchestrator.py` oder `execution_dispatcher.py`

**Aufgaben:**

- [ ] Neues D10 Event `prompt_cache` oder Erweiterung bestehender LLM-Usage Events definieren.
- [ ] Payload-Felder:
  - `cache_hits`
  - `cache_misses`
  - `cache_bypassed`
  - `estimated_tokens_saved`
  - `cached_tokens_provider_reported`
  - `native_cache_applied`
  - `provider`
  - `model`
  - `prompt_cache_version`
- [ ] D15 Integrity-Kontrakt erweitern, falls nötig.
- [ ] `calculate_cost()` nicht brechen: vorhandener Support für `cached_tokens` bleibt SSOT.
- [ ] Provider-reported `cached_tokens` und Janus-estimated savings getrennt halten.

**Tests:**

- D10 Payload akzeptiert Cache-Metriken.
- Cost Calculator rechnet cached tokens weiterhin günstiger, wenn Modellpreis vorhanden.
- Fehlende Cache-Felder brechen Logging nicht.

**CU:** 3

---

## Phase 3 — OpenAI Native Cache Alignment

**Ziel:** OpenAI optimal nutzen, ohne Chat-Completions-Vertrag zu brechen.

**Betroffene Datei:**

- `backend/llm_providers/openai/service.py`

**Strategie:**

- Keine riskante künstliche Prompt-Verkürzung.
- Stabilen Prompt-Prefix erhalten.
- `usage.cached_tokens` / `prompt_tokens_cached` weiter auswerten.
- Optional: Capability-Flag pro Modell im Model Catalog ergänzen.

**Aufgaben:**

- [ ] OpenAI Usage-Extraktion auditieren.
- [ ] `cached_tokens` aus verschachtelten Usage-Strukturen robust extrahieren, falls SDK dies anders liefert.
- [ ] `prompt_cache_decision` nicht an OpenAI API durchreichen; Gateway-only Flag entfernen wie bei anderen Flags.
- [ ] Provider-Metrik in Response ergänzen:
  - `usage.cached_tokens`
  - `cost.cached_input_discount_applied` optional.

**Tests:**

- OpenAI Service entfernt Gateway-only Cache-Flags aus `kwargs`.
- Tool-Choice-Fix aus D18 bleibt intakt.
- Tool-Call-Antworten enthalten weiterhin `raw_assistant_response`.

**CU:** 4

---

## Phase 4 — Gemini Safe Adapter

**Ziel:** Gemini nicht destabilisieren; native Cache erst nach Basisvalidierung.

**Betroffene Datei:**

- `backend/llm_providers/gemini/service.py`

**Risiko:**

Gemini hat strikte Tool-/Function-Call-Sonderlogik und bekannte Anforderungen wie Name-Sanitization und Thought-Signature-Preservation. Prompt-Caching darf diese Pfade nicht rekonstruieren oder beschädigen.

**Aufgaben Phase 4A — Safe Mode:**

- [ ] `prompt_cache_decision` als Gateway-only Flag entfernen.
- [ ] Janus-Metriken loggen, aber keine Gemini native cache mutation.
- [ ] Tests für Tool-Calls, Name-Sanitization und History-Preservation laufen lassen.

**Aufgaben Phase 4B — Native Gemini Cache optional:**

- [ ] Nur wenn SDK/API im Projekt eindeutig unterstützt.
- [ ] `cachedContent` / native Cache-ID nur für rein statische Segmente.
- [ ] Cache-ID an Provider-Adapter binden, nicht an generischen Orchestrator.
- [ ] Bei jedem Fehler: automatischer Fallback auf normalen Gemini Call.

**Tests:**

- Gemini Tool-Call Smoke bleibt grün.
- Dot-Notation Skill-Namen funktionieren weiterhin.
- Kein Verlust von raw API parts / thought signatures.

**CU:** 5 für Safe Mode, 7 für Native Cache

---

## Phase 5 — Persistent Cache Store

**Ziel:** Wiederverwendung über Sessions hinweg, optional und sicher.

**Option A — JSONL / SQLite lokal:**

- Minimal, gut für Desktop-Janus.
- Pfad unter AppData über bestehende Path-Utilities.

**Option B — DB-Tabelle:**

- Nur falls Supabase/SQL-Kontrakt sauber erweitert werden soll.
- Höherer Migrationsaufwand.

**Empfehlung:** Phase 5 zuerst lokal mit SQLite oder JSONL, nicht Supabase.

**Aufgaben:**

- [ ] Store-Interface definieren: `get`, `put`, `stats`, `purge_expired`.
- [ ] TTL + max entries + max bytes.
- [ ] Keine Speicherung sensibler Rohinhalte, wenn nicht nötig.
- [ ] Optional nur Hash + metadata + token_estimate speichern.

**CU:** 4

---

## Phase 6 — UI Metrics / Settings

**Ziel:** Transparenz für Nutzer.

**Betroffene Dateien wahrscheinlich:**

- `frontend/js/settings.js`
- `frontend/js/app.js`
- ggf. CSS unter `frontend/css/`

**Anzeigen:**

- Cache aktiv / deaktiviert.
- Cache-Hit-Rate.
- Provider-reported cached tokens.
- Estimated tokens saved.
- Estimated cost saved.

**Settings:**

- `Smart Mode`: automatisch.
- `Advanced Mode`: Cache deaktivieren / persistent cache leeren.

**Wichtig:** UI erst nach Backend-Stabilität. Nicht in Phase 1–3 vermischen.

**CU:** 3

---

# 9️⃣ Testing Strategy

## Unit Tests

- `tests/test_prompt_cache.py`

Pflichtfälle:

- [ ] Deterministische Hashes.
- [ ] Modellwechsel invalidiert.
- [ ] Providerwechsel invalidiert.
- [ ] Prompt-Version invalidiert.
- [ ] Tool-Schema-Hash invalidiert.
- [ ] User Input nie cachebar.
- [ ] Recent History in Phase 1 nicht cachebar.
- [ ] Empty/None Content robust.

## Integration Tests

- [ ] Chat Request mit OpenAI: normale Antwort unverändert, Cache-Metrik vorhanden.
- [ ] Chat Request mit Tool-Call: Tool-Call weiterhin möglich.
- [ ] Gemini Tool-Call Smoke: keine Regression bei Sanitization.
- [ ] Ollama Smalltalk: keine Tools, keine Cache-Fehlannahmen.

## Regression Tests

- [ ] D18 Tool-Choice-Preservation bleibt grün.
- [ ] D10 Logging nimmt Payload an.
- [ ] D15 Integrity Check bleibt PASS.
- [ ] Cost Calculator cached token pricing bleibt korrekt.

## Statistical Validation

Nach Implementierung:

- [ ] 10 Runs gleicher stabiler Systemprompt mit gleichem Modell.
- [ ] 10 Runs mit Modellwechsel.
- [ ] 10 Runs mit Prompt-Version-Bump.
- [ ] Report: Hit Rate, cached tokens, estimated saved tokens, Kosten vor/nach.

---

# 🔟 Risk Register

| Risiko | Schwere | Gegenmaßnahme |
|---|---:|---|
| Falscher Cache-Hit vermischt Kontexte | Kritisch | Hash enthält Provider, Modell, Version, Segmenttyp, Tool-Schema |
| Gemini Tool-Call Regression | Hoch | Phase 4 Safe Mode zuerst; keine Part-Rekonstruktion |
| OpenAI Gateway-only Flags werden an API gesendet | Mittel | Flags explizit aus `kwargs.pop()` entfernen |
| Telemetrie Schema Drift | Mittel | D15 Contract erweitern / Tests |
| UI zeigt geschätzte Einsparung als echte Kosten | Mittel | Provider-reported und estimated strikt trennen |
| Sensitive Daten im persistenten Cache | Hoch | Standard: nur Hash/Metadata/Token Estimate speichern |
| Cache bläht RAM auf | Mittel | TTL + FIFO + max bytes |

---

# 1️⃣1️⃣ File-Level Implementation Plan

## Neue Dateien

- `backend/services/prompt_cache.py`
- `tests/test_prompt_cache.py`

## Wahrscheinlich zu ändernde Dateien

- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/llm_providers/openai/service.py`
- `backend/llm_providers/gemini/service.py`
- `backend/services/cost_calculator.py`
- `backend/services/logging/logger_core.py`
- `backend/data/schemas_logging.py`
- `backend/services/logging/integrity_engine.py`
- `backend/config/model_catalog.json`
- Optional später: `frontend/js/settings.js`, `frontend/js/app.js`

## Nicht anfassen ohne expliziten Grund

- `backend/config/model_routing.json`
- Skill-Routing-Assignments
- Tool-Manager-Registrierung
- Gemini Tool-Call History-Rekonstruktion ohne dedizierte Tests

---

# 1️⃣2️⃣ AI Studio Orchestration Plan

## Triage-Einschätzung

| Feld | Wert |
|---|---|
| Geschätzte Dateien | 6–10 |
| Schema-Touch | Ja |
| Provider-Touch | Ja |
| Breaking-Change-Risiko | Mittel |
| CU Gesamt | 8 |
| Empfehlung | AI Studio Blueprint → Kimi K2.6 Umsetzung in Phasen → SWE 1.6 Review |

## Modell-/Agenten-Rollen

### AI Studio / Gemini Pro oder Flash — Blueprint Controller

**Aufgabe:**

- Kontext lesen.
- Phasen bestätigen.
- CU feinjustieren.
- Handover pro Phase erzeugen.
- D15/D10-Kontrakte prüfen.

### Kimi K2.6 — Primary Implementation Engine

**Aufgabe:**

- Phase 1–3 implementieren.
- Tests schreiben.
- Minimal-invasive Codeänderungen.
- Keine Architektur-Rewrites.

### SWE 1.6 — Review / Hardening

**Aufgabe:**

- Provider-Adapter prüfen.
- Edge Cases und Schema Drift prüfen.
- Gemini-Risiko bewerten.
- Lint/Test Failures final bereinigen.

---

# 1️⃣3️⃣ Ready-to-Copy AI Studio Master Prompt

```markdown
# Pro-Blueprint: Prompt Caching System | Status: BLUEPRINT_READY | CU: 8

**Ziel-Editor:** AI Studio orchestriert Kimi K2.6 + SWE 1.6  
**Kategorie:** Architektur / Multi-Provider Feature  
**Projekt:** Diamond-OS / Janus

## AUSGANGSLAGE

Janus soll das Feature aus `documentation/Planned Features/PROMPT CACHING SYSTEM.md` im Diamondstandard implementieren. Ziel ist ein provider-agnostisches Prompt-Caching-System, das stabile Prompt-Segmente erkennt, deterministische Cache-Keys nutzt, Provider-native Cache-Fähigkeiten optimal aber sicher einbindet und Token-/Kostenersparnisse sauber in D10/D13/D15-kompatibler Telemetrie sichtbar macht.

## REFERENZEN

- `PROJECT_STATE.md`
- `WHAT_I_LEARNED.md`
- `documentation/Planned Features/PROMPT CACHING SYSTEM.md`
- `documentation/tasks/task_056_prompt_caching_system_diamond_plan.md`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/services/chat_orchestrator.py`
- `backend/llm_providers/shared/base_provider.py`
- `backend/llm_providers/openai/service.py`
- `backend/llm_providers/gemini/service.py`
- `backend/services/cost_calculator.py`
- `backend/services/logging/logger_core.py`
- `backend/data/schemas_logging.py`
- `backend/services/logging/integrity_engine.py`

## ZIEL

Erstelle ein umsetzbares Handover für Kimi K2.6 für Phase 1–3:

1. `backend/services/prompt_cache.py` mit Segmenter, Cache-Key und In-Memory Store.
2. Integration in `execution_dispatcher.py`, ohne Messages semantisch zu verändern.
3. D10-kompatible Cache-Metriken.
4. OpenAI-safe Usage-/cached_tokens-Auswertung, ohne Tool-Choice-Regressions.
5. Tests für Segmentierung, Invalidation, Logging und Provider-Gateway-Flags.

## GUARDRAILS

- Keine Änderung an `model_routing.json`.
- Keine KI-basierte Validierung.
- Keine Antwort-/Completion-Caches; nur Prompt-Segment-Metrik und provider-native Prompt-Cache-Unterstützung.
- Gemini zunächst nur Safe Mode: keine native Cache-Mutation, bis Tool-Call-Specials separat geprüft sind.
- Provider-reported cached tokens und Janus-estimated saved tokens getrennt halten.
- D15 Integrity darf nicht brechen.

## NEXT ACTION LOOP

1. ANALYSE: Bestätige betroffene Dateien und Provider-Lücken.
2. STRATEGIE: Prüfe, ob Phase 1–3 in einem Kimi-Task möglich sind oder splitten.
3. BLUEPRINT: Erzeuge Kimi-Handover mit Akzeptanzkriterien.
4. HANDOVER: Erzeuge SWE-Review-Checklist.
5. DIAMOND-REPORT: Definiere Abschlussreport-Format.

## OUTPUT

- Kimi K2.6 Handover für Phase 1–3.
- SWE 1.6 Review-Checklist.
- Testliste mit konkreten Kommandos.
- Risiken / Stop-Conditions.
```

---

# 1️⃣4️⃣ Kimi K2.6 Handover — Phase 1–3

```markdown
## Kimi-Handover: TASK-056 Prompt Caching System Phase 1–3 | CU: 6

**Ziel-Editor:** Windsurf / Kimi K2.6  
**Kategorie:** Feature / Backend / Provider-safe  

## 1. Aufgabenstellung

Implementiere die sichere Basis des Prompt Caching Systems:

- Neuer deterministischer Prompt-Segmenter.
- Cache-Key-Builder mit Provider/Model/Version/Segment-Type/Content-Hash.
- In-Memory Cache Decision Layer.
- Integration in `execution_dispatcher.py` nach Aufbau von `wf.messages`.
- D10-kompatible Cache-Metriken.
- OpenAI Gateway-only Flag Cleanup und cached-token Usage Robustheit.

## 2. Betroffene Dateien

- `backend/services/prompt_cache.py`
- `backend/services/orchestrator/execution_dispatcher.py`
- `backend/llm_providers/openai/service.py`
- `backend/services/logging/logger_core.py`
- `backend/data/schemas_logging.py`
- `tests/test_prompt_cache.py`

## 3. NEXT ACTION LOOP

0. THINK: Max 3–5 Gedanken. Bestehenden Prompt-Aufbau bestätigen.
1. IMPL: Minimal implementieren, keine Provider-Message-Mutation.
2. TEST: `pytest tests/test_prompt_cache.py`
3. LINTER: `ruff check backend/services/prompt_cache.py tests/test_prompt_cache.py`
4. IMPORTS: Keine Circular Imports; Pydantic/imports oben.
5. DIAMOND-REPORT: Dateien, Tests, Risiken, Metriken dokumentieren.

## 4. Akzeptanzkriterien

- [ ] Gleicher stabiler Prompt erzeugt gleiche Cache Keys.
- [ ] Modell-/Providerwechsel erzeugt andere Cache Keys.
- [ ] User Input wird nie cachebar markiert.
- [ ] Messages an Provider bleiben in Phase 1 semantisch unverändert.
- [ ] OpenAI erhält kein `prompt_cache_decision` in API params.
- [ ] Tests sind grün.
- [ ] D10/D15 brechen nicht.

## 5. Fallback

Wenn 2× Fail bei Provider-Integration: Provider-Teil zurückstellen, nur Segmenter + Tests liefern, SWE 1.6 Review eskalieren.
```

---

# 1️⃣5️⃣ SWE 1.6 Review Checklist

```markdown
## SWE 1.6 Review: TASK-056 Prompt Caching System

## Fokus

- Correctness vor Einsparung.
- Kein falscher Cache-Hit.
- Keine Provider-Regressions.
- Keine Telemetrie-Schema-Drift.

## Prüfpunkte

- [ ] Cache-Key enthält Provider, Modell, Prompt-Version, Segment-Type und Content-Hash.
- [ ] User Input / Recent History / Tool Results werden nicht gecached.
- [ ] Provider-Gateway-only Flags werden nicht an externe APIs gesendet.
- [ ] OpenAI `tool_choice` Preservation aus D18 bleibt intakt.
- [ ] Gemini-Code wurde in Phase 1–3 nicht riskant verändert.
- [ ] `calculate_cost()` trennt `cached_tokens` von normalen Input Tokens.
- [ ] D10 Payload ist robust bei fehlenden Cache-Feldern.
- [ ] Tests decken Invalidation ab.
- [ ] Keine Änderung an `model_routing.json`.

## Stop Conditions

- Falsche Wiederverwendung von Kontext möglich.
- Tool-Calls brechen bei OpenAI oder Gemini.
- D15 Integrity Check failt.
- API-Provider erhält unbekannte kwargs.
```

---

# 1️⃣6️⃣ Completion Gate

- [ ] Phase 1 Tests grün.
- [ ] Phase 2 Telemetrie sichtbar.
- [ ] Phase 3 OpenAI Regression grün.
- [ ] Gemini Safe Mode ohne Regression.
- [ ] D15 Integrity Check grün.
- [ ] Cost Calculator cached token test grün.
- [ ] PROJECT_STATE.md nach Implementierung aktualisiert.
- [ ] WHAT_I_LEARNED.md Pattern ergänzt, falls neue stabile Lösung entsteht.
- [ ] Audit Trail unten aktualisiert.

---

# 1️⃣7️⃣ Audit Trail

| Datum | Status | Änderung | Verantwortlich | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| 2026-04-29 | BLUEPRINT_READY | Diamond-Umsetzungsplan erstellt | Cascade | Plan für AI Studio Orchestrierung mit Kimi K2.6 und SWE 1.6 |

---

# 1️⃣8️⃣ Lessons Learned

- Noch offen nach Implementierung.

---

# 💎 CASCADE REVIEW — Bewertung & Optimierungsempfehlungen

> **Reviewer:** Cascade (Windsurf / Kimi)
> **Datum:** 2026-04-29
> **Kennzeichnung:** Alle Empfehlungen sind mit `[EMPFEHLUNG]` markiert.
> Alle identifizierten Risiken sind mit `[RISIKO]` markiert.
> Originaler Plan-Inhalt bleibt unverändert.

---

## Gesamtbewertung: **7.5 / 10**

### Was der Plan stark macht (Punkte-Treiber)

- **Phasierung vorbildlich:** 7 klar abgegrenzte Phasen mit steigender Risikostufe.
- **Provider-Awareness:** Gemini Safe Mode zuerst ist exakt richtig angesichts Thought-Signature und Name-Sanitization.
- **D10/D15/D18 Regressions-Awareness:** Explizite Nennung bekannter Bugs und Patterns aus WHAT_I_LEARNED.
- **"No wrong reuse" Prinzip:** Korrekte Priorisierung — ein falscher Cache-Hit ist katastrophal.
- **AI Studio Orchestrierungs-Handover:** Ready-to-copy Prompts sind direkt nutzbar.
- **Must-not Liste:** Vollständig und korrekt.

### Wo Punkte fehlen (kritische Lücken)

Die folgenden 8 Punkte sind der Grund für den Abzug von 2.5 Punkten. Jeder adressiert einen blinden Fleck, der bei der Implementierung zu Fehlern oder wirkungslosem Caching führen würde.

---

## [RISIKO] R1 — System-Prompt ist NICHT stabil (Clock-Line-Killer)

**Schwere: Kritisch — macht Phase 1 wirkungslos wenn nicht adressiert.**

Der Plan nimmt an: `system` Segment = cachebar = stabil. Die Realität in `execution_dispatcher.py`:

```
wf._clock_line = f"AKTUELLES DATUM/UHRZEIT: {wf._day_name}, {wf._now_local.strftime('%d.%m.%Y, %H:%M')} Uhr\n\n"
wf.final_system_prompt = wf._clock_line + wf.final_system_prompt
```

**Problem:** Die Clock-Line ändert sich **jede Minute**. Da sie an den Anfang des System-Prompts geprepended wird, invalidiert sie den gesamten System-Prompt-Hash 1440 Mal pro Tag. OpenAI's automatisches Prefix-Caching funktioniert **nur bei stabilem Prefix** — die Clock-Line zerstört das sofort.

Weitere dynamische Injections im System-Prompt:

| Injection | Ort (Zeile) | Frequenz der Änderung |
|---|---|---|
| `_clock_line` | 279-280 | Jede Minute |
| `_identity` / `_id_directive` / `_anchor` | 239-275 | Pro User (stabil pro Session) |
| `_suggestion_suffix` | 296-307 | Pro Request (nutzt `memory_context` + `user_text`) |
| `capability_guidance` | 218-236 | Pro Request (skill-abhängig) |
| `_formatted_coupons` | 316-319 | Pro Request |

### [EMPFEHLUNG] R1-FIX — Sub-Segment-Zerlegung des System-Prompts

Der Segmenter darf den System-Prompt **nicht als einen monolithischen Block** behandeln. Stattdessen muss der System-Prompt in **Sub-Segmente** zerlegt werden:

```python
class SystemPromptLayer(str, Enum):
    CLOCK_LINE = "clock_line"              # NICHT cachebar (ändert sich jede Minute)
    IDENTITY_ANCHOR = "identity_anchor"    # Cachebar pro User (stabil pro Session)
    IDENTITY_DIRECTIVE = "identity_dir"    # Cachebar pro User + Provider
    BASE_PROMPT = "base_prompt"            # Cachebar (DB-Persönlichkeit)
    VERBOSITY_CONTROL = "verbosity"        # Cachebar (Registry-Version)
    UI_GUIDANCE = "ui_guidance"            # Cachebar (Code-Version)
    RESEARCH_GUIDANCE = "research_guide"   # Cachebar (Code-Version)
    TOOL_PROTOCOL = "tool_protocol"        # Cachebar (Code-Version)
    SMALL_TALK_GUARD = "small_talk"        # Cachebar (Code-Version)
    CAPABILITY_GUIDANCE = "capability"     # NICHT cachebar (skill-abhängig pro Request)
    SUGGESTION_SUFFIX = "suggestion"       # NICHT cachebar (memory + user_text)
    SKILL_DIRECTIVES = "skill_directives"  # Cachebar pro Skill-Set
    COUPONS = "fact_coupons"               # NICHT cachebar
```

**Konsequenz für den Segmenter:** Die Funktion `segment_messages()` braucht Zugriff auf die einzelnen `wf.*`-Felder **vor** der Konkatenierung zu `wf.final_system_prompt`. Der Integrationspunkt muss **vor** Zeile 314 (`wf.messages = [...]`) liegen, nicht danach.

**Konsequenz für OpenAI:** Um OpenAI's automatisches Prefix-Caching zu nutzen, müssen die stabilen Blöcke **zuerst** stehen und die dynamischen **zuletzt**. Das bedeutet: Clock-Line ans Ende verschieben oder als separates System-Message senden.

---

## [RISIKO] R2 — Suggestion-Suffix nutzt `user_text` und `memory_context`

**Schwere: Hoch.**

```python
_suggestion_suffix = SuggestionEngine.build_suggestion_directive(
    suggestion_mode, [], str(wf.memory_context_string or ""), str(wf.user_text or "")
)
```

Der Suggestion-Suffix wird mit dem aktuellen `user_text` und `memory_context_string` gebaut und dann an den System-Prompt angehängt. Das macht den gesamten System-Prompt pro Request einzigartig, selbst wenn alle anderen Teile stabil wären.

### [EMPFEHLUNG] R2-FIX

- Suggestion-Suffix als eigenes **nicht-cacheables** Segment klassifizieren.
- Alternativ: Suggestion-Directive als separates System-Message (`role: system`) nach der History senden, statt in den System-Prompt-String einzubauen.

---

## [RISIKO] R3 — Fehlende Concurrency-Sicherheit

**Schwere: Mittel.**

Der Plan definiert einen In-Memory Store, aber kein Locking. `execution_dispatcher.py` läuft **async** — mehrere Chat-Requests können parallel segmentieren und den Cache lesen/schreiben. Ohne `asyncio.Lock` oder thread-safe Dict sind Race Conditions möglich.

### [EMPFEHLUNG] R3-FIX

```python
class PromptCacheStore:
    def __init__(self, max_entries: int = 500, ttl_seconds: int = 3600):
        self._store: dict[str, PromptCacheEntry] = {}
        self._lock = asyncio.Lock()  # Concurrency-Guard
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds

    async def get(self, key: str) -> PromptCacheEntry | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry and not entry.is_expired(self._ttl_seconds):
                return entry
            return None

    async def put(self, key: str, entry: PromptCacheEntry) -> None:
        async with self._lock:
            if len(self._store) >= self._max_entries:
                self._evict_oldest()
            self._store[key] = entry
```

---

## [RISIKO] R4 — Streaming nicht adressiert

**Schwere: Mittel.**

Der Plan erwähnt Streaming nicht. Die `execution_engine.py` hat einen kompletten **Stream-Tool-Loop** (`run_tool_loop_stream`, ~800 Zeilen). Cache-Metriken müssen auch im Streaming-Pfad emittiert werden:

- `_async_iter_llm_stream()` ist der Provider-Aufruf im Stream-Modus.
- Usage-Events kommen als `StreamEvent(type="usage", ...)`.
- Cache-Decision muss **vor** dem Stream-Aufruf feststehen.
- Cache-Metriken sollten als eigenes `StreamEvent(type="cache_metrics", ...)` oder als Teil des Usage-Events emittiert werden.

### [EMPFEHLUNG] R4-FIX

- Phase 2 (Telemetrie) muss explizit den Streaming-Pfad adressieren.
- Cache-Metriken als `StreamEvent` mit `type="cache_metrics"` definieren.
- Non-stream und stream Pfad müssen dieselbe `PromptCacheDecision` erhalten.
- Im Kimi-Handover unter "Betroffene Dateien" ergänzen: `backend/services/orchestrator/execution_engine.py`.

---

## [RISIKO] R5 — Token-Counting-Strategie fehlt

**Schwere: Mittel.**

`PromptSegment.token_estimate` ist definiert, aber der Plan sagt nicht, **wie** Tokens gezählt werden. Optionen:

| Methode | Pro | Contra |
|---|---|---|
| `tiktoken` (OpenAI) | Exakt für OpenAI-Modelle | Falsch für Gemini/Ollama, extra Dependency |
| `len(content) / 4` | Schnell, keine Dependency | ~25% Fehlerquote |
| Provider-spezifisch | Korrekt pro Provider | Komplexität |

### [EMPFEHLUNG] R5-FIX

- Phase 1: Einfache Heuristik `len(content.split()) * 1.3` als Schätzung.
- Phase 3: Für OpenAI `tiktoken` nutzen (ist möglicherweise schon Dependency).
- Token-Estimate immer als **Schätzung** markieren, nie als exakt behaupten.
- Im `PromptCacheDecision` Feld ergänzen: `token_estimation_method: Literal["heuristic", "tiktoken", "provider_reported"]`.

---

## [RISIKO] R6 — Keine Baseline-Messung vor Implementierung

**Schwere: Mittel — ohne Baseline kein Beweis für Einsparungen.**

Der Plan behauptet 20–80% Einsparung, definiert aber keine Methode, den IST-Zustand zu messen. Ohne Vorher-Nachher-Vergleich kann der Erfolg nicht verifiziert werden.

### [EMPFEHLUNG] R6-FIX — Phase 0 um Baseline erweitern

Phase 0 sollte einen **Baseline-Snapshot** erzeugen:

- 10 typische Chat-Requests (Smalltalk, Tool-Call, RAG, Identity) manuell oder automatisiert ausführen.
- Pro Request loggen: `total_input_tokens`, `provider_cached_tokens`, `total_cost`.
- Ergebnis als `baseline_prompt_cache_metrics.json` unter `backend/config/` speichern.
- Nach Phase 3: gleiche 10 Requests wiederholen, Delta berechnen.

---

## [RISIKO] R7 — `execution_dispatcher.py` Integrationspunkt zu spät

**Schwere: Hoch — bestimmt, ob der Cache überhaupt sinnvolle Segmente sieht.**

Der Plan sagt: "In `execution_dispatcher.py` nach `wf.messages` Aufbau und vor `wf.gateway_kwargs`."

Das ist **nach** der Konkatenierung aller Teile zu `wf.final_system_prompt` (Zeile 314). Zu diesem Zeitpunkt ist der System-Prompt ein **monolithischer String** — der Segmenter kann die Sub-Segmente nicht mehr unterscheiden.

### [EMPFEHLUNG] R7-FIX — Integrationspunkt VOR Konkatenierung

Der Segmenter muss **vor** Zeile 314 (`wf.messages = [...]`) aufgerufen werden, wenn die einzelnen `wf.*`-Felder noch separat vorliegen:

```python
# Integrationspunkt: NACH Zeile 307 (suggestion_suffix), VOR Zeile 314 (messages=[])
from backend.services.prompt_cache import segment_and_decide

wf.prompt_cache_decision = segment_and_decide(
    provider=request.provider,
    model=wf.chosen_model,
    segments={
        "base_prompt": wf.system_prompt_for_llm,
        "identity_directive": getattr(wf, '_id_directive', ''),
        "identity_anchor": getattr(wf, '_anchor', ''),
        "clock_line": wf._clock_line,
        "ui_guidance": wf.ui_guidance,
        "research_guidance": wf.research_guidance,
        "tool_protocol": wf.tool_protocol_guidance,
        "small_talk_guard": wf.small_talk_guard,
        "capability_guidance": wf.capability_guidance,
        "suggestion_suffix": _suggestion_suffix or '',
        "skill_directives": '\n'.join(getattr(wf, '_skill_directive_parts', [])),
    },
)
```

Dies erfordert **keinen** Umbau des Prompt-Aufbaus, sondern nur einen Lesezugriff auf die bereits vorhandenen Felder.

---

## [RISIKO] R8 — Kein Rollback-Plan

**Schwere: Niedrig-Mittel.**

Feature-Flag ist erwähnt (`PROMPT_CACHE_ENABLED`), aber kein expliziter Rollback-Plan:

- Was passiert, wenn das Flag mitten in einer Session getoggelt wird?
- Wird der In-Memory Cache geleert?
- Werden laufende Requests abgebrochen?

### [EMPFEHLUNG] R8-FIX

- Feature-Flag wird **nur beim Serverstart** gelesen, nicht hot-reloadable.
- Bei `PROMPT_CACHE_ENABLED=false`: Segmenter läuft trotzdem, emittiert nur Metriken mit `cache_bypassed=N`, `cache_hits=0`. Damit bleibt die Telemetrie konsistent.
- Rollback = Flag auf `false` setzen + Neustart. Kein spezieller Code nötig.

---

## [EMPFEHLUNG] E1 — `chat_id` / User-Scoping im Cache-Key

Der aktuelle Cache-Key enthält kein `chat_id` oder User-Scope. Für die meisten Segmente ist das korrekt (System-Prompt ist gleich für alle Chats). Aber:

- `identity_directive` enthält den **User-Namen** → muss pro User gecached werden.
- `history_summary` (falls in späteren Phasen cachebar) ist pro Chat.

**Fix:** Optional `user_id` als Cache-Key-Komponente für identity-Segmente. Nicht für system/directive/tool_schema.

---

## [EMPFEHLUNG] E2 — D13 Optimization Integration explizit machen

Der Plan erwähnt D13-Kompatibilität, aber nicht, wie die Optimization Engine die Cache-Metriken nutzen soll. D13 hat bereits `CACHE_ENABLE` als Allowed Action.

**Fix:** In Phase 2 einen D13-kompatiblen Event-Typ definieren:

```python
# D13-kompatibles Action-Format
{
    "action_type": "CACHE_ENABLE",
    "skill_id": "global",
    "payload": {
        "cache_hit_rate": 0.72,
        "estimated_tokens_saved": 15420,
        "estimated_cost_saved_eur": 0.0023
    }
}
```

---

## [EMPFEHLUNG] E3 — OpenAI Prefix-Stability-Optimierung

OpenAI cached automatisch Prompt-Prefixe > 1024 Tokens, wenn sie identisch sind. Der Plan erwähnt das nicht explizit.

**Fix:** Die **Message-Reihenfolge** sollte so optimiert werden, dass stabile Segmente zuerst stehen:

```text
1. Identity Anchor (stabil pro User)
2. Identity Directive (stabil pro User + Provider)
3. Base System Prompt (stabil)
4. Verbosity + Directives (stabil)
5. UI/Research/Tool Guidance (stabil)
6. --- ab hier dynamisch ---
7. Skill Directives (variabel pro Request)
8. Suggestion Suffix (variabel pro Request)
9. Capability Guidance (variabel pro Request)
10. Clock Line (variabel jede Minute)
```

Dies maximiert den stabilen Prefix für OpenAI **ohne API-Änderung** — nur durch Umsortierung innerhalb von `execution_dispatcher.py`. Phase 3 sollte diese Optimierung explizit enthalten.

---

## [EMPFEHLUNG] E4 — Kimi-Handover um R1/R4/R7 ergänzen

Der Kimi-Handover (Section 14) adressiert die oben genannten Risiken nicht. Kimi K2.6 wird ohne diese Informationen den System-Prompt als monolithisch behandeln und ein wirkungsloses Caching bauen.

**Fix für den Handover:**

Unter "1. Aufgabenstellung" ergänzen:

> **ACHTUNG: Der System-Prompt in Janus ist NICHT monolithisch stabil.** Er enthält eine Clock-Line (jede Minute anders), Identity-Injections (pro User), Suggestion-Suffixe (pro Request) und Capability-Guidance (pro Skill-Set). Der Segmenter muss die einzelnen `wf.*`-Felder **vor** der Konkatenierung analysieren, nicht den fertigen String.

Unter "2. Betroffene Dateien" ergänzen:

> - `backend/services/orchestrator/execution_engine.py` (Streaming-Pfad für Cache-Metriken)

---

## Zusammenfassung: Optimiertes Scoring

| Kriterium | Original | Nach Empfehlungen |
|---|---:|---:|
| Architektur-Klarheit | 9/10 | 9/10 |
| Provider-Awareness | 9/10 | 9/10 |
| Realismus der Segment-Analyse | 5/10 | 9/10 (mit R1/R7) |
| Concurrency/Streaming | 4/10 | 8/10 (mit R3/R4) |
| Messbarkeit | 5/10 | 8/10 (mit R5/R6) |
| Handover-Qualität | 8/10 | 9/10 (mit E4) |
| Rollback/Safety | 6/10 | 8/10 (mit R8) |
| Diamond-Stack-Integration | 8/10 | 9/10 (mit E2) |
| **Gesamt** | **7.5/10** | **9/10** |

---

## Aktualisierter Audit Trail

| Datum | Status | Änderung | Verantwortlich | Bemerkung |
| :--- | :--- | :--- | :--- | :--- |
| 2026-04-29 | BLUEPRINT_READY | Diamond-Umsetzungsplan erstellt | Cascade | Plan für AI Studio Orchestrierung mit Kimi K2.6 und SWE 1.6 |
| 2026-04-29 | REVIEW_COMPLETE | Cascade Review: 7.5/10, 8 Risiken, 4 Empfehlungen | Cascade | Kritische Lücken: Clock-Line-Killer (R1), Integrationspunkt (R7), Streaming (R4), Concurrency (R3) |
