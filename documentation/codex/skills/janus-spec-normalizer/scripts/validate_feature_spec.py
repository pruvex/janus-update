import re
import sys
from pathlib import Path


CURRENT_TITLE = "# JANUS FEATURE SPEC - DIAMANTSTANDARD v4.4.3"
LEGACY_TITLES = {
    "# JANUS FEATURE SPEC – DIAMANTSTANDARD v4.4.3",
    "# JANUS FEATURE SPEC â€“ DIAMANTSTANDARD v4.4.3",
}

COMMON_HEADINGS = [
    "## SPEC REVIEW EXECUTION ROUTING",
    "## FEATURE IDENTITY",
    "## USER VALUE",
    "## TARGET SURFACE",
    "## USER ACTION SURFACE",
    "## SYSTEM BEHAVIOR",
    "## DATA / PERSISTENCE",
    "## CONSTRAINTS",
    "## SECURITY / PRIVACY",
    "## EDGE CASES",
    "## DEFINITION OF DONE",
    "## TEST STRATEGY",
    "## OUT OF SCOPE",
    "## INTERNAL COMPLEXITY BREAKDOWN",
]

CURRENT_ROUTING_KEYS = [
    "target_skill",
    "recommended_model",
    "recommended_reasoning",
    "new_chat",
    "complexity_score",
    "confidence",
    "dashboard_hint",
    "reason",
]

LEGACY_ROUTING_KEYS = [
    "target_skill",
    "execution_mode",
    "complexity_score",
    "confidence",
    "dashboard_hint",
    "reason",
]

STRUCTURED_SECTIONS = {
    "## FEATURE IDENTITY",
    "## TARGET SURFACE",
    "## USER ACTION SURFACE",
    "## DATA / PERSISTENCE",
    "## SECURITY / PRIVACY",
    "## TEST STRATEGY",
}


def fail(errors, message):
    errors.append(message)


def section(lines, heading):
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return lines[start:end]


def parse_key_values(lines):
    values = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:]
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def parse_score(line, label):
    pattern = rf"^(?:- )?{re.escape(label)}:\s*(\d+)\b"
    match = re.match(pattern, line.strip())
    if not match:
        return None
    return int(match.group(1))


def parse_complexity_values(lines):
    values = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:]
        key, value = stripped.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def detect_contract(routing_values):
    keys = list(routing_values.keys())
    if keys == CURRENT_ROUTING_KEYS:
        return "current"
    if keys == LEGACY_ROUTING_KEYS:
        return "legacy"
    return None


def validate_heading_order(lines, errors):
    last_position = -1
    for heading in COMMON_HEADINGS:
        if heading not in lines:
            fail(errors, f"Missing heading: {heading}")
            continue
        position = lines.index(heading)
        if position < last_position:
            fail(errors, "Required headings are not in the required order.")
            break
        last_position = position


def validate_structured_sections(lines, errors):
    for heading in STRUCTURED_SECTIONS:
        for line in section(lines, heading):
            stripped = line.strip()
            if not stripped or stripped.startswith("Nicht zutreffend:"):
                continue
            if line.startswith((" ", "\t")):
                continue
            if ":" in line and not stripped.startswith("- "):
                fail(errors, f"Structured field in {heading} must start with '- ': {line}")


def validate_definition_of_done(lines, errors):
    for line in section(lines, "## DEFINITION OF DONE"):
        stripped = line.strip()
        if not stripped or stripped.startswith("Nicht zutreffend:"):
            continue
        if stripped.startswith("- ") and not stripped.startswith("- [ ] "):
            fail(errors, f"Definition of Done item must be checkbox syntax: {line}")


def validate_complexity(lines, routing_values, errors, model_key):
    complexity = section(lines, "## INTERNAL COMPLEXITY BREAKDOWN")
    labels = [
        "Scope Size",
        "Architectural Risk",
        "State / Persistence Complexity",
        "Cross-System Dependencies",
        "Ambiguity Level",
    ]
    scores = []
    for label in labels:
        line = next((x for x in complexity if x.strip().startswith((label + ":", "- " + label + ":"))), None)
        score = parse_score(line or "", label)
        if score is None or score < 0 or score > 20:
            fail(errors, f"{label} must start with a 0-20 integer.")
        else:
            scores.append(score)

    total_line = next((x for x in complexity if x.strip().startswith(("Total Complexity Score:", "- Total Complexity Score:"))), None)
    total = parse_score(total_line or "", "Total Complexity Score")
    if total is None:
        fail(errors, "Total Complexity Score is missing or invalid.")
    elif len(scores) == 5 and total != sum(scores):
        fail(errors, "Total Complexity Score must equal the sum of the five dimensions.")

    internal = parse_complexity_values(complexity)
    if model_key == "recommended_model" and total is not None and routing_values.get("complexity_score") and int(routing_values["complexity_score"]) != total:
        fail(errors, "Routing complexity_score must equal Total Complexity Score.")
    if routing_values.get(model_key) != internal.get("Routing Decision"):
        fail(errors, f"{model_key} must equal internal Routing Decision.")
    if routing_values.get("confidence") != internal.get("Routing Confidence"):
        fail(errors, "Routing confidence must equal internal Routing Confidence.")
    if routing_values.get("dashboard_hint") != internal.get("Dashboard Hint"):
        fail(errors, "Routing dashboard_hint must equal internal Dashboard Hint.")
    return internal


