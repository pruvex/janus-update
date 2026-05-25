#!/usr/bin/env python3
"""Validate Janus release readiness metadata before expensive build/publish steps."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def run_git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.STDOUT).strip()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def warn(warnings: list[str], message: str) -> None:
    warnings.append(message)


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        fail(errors, f"Missing file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        fail(errors, f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return {}
    if not isinstance(value, dict):
        fail(errors, f"Expected JSON object: {path}")
        return {}
    return value


def parse_backend_version(path: Path, errors: list[str]) -> str | None:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        fail(errors, f"Missing backend version file: {path}")
        return None
    match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', text)
    if not match:
        fail(errors, f"Could not parse APP_VERSION in {path}")
        return None
    return match.group(1)


def validate_versions(repo: Path, errors: list[str], warnings: list[str]) -> str | None:
    package = load_json(repo / "package.json", errors)
    lock = load_json(repo / "package-lock.json", errors)
    version = package.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        fail(errors, "package.json version is missing or not semver-like")
        return None

    lock_version = lock.get("version")
    lock_root = None
    packages = lock.get("packages")
    if isinstance(packages, dict) and isinstance(packages.get(""), dict):
        lock_root = packages[""].get("version")

    if lock_version != version:
        fail(errors, f"package-lock.json version mismatch: {lock_version!r} != {version!r}")
    if lock_root != version:
        fail(errors, f"package-lock root version mismatch: {lock_root!r} != {version!r}")

    backend_version = parse_backend_version(repo / "backend" / "version.py", errors)
    if backend_version != version:
        fail(errors, f"backend/version.py mismatch: {backend_version!r} != {version!r}")

    changelog = repo / "CHANGELOG.md"
    if not changelog.exists():
        warn(warnings, "CHANGELOG.md missing; release notes source may be elsewhere")
    else:
        text = changelog.read_text(encoding="utf-8-sig", errors="replace")
        if "[Unreleased]" not in text and version not in text:
            warn(warnings, "CHANGELOG.md contains neither [Unreleased] nor current version")

    return version


def validate_git(repo: Path, mode: str, errors: list[str], warnings: list[str]) -> str:
    try:
        branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        dirty = run_git(repo, "status", "--porcelain")
    except subprocess.CalledProcessError as exc:
        fail(errors, f"Git check failed: {exc.output.strip()}")
        return "unknown"

    if mode == "publish":
        if branch != "master":
            fail(errors, f"Publish mode requires branch master, current branch is {branch}")
        if dirty:
            fail(errors, "Publish mode requires a clean working tree")
    elif mode == "production-prep":
        if branch not in {"develop", "master"}:
            fail(errors, f"Unexpected production-prep branch: {branch}")
        if dirty:
            warn(warnings, "Working tree is dirty; production publish will require clean release state")
    else:
        if dirty:
            warn(warnings, "Working tree is dirty; rehearsal can inspect metadata but production publish is blocked")

    return branch


def manifest_issue(message: str, strict: bool, errors: list[str], warnings: list[str]) -> None:
    if strict:
        fail(errors, message)
    else:
        warn(warnings, message)


def validate_manifest(repo: Path, version: str | None, strict: bool, errors: list[str], warnings: list[str]) -> None:
    manifest_path = repo / "release" / "janus-update-manifest.json"
    if not manifest_path.exists():
        warn(warnings, "release/janus-update-manifest.json not present yet")
        return

    manifest = load_json(manifest_path, errors)
    if version and manifest.get("version") != version:
        manifest_issue(f"Manifest version mismatch: {manifest.get('version')!r} != {version!r}", strict, errors, warnings)

    asset_name = manifest.get("assetName")
    if not isinstance(asset_name, str) or not asset_name:
        manifest_issue("Manifest assetName missing", strict, errors, warnings)
    elif not (repo / "release" / asset_name).exists():
        manifest_issue(f"Manifest asset missing: release/{asset_name}", strict, errors, warnings)

    sha256 = manifest.get("sha256")
    if not isinstance(sha256, str) or not SHA256_RE.match(sha256):
        manifest_issue("Manifest sha256 must be 64 lowercase hex characters", strict, errors, warnings)

    if not isinstance(manifest.get("critical"), bool):
        manifest_issue("Manifest critical must be boolean", strict, errors, warnings)

    created_at = manifest.get("createdAt")
    if not isinstance(created_at, str) or not created_at:
        manifest_issue("Manifest createdAt missing", strict, errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Janus release readiness metadata.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Janus repository root")
    parser.add_argument(
        "--mode",
        choices=["rehearsal", "production-prep", "publish"],
        default="rehearsal",
        help="Release gate strictness",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    branch = validate_git(repo, args.mode, errors, warnings)
    version = validate_versions(repo, errors, warnings)
    validate_manifest(repo, version, args.mode == "publish", errors, warnings)

    print("JANUS RELEASE READINESS")
    print(f"- Repo: {repo}")
    print(f"- Mode: {args.mode}")
    print(f"- Branch: {branch}")
    print(f"- Version: {version or 'unknown'}")

    for item in warnings:
        print(f"WARN: {item}")

    if errors:
        print("RELEASE READINESS FAILED")
        for item in errors:
            print(f"ERROR: {item}")
        return 1

    if warnings:
        print("RELEASE READINESS PASS WITH WARNINGS")
    else:
        print("RELEASE READINESS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
