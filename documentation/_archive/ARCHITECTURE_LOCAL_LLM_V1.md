# Janus – Lokale LLM-Architektur (Pruki) V1

## Architekturübersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTENT PARSER (Fast Lane)                          │
│  intent_classifier.py  +  SkillSelector._domain_priorities     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Heuristik: Greeting / Thanks / Confirmation → skip LLM  │   │
│  │ Keyword:   Domain-Keywords → Skill-Familien-Präfilter    │   │
│  │ Semantic:  ChromaDB janus_skill_index → top-k Skills     │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           CAPABILITY LAYER (ollama_adapter.py)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ OllamaCapabilities   – Modell-Feature-Flags             │   │
│  │   supports_native_tools, tool_blind, json_mode, ...     │   │
│  │                                                          │   │
│  │ SkillAffinityRegistry – Skill-Familien-Metadaten         │   │
│  │   intent_keywords, deterministic_fallback,               │   │
│  │   max_context_tokens, requires_external_api              │   │
│  │                                                          │   │
│  │ match_intent_to_skills(prompt) → [skill_id, ...]         │   │
│  │ classify_tool_call_failure(skill, error, provider)       │   │
│  │   → ToolCallFailure(retryable, degrade, strategy)        │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               SKILL ROUTER (skill_router.py)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ resolve_tool_name(name)  – Legacy ↔ Skill-ID Mapping    │   │
│  │ get_tool_definition(name) – Pydantic-Schema Auflösung   │   │
│  │                                                          │   │
│  │ Quellen: backend/skills/**/*.json (48 Katalogdateien)    │   │
│  │ Fallback: documentation/skill_mapping.json               │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              LLM GATEWAY (llm_gateway.py)                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ reason_and_respond() – Haupt-Agentenloop                 │   │
│  │                                                          │   │
│  │ Ollama-Spezifisch:                                       │   │
│  │  1. Tool-Limitierung (max 10) mit Intent-Boost           │   │
│  │  2. Synthesis-Phase (Text-Only nach Tool-Ergebnis)       │   │
│  │  3. Forced-Tool Retry bei fehlgeschlagenem Tool-Call     │   │
│  │  4. Budget-Guard (max 90s pro Request)                   │   │
│  │  5. Loop-Protection (3x invalid → Abbruch)              │   │
│  │                                                          │   │
│  │ Provider-Agnostisch:                                     │   │
│  │  - Tool-Call Deduplizierung                              │   │
│  │  - Policy-Engine Integration                             │   │
│  │  - Routing-Quality-Guards                                │   │
│  │  - Local-Business Rendering                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              TOOL EXECUTOR (tool_executor.py)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Alias-Auflösung → Skill-Router → Schema-Validierung     │   │
│  │ → Kontext-Injektion → Ausführung → Telemetrie           │   │
│  │                                                          │   │
│  │ Sicherheitsschichten:                                    │   │
│  │  - PolicyEngine (REQUIRE_CONSENT / ALLOW)                │   │
│  │  - Sandbox-Level (workspace_only)                        │   │
│  │  - Rate-Limiting (max_calls_per_turn)                    │   │
│  │  - Phase-Filterung (allowed_skill_ids)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              SKILL IMPLEMENTATIONS (tools/*.py)                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ geo_service.py   │  │ media_tools.py   │  ...               │
│  │  routing          │  │  image gen       │                    │
│  │  local_business   │  │  tts/mp3         │                    │
│  │  (OSM fallback)   │  │                  │                    │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Implementierte Komponenten

### 1. Capability Layer (`backend/llm_providers/ollama_adapter.py`)

| Komponente | Beschreibung |
|---|---|
| `OllamaCapabilities` | Frozen Dataclass mit Modell-Feature-Flags (tool_blind, json_mode, streaming, synthesis) |
| `SkillAffinity` | Frozen Dataclass pro Skill: Intent-Keywords, Fallback-Strategie, Context-Limits |
| `SkillAffinityRegistry` | Dict mit 9 Kern-Skills, lazy-initialized |
| `match_intent_to_skills()` | Deterministischer Keyword-Matcher, kein LLM nötig |
| `classify_tool_call_failure()` | Klassifiziert Fehler → retryable / terminal / degrade |
| `has_deterministic_fallback()` | Prüft ob ein Skill provider-agnostischen Fallback hat |

### 2. Intent Parser (`backend/services/skill_selector.py`, `backend/utils/intent_classifier.py`)

| Komponente | Beschreibung |
|---|---|
| `SkillSelector._domain_priorities()` | Keyword → Domain-Mapping (system, filesystem, memory, ...) |
| `SkillSelector._semantic_search()` | ChromaDB-basierte Skill-Discovery |
| `intent_classifier.py` | Fast-Lane Heuristiken (Greeting, Thanks, Identity, Confirmation) |
| **Bug-Fix** | `\\b` → `\b` in `_contains_keyword()` — Domain-Keywords matchten nie |

### 3. Skill Router (`backend/services/skill_router.py`, `backend/services/llm_gateway.py`)

| Komponente | Beschreibung |
|---|---|
| `_limit_local_tool_definitions()` | Intent-Aware Tool-Limitierung für Ollama (max 10 Tools) |
| `_ensure_forced_tool_visible()` | Garantiert, dass erzwungene Tools nicht aus der Liste fallen |
| `reason_and_respond()` | Multi-Round Agenten-Loop mit Synthesis-Phase |
| Forced-Tool Retry | OpenAI + Ollama: Retry bei ausgebliebenem Tool-Call |

### 4. Fallback-Mechanismen

| Fallback | Trigger | Strategie |
|---|---|---|
| OSM Overpass Rotation | Server-Timeout/504 | 3 Server Round-Robin |
| DuckDuckGo Soft-Fail | Captcha/leeres Ergebnis | → OSM Business-Suche |
| Synthesis-Fallback | Tool-Ergebnis vorhanden | Text-Only mit kurzem Prompt |
| Budget-Guard | >90s verbraucht | Synthese überspringen |
| Loop-Protection | 3x gleicher invalider Call | Abbruch mit Hinweis |
| Deterministic Routing | Ollama liefert kaputte Links | Nachträgliches Link-Append |

## Testabdeckung

```
backend/tests/test_architecture_layers.py     — 35 Tests (NEU)
  TestSkillAffinityRegistry                   —  6 Tests
  TestIntentMatcher                           — 11 Tests
  TestToolCallFailureClassification           —  6 Tests
  TestIntentAwareToolLimiting                 —  2 Tests
  TestSkillSelectorKeywordFix                 —  4 Tests
  Parametrized Skill Coverage                 —  6 Tests

backend/tests/test_skill_router_executor.py   — 17 Tests (bestehend, grün)
backend/tests/test_policy_bypass_gateway.py   — 41 Tests (bestehend, grün)

Gesamt: 93 Tests grün, 0 Fehler
```

## Empfehlungen für kleine Anpassungen

1. **SkillAffinity erweitern**: Wenn neue Skills registriert werden, `_build_default_affinity_registry()` ergänzen
2. **Intent-Keywords tunen**: Bei Fehlroutings die `intent_keywords` Tupel in der Registry anpassen
3. **Ollama Tool-Limit**: Aktuell 10; bei größeren Modellen (70b+) kann `limit` erhöht werden
4. **classify_tool_call_failure nutzen**: Im Gateway-Loop bei `OPERATION_FAILED` Ergebnissen die Failure-Klassifizierung aufrufen, um automatisch zwischen Retry und Degrade zu entscheiden

## Potenzielle Edge-Cases

| Edge-Case | Risiko | Mitigation |
|---|---|---|
| Multi-Intent Prompt (z.B. "Route + Restaurant + PDF") | Nur top-3 Skills geboostet | `top_k` Parameter anpassen |
| Neuer Skill ohne Affinity-Eintrag | Kein Intent-Boost, aber Tool bleibt nutzbar | Warning-Log hinzufügen |
| Gemma2 tool_blind + forced tool | Tool-Choice wird ignoriert | JSON-Fallback-Instruction aktiv |
| ChromaDB nicht verfügbar | Semantic Search schlägt fehl | Graceful Fallback auf Domain-Keywords |
| Ollama Timeout in Synthesis | Budget-Guard verhindert zweiten Versuch | `final_synthesis` Budget separat |
