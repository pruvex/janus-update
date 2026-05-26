import re
import sys
from pathlib import Path


RESULTS = {"FIXED", "NEEDS RETEST", "ESCALATION REQUIRED", "BLOCKED", "OUT OF SCOPE"}


def validate(text):
    errors = []
    text = text.lstrip("\ufeff")
    match = re.search(r"^SKILL 5 DEBUG RESULT:\s*(.+?)\s*$", text, re.MULTILINE)
    if not match:
        errors.append("Missing SKILL 5 DEBUG RESULT line.")
        result = None
    else:
        result = match.group(1).strip()
        if result not in RESULTS:
            errors.append(f"Invalid debug result: {result}")

    if "Iteration:" not in text:
        errors.append("Missing Iteration.")
    if "Progress-Validierung:" not in text:
        errors.append("Missing Progress-Validierung.")

    if result == "FIXED":
        if "Auto-Verification:\n- Status: PASS" not in text:
            errors.append("FIXED requires Auto-Verification PASS.")
        if "Final Feature Suite: PASS" not in text and "Final Feature Suite: N/A WITH REASON" not in text:
            errors.append("FIXED requires Final Feature Suite PASS or N/A WITH REASON.")
        if "NEXT_SKILL_HANDOFF" not in text:
            errors.append("FIXED requires NEXT_SKILL_HANDOFF.")

    if result in {"NEEDS RETEST", "ESCALATION REQUIRED", "BLOCKED"} and "NEXT_SKILL_HANDOFF" not in text:
        errors.append(f"{result} requires NEXT_SKILL_HANDOFF.")

    if "BEGIN COPY FOR RETEST" in text or "END COPY FOR RETEST" in text:
        errors.append("Forbidden free-form retest block found.")

    forbidden_secret_patterns = [
        r"Bearer\s+[A-Za-z0-9._\-]+",
        r"JWT_SECRET_KEY\s*=\s*\S+",
        r"api_key\s*:\s*\S+",
        r"jwt_secret_key\s*:\s*\S+",
        r"Authorization:\s*\S+",
    ]
    for pattern in forbidden_secret_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            errors.append("Potential secret material found.")

    if "NEXT_SKILL_HANDOFF" in text:
        for field in ["Target Skill:", "Canonical State:", "Required Artifacts:", "Evidence Paths:", "Failure Code:", "Changed Files:", "Decision:", "Reason:", "Copy Prompt:"]:
            if field not in text:
                errors.append(f"NEXT_SKILL_HANDOFF missing field: {field}")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_debug_result.py <path-to-debug-result.md>")
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    errors = validate(text)
    if errors:
        print("DEBUG RESULT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("DEBUG RESULT VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
