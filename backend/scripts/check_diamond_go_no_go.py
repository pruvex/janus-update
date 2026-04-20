import csv
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from backend.tools.pdf_editor import _get_monitor_log_path


def _parse_bool(value: str) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes", "on"}


def _parse_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> int:
    monitor_path = _get_monitor_log_path()
    if not monitor_path.exists():
        print(f"Monitor log not found at {monitor_path}")
        return 2

    fieldnames = [
        "timestamp",
        "filename",
        "mode",
        "quality_gate",
        "go_no_go",
        "status",
        "diff_ratio",
        "shadow_gate_status",
        "overflow",
        "overflow_items",
        "font_shrinkage_pt",
    ]
    with monitor_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, fieldnames=fieldnames)
        next(reader, None)
        entries = [row for row in reader if any(row.values())]

    if not entries:
        print("Monitor log is empty")
        return 2

    latest = entries[-1]
    go_no_go_status = (latest.get("status") or "").strip()
    gate_status = (latest.get("shadow_gate_status") or "").strip()
    diff_ratio = latest.get("diff_ratio") or ""
    overflow = _parse_bool(latest.get("overflow"))
    font_shrinkage = _parse_float(latest.get("font_shrinkage_pt"))

    print("Latest monitoring entry:")
    print(
        f"  filename: {latest.get('filename')} | go_no_go_status={go_no_go_status} | gate={gate_status} | diff_ratio={diff_ratio} | overflow={overflow}"
    )

    failures = []
    if go_no_go_status.lower() != "ready_for_review":
        failures.append("go_no_go is not ready_for_review")
    if gate_status.lower() != "passed":
        failures.append("shadow gate did not pass")
    try:
        diff_ratio_value = float(diff_ratio)
    except (TypeError, ValueError):
        diff_ratio_value = 0.0
    if diff_ratio_value > 0.2:
        failures.append(f"diff_ratio ({diff_ratio_value}) is above 0.2")
    if overflow:
        failures.append("overflow detected")
    if font_shrinkage > 1.0:
        failures.append(
            f"Font shrinkage detected! Font is {font_shrinkage}pt smaller than original."
        )

    if failures:
        print("Alerts:")
        for issue in failures:
            print(f"  - {issue}")
        return 1

    print("Go/No-Go status is green (ready_for_review). You can trigger the live test now.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
