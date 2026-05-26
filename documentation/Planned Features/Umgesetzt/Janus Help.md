# FEATURE DOSSIER — JANUS HELP & CAPABILITY SYSTEM (v2 · Diamond Standard)

> **Hand-Off-Dokument** für AI Studio (Orchestrator) → SWE 1.6 (Architekt) → Kimi K2.5 (Executor).
> v1-Konzept (siehe unten, unverändert) ist der **Vision-Anker**. Dieser v2-Block ist die **ausführbare Spezifikation**.

---

## 0. META

| Feld | Wert |
|---|---|
| **Task-ID** | `FEAT-HELP-001` |
| **Status** | SPEC READY → EXECUTION PENDING |
| **Repo-Root** | `c:\KI\Janus-Projekt` |
| **Owner** | Diamond-OS (Janus) |
| **Orchestrator-Modell** | AI Studio (Gemini 2.5 Pro / o.ä.) |
| **Architekt-Modell** | SWE 1.6 |
| **Executor-Modell** | Kimi K2.5 |
| **Breaking Changes** | Nein (additive Feature) |
| **Migrations** | Keine (read-only Registry) |

---

## 1. EVALUATION v1-DOSSIER

### Stärken (bleiben ✓)
- Klares Produkt-Narrativ (`„Ein System ist nur so gut wie seine Erklärbarkeit“`).
- Anti-Halluzinations-Grundsatz (`nur aus Registry antworten`) — Diamant-Prinzip.
- Drei-Intent-Kategorisierung (Capability / How-To / Navigation) ist korrekt minimal.
- MCL-Action-Integration ist strategisch richtig gedacht.

### Lücken (werden in v2 geschlossen ✗ → ✓)
| Lücke v1 | Fix v2 |
|---|---|
| Keine realen File-Pfade / Module | §3 Codebase-Anchors |
| Keine Registry-Herkunft (manuell vs. auto-generiert?) | §5.2 Auto-Discovery aus `backend/skills/**/*.json` |
| Intent-Detection nicht an `intent_engine.py` angebunden | §4.2 Intent-Binding-Contract |
| Keine Test-Strategie | §8 Test-Contracts (Unit + Integration + Anti-Halluzination) |
| Kein Rollen-Split für Multi-Agent-Implementation | §6 Rollen-Matrix |
| `actions`-Payload nicht an existierende MCL-Spec gebunden | §7.3 MCL-Bridging |
| Mehrsprachigkeit nur erwähnt, nicht definiert | §5.4 `i18n`-Feld pro Capability |

---

## 2. DIAMANT-SCOPE (das was v2 baut)

**In-Scope:**
1. **Capability Registry** als statischer JSON-Store (`backend/data/capability_registry.json`) + Auto-Discovery-Loader.
2. **Help-Skill** (`backend/skills/system/help.json` + Handler `backend/services/help_skill.py`).
3. **Intent-Detection-Erweiterung** in `backend/services/orchestrator/intent_engine.py` → drei neue Detektoren + `IntentDetectionResult`-Flags.
4. **Orchestrator-Routing**: Help-Intent ⇒ Help-Skill direkt, ohne LLM-Planner (Fast-Path).
5. **Response-Generator** mit deterministischen Templates pro Intent-Typ.
6. **Anti-Halluzinations-Guardrail**: Help-Skill hat `disable_tools=True` und darf **ausschließlich** Registry-Inhalte als System-Context bekommen.
7. **Test-Suite**: Unit (Registry-Loader, Intent-Detectors), Integration (End-to-End Help-Queries), Anti-Halluzination (Registry-Removal → „Dazu habe ich keine Information“).

**Out-of-Scope (v3+):**
- Multilingual Answer-Generation (nur `i18n`-Feld-Struktur wird vorbereitet).
- Frontend-Quick-Action-Bubbles (UI-Task, separates Dossier).
- Dynamische Registry-Aktualisierung zur Laufzeit.

---

