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
    if path.startswith("documentation/codex/skills/"):
        return "skill-rules"
    if (
        path.startswith("scripts/git-hooks/")
        or path in {"scripts/save.ps1", "scripts/verify-codex-dev-environment.ps1"}
        or path.startswith("documentation/codex/CODEX_")
        or path == "documentation/codex/SKILL_USAGE_LOG.md"
    ):
        return "codex-governance"
    if path.startswith("frontend/"):
        return "frontend"
    if path.startswith("backend/"):
        return "backend"
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

    active = set(groups)
    implementation = sorted(active & {"frontend", "backend", "tooling"})
    companions = active - {"frontend", "backend", "tooling", "skill-rules", "release-verification"}
    if implementation and "skill-rules" not in active and "release-verification" not in active and len(implementation) <= 2:
        print("\nLean mode candidate:")
        print("- One combined commit is reasonable if these files belong to one validated Backlog item plus its evidence and closeout docs.")
        if companions:
            print(f"- Companion buckets that may stay together: {', '.join(sorted(companions))}")

    print("\nCommit order recommendation:")
    print("1. one lean commit for a single validated Backlog item, if applicable")
    print("2. stop after the intended item commit unless the user explicitly asked for leftover cleanup")
    print("3. skill-rules")
    print("4. release-verification")
    print("5. separate product slices only when scopes are genuinely unrelated")
    print("6. generated-test-artifacts (only if explicitly needed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
