# 🏛️ Diamond Refactoring Roadmap (Elite Standard)

**Zweck:** Geplante Zerlegung von God-Objects zur Sicherstellung der Systemstabilität.  
**Status:** Initialer Entwurf nach Code-Weight-Audit April 2026. **Cleanup-Phase (Imports / F401): COMPLETE** (SYS-CLEANUP-F401, 2026-04-10). **Skill Contract V1 (Tool-Rollout): COMPLETE** (SYS-SKILL-CONTRACT-V1, 2026-04-11).  
**Referenz:** ORCH-TRANSFORM-EPIC (Vollständige ChatOrchestrator Transformation als Template)

---

## ✅ Skill Contract V1 (Tool-Rollout / `ToolResultV1`) — COMPLETE

| Maßnahme | Status |
|----------|--------|
| Einheitlicher Tool-Rückgabevertrag (`ToolResultV1` in `backend/data/schemas_tools.py`) | **COMPLETE** |
| Ziel-Tools (u. a. Calendar, Gmail, Contact, Memory) auf Vertrag umgestellt | **COMPLETE** |
| Legacy-Kompatibilität bei Serialisierung (`success`, `output` in `model_dump()`) | **COMPLETE** (`@computed_field`, siehe `WHAT_I_LEARNED.md`) |
| Namens-Brücke `contacts_tools` → `contact_tools` | **COMPLETE** (Thin Re-Export) |

*Weitere Architektur-Refactors (TOP 5 God-Objects) bleiben wie unten — unabhängig vom Skill-Contract-Rollout.*

---

## ✅ Cleanup-Phase (Imports) — COMPLETE

| Maßnahme | Status |
|----------|--------|
| Ruff `F401` unter `backend/` (ohne `venv`) | **0 Treffer** — ungenutzte Imports entfernt oder explizite Re-Exports / `__all__` |
| Legacy-Ollama-Einstiegspunkte | **`ollama_service.py` / `ollama_adapter.py`** als Thin-Facade-Shims (keine duplizierte Logik) |
| Syntax-Check | **`python -m py_compile`** über `backend/**/*.py` (ohne `venv`) PASS |

*Nächste Phasen sind **Architektur-Refactors** (siehe TOP 5), nicht Import-Hygiene.*

---

## 🎯 TOP 5 REFAC-TARGETS

### 1. Vision Fusion Engine (`backend/services/vision/utils.py`) — **Architecture Work in Progress**
- **Gewicht:** ~6.500 Zeilen
- **Problem:** Vermischung von statischen Thresholds, CLIP-Mapping und Live-Reporter-Logik
- **Ziel:** Split in `vision_constants.py`, `fusion_engine.py` und `reporter_pipelines.py`
- **Pattern:** Service-Agnostic Dispatcher (wie bei ChatOrchestrator)
- **CU-Schätzung:** 8
- **Status-Hinweis:** Noch **nicht** wie der Orchestrator zerlegt — bewusst als **Architecture Work in Progress** geführt, bis Split und Re-Exports stabil sind.

### 2. Geo-Intelligence Service (`backend/tools/geo_service.py`)
- **Gewicht:** ~2.300 Zeilen
- **Problem:** Hält Scraping, Geocoding und LLM-Logik in einer Klasse
- **Ziel:** Umstellung auf das Registry-Pattern (wie Orchestrator)
- **Pattern:** Registry-Pattern mit dedizierten Sub-Modulen
- **CU-Schätzung:** 6

### 3. Memory Core Manager (`backend/services/memory/`, Shim `memory_manager.py`) — **COMPLETE ✅**
- **Gewicht:** Ehem. ~1.600 Zeilen Monolith → Paket `backend/services/memory/` + Thin-Shim
- **Problem:** Zu breite API (CRUD, Retrieval, …) im God-Object
- **Ziel:** Trennung der Verantwortlichkeiten nach Diamond-Standard (**Slice 1:** CRUD + Retrieval extrahiert)
- **Pattern:** `crud_service.py` + `retrieval_service.py` + `__init__.py`-Barrel; **`memory_manager.py`** als Kompatibilitäts-Shim (`from backend.services.memory import *` + Legacy-Attribute)
- **CU-Schätzung:** 7
- **Epic (abgeschlossen):** `documentation/tasks/task_020_memory_core_refactor_epic.md` (**Task 020**)
- **Status-Hinweis:** Target #3 **COMPLETE ✅**; Fan-in bleibt über Shim stabil; optionale Folge-Slices (weitere Auslagerung) siehe Epic §6.