## 3. CODEBASE-ANCHORS (real files, verified)

| Zweck | Pfad | Status |
|---|---|---|
| Skill-JSONs (Vorbild-Schema) | `backend/skills/system/*.json`, `backend/skills/knowledge/*.json` | existiert ✓ |
| Intent-Engine | `backend/services/orchestrator/intent_engine.py` → `detect_all_intents` | existiert ✓ |
| Intent-Result-Schema | `backend/services/orchestrator/intent_engine.py` → `IntentDetectionResult` | existiert ✓ |
| Chat-Orchestrator | `backend/services/chat_orchestrator.py` (Intent-Dispatch ~Zeile 1105–1120) | existiert ✓ |
| Skill-Schema-Konvention | siehe `backend/skills/knowledge/query.json` (legacy_name / skill / capabilities / tags) | existiert ✓ |
| MCL-Spec | `documentation/architecture/JANUS_MCL_SPECIFICATION.md` | existiert ✓ |
| Neu (v2) | `backend/data/capability_registry.json` | **zu erstellen** |
| Neu (v2) | `backend/services/help_skill.py` | **zu erstellen** |
| Neu (v2) | `backend/services/capability_registry.py` (Loader + Auto-Discovery) | **zu erstellen** |
| Neu (v2) | `backend/skills/system/help.json` | **zu erstellen** |
| Neu (v2) | `backend/tests/test_help_skill.py` | **zu erstellen** |
| Neu (v2) | `backend/tests/integration/test_help_end_to_end.py` | **zu erstellen** |

---

## 4. ARCHITEKTUR (grounded)

### 4.1 Flow

```
User Prompt
   │
   ▼
intent_engine.detect_all_intents(user_text)
   │
   ├─► is_capability_query? ──┐
   ├─► is_howto_query?        ├──► HELP FAST-PATH (kein Planner, kein LLM-Tool-Loop)
   └─► is_navigation_query? ──┘           │
                                          ▼
                              help_skill.handle(query, intent_type)
                                          │
                                          ▼
                              capability_registry.lookup(...)
                                          │
                                          ▼
                              response_generator(template, registry_data)
                                          │
                                          ▼
                              {text, suggestions[], actions[]}
                                          │
                                          ▼
                              ExecutionResponse (normaler Finalizer-Path)
```

### 4.2 Intent-Binding-Contract

Neue Detektoren in `intent_engine.py`:
- `detect_capability_overview(text) -> bool` — matcht „was kannst du“, „was kann janus“, „deine fähigkeiten“, „features“
- `detect_how_to(text) -> bool` — matcht „wie kann ich“, „wie lade ich“, „wie benutze ich“, „wie funktioniert“
- `detect_navigation(text) -> bool` — matcht „wo finde ich“, „wo sind meine“, „wo ist“

`IntentDetectionResult` bekommt drei neue Boolean-Felder:
```python
is_capability_overview: bool = False
is_how_to: bool = False
is_navigation_query: bool = False
```

**Priorität**: Help-Intents feuern NUR wenn weder `is_identity_query` noch `is_greeting` noch `is_self_referential_query` zutreffen.

### 4.3 Orchestrator-Hook

In `chat_orchestrator.py`, **vor** `use_agent_factory`-Block (~Zeile 968), neue Fast-Path-Branch:
```python
if (wf.intents.is_capability_overview or wf.intents.is_how_to or wf.intents.is_navigation_query) \
        and not wf.has_image and not wf.is_policy_response:
    wf.help_result = await self.help_skill.handle(
        query=wf.user_text,
        intent_type=_resolve_help_intent(wf.intents),
        context={"chat_id": request.chat_id},
    )
    wf.final_text_to_generate = wf.help_result.answer
    wf.final_ui_command = wf.help_result.actions[0] if wf.help_result.actions else None
    wf.skip_llm_generation = True
    wf.use_agent_factory = False
```

---

## 5. DATENMODELL

