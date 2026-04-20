# Skill Development Guide (Janus)

Dieser Guide ist der verbindliche Standard fuer neue Skills.

## 1) Input-Schema mit Pydantic definieren

Jeder Skill bekommt ein explizites Input-Schema in `backend/data/schemas.py`.

```python
from pydantic import BaseModel, Field

class DownloadFontArgs(BaseModel):
    family: str = Field(..., description="Font-Familie")
    weight: int = Field(400, ge=100, le=900)
```

Regeln:
- Pflichtfelder immer mit `...` markieren.
- Constraints (`ge`, `le`, `pattern`, `Literal`) aktiv nutzen.
- Beschreibungen (`description`) fuer LLM-Verstaendlichkeit setzen.

## 2) Handler-Funktion implementieren

Handler kommen in die passende Domain (z. B. `backend/services/...`).

```python
def download_font(family: str, weight: int, db=None) -> dict:
    # Domain-Logik
    return {
        "status": "ok",
        "data": {
            "family": family,
            "weight": weight,
            "saved": True,
        },
    }
```

## 3) SkillResponse ist Pflicht

Jeder Skill MUSS im `SkillResponse`-Format enden:
- `status`: `ok | error | permission_required`
- `data`: Payload bei Erfolg
- `error`: `{code, message, details?}` bei Fehlern
- `execution_time_ms`: optionale Laufzeit des Skill-Aufrufs

Referenz: `backend/data/schemas.py -> SkillResponse`.

Wichtig:
- Keine freien String-Fehler als einziges Ergebnis.
- Fehler immer mit stabilem `error.code` liefern.

## 4) Tool registrieren

Tool in `backend/tool_registry.py` registrieren:
- `func`
- `args_schema`
- `description`

Dabei gilt:
- Funktionsname = Legacy-Name (fuer Rueckwaertskompatibilitaet)
- Skillname wird ueber Mapping vergeben (siehe naechster Schritt)

## 5) Mapping in `skill_mapping.json`

Jeder neue Skill braucht einen Eintrag in:
- `documentation/skill_mapping.json`

Format:

```json
{
  "download_font": {
    "skill": "system.download_font",
    "capabilities": ["file_read", "font_management"]
  }
}
```

Regeln:
- Links: Legacy-Toolname (Handler/Funktionsname)
- Rechts: Objekt mit `skill` (`<domain>.<action>`) und `capabilities`
- Domain konsistent waehlen (`knowledge`, `filesystem`, `system`, ...)
- Capabilities als kurze Funktions-Labels definieren (`document_analysis`, `file_read`, `mail_write`, ...)

## 5b) Modularer Skill-Catalog (V3.2)

Produktiv gilt jetzt der modulare Catalog unter:
- `backend/skills/<domain>/<action>.json`

Empfohlenes Dateiformat:

```json
{
  "legacy_name": "delete_file",
  "skill": "filesystem.delete_file",
  "version": "1.0.0",
  "sandbox_level": "workspace_only",
  "capabilities": ["file_delete", "workspace_mutation"],
  "max_calls_per_turn": 3,
  "depends_on": []
}
```

Hinweis:
- `documentation/skill_mapping.json` bleibt als Fallback/Kompatibilitaet erhalten.
- Neue Skills bevorzugt direkt im `backend/skills/` Catalog eintragen.

## 6) Risiko-Level festlegen

Jeder Skill braucht eine Risk-Klassifikation fuer die Policy:
- `read_only`: nur Lesen/Analyse
- `confirm_required`: potenziell riskante Side-Effects (z. B. delete, write, send)
- `restricted`: hochkritisch, zusaetzliche Restriktionen

Checklist:
1. Side-Effects vorhanden?
2. Externe Systeme betroffen (Datei, Mail, Kalender, Netzwerk)?
3. User-Consent erforderlich?

Policy muss den Skill vor Handler-Ausfuehrung bewerten.

## 6b) Versioning & Sandbox-Level

Jeder produktive Skill sollte setzen:
- `version`: semantische Version (`MAJOR.MINOR.PATCH`), z. B. `1.0.0`
- `sandbox_level`:
  - `unrestricted`
  - `workspace_only`
  - `read_only_fs`

Regel:
- Bei `workspace_only` prueft der Executor Pfad-Argumente vor Dispatch.
- Verstoesse werden mit `error.code = SANDBOX_VIOLATION` blockiert.

