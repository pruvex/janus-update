from __future__ import annotations

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / "backend" / "skills"


def iter_skill_catalogs() -> list[Path]:
    return sorted(SKILLS_ROOT.rglob("*.json"))


def load_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        print(f"ERROR: Konnte {path} nicht lesen: {exc}")
        return None
    if not isinstance(data, dict):
        print(f"ERROR: {path} enthält kein JSON-Objekt.")
        return None
    return data


def check_coverage() -> int:
    missing_flag: list[tuple[str, Path]] = []
    invalid_json = False

    for path in iter_skill_catalogs():
        payload = load_json(path)
        if payload is None:
            invalid_json = True
            continue

        if payload.get("is_agent_ready") is not True:
            continue

        if "deterministic_renderer" in payload:
            continue

        skill_id = str(payload.get("skill") or path.stem).strip() or path.stem
        missing_flag.append((skill_id, path))

    if invalid_json:
        print("\nRenderer-Coverage-Check konnte nicht vollständig ausgewertet werden.")
        return 2

    if not missing_flag:
        print("OK: Alle agent-ready Skills haben ein `deterministic_renderer`-Flag.")
        return 0

    print("WARNUNG: Agent-ready Skills ohne `deterministic_renderer`-Flag gefunden:\n")
    for skill_id, path in missing_flag:
        rel_path = path.relative_to(PROJECT_ROOT)
        print(f"- {skill_id} ({rel_path})")

    print("\nHinweis: Für jeden dieser Skills muss geprüft werden, ob ein deterministischer Renderer erforderlich ist.")
    return 1


if __name__ == "__main__":
    raise SystemExit(check_coverage())