### 5.1 Registry-Schema (`backend/data/capability_registry.json`)

```json
{
  "version": "1.0.0",
  "categories": {
    "file_management": {
      "display_name": "Dateiverwaltung",
      "icon": "📁",
      "description": "Verwalte Dateien auf deiner Festplatte",
      "abilities": [
        {
          "id": "file.upload",
          "label": "Dateien hochladen",
          "skill_refs": ["filesystem.upload"],
          "how_to": {
            "de": "Ziehe eine Datei per Drag & Drop in den Chat oder nutze das Upload-Symbol.",
            "en": "Drag and drop a file into the chat, or use the upload button."
          }
        }
      ],
      "ui_locations": {
        "files": {
          "label": "Dateimanager",
          "action": {"type": "open_module", "payload": {"module": "files"}}
        }
      }
    }
  }
}
```

### 5.2 Auto-Discovery (`capability_registry.py`)

Beim Laden: Parse ALL `backend/skills/**/*.json` und reichere die statische Registry mit `skill_refs` an. Quelle: `skill`-Feld + `capabilities`-Array (z.B. `"document_analysis"`, `"semantic_search"` aus `knowledge/query.json`). **Widerspruchs-Detektion**: Wenn Registry eine Ability referenziert, deren `skill_refs` nicht im Skills-Verzeichnis existiert → Log-Warning `CAPABILITY_REGISTRY_ORPHAN`.

### 5.3 Input/Output-Contract (Pydantic, bestehender Style analog `schemas.py`)

```python
# backend/services/orchestrator/help_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

HelpIntentType = Literal["capability_overview", "how_to", "navigation"]

class HelpInput(BaseModel):
    query: str
    intent_type: HelpIntentType
    context: Optional[Dict[str, Any]] = None
    language: str = "de"

class HelpAction(BaseModel):
    type: str  # z.B. "open_settings", "open_module"
    payload: Dict[str, Any] = Field(default_factory=dict)

class HelpOutput(BaseModel):
    answer: str
    suggestions: List[str] = Field(default_factory=list)
    actions: List[HelpAction] = Field(default_factory=list)
    source_category: Optional[str] = None  # für Audit/Tests
    fallback_used: bool = False  # True = „Dazu habe ich keine Information“
```

### 5.4 i18n-Vorbereitung

Jedes `how_to` und `display_name` darf ein Dict `{lang: str}` sein oder ein Plain-String (= implizit `de`). Generator wählt via `language` aus `HelpInput`; fehlt die Sprache → fallback auf `de`.

---

## 6. IMPLEMENTATION PLAN — AI STUDIO ORCHESTRATION

### 6.1 Phasen

| Phase | Liefergegenstand | Modell | Verifikation |
|---|---|---|---|
| **P1** | Architektur-Review + Detail-Schema (confirms §3–§5) | **SWE 1.6** | Signed-off durch AI Studio |
| **P2** | Capability Registry JSON (Content) | **Kimi K2.5** | `pytest backend/tests/test_help_skill.py::test_registry_loads` |
| **P3** | `capability_registry.py` (Loader + Auto-Discovery) | **Kimi K2.5** | Unit-Tests Registry-Loader |
| **P4** | `help_schemas.py` + `help_skill.py` Handler | **Kimi K2.5** | Unit-Tests Handler |
| **P5** | `intent_engine.py` Detektoren + `IntentDetectionResult`-Felder | **Kimi K2.5** | Unit-Tests Detectors |
| **P6** | `chat_orchestrator.py` Fast-Path-Hook | **SWE 1.6** (kritische Integration) | Integration-Test |
| **P7** | `backend/skills/system/help.json` Registration | **Kimi K2.5** | Skill-Schema-Validierung |
| **P8** | End-to-End-Test-Suite | **Kimi K2.5** | `pytest backend/tests/integration/test_help_end_to_end.py` |
| **P9** | Anti-Halluzinations-Regression | **SWE 1.6** | Registry-Mock-Ablation-Test |

