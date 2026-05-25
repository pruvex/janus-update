import argparse
from pathlib import Path


FILES = [
    "documentation/01_CENTRAL_TASK_REGISTRY.md",
    "PROJECT_STATE.md",
    "WHAT_I_LEARNED.md",
    "CHANGELOG.md",
    "documentation/backlog/BACKLOG.md",
    "documentation/pipeline/TEST_PIPELINE_RUN_LOG.md",
]


def contains(path: Path, marker: str) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        return marker in path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--require", action="append", default=[])
    args = parser.parse_args()

    repo = Path(args.repo)
    marker = args.marker
    required = args.require or FILES

    missing = []
    print("DOCUMENTATION UPDATE VALIDATION")
    print(f"- Repo: {repo}")
    print(f"- Marker: {marker}")
    for rel in required:
        path = repo / rel
        ok = contains(path, marker)
        print(f"- {rel}: {'PASS' if ok else 'MISSING'}")
        if not ok:
            missing.append(rel)

    if missing:
        print("DOCUMENTATION UPDATE VALIDATION FAILED")
        for rel in missing:
            print(f"- Missing marker in {rel}")
        return 1

    print("DOCUMENTATION UPDATE VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