### 4. PDF Generation Engine (`backend/tools/pdf_generator.py`)
- **Gewicht:** ~1.800 Zeilen
- **Problem:** Layout-Logik hart mit Dateisystem-Operationen verdrahtet
- **Ziel:** Trennung von Layout-Engine und I/O-Layer
- **Pattern:** Engine + Adapter Pattern
- **CU-Schätzung:** 5

### 5. Link-Rendering Framework (`backend/llm_providers/gemini/link_renderer.py`)
- **Gewicht:** ~1.556 Zeilen (Ist-Stand Audit)
- **Problem:** Monolithischer Renderer mit vielen Skill-Spezialpfaden (Gemini)
- **Ziel:** Provider-Agnostic Core + skill-spezifische Adapter / Registry
- **Pattern:** Strategy Pattern mit Registry (analog Orchestrator)
- **CU-Schätzung:** 6

---

## 📊 Code-Weight-Übersicht

| Modul | Zeilen | Komplexität | Priorität | Architektur-Status |
|-------|--------|-------------|-----------|-------------------|
| Vision Fusion Engine | ~6.500 | Hoch | P1 | **Work in Progress** (Split geplant, noch monolithisch) |
| Geo-Intelligence Service | ~2.300 | Mittel | P2 | Geplant |
| Memory Core Manager | ~1.600 → Paket + Shim | Hoch | P1 | **COMPLETE ✅** (Task 020 — `memory/crud_service`, `memory/retrieval_service`, Shim `memory_manager.py`) |
| PDF Generation Engine | ~1.800 | Mittel | P2 | Geplant |
| Link-Rendering Framework | ~1.556 | Hoch | P2 | Geplant |

---

### 🔍 Audit Findings 2026-04-10

*Quelle: statische Analyse über `backend/` (ohne `venv/`); Ruff F401; AST-Tiefe für Kontrollfluss.*

#### Circular Dependency Check (Import-Graph, modul-exakt)

- **Methode:** Pro `.py`-Datei als Knoten `backend.…`; Kante nur, wenn ein `import` / `from … import` ein **existierendes** Zielmodul (gleiche Datei) referenziert — **keine** Wildcard-Expansion aller Submodules.
- **Ergebnis — starke Zusammenhangskomponenten (SCC) mit >1 Modul:**
  1. **Großcluster (~40 Module):** u. a. `backend.main`, `backend.api.routers.{chat,memory,projects,styles}`, `backend.services.chat_orchestrator`, `backend.services.llm_gateway`, `backend.services.tool_executor`, `backend.tool_registry`, mehrere `llm_providers.*.gateway`, `backend.utils.intent_classifier`, diverse `tools.*` und `orchestrator/*`. Das ist ein **Hub-/Fächer-Graph** (viele Pfade über gemeinsame Zentralen), nicht zwingend ein klassischer Zwei-Modul-Importzyklus — signalisiert aber **hohe globale Kopplung**.
  2. **`backend.data.database` ↔ `backend.data.models`** (2 Module) — typisch für SQLAlchemy-Modelle und Session-Binding.
  3. **Renderer-Cluster (~11 Module):** `backend.renderers.registry` und `backend.renderers.implementations.*` — Registry importiert Implementierungen, Implementierungen registrieren sich über Registry.
- **api/ ↔ services/ (direkte Kanten):** In dieser Modellierung gibt es **keine** Kanten `backend.services.*` → `backend.api.*` (0). **api → services** kommt vor (Router importieren Services) — **erwartungskonform**.
- **Limitation:** Laufzeit-Imports (`importlib`, dynamische Strings) und Package-`__init__`-Nebenwirkungen sind **nicht** vollständig erfasst.

#### Complexity Mapping (max. Kontrollfluss-Verschachtelung > 4)

Gemessen als maximale Tiefe von `if` / `for` / `while` / `with` / `try` / `match` im Funktionsrumpf (ohne Tests). **Top 5:**

| Rang | Tiefe | Ort | Methode |
|------|-------|-----|---------|
| 1 | **13** | `backend/services/vision/plugins/footwear_plugin.py` | `FootwearPlugin.evaluate` |
| 2 | **12** | `backend/services/vision/plugins/necklace_plugin.py` | `NecklacePlugin.evaluate` |
| 3 | **10** | `backend/services/orchestrator/execution_dispatcher.py` | `execute_generation` |
| 4 | **9** | `backend/api/routers/images.py` | `get_preview_size` |
| 5 | **9** | `backend/services/memory_manager.py` | `save_memory_snippet` |