### 6.2 Rollen-Matrix

**AI Studio (Orchestrator-Rolle)**
- Zerlegt v2-Spec in Phase-Prompts.
- Gibt jedem Sub-Modell **nur** den Kontext, den es braucht (Scope-Isolation).
- Reviewt Output, fordert Fixes an, signiert Phasen ab.
- Pflegt den Audit-Trail.

**SWE 1.6 (Architekt / Senior)**
- P1: Validiert Anchors aus §3 gegen echten Code (Dateipfade, Imports, Klassennamen).
- P6: Integriert den Fast-Path im `chat_orchestrator.py` — kritische Stelle weil neben `use_agent_factory`-Logik.
- P9: Designt Ablation-Tests (Registry-Removal, Orphan-Detection).

**Kimi K2.5 (Executor)**
- P2–P5, P7, P8: File-level Implementation nach exakten Contracts.
- Hält sich strikt an §5 und §7-Contracts.
- Produziert Tests parallel zu jedem Modul.

### 6.3 Handover-Blöcke (copy-paste für AI Studio)

> **BLOCK P1 → SWE 1.6**
> ```
> Aufgabe: Architektur-Review für Janus Help & Capability System v2.
> Lies: documentation/Planned Features/Janus Help.md §0–§5.
> Verifiziere gegen echten Code:
>   - backend/services/orchestrator/intent_engine.py (IntentDetectionResult, detect_all_intents)
>   - backend/services/chat_orchestrator.py (Zeile 960–980, use_agent_factory-Block)
>   - backend/skills/system/*.json (Schema-Konvention)
> Liefere: Markdown-Report mit (a) bestätigten Anchors, (b) Abweichungen, (c) finalem Detail-Schema für help_schemas.py.
> KEINE Implementation — nur Review.
> ```

> **BLOCK P3 → Kimi K2.5**
> ```
> Aufgabe: Implementiere backend/services/capability_registry.py.
> Inputs:
>   - Schema: §5.1 aus documentation/Planned Features/Janus Help.md
>   - Auto-Discovery: §5.2
>   - Orphan-Detection: Log-Warning "CAPABILITY_REGISTRY_ORPHAN"
> Output-Contract:
>   class CapabilityRegistry:
>     def __init__(self, registry_path: str, skills_dir: str): ...
>     def load(self) -> None: ...
>     def get_overview(self, language: str = "de") -> dict: ...
>     def get_how_to(self, ability_id: str, language: str = "de") -> str | None: ...
>     def get_navigation(self, query: str, language: str = "de") -> dict | None: ...
>     def all_categories(self) -> list[str]: ...
> Tests: backend/tests/test_capability_registry.py (min. 6 Tests, siehe §8.1).
> NICHTS an Orchestrator/Intent-Engine ändern.
> ```

> **BLOCK P6 → SWE 1.6**
> ```
> Aufgabe: Integriere Help-Fast-Path in backend/services/chat_orchestrator.py.
> Randbedingung: Fast-Path MUSS vor use_agent_factory-Evaluation greifen, aber NACH greeting/identity/opinion-Check.
> Referenz: §4.3.
> Regression-Test: Alle existierenden Tests in backend/tests/test_orchestrator_logic.py MÜSSEN weiterhin passen.
> Neu-Test: backend/tests/integration/test_help_end_to_end.py::test_capability_query_uses_fast_path
> ```

---

## 7. FILE CONTRACTS

### 7.1 `backend/services/help_skill.py`

```python
from backend.services.capability_registry import CapabilityRegistry
from backend.services.orchestrator.help_schemas import HelpInput, HelpOutput, HelpAction

class HelpSkill:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    async def handle(self, *, query: str, intent_type: str,
                     context: dict | None = None, language: str = "de") -> HelpOutput:
        # deterministic, NO LLM call
        ...
```

**Invariante:** Handler **darf nie** `llm_gateway.*` importieren oder aufrufen. Verletzung = CI-Fail.

