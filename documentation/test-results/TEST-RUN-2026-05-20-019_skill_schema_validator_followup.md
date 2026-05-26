# Skill Schema Validator Follow-up

## Kontext

Der globale Validator `backend/tools/validate_skill_schemas.py` war nach Abschluss von TEST-RUN-2026-05-20-019 rot, weil er Skill-Manifeste direkt gegen Python-Funktionssignaturen verglich. Das erzeugte falsche Fehler fuer injizierte Runtime-Parameter wie `db`, `api_key`, `provider`, `model`, Wrapper-Objekte und ToolManager-registrierte Pydantic-Schemas.

## Umsetzung

- Validator vergleicht deklarierte Manifest-Input-Contracts jetzt gegen die LLM-facing ToolManager-Schemas.
- Metadata-only-Manifeste werden als gueltig behandelt, weil ihr Runtime-Schema aus `register_all_tools()` stammt.
- Echte Manifest-Contract-Abweichungen wurden behoben:
  - `filesystem.delete_directory`: `directory_path` -> `path`
  - `filesystem.list_directory`: `pattern` ergaenzt
  - `video.search`: `min_views` und `safe_search` ergaenzt
  - `video.understand`: `source` ergaenzt
- Video-Understanding ist nun kanonisch als `video.understand` registriert.
- Skill-Katalog laedt bei `legacy_name` zusaetzlich den kanonischen `skill`-Namen als Self-Alias.

## Verifikation

- `$env:PYTHONIOENCODING='utf-8'; python backend\tools\validate_skill_schemas.py` -> PASS
- `python -m pytest backend\tests\test_skill_selector_capability_registry_integrity.py backend\tests\test_capability_registry.py backend\tests\unit\test_capability_registry_logic.py backend\tests\unit\test_skill_selector_filesystem_calendar.py -q` -> 41 passed
- `python -m py_compile backend\tools\validate_skill_schemas.py backend\tool_registry.py backend\services\agent_planner.py backend\services\capability_registry.py backend\services\tool_manager.py` -> PASS

## Ergebnis

Der zuvor benannte Restbefund ist abgeschlossen. Der Validator ist wieder als CI-/Audit-Signal nutzbar.