## 6c) Skill-Komposition (`depends_on`)

Wenn ein Skill andere Skills voraussetzt, trage sie in `depends_on` ein.
Beispiel:

```json
"depends_on": ["knowledge.query", "system.wikipedia_summary"]
```

Der Router validiert Abhaengigkeiten beim Catalog-Load und loggt fehlende Eintraege.

## 6d) Building Macros with Internal Skill Calls

Composite Skills koennen andere Skills direkt aus ihrem Handler heraus aufrufen. Dabei gelten folgende Regeln:

1. Verwende `call_internal_skill(skill_id: str, args: dict)` aus `ToolExecutor`.
   - Es ist **keine** neue LLM-Runde, das Makro bleibt innerhalb eines Skillturns.
   - Die originale `trace_id` wird transparent weitergereicht, damit alle Steps konsistent protokolliert werden.
2. Jede interne Aufruf-Target wird **erneut durch die Policy** geprüft (`POLICY: REQUIRE_CONSENT` blockiert auch interne Makros).
3. Telemetrie markiert interne Calls mit `__call_type = internal` in Arguments/Response, so dass Dashboards Composite-Flows erkennen.
4. Achte auf `SkillResponse`-Consistency und dokumentiere Backup-/Rollback `details` im Fehlerfall.
5. Trage `depends_on` ein, wenn ein Macro bestimmte Skills voraussetzt, damit der Skill-Catalog die Dependency-Linie sichtbar macht.

Beispiel: `knowledge.hardened_edit` sichert ein PDF, kopiert eine Backup-Datei und ruft dann `knowledge.edit_pdf` intern.

## 7) Test-Mindeststandard

Pflicht fuer jeden neuen Skill:
1. Contract-Test: Schema + SkillResponse (ok/error)
2. Policy-Test: `REQUIRE_CONSENT`/Bypass-Verhalten falls relevant
3. Mapping-Smoke: Name ist via SkillRouter aufloesbar
4. Guardrail-Test: `max_calls_per_turn` blockiert Mehrfachaufrufe mit `RATE_LIMIT_EXCEEDED`
5. Trace-Test: Mehrere Calls in einem Turn teilen dieselbe `trace_id`

## 8) Agent-Grade Metadaten & Guardrails

`SkillMetadata` (siehe `backend/data/schemas.py`) sollte fuer produktive Skills gepflegt werden:
- `examples`: in-context Beispiele fuer robuste Tool-Calls
- `latency_class`: `fast|normal|slow`
- `tags`: freie Klassifikation
- `capabilities`: Faehigkeitslabels fuer Capability-Routing
- `is_agent_ready`: Freigabe fuer Agent-Komposition
- `max_calls_per_turn`: harte Ausfuehrungsgrenze pro Turn (Default: 3)

## 9) Deep Tracing (Flight Recorder)

Jeder Tool-Call wird in `SkillTelemetry` gespeichert mit:
- `trace_id` (gleich fuer alle Calls eines Requests)
- `arguments_json` (vollstaendige Input-Argumente)
- `response_json` (vollstaendige Contract-Antwort)
- `latency_ms`, `success`, `error_code`

Regel: Telemetrie darf den Chat-Flow nie blockieren (Fehler beim Logging nur warnen).

## 9b) Dry-Run Mode (Simulation)

`ToolExecutor.execute_tool_calls(..., dry_run=True)` fuehrt Handler nicht aus,
sondern liefert:
- `status = dry_run_success`
- geplanten Aufruf (`planned_call`) in `data`

Nutzen:
- sichere End-to-End Agent-Tests ohne reale Side-Effects (Delete/Send/Write).

## 9c) Provider-spezifisches MoA-Routing

Fuer Skills mit unterschiedlichen optimalen Modellen pro Provider kann `optimal_model_tier` als Dict angegeben werden.

### Syntax

```json
{
  "optimal_model_tier": {
    "openai": "balanced",
    "gemini": "speed", 
    "ollama": "speed"
  }
}
```

### Verfügbare Tiers

- `speed`: Schnellstes Modell (z.B. `gpt-5.4-mini`, `gemini-3-flash-preview`)
- `balanced`: Ausgewogenes Modell (z.B. `gpt-5.4-mini`)
- `logic`: Leistungsstarkes Modell (z.B. `gpt-5.4-pro`, `gemini-3-pro-preview`)
- `vision`: Vision-fähiges Modell (z.B. `gpt-4o`, `gemini-pro-vision`)