### 7.2 `backend/skills/system/help.json`

```json
{
  "legacy_name": "help_query",
  "skill": "system.help",
  "version": "1.0.0",
  "sandbox_level": "read_only",
  "latency_class": "instant",
  "tags": ["system", "help", "meta"],
  "capabilities": ["self_explanation", "capability_listing", "how_to_guidance"],
  "is_agent_ready": false,
  "max_calls_per_turn": 1,
  "depends_on": [],
  "examples": [
    {"input": "Was kannst du?", "intent": "capability_overview"},
    {"input": "Wie lade ich eine Datei hoch?", "intent": "how_to"},
    {"input": "Wo finde ich meine Erinnerungen?", "intent": "navigation"}
  ]
}
```

### 7.3 MCL-Bridging (actions → ExecutionResponse)

- `HelpOutput.actions[0]` → `ExecutionResponse.ui_command` (existierendes Feld).
- Action-Types beschränkt auf existierende MCL-Ops (siehe `documentation/architecture/JANUS_MCL_SPECIFICATION.md`): `open_settings`, `open_module`, `focus_section`.

---

## 8. TEST-CONTRACTS

### 8.1 Unit: `backend/tests/test_capability_registry.py` (min. 6 Tests)
1. `test_registry_loads_without_error`
2. `test_auto_discovery_matches_skill_files` — alle `skill_refs` müssen in `backend/skills/**` existieren.
3. `test_orphan_skill_ref_logs_warning`
4. `test_get_overview_returns_all_categories`
5. `test_get_how_to_returns_de_fallback_when_en_missing`
6. `test_get_navigation_matches_by_keyword`

### 8.2 Unit: `backend/tests/test_help_skill.py`
1. `test_handle_capability_overview_returns_registry_categories`
2. `test_handle_how_to_returns_correct_ability_instruction`
3. `test_handle_navigation_returns_ui_action`
4. `test_handle_unknown_query_returns_fallback` — `fallback_used=True`, Text = `"Dazu habe ich keine Information."`
5. `test_handle_never_calls_llm_gateway` — mock `llm_gateway.reason_and_respond` und assert 0 calls.

### 8.3 Integration: `backend/tests/integration/test_help_end_to_end.py`
1. `test_capability_query_uses_fast_path` — mock `llm_gateway.reason_and_respond` und assert 0 calls für Prompt „Was kannst du?“.
2. `test_howto_query_returns_deterministic_answer`
3. `test_navigation_query_returns_ui_command`
4. `test_help_path_does_not_trigger_agent_factory`

### 8.4 Anti-Halluzinations-Regression: `backend/tests/test_help_anti_halluzination.py`
1. `test_registry_missing_category_returns_fallback` — Registry-Mock ohne Kategorie → Fallback greift.
2. `test_answer_only_contains_registry_strings` — substring-check: jedes Wort aus `answer` muss entweder generisches Template-Wort sein oder aus Registry stammen.

---

## 9. ACCEPTANCE CRITERIA (Definition of Done)

- [ ] `pytest backend/tests/test_capability_registry.py` — all pass
- [ ] `pytest backend/tests/test_help_skill.py` — all pass
- [ ] `pytest backend/tests/integration/test_help_end_to_end.py` — all pass
- [ ] `pytest backend/tests/test_help_anti_halluzination.py` — all pass
- [ ] `pytest backend/tests/test_orchestrator_logic.py` — **keine Regression**
- [ ] Help-Fast-Path: Prompt „Was kannst du?“ → Response-Latenz < 50 ms (P95, lokal gemessen).
- [ ] Zero `llm_gateway`-Calls im Help-Pfad (mock-verifiziert).
- [ ] Registry lädt auch wenn `backend/skills/` temporär leer → Log-Warning statt Crash.
- [ ] `CAPABILITY_REGISTRY_ORPHAN`-Warnings = 0 bei aktueller Codebase.
- [ ] Alle neuen Dateien haben keine TODOs / keine `pass`-Stubs.

