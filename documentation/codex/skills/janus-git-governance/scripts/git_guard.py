import os
import re
import subprocess
import sys
from pathlib import Path


MAX_FILE_MB = 90
IMPLEMENTATION_BUCKETS = {"frontend", "backend", "tooling"}
COMPANION_BUCKETS = {
    "codex-governance",
    "dashboard-backlog-sync",
    "generated-test-artifacts",
    "manual-review",
    "release-notes",
}
STRICT_SPLIT_BUCKETS = {"skill-rules", "release-verification"}
MAX_IMPLEMENTATION_BUCKETS = 2


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


def extract_backlog_markers(path_text):
    return set(re.findall(r"BACKLOG-\d+", path_text.upper()))


def evaluate_changeset(buckets, markers):
    active_buckets = sorted([bucket for bucket, count in buckets.items() if count > 0])
    active_set = set(active_buckets)
    active_markers = sorted(marker for marker, count in markers.items() if count > 0)

    if not active_buckets:
        return active_buckets, active_markers, None

    if "skill-rules" in active_set and len(active_set) > 1:
        return (
            active_buckets,
            active_markers,
            "BLOCKER: skill-rules are mixed with non-skill work. Keep governance changes separate.",
        )

    if "release-verification" in active_set and len(active_set - {"release-verification", "release-notes"}) > 0:
        return (
            active_buckets,
            active_markers,
            "BLOCKER: release verification is mixed with normal development work. Commit it separately.",
        )

    implementation_buckets = sorted(active_set & IMPLEMENTATION_BUCKETS)
    noncompanion_buckets = sorted(
        bucket
        for bucket in active_set
        if bucket not in IMPLEMENTATION_BUCKETS
        and bucket not in COMPANION_BUCKETS
        and bucket not in STRICT_SPLIT_BUCKETS
    )
    if len(implementation_buckets) > MAX_IMPLEMENTATION_BUCKETS:
        return (
            active_buckets,
            active_markers,
            "BLOCKER: too many implementation surfaces are mixed together. Split into smaller feature slices.",
        )
    if noncompanion_buckets:
        return (
            active_buckets,
            active_markers,
            f"BLOCKER: non-companion scope detected: {', '.join(noncompanion_buckets)}",
        )
    return active_buckets, active_markers, None


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


def status_entries(cwd):
    code, out, err = run(cwd, "status", "--porcelain=v1")
    if code != 0:
        raise RuntimeError(err or out)
    return [line for line in out.splitlines() if line]


def staged_entries(cwd):
    code, out, err = run(cwd, "diff", "--cached", "--name-status", "-z")
    if code != 0:
        raise RuntimeError(err or out)
    if not out:
        return []

    tokens = out.split("\x00")
    entries = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token:
            i += 1
            continue
        status = token
        if i + 1 >= len(tokens):
            break
        path = tokens[i + 1]
        entries.append(f"{status:<2} {path}")
        i += 2
    return entries


def file_size_mb(path):
    try:
        return path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0


def main():
    args = [arg for arg in sys.argv[1:] if arg]
    staged_only = "--staged-only" in args
    args = [arg for arg in args if arg != "--staged-only"]
    cwd = Path(args[0] if args else ".").resolve()
    if not (cwd / ".git").exists():
        print(f"GIT GUARD FAILED: not a git repository: {cwd}")
        return 2

    code, branch, err = run(cwd, "branch", "--show-current")
    if code != 0:
        print(f"GIT GUARD FAILED: {err}")
        return 2

    code, remotes, err = run(cwd, "remote", "-v")
    if code != 0:
        print(f"GIT GUARD FAILED: {err}")
        return 2

    entries = staged_entries(cwd) if staged_only else status_entries(cwd)
    staged = [e for e in entries if e[:2] != "??" and e[0] != " "]
    unstaged = [e for e in entries if e[:2] != "??" and e[1] != " "]
    untracked = [e for e in entries if e[:2] == "??"]
    buckets = {}
    markers = {}

    large = []
    for entry in entries:
        raw = entry[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        normalized = raw.strip('"')
        bucket = classify_bucket(normalized)
        buckets[bucket] = buckets.get(bucket, 0) + 1
        for marker in extract_backlog_markers(normalized):
            markers[marker] = markers.get(marker, 0) + 1
        path = cwd / normalized
        if path.is_file():
            size = file_size_mb(path)
            if size >= MAX_FILE_MB:
                large.append((normalized, size))

    print("GIT GUARD REPORT")
    print(f"- Repository: {cwd}")
    print(f"- Branch: {branch or '(detached)'}")
    print(f"- Scope: {'staged-only' if staged_only else 'full-worktree'}")
    print(f"- Dirty entries: {len(entries)}")
    print(f"- Staged entries: {len(staged)}")
    print(f"- Unstaged entries: {len(unstaged)}")
    print(f"- Untracked entries: {len(untracked)}")
    print(f"- Changeset buckets: {len([k for k, v in buckets.items() if v > 0])}")
    print("- Remotes:")
    for line in remotes.splitlines():
        print(f"  {line}")

    if branch == "master":
        print("BLOCKER: normal development commits are not allowed on master.")
    if "backup" not in remotes:
        print("BLOCKER: backup remote is missing.")
    if "origin" not in remotes:
        print("WARNING: origin remote is missing.")

    if large:
        print("BLOCKER: large non-ignored files detected:")
        for raw, size in large:
            print(f"  {raw} ({size:.1f} MB)")
    else:
        print("- Large file risk: none detected in dirty entries")

    active_buckets, active_markers, mixed_blocker_message = evaluate_changeset(buckets, markers)
    if active_buckets:
        print(f"- Active buckets: {', '.join(active_buckets)}")
    if active_markers:
        print(f"- Backlog markers in scope: {', '.join(active_markers)}")
    if mixed_blocker_message:
        print(mixed_blocker_message)
        print(
            "BLOCKER: mixed changeset risk detected. Run propose_changesets.py and split only the unrelated scope."
        )
    elif active_buckets:
        if active_markers:
            print("- Lean mode: one backlog-linked commit is reasonable if the staged scope matches this item and its closeout artifacts.")
        else:
            print("- Lean mode: one coherent commit is reasonable if the scope is intentional and validated.")

    if entries:
        print("- Recommendation: review and stage coherent path groups; avoid git add .")
        print(
            "- Helper: python C:\\Users\\pruve\\.codex\\skills\\janus-git-governance\\scripts\\propose_changesets.py C:\\KI\\Janus-Projekt"
        )
    else:
        print("- Recommendation: no commit needed; worktree clean")

    mixed_blocker = mixed_blocker_message is not None and len(entries) > 0
    return 1 if branch == "master" or large or "backup" not in remotes or mixed_blocker else 0


if __name__ == "__main__":
    raise SystemExit(main())