### Ablauf

1. **Skill-JSON**: `optimal_model_tier` als Dict mit Provider-Mapping
2. **ToolManager**: `get_optimal_model_tier(skill_id, provider)` löst das optimale Tier auf
3. **Gateway-Routing**: `resolve_moa_model()` wählt das passende Modell aus der Hierarchie
4. **Modell-Wechsel**: Tool-Loop läuft mit dem optimierten Modell
5. **Rücksprung**: Finale Synthese erfolgt wieder mit dem User-Basismodell

### Logging

Bei aktivem MoA-Wechsel wird geloggt:
```
💎 SKILL-MOA AKTIV: Wechsle für Skill 'system.websearch' (Tier=speed) von 'gemini-3-pro-preview' → 'gemini-3-flash-preview' [Provider: gemini]
```

### Legacy-Unterstützung

Alte Skills mit String-Format werden weiterhin unterstützt:
```json
{
  "optimal_model_tier": "logic"  // Fallback für alle Provider
}
```

## 10) Deterministic Renderer (Diamond Standard)

Fuer Skills mit stabiler, strukturierter Ausgabe (z.B. Routing, Wetter, Laenderinfo)
kann ein **Deterministic Renderer** implementiert werden. Dieser erzeugt die Antwort
direkt aus den Tool-Ergebnis-Daten – **ohne LLM-Synthese** – was Latenz, Kosten und
Determinismus verbessert.

### Architektur

```
Tool-Ergebnis (SkillResponse)
  └─ status: "ok" + data: {...}
       └─ Registry: get_renderer(skill_id)
            └─ Renderer.render(data) → Markdown-Text
                 └─ Direkte Rueckgabe (kein LLM-Call)
```

### Neuen Renderer erstellen

1. Erstelle `backend/renderers/implementations/<skill>_renderer.py`
2. Implementiere `BaseRenderer` (ABC aus `backend/renderers/base.py`):

```python
from backend.renderers.base import BaseRenderer
from backend.renderers.registry import register_renderer

class MySkillRenderer(BaseRenderer):
    skill_id = "system.my_skill"

    def render(self, data: dict) -> str:
        value = data.get("field", "Standardwert")
        return f"**Ergebnis:** {value}"

register_renderer(MySkillRenderer())
```

3. Import in `backend/renderers/registry.py` → `_ensure_loaded()` hinzufuegen
4. Skill-JSON: `"deterministic_renderer": true` setzen
5. Tests in `tests/renderers/test_renderers.py` ergaenzen (full/partial/empty data)

### Regeln

- **Graceful Degradation:** Bei Renderer-Fehler faellt das System automatisch auf
  LLM-Synthese zurueck. Kein Renderer darf eine Exception nach aussen propagieren.
- **`.get()` mit Defaults:** Jedes Feld mit `data.get("key", "Fallback")` abrufen.
- **Nur `status=ok`:** Renderer werden nur bei erfolgreichen Tool-Ergebnissen aufgerufen.
  Fehler-Responses (`status=error`) gehen weiterhin durch die LLM-Synthese.
- **Mindestlaenge:** Gerenderte Texte unter 10 Zeichen werden als Fehlschlag gewertet.

### Aktuelle Renderer

| Skill | Renderer-Klasse | Seit |
|-------|----------------|------|
| `system.routing` | `RoutingRenderer` | 2026-03-17 |
| `system.weather` | `WeatherRenderer` | 2026-03-17 |
| `system.country_info` | `CountryInfoRenderer` | 2026-03-17 |

## 10b) Gemini Link-Renderer & ID-Anchors (Diamond Standard)

Fuer Websearch-Skills mit dynamischen, aber strukturierten Links (z.B. Produktpreise, Wikipedia-Referenzen)
wurde ein spezialisierter **ID-basierter Link-Renderer** implementiert. Dieser trennt Link-Generierung
vom LLM-Synthese-Prozess und eliminiert Halluzinations-Risiken bei URLs.

### Prinzip: ID-Anchor Protocol