---

## 10. ANTI-HALLUZINATIONS-GUARDRAILS (non-negotiable)

1. Help-Skill ruft **nie** ein LLM — reine Template-Rendering-Pipeline.
2. Registry ist **Single Source of Truth**. Zu einer Frage mit keinem Match → `fallback_used=True` + fester Text.
3. Jeder `answer`-String wird aus Registry-Feldern zusammengesetzt — keine freien LLM-Completions.
4. CI-Check (ruff/grep): Import von `llm_gateway` in `help_skill.py` = build-break.
5. Registry-Tests mit **Golden-File**-Snapshot (`backend/tests/fixtures/help_golden.json`), um versehentliche Text-Drift zu erkennen.

---

## 11. RISIKEN & ROLLBACK

| Risiko | Mitigation |
|---|---|
| Fast-Path-Hook trifft fälschlicherweise bei nicht-Help-Intents | Strikte Präzedenz nach greeting/identity/opinion (§4.2) + Integration-Test |
| Registry-JSON wird korrupt | Pydantic-Validierung beim Load + Fallback auf leere Registry + Log-Error |
| Intent-Detektoren haben False-Positives bei Audit-Requests | Konjunktive Guards: `is_audit_request=False` ist Voraussetzung |
| Rollback | Single-Flag `help_system.enabled` in Config; bei `False` greift Fast-Path nicht → alter Pfad aktiv |

---

## 12. SELBSTBEWERTUNG (was ich davon halte)

**Kurz:** Die v1-Idee ist **richtig und wichtig**. Aber das Dossier adressiert zu 80 % das „was“ und zu 20 % das „wie“ — für Solo-Implementation durch einen Menschen ok, für Multi-Agent-Orchestration (AI Studio → SWE 1.6 → Kimi) **unzureichend**.

**Die drei kritischsten Diamant-Upgrades in v2:**
1. **Auto-Discovery** statt manuell gepflegter Registry → verhindert Drift zwischen Skills und Registry.
2. **Fast-Path ohne LLM** → macht Help-Antworten deterministisch **und** schnell **und** halluzinationsfrei in einem Zug.
3. **Rollen-Split mit exakten Handover-Blöcken** → AI Studio kann ohne weiteres Nachfragen direkt Phase für Phase delegieren.

**Empfehlung vor dem Start:** Phase P1 (SWE-1.6-Review) **nicht überspringen**. Der Check gegen den tatsächlichen Code kostet 10 Minuten und verhindert, dass Kimi an falschen Anchors arbeitet.

---

---

# FEATURE DOSSIER: JANUS HELP & CAPABILITY SYSTEM (Self-Explaining AI) — v1 ORIGINAL (VISION-ANCHOR)

> Nachfolgend: das ursprüngliche Konzept-Dossier, unverändert als Vision-Anker.


🧠 1. ZIEL DES FEATURES

Das Janus Help & Capability System ermöglicht es Janus, seine eigenen Fähigkeiten, Nutzungsmöglichkeiten und Bedienlogik vollständig, korrekt und kontextabhängig zu erklären.

💥 CORE VALUE

💎 „Janus ist nicht nur ein Tool — Janus kann dir erklären, wie du ihn optimal benutzt.“

🚨 2. PROBLEM
❌ Aktueller Zustand
User wissen nicht:
was Janus kann
wie man Features nutzt
wo Dinge zu finden sind
❌ Konsequenz
geringe Nutzungstiefe
Frustration
Features bleiben unentdeckt
💎 3. LÖSUNG

👉 Zentrale Capability Registry + intelligenter Help-Skill

Janus beantwortet Fragen wie:

„Was kannst du alles?“
„Wie lade ich eine Datei hoch?“
„Wo finde ich meine Erinnerungen?“
🧱 4. ARCHITEKTURPOSITION
User Prompt
   ↓
Intent Detection (help / how_to / capability)
   ↓
