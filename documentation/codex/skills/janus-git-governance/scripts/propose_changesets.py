import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def run(cwd, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode, result.stdout.rstrip("\n"), result.stderr.strip()


def classify_bucket(path_text):
    path = path_text.replace("\\", "/")
    if (
        path.startswith("scripts/git-hooks/")
        or path.startswith("documentation/codex/skills/janus-git-governance/")
        or path.startswith("documentation/codex/CODEX_")
        or path == "documentation/codex/SKILL_USAGE_LOG.md"
    ):
        return "codex-governance"
    if path.startswith("frontend/"):
        return "frontend"
    if path.startswith("backend/"):
        return "backend"
    if path.startswith("documentation/codex/skills/"):
        return "skill-rules"
    if path.startswith("documentation/release/"):
        return "release-verification"
    if path == "janus-dashboard/data/backlog.snapshot.json" or path.startswith("documentation/backlog/"):
        return "dashboard-backlog-sync"
    if path.startswith("playwright-report/") or path.startswith("test-results/"):
        return "generated-test-artifacts"
    if path in {"package.json", "package-lock.json"}:
        return "tooling"
    if path in {"CHANGELOG.md", "release_notes.md"}:
        return "release-notes"
    return "manual-review"


def main():
    cwd = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    code, out, err = run(cwd, "status", "--porcelain=v1")
    if code != 0:
        print(f"FAILED: {err or out}")
        return 2

    entries = [line for line in out.splitlines() if line]
    groups = defaultdict(list)
    for entry in entries:
        raw = entry[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        raw = raw.strip('"')
        groups[classify_bucket(raw)].append(raw)

    print("CHANGESET PROPOSAL")
    print(f"- Repository: {cwd}")
    print(f"- Dirty entries: {len(entries)}")
    for bucket in sorted(groups):
        paths = sorted(set(groups[bucket]))
        print(f"\n[{bucket}] ({len(paths)} files)")
        for path in paths:
            print(f"- {path}")
        quoted = " ".join([f'"{p}"' for p in paths])
        print(f"git add -- {quoted}")

    print("\nCommit order recommendation:")
    print("1. codex-governance")
    print("2. skill-rules")
    print("3. dashboard-backlog-sync")
    print("4. release-verification")
    print("5. frontend/backend/tooling")
    print("6. generated-test-artifacts (only if explicitly needed)")
    print("7. manual-review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