```
Phase 1: LLM Synthese
  └─ Prompt enthält ID-ANCHOR DIRECTIVE: "Nutze [[PRODUCT:id]] fuer bekannte Produkte"
  └─ LLM liefert Text mit [[PRODUCT:iphone_15]] statt roher URLs

Phase 2: Deterministic Rendering
  └─ LinkRenderer ersetzt [[PRODUCT:id]] durch Deep-Link aus config/idealo_product_map.json
  └─ Unbekannte IDs werden gestrippt (Fail-Safe)
  └─ Wikipedia-Links aus groundingMetadata werden am Satzende angehaengt
```

### Architektur-Komponenten

| Modul | Zweck |
|-------|-------|
| `backend/llm_providers/gemini/link_renderer.py` | Zentrale Rendering-Logik, I/O-frei |
| `backend/llm_providers/gemini/constants.py` | ID_INJECTION_DIRECTIVE, PRICE_PRECISION_DIRECTIVE |
| `config/idealo_product_map.json` | Produkte mit IDs, URLs und Aliassen |

### Implementierung fuer neue Skills

1. **Compiler-Direktive injizieren** (falls Skill Produkte referenziert):
```python
from backend.llm_providers.gemini.constants import ID_INJECTION_DIRECTIVE
constraints.append(ID_INJECTION_DIRECTIVE)
```

2. **Renderer im Gateway verwenden**:
```python
from backend.llm_providers.gemini.link_renderer import get_link_renderer

renderer = get_link_renderer()
rendered_text = renderer.render_links(
    text=llm_output,
    grounding_chunks=grounding_metadata.get("groundingChunks", []),
    enable_idealo=True,
    enable_wikipedia=True
)
```

3. **Produkt-Map erweitern** (falls neue Produkte):
```json
{
  "product_id": {
    "name": "Display Name",
    "url": "https://www.idealo.de/...",
    "aliases": ["alias1", "alias2"]
  }
}
```

### Sicherheits-Features

- **max_links_per_turn = 8**: Verhindert UI-Freeze bei Halluzinations-Loops
- **Fail-Safe fuer unbekannte IDs**: [[PRODUCT:unknown]] wird komplett entfernt
- **Keine HTTP-Checks im Hot-Path**: Link-Validierung findet offline statt

### Referenz-Implementierung

Siehe `backend/llm_providers/gemini/link_renderer.py` fuer die vollstaendige
Diamond-Standard Implementierung mit:
- ID-Aufloesung via Regex
- Alias-Matching fuer fuzzy Produktnamen
- Wikipedia-Link-Extraktion aus groundingMetadata
- Sicherheitslimits und Graceful Degradation

## 11) Definition of Done fuer einen neuen Skill

Ein Skill gilt als fertig, wenn:
- Input-Schema vorhanden
- SkillResponse-konforme Ausgaben vorhanden
- Mapping in `skill_mapping.json` vorhanden
- Catalog-Datei unter `backend/skills/<domain>/<action>.json` vorhanden
- Risk-Level dokumentiert und Policy geprueft
- Capability-Labels und `max_calls_per_turn` sinnvoll gesetzt
- `version`, `sandbox_level`, `depends_on` gepflegt
- Trace-/Telemetry-Daten bei Testaufruf vorhanden
- Contract-/Integrationstests gruen

## 7. Skill Naming and Deprecation Policy (Diamond-Standard)

Um die Stabilitaet des Systems zu gewaehrleisten, gelten folgende verbindliche Regeln fuer die Benennung und Aenderung von Skills:

1. **Kanonisches Format:** Alle neuen Skill-IDs MUeSSEN dem Format `domain.action` folgen (z.B. `calendar.create_event`). Die ID ist der primaere, unveraenderliche Schluessel eines Skills.
2. **Keine Umbenennung:** Einmal definierte Skill-IDs sollten nicht mehr geaendert werden. Bevorzuge die Erstellung eines neuen Skills mit einer besseren ID, falls die alte irrefuehrend ist.
3. **Ausnahmefall: Umbenennung mit Deprecation:** Falls eine Umbenennung unvermeidbar ist (z.B. bei einem grossen Refactoring), MUSS der `legacy_name` im Skill-Katalog (`<skill>.json`) gesetzt werden.
   - Der Wert muss die **exakte alte Skill-ID** sein.
   - Dieser Alias MUSS fuer mindestens einen vollen Release-Zyklus aktiv bleiben.
   - Es MUSS ein Ticket erstellt werden, um den `legacy_name` im Folge-Release zu entfernen.
