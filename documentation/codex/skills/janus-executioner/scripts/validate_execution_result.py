import re
import sys
from pathlib import Path


def validate(text):
    errors = []

    if "TASK COMPLETE" in text or "ALL TASKS COMPLETE" in text:
        marker = "Auto-Verification:\n- Status: PASS"
        if marker not in text:
            errors.append("TASK COMPLETE requires immediately preceding Auto-Verification PASS block.")
        if "Auto-Verification:\n- Status: FAIL" in text:
            errors.append("TASK COMPLETE cannot coexist with Auto-Verification FAIL.")
        if "Auto-Verification:\n- Status: N/A" in text:
            errors.append("TASK COMPLETE cannot use Auto-Verification N/A.")

    if "FINAL AUDIT" in text and "Auto-Verification:\n- Status: FAIL" in text:
        errors.append("Cannot route to final audit after failed Auto-Verification.")

    if "Provider" in text or "provider" in text:
        forbidden = ["Fallback auf GPT", "Fallback auf Gemini", "mit anderem Provider erfolgreich"]
        for token in forbidden:
            if token in text:
                errors.append(f"Forbidden provider fallback wording: {token}")

    if "TASK EXECUTION BLOCKED" in text and "NEXT_SKILL_HANDOFF" not in text:
        errors.append("Blocked execution must include NEXT_SKILL_HANDOFF.")

    if re.search(r"Changed Files:\s*documentation/test-runs/.*_plan\.json", text):
        errors.append("Execution result must not list manual generated TestPlan patch as changed file.")

    if "Manual Janus Validation Gate" in text and "Auto-Verification:\n- Status: PASS" not in text:
        errors.append("Manual gate cannot replace Auto-Verification PASS.")

    if "NEXT_SKILL_HANDOFF" in text:
        for field in ["Target Skill:", "Canonical State:", "Required Artifacts:", "Evidence Paths:", "Failure Code:", "Changed Files:", "Decision:", "Reason:", "Copy Prompt:"]:
            if field not in text:
                errors.append(f"NEXT_SKILL_HANDOFF missing field: {field}")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_execution_result.py <path-to-execution-result.md>")
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    errors = validate(text)
    if errors:
        print("EXECUTION RESULT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("EXECUTION RESULT VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
