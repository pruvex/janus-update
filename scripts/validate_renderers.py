from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.renderers.registry import get_all_renderer_skill_ids

SKILLS_ROOT = PROJECT_ROOT / "backend" / "skills"


def iter_skill_catalogs() -> list[Path]:
    return sorted(SKILLS_ROOT.rglob("*.json"))


def load_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception as exc:
        print(f"ERROR: Konnte {path} nicht lesen: {exc}")
        return None

    if not isinstance(payload, dict):
        print(f"ERROR: {path} enthält kein JSON-Objekt.")
        return None

    return payload


def validate_renderers() -> int:
    registered = set(get_all_renderer_skill_ids())
    failed = False

    for path in iter_skill_catalogs():
        data = load_json(path)
        if data is None:
            failed = True
            continue

        if not data.get("deterministic_renderer"):
            continue

        skill_id = str(data.get("skill") or "").strip()
        if not skill_id:
            print(f"❌ FEHLER: {path.relative_to(PROJECT_ROOT)} hat `deterministic_renderer: true`, aber keine gültige `skill`-ID.")
            failed = True
            continue

        if skill_id not in registered:
            print(
                f"❌ FEHLER: Skill {skill_id} hat 'deterministic_renderer': true, "
                f"aber ist nicht in der Renderer-Registry registriert! "
                f"({path.relative_to(PROJECT_ROOT)})"
            )
            failed = True
        else:
            print(f"✅ OK: {skill_id} ist korrekt registriert.")

    if failed:
        print("\nRenderer-Validierung fehlgeschlagen.")
        return 1

    print("\n🚀 Alle Renderer-Flags validiert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_renderers())