*Weitere Kandidaten auf Tiefe 9 (gleichauf):* `OpenAIImageGeneration.generate_image` (`capabilities/openai_image_generation.py`), `GeminiServiceProvider.generate_response` (`gemini/service.py`), `HairPlugin.evaluate` (`vision/plugins/hair_plugin.py`).

#### Pattern Divergence (Registry / Handler wie Orchestrator)

Module unter `backend/services/`, die **explizit** das eingeführte Muster nutzen (`prompt_registry`, `policy_handler`, `intercept_handler` / `PromptRegistry`): **nur**  
`chat_orchestrator.py`, `orchestrator/execution_dispatcher.py`, `orchestrator/prompt_registry.py`, `orchestrator/policy_handler.py`, `orchestrator/intercept_handler.py`.

**Folge:** Größere Services (`memory_manager`, `tool_executor`, `vision_service`, `ollama_manager`, …) und Tools folgen **noch nicht** diesem Muster — weder Pflicht noch Fehler, aber **inkonsistent** zur „Diamond Elite“-Orchestrierung.

#### Ghost Code Detector

- **Ungenutzte Imports (Ruff `F401`):** **BEREINIGT (SYS-CLEANUP-F401, 2026-04-10).** Zielzustand: `ruff check backend --select F401` → **0** (ohne `venv`). Side-Effect-Imports über `from . import m as m` / `__all__` abgesichert.
- **Legacy-Hinweis:** Aggressive `--fix`-Läufe können Duplikat-Module beschädigen — Thin-Facade-Shims bevorzugen (siehe `WHAT_I_LEARNED.md` → Thin Facade / Shim Pattern).
- **Ungenutzte Funktionen:** Kein vollständiger Lauf mit `vulture` im Workspace; Empfehlung: `pip install vulture` + CI-Job oder Coverage-gestützte Bereinigung.

#### Refac-Impact / Kopplungs-Score (1 = gering, 10 = sehr riskant)

Subjektive Einschätzung auf Basis Import-Fächer, öffentlicher API-Fläche und Audit-Graph:

| Datei | Kopplungs-Score | Kurzbegründung |
|-------|-----------------|----------------|
| `vision/utils.py` | **7** | Riesige Oberfläche; wenige direkte Importer, aber zentral für Live-Portrait/Orchestrator-Pfad; Split erfordert stabile Re-Exports. |
| `geo_service.py` | **4** | Primär über `tool_registry` angebunden; überschaubare Produktions-Fan-in. |
| `memory_manager.py` | **8** | Hohe Fan-in (`main`, API `memory`, Orchestrator, Extractor, Tools, Context-Builder). |
| `pdf_generator.py` | **5** | Storybook, `pdf_editor`, Registry; mittlere Kopplung, klare Tool-Grenze. |
| `gemini/link_renderer.py` | **3** | Schwerpunkt Gateway + Tests; relativ isoliert splittbar. |

---

## 🔧 Erfolgsmetrik (ORCH-TRANSFORM-EPIC Template)

**Ziel:** Jedes Refac-Target erreicht den Status:
- ✅ **ZERO** harte Keywords/Regex/Prompts im Hauptmodul
- ✅ **6+** dedizierte Service-Module extrahiert (wo sinnvoll)
- ✅ **Syntax-Check** PASS für alle neuen Module
- ✅ **Import-Check** PASS für alle Cross-Module-Dependencies
- ✅ **Diamond Gold** Zertifizierung

---

## 📝 Notizen

- **Epic-Referenz:** ORCH-TRANSFORM-EPIC (abgeschlossen 2026-04-10)
- **Pattern-Referenz:** `WHAT_I_LEARNED.md` → "Service-Agnostic Dispatcher Pattern (V2)"
- **Nächster Schritt:** Architecture Work in Progress — **Vision Fusion Engine** (`vision/utils.py`). **Memory Core Manager (Target #3):** ✅ **COMPLETE** — siehe Task 020.

---

**Version:** 1.3 — Target #3 Memory Core (Task 020) **COMPLETE ✅**  
**Erstellt:** 2026-04-10  
**Autor:** Kimi K2.5 (basierend auf ORCH-TRANSFORM-EPIC Erfolg); Cleanup-Delta 2026-04-10; Task-020-Delta 2026-04-12
