---
description: Bulk File Move Feature — Parameter-Upgrade + Intent-basierte Modell-Eskalation + RAG-Sortier-Policy
---

# Task FEAT-FS-BULK-MOVE: Bulk File Move Feature

## 1. Ziel
Bulk-Datei-Verschiebe-Operationen verbessern durch exakte Dateilisten statt Glob-Pattern, Intent-basierte Modell-Eskalation für komplexe Sortieraufgaben und RAG-Sortier-Policy für indizierte PDFs.

## 2. Beeinflusst
- Keine abhängigen Tasks

## 3. Anforderungen
### 3.1 Funktionale Anforderungen
- `move_files` Skill soll eine exakte Liste von Dateinamen (`file_names: List[str]`) statt eines Glob-Patterns akzeptieren
- Bei Sortier-Intents soll automatisch auf ein Logic-Tier-Modell eskaliert werden
- PDFs in `list_directory` sollen mit `[INDIZIERT]` markiert werden, wenn sie im IndexStore indiziert sind
- Neue Prompt-Direktive `rag_sort_policy` soll die RAG-Nutzung vor Verschiebe-Aktionen erzwingen

### 3.2 Nicht-funktionale Anforderungen
- Rate-Limits für FS-Skills erhöhen (create_directory: 3→20, move_file: 3→50, move_files: 3→10)
- Parameter-Trinity synchron halten (schemas.py, move_files.json, filesystem_manager.py)

## 4. Implementierung
### 4.1 Schema-Upgrade
- `backend/data/schemas.py`: `MoveFilesArgs` — `pattern` entfernt, `file_names: List[str]` hinzugefügt

### 4.2 Skill-JSON
- `backend/skills/filesystem/move_files.json`: Parameter `pattern` → `file_names: list[str]`, `max_calls_per_turn` auf 10 erhöht, Beschreibung mit Batch-Nutzungs-Hinweis

### 4.3 Backend-Logik
- `backend/services/filesystem_manager.py`: `move_files()` iteriert über `file_names` Liste statt Glob-Pattern
- `backend/services/filesystem_manager.py`: `list_directory()` mit PDF-Indizierungs-Markierung `[INDIZIERT]` via IndexStore-Check

### 4.4 Rate-Limits
- `backend/skills/filesystem/create_directory.json`: max_calls_per_turn 3→20
- `backend/skills/filesystem/move_file.json`: max_calls_per_turn 3→50, Warnung gegen Bulk-Missbrauch
- `backend/skills/filesystem/read_file.json`: PDF-Umleitung zu Knowledge-Tools

### 4.5 Intent-Override
- `backend/services/orchestrator/execution_dispatcher.py`: `_apply_pre_resolution_guards()` mit MOA_MODEL_HIERARCHY für Sortier-Intents (`sortiere` + `pdf/dateien`)
- `backend/services/orchestrator/execution_dispatcher.py`: Knowledge-Skills (`knowledge.query`, `knowledge.read_full_text`) zu `relevant_skill_ids` bei Sortier-Intent hinzufügen

### 4.6 RAG-Sort-Policy
- `backend/services/orchestrator/prompt_registry.py`: `rag_sort_policy` Direktive in `apply_verbosity_control` injiziert

### 4.7 Model Catalog
- `backend/services/model_catalog.py`: `get_models_by_provider()` Funktion erstellt

## 5. Verifikation
### 5.1 Unit-Tests
- Audit: Parameter Trinity synchron (file_names: List[str] in schemas.py, move_files.json, filesystem_manager.py) ✅

### 5.2 Integration-Tests
- Test mit Sortier-Intent erwartet: (a) Log zeigt `[INTENT-OVERRIDE] Sortier-Auftrag erkannt`, (b) Modell eskaliert zu Logic-Tier, (c) knowledge.query und knowledge.read_full_text in relevant_skill_ids

## 6. Ergebnis & Audit-Trail
### 6.1 Files Changed
| Datei | Änderung |
|-------|----------|
| `backend/data/schemas.py` | MoveFilesArgs: pattern → file_names: List[str] |
| `backend/skills/filesystem/move_files.json` | Parameter file_names, max_calls_per_turn 10, Batch-Hinweis |
| `backend/skills/filesystem/move_file.json` | max_calls_per_turn 50, Bulk-Missbrauch-Warnung |
| `backend/skills/filesystem/create_directory.json` | max_calls_per_turn 20 |
| `backend/skills/filesystem/read_file.json` | PDF-Umleitung zu Knowledge-Tools |
| `backend/services/filesystem_manager.py` | move_files() mit file_names-Iteration, list_directory() mit [INDIZIERT]-Markierung |
| `backend/services/orchestrator/execution_dispatcher.py` | _apply_pre_resolution_guards() mit Intent-Override + relevant_skill_ids |
| `backend/services/orchestrator/prompt_registry.py` | rag_sort_policy Direktive + Injektion |
| `backend/services/model_catalog.py` | get_models_by_provider() Funktion erstellt |

### 6.2 Was wurde gemacht
Bulk-Datei-Verschiebe-Operationen nutzen jetzt exakte Dateilisten für präzise Kontrolle. Komplexe Sortieraufgaben eskalieren automatisch zum Logic-Tier-Modell. PDFs in list_directory zeigen Indizierungs-Status. RAG-Sort-Policy erzwingt Knowledge-Query für indizierte Dateien vor Move-Operationen.

### 6.3 Test-Ergebnis
Audit: Parameter Trinity synchron ✅

## 7. Debugging-Log
Keine Probleme während der Implementierung.

## 8. Abgeschlossen
**Status:** 🥇 SEALED & COMPLETE (2026-04-24)
