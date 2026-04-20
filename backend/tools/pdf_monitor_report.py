import csv
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.utils.paths import get_user_docs_dir

LOG_FILENAME = "PDF_Diamond_Monitoring.csv"


def get_monitor_log_path() -> Path:
    override = (os.getenv("JANUS_PDF_MONITOR_LOG") or "").strip()
    docs_dir = Path(get_user_docs_dir())
    if override:
        candidate = Path(override)
        return candidate if candidate.is_absolute() else docs_dir / candidate
    return docs_dir / LOG_FILENAME


def read_log(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def format_row(row: Dict[str, Any]) -> str:
    status = row.get("status") or ""
    overflow = row.get("overflow")
    gate = row.get("shadow_gate_status") or ""
    diff_ratio = row.get("diff_ratio") or ""
    return (
        f"{row.get('timestamp')} | {row.get('filename')} | go_no_go={status} "
        f"gate={gate} diff_ratio={diff_ratio} overflow={overflow}"
    )


def generate_html(rows: List[Dict[str, Any]], output: Path) -> None:
    lines = ["<html><body><h1>PDF Diamond Monitoring</h1><table border=1>"]
    if rows:
        headers = rows[0].keys()
        lines.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
        for row in rows:
            lines.append("<tr>" + "".join(f"<td>{row.get(h,'')}</td>" for h in headers) + "</tr>")
    else:
        lines.append("<p>No entries yet.</p>")
    lines.append("</table></body></html>")
    output.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="PDF Diamond Monitoring Report")
    parser.add_argument("--tail", type=int, default=20, help="Number of recent entries to show")
    parser.add_argument("--html", type=Path, help="Optional HTML output path")
    args = parser.parse_args()

    path = get_monitor_log_path()
    rows = read_log(path)
    subset = rows[-args.tail:]

    if not subset:
        print(f"No monitoring entries found at {path}")
        return

    print(f"Reporting from {path} (last {len(subset)} entries):")
    for row in subset:
        print(format_row(row))

    if args.html:
        generate_html(subset, args.html)
        print(f"HTML report written to {args.html}")

if __name__ == "__main__":
    main()
