import os
import subprocess
import sys
from pathlib import Path


MAX_FILE_MB = 90


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


def file_size_mb(path):
    try:
        return path.stat().st_size / (1024 * 1024)
    except OSError:
        return 0


def main():
    cwd = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
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

    entries = status_entries(cwd)
    staged = [e for e in entries if e[:2] != "??" and e[0] != " "]
    unstaged = [e for e in entries if e[:2] != "??" and e[1] != " "]
    untracked = [e for e in entries if e[:2] == "??"]

    large = []
    for entry in entries:
        raw = entry[3:].strip()
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1].strip()
        path = cwd / raw.strip('"')
        if path.is_file():
            size = file_size_mb(path)
            if size >= MAX_FILE_MB:
                large.append((raw, size))

    print("GIT GUARD REPORT")
    print(f"- Repository: {cwd}")
    print(f"- Branch: {branch or '(detached)'}")
    print(f"- Dirty entries: {len(entries)}")
    print(f"- Staged entries: {len(staged)}")
    print(f"- Unstaged entries: {len(unstaged)}")
    print(f"- Untracked entries: {len(untracked)}")
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

    if entries:
        print("- Recommendation: review and stage coherent path groups; avoid git add .")
    else:
        print("- Recommendation: no commit needed; worktree clean")

    return 1 if branch == "master" or large or "backup" not in remotes else 0


if __name__ == "__main__":
    raise SystemExit(main())
