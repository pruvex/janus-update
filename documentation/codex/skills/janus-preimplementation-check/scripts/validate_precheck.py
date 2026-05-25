import sys
from pathlib import Path


REQUIRED = [
    "PRE-CHECK RESULT",
    "PRE-CHECK PASSED",
    "BEGIN COPY FOR SKILL 4",
    "Pre-Check: PRE-CHECK PASSED",
    "Pre-Check Context:",
    "Scope-Regel:",
    "Automated Evidence Gate:",
    "npx playwright test <runner> --headed --workers=1 --reporter=list",
    "Artifact Identity Check:",
    "Oracle-/TestPlan-Regel:",
    "END COPY FOR SKILL 4",
]

FORBIDDEN = [
    "PRE-CHECK RESULT: PASSED",
    "PRE-CHECK ERGEBNIS",
    "Pre-Check Decision:",
    "Skill 4 Handover",
    "BEGIN COPY FOR @[/SKILL 4",
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

    begin = text.find("BEGIN COPY FOR SKILL 4")
    end = text.find("END COPY FOR SKILL 4")
    if begin == -1 or end == -1 or end < begin:
        errors.append("Copyblock boundaries are invalid.")
    if text.count("```text") != 1:
        errors.append("PASS output must contain exactly one fenced text codeblock.")

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
