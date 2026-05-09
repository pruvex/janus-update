from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
BACKLOG_PATH = PROJECT_ROOT / "documentation" / "backlog" / "BACKLOG.md"
SNAPSHOT_PATH = DASHBOARD_ROOT / "data" / "backlog.snapshot.json"

sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.backlog.parser import parse_backlog_file


def main() -> int:
    data = parse_backlog_file(BACKLOG_PATH).model_dump(mode="json")
    data["source"] = str(SNAPSHOT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/")
    data["generated_from"] = str(BACKLOG_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/")
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    data["snapshot_schema"] = "janus-dashboard.backlog.v1"
    data["is_stale"] = False

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = data["counts"]
    print(
        "Backlog snapshot synced: "
        f"total={counts['total']} active={counts['active']} done={counts['done']} "
        f"routing_missing={counts['routing_missing']} -> {SNAPSHOT_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