def validate_current_contract(lines, routing_values, errors):
    if routing_values.get("target_skill") != "janus-spec-review":
        fail(errors, "target_skill must be janus-spec-review.")
    if not routing_values.get("recommended_model"):
        fail(errors, "recommended_model must be non-empty.")
    if not routing_values.get("recommended_reasoning"):
        fail(errors, "recommended_reasoning must be non-empty.")
    if routing_values.get("new_chat") not in {"yes", "no"}:
        fail(errors, "new_chat must be yes or no.")
    if not re.fullmatch(r"\d{1,3}", routing_values.get("complexity_score", "")):
        fail(errors, "complexity_score must be an integer.")
    if routing_values.get("confidence") not in {"LOW", "MEDIUM", "HIGH"}:
        fail(errors, "confidence must be LOW, MEDIUM, or HIGH.")
    if routing_values.get("dashboard_hint") not in {"SAFE", "CAUTION", "CRITICAL"}:
        fail(errors, "dashboard_hint must be SAFE, CAUTION, or CRITICAL.")
    if not routing_values.get("reason") or len(routing_values.get("reason", "")) > 220:
        fail(errors, "reason must be non-empty and max 220 characters.")

    for line in section(lines, "## DATA / PERSISTENCE"):
        if line.strip().startswith("- Persistence Required:"):
            value = line.split(":", 1)[1].strip()
            if value not in {"YES", "NO"}:
                fail(errors, "Persistence Required must be YES or NO.")

    internal = validate_complexity(lines, routing_values, errors, "recommended_model")
    if routing_values.get("recommended_reasoning") != internal.get("Routing Reasoning"):
        fail(errors, "recommended_reasoning must equal internal Routing Reasoning.")


def validate_legacy_contract(lines, routing_values, errors):
    if routing_values.get("target_skill") != "SPEC_REVIEW":
        fail(errors, "target_skill must be SPEC_REVIEW.")
    if routing_values.get("execution_mode") not in {"SWE_1_6", "GPT_5_5"}:
        fail(errors, "execution_mode must be SWE_1_6 or GPT_5_5.")
    if not re.fullmatch(r"\d{1,3}", routing_values.get("complexity_score", "")):
        fail(errors, "complexity_score must be an integer.")
    if routing_values.get("confidence") not in {"LOW", "MEDIUM", "HIGH"}:
        fail(errors, "confidence must be LOW, MEDIUM, or HIGH.")
    if routing_values.get("dashboard_hint") not in {"SAFE", "CAUTION", "CRITICAL"}:
        fail(errors, "dashboard_hint must be SAFE, CAUTION, or CRITICAL.")
    if not routing_values.get("reason") or len(routing_values.get("reason", "")) > 180:
        fail(errors, "reason must be non-empty and max 180 characters.")

    for line in section(lines, "## DATA / PERSISTENCE"):
        if line.strip().startswith("- Persistence Required:"):
            value = line.split(":", 1)[1].strip()
            if value not in {"YES", "NO"}:
                fail(errors, "Persistence Required must be YES or NO.")

    validate_complexity(lines, routing_values, errors, "execution_mode")


def validate(text):
    errors = []
    stripped = text.strip()

    if stripped.startswith("```"):
        match = re.fullmatch(r"```markdown\n(?P<body>.*)\n```", stripped, re.DOTALL)
        if not match:
            fail(errors, "Fenced output must be exactly one markdown code block.")
            body = stripped
        else:
            body = match.group("body")
    else:
        body = stripped

    lines = body.splitlines()
    if not lines or lines[0] not in ({CURRENT_TITLE} | LEGACY_TITLES):
        fail(errors, f"First line must be exactly: {CURRENT_TITLE}")

    validate_heading_order(lines, errors)
    validate_structured_sections(lines, errors)

    routing_values = parse_key_values(section(lines, "## SPEC REVIEW EXECUTION ROUTING"))
    contract = detect_contract(routing_values)
    if contract == "current":
        validate_current_contract(lines, routing_values, errors)
    elif contract == "legacy":
        validate_legacy_contract(lines, routing_values, errors)
    else:
        fail(errors, "Routing block keys must match the current or legacy contract exactly and in order.")

    validate_definition_of_done(lines, errors)

    forbidden = [
        "BEGIN_SPEC_MARKDOWN",
        "END_SPEC_MARKDOWN",
        "```python",
        "```javascript",
        "CREATE TABLE",
        "def ",
        "function ",
    ]
    for token in forbidden:
        if token in body:
            fail(errors, f"Forbidden token found: {token}")

    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_feature_spec.py <path-to-spec.md>")
        return 2

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    errors = validate(text)
    if errors:
        print("SPEC VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SPEC VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
