#!/usr/bin/env python3
"""
Generate GitHub Release Notes from CHANGELOG.md.
Creates a formatted markdown file for electron-builder to use.

Usage:  python tools/generate_release_notes.py
Output: RELEASE_NOTES.md (in project root)
"""
import re
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"
OUTPUT_FILE = PROJECT_ROOT / "RELEASE_NOTES.md"


def extract_changelog_entry(version):
    """Extract the changelog entry for a specific version from CHANGELOG.md."""
    if not CHANGELOG.exists():
        print(f"❌ CHANGELOG.md not found at {CHANGELOG}")
        return None

    content = CHANGELOG.read_text(encoding="utf-8")

    # Find the section for the specific version
    # Pattern: ## [VERSION] - DATE
    pattern = rf'## \[{re.escape(version)}\].*?\n((?:.*?\n)*?)(?=\n## \[|$)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print(f"❌ No changelog entry found for version {version}")
        return None

    section = match.group(1).strip()
    return section


def move_unreleased_to_version(version):
    """Move [Unreleased] entries to new version in CHANGELOG.md."""
    if not CHANGELOG.exists():
        print(f"❌ CHANGELOG.md not found at {CHANGELOG}")
        return

    content = CHANGELOG.read_text(encoding="utf-8")

    # Check if [Unreleased] section exists
    unreleased_pattern = r'## \[Unreleased\].*?\n((?:.*?\n)*?)(?=\n## \[|$)'
    unreleased_match = re.search(unreleased_pattern, content, re.DOTALL)

    if not unreleased_match:
        print("ℹ️  No [Unreleased] section found in CHANGELOG.md")
        return

    unreleased_content = unreleased_match.group(1).strip()

    # Check if unreleased has content
    if not unreleased_content or unreleased_content.count('\n') < 2:
        print("ℹ️  [Unreleased] section is empty or has no meaningful content")
        return

    # Check if version section already exists
    version_pattern = rf'## \[{re.escape(version)}\]'
    if re.search(version_pattern, content):
        print(f"⚠️  Version [{version}] already exists in CHANGELOG.md. Skipping move.")
        return

    # Move [Unreleased] to new version
    today = datetime.now().strftime('%Y-%m-%d')
    new_version_section = f"## [{version}] - {today}\n\n{unreleased_content}\n\n"

    # Replace [Unreleased] section with empty [Unreleased]
    empty_unreleased = "## [Unreleased]\n\n"
    content = re.sub(unreleased_pattern, empty_unreleased, content, count=1, flags=re.DOTALL)

    # Insert new version section after [Unreleased]
    content = content.replace(empty_unreleased, empty_unreleased + new_version_section)

    # Write back
    CHANGELOG.write_text(content, encoding="utf-8")
    print(f"✅ Moved [Unreleased] entries to [{version}] in CHANGELOG.md")


def get_version_from_package_json():
    """Read version from package.json."""
    pkg_json = PROJECT_ROOT / "package.json"
    if pkg_json.exists():
        import json
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        return pkg.get("version", "UNKNOWN")
    return "UNKNOWN"


def generate_release_notes():
    """Generate complete release notes markdown from CHANGELOG.md."""
    version = get_version_from_package_json()
    print(f"Generating release notes for version: {version}")

    # Move [Unreleased] to new version
    move_unreleased_to_version(version)

    changelog_entry = extract_changelog_entry(version)

    # Build release notes
    notes = []
    notes.append(f"# Janus Projekt {version}")
    notes.append(f"**Released:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    notes.append("")

    if changelog_entry:
        notes.append(changelog_entry)
    else:
        notes.append("## 🚀 Changes in this Release")
        notes.append("")
        notes.append("No changelog entry found for this version.")
        notes.append("")

    notes.append("## Installation")
    notes.append("Download the installer from the GitHub releases page.")
    notes.append("")
    notes.append("## Known Issues")
    notes.append("None reported for this release.")
    notes.append("")

    return "\n".join(notes)


def main():
    print("Generating release notes...")
    
    notes = generate_release_notes()
    OUTPUT_FILE.write_text(notes, encoding="utf-8")
    
    print(f"✅ Release notes written to {OUTPUT_FILE}")
    print(f"\nPreview:")
    print("-" * 60)
    print(notes)
    print("-" * 60)


if __name__ == "__main__":
    main()
