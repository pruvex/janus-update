import re
import sys
from pathlib import Path


RESULTS = {"PASS", "PASS WITH FIXES", "BLOCKED"}


def validate(text: str):
    errors = []
    warnings = []
    match = re.search(r"^FINAL AUDIT RESULT:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        legacy = re.search(r"^## Result\s*\n\s*(PASS|PASS WITH FIXES|BLOCKED)\s*$", text, re.MULTILINE)
        if legacy:
            result = legacy.group(1).strip()
            warnings.append("Legacy audit format: missing FINAL AUDIT RESULT line.")
        else:
            errors.append("Missing FINAL AUDIT RESULT line.")
            result = None
    else:
        result = match.group(1).strip()
        if result not in RESULTS:
            errors.append(f"Invalid FINAL AUDIT RESULT: {result}")

    if "Audit Scope" not in text and "## Audit Scope" not in text and "Scope Verified" not in text:
        errors.append("Missing Audit Scope section.")
    if "Validation Evidence" not in text and "Testmatrix" not in text and "## Result" not in text:
        errors.append("Missing validation evidence/test matrix.")
    if "Findings" not in text and "Notes" not in text:
        errors.append("Missing Findings section.")

    if result in {"PASS", "PASS WITH FIXES"}:
        if "NEXT_SKILL_HANDOFF" not in text and "Completion" not in text:
            target = warnings if warnings else errors
            target.append("PASS audit should include NEXT_SKILL_HANDOFF or completion section.")
        if "FAILED" in text or "ASSERTION_MISMATCH" in text:
            errors.append("PASS audit contains failure/debug indicators.")

    if result == "BLOCKED":
        if "NEXT_SKILL_HANDOFF" not in text and "Required Action" not in text:
            errors.append("BLOCKED audit must include next action or handoff.")

    forbidden = [
        "STATUS: READY FOR PRODUCTION",
        "Audit Result: APPROVED",
        "Recommendation: APPROVE FOR SKILL 7",
        "READY FOR AUDIT",
    ]
    for token in forbidden:
        if token in text:
            errors.append(f"Forbidden status synonym found: {token}")

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_final_audit.py <path-to-final-audit.md>")
        return 2
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors, warnings = validate(text)
    if errors:
        print("FINAL AUDIT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("FINAL AUDIT LEGACY WARNINGS")
            for warning in warnings:
                print(f"- {warning}")
        return 1
    if warnings:
        print("FINAL AUDIT VALIDATION PASS WITH LEGACY WARNINGS")
        for warning in warnings:
            print(f"- {warning}")
        return 0
    print("FINAL AUDIT VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