💎 Help & Capability Skill (THIS)
   ↓
Capability Registry
   ↓
Response Generator
   ↓
Chat Output (+ optional Actions)
⚙️ 5. TECHNISCHER KONTRAKT
📥 INPUT
class HelpInput(BaseModel):
    query: str
    context: dict | None = None
📤 OUTPUT
class HelpOutput(BaseModel):
    answer: str
    suggestions: list[str] | None
    actions: list[dict] | None
🧩 6. CAPABILITY REGISTRY (KERNSTÜCK)
Struktur (zentral gespeichert)
{
  "file_management": {
    "name": "Dateiverwaltung",
    "description": "Verwalte Dateien auf deiner Festplatte",
    "abilities": [
      "Dateien erstellen",
      "Dateien löschen",
      "Dateien verschieben",
      "Dateien umbenennen"
    ],
    "how_to": {
      "upload": "Ziehe eine Datei per Drag & Drop in den Chat oder nutze das Upload-Symbol.",
      "find_file": "Sage z.B.: 'Finde die Datei Rechnung.pdf'"
    },
    "ui_locations": {
      "files": "Dateien findest du im Dateimanager-Modul"
    }
  }
}
🔐 7. GRUNDREGEL: KEINE HALLUZINATIONEN

💎 Janus darf ausschließlich aus der Registry antworten

❌ Verboten:
Features erfinden
unklare Aussagen
✔ Erlaubt:
nur validierte Fähigkeiten
🧠 8. INTENT DETECTION
Unterstützte Intent-Typen
🟢 Capability Overview
„Was kannst du?“
„Was kann Janus alles?“
🟡 How-To
„Wie lade ich eine Datei hoch?“
„Wie benutze ich den Bildeditor?“
🔵 Navigation
„Wo finde ich meine Erinnerungen?“
„Wo sind meine Dateien?“
🧠 9. RESPONSE GENERATOR
🟢 Capability Overview Output
Ich kann dir bei folgenden Dingen helfen:

📁 Dateiverwaltung
- Dateien erstellen, löschen, verschieben

🌐 Internet
- Informationen suchen
- Videos finden

🧠 Wissen
- Inhalte erklären und zusammenfassen
🟡 How-To Output
Du kannst eine Datei so hochladen:

👉 Ziehe sie einfach per Drag & Drop in den Chat  
👉 oder nutze das Upload-Symbol
🔵 Navigation Output
Deine Erinnerungen findest du:

👉 in den Einstellungen  
👉 unter dem Punkt „Erinnerungen“
💡 10. SMART SUGGESTIONS (OPTIONAL)

Nach jeder Antwort:

💡 Du kannst auch fragen:
- „Was kannst du alles?“
- „Wie erstelle ich eine Datei?“
🧩 11. UI ACTION INTEGRATION (MCL)
Beispiel:
{
  "actions": [
    {
      "type": "open_settings",
      "payload": {
        "section": "memory"
      }
    }
  ]
}

👉 ermöglicht:

direkte Navigation
bessere UX
⚠️ 12. EDGE CASES
❗ Unbekannte Frage
„Dazu habe ich keine Information.“
❗ Mehrdeutige Frage

→ Nachfrage stellen

🚀 13. ERWEITERUNGEN
🟡 Multilingual Support
Antworten in User-Sprache
🟡 Dynamische Features
Registry wird automatisch erweitert
🟡 Skill-Integration
jede neue Funktion registriert sich automatisch
🔥 14. SYSTEM-DEFINITION

💎 Das Help-System ist die zentrale Wissensquelle über Janus selbst.

💎 15. BEST PRACTICE

✔ klare Kategorien
✔ konkrete Anleitungen
✔ keine generischen Antworten

💎 16. FINAL FAZIT

❌ User muss selbst herausfinden, wie alles funktioniert
✔ Janus erklärt alles verständlich

💎 „Ein System ist nur so gut wie seine Erklärbarkeit.“