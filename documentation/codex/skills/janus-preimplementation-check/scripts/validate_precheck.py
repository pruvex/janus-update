import sys
from pathlib import Path


REQUIRED = [
    "PRE-CHECK RESULT",
    "PRE-CHECK PASSED",
    "Pre-Check: PRE-CHECK PASSED",
    "Pre-Check Context:",
    "Scope-Regel:",
    "Automated Evidence Gate:",
    "npx playwright test <runner> --headed --workers=1 --reporter=list",
    "Artifact Identity Check:",
    "Oracle-/TestPlan-Regel:",
    "NEXT STEP",
    "Recommended Skill: janus-executioner",
    "Recommended Model:",
    "Recommended Intelligence:",
    "User Action:",
]

FORBIDDEN = [
    "PRE-CHECK RESULT: PASSED",
    "PRE-CHECK ERGEBNIS",
    "Pre-Check Decision:",
    "Skill 4 Handover",
    "BEGIN COPY FOR SKILL 4",
    "BEGIN COPY FOR @[/SKILL 4",
    "END COPY FOR SKILL 4",
    "Copy Prompt:",
    "Manual Janus Validation Gate",
    "Stop at Manual Janus Validation Gate",
    "Execution Model:",
    "Changed Files:",
    "Geaenderte Dateien:",
    "TestPlan neu generiert",
    "TestRun ausgefuehrt",
    "TestRun ausgeführt",
    "Implementation Complete",
]


def validate(text):
    errors = []
    for token in REQUIRED:
        if token not in text:
            errors.append(f"Missing required literal: {token}")
    for token in FORBIDDEN:
        if token in text:
            errors.append(f"Forbidden literal found: {token}")

    if "PRE-CHECK PASSED" in text:
        result_index = text.find("PRE-CHECK RESULT")
        passed_index = text.find("PRE-CHECK PASSED")
        if result_index == -1 or passed_index == -1 or passed_index < result_index:
            errors.append("PRE-CHECK PASSED must follow PRE-CHECK RESULT.")
        between = text[result_index:passed_index].splitlines()
        if len([line for line in between if line.strip()]) > 1:
            errors.append("PRE-CHECK PASSED must directly follow PRE-CHECK RESULT.")

    if "BEGIN COPY" in text or "Copy Prompt:" in text:
        errors.append("Codex-native precheck output must not contain copy-paste handoff prompts.")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_precheck.py <path-to-precheck-output.md>")
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    errors = validate(text)
    if errors:
        print("PRECHECK VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PRECHECK VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
