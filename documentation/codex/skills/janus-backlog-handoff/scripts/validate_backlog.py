import re
import sys
from pathlib import Path


STATUS_HEADINGS = ["NEEDS INFO", "READY", "IN PROGRESS", "DONE", "BLOCKED"]
TYPES = {"BUG", "CHANGE", "ENHANCEMENT", "IMPROVEMENT", "TECH_DEBT", "UNCLEAR"}
STATUSES = set(STATUS_HEADINGS)
ENTRY_POINTS = {
    "SPEC_PIPELINE_START",
    "TASK_BREAKDOWN",
    "PRE_IMPLEMENTATION_VERIFICATION",
    "EXECUTION_READY",
    "ROUTING_BLOCKED",
}
NEXT_SKILLS = {"SKILL 1", "SKILL 2", "SKILL 3", "SKILL 4", "none", "DONE"}


def parse_field(block, field):
    pattern = rf"^- \*\*{re.escape(field)}:\*\*\s*(.+?)\s*$"
    for line in block:
        match = re.match(pattern, line)
        if match:
            return match.group(1).strip()
    return None


def iter_items(lines):
    current_section = None
    current_title = None
    current = []
    for line in lines:
        heading = re.match(r"^## (NEEDS INFO|READY|IN PROGRESS|DONE|BLOCKED)\s*$", line)
        if heading:
            if current_title:
                yield current_section, current_title, current
            current_section = heading.group(1)
            current_title = None
            current = []
            continue
        item = re.match(r"^### (BACKLOG-\d{3,})\b.*", line)
        if item:
            if current_title:
                yield current_section, current_title, current
            current_title = item.group(1)
            current = [line]
            continue
        if current_title:
            current.append(line)
    if current_title:
        yield current_section, current_title, current


def validate(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    errors = []
    warnings = []

    for heading in STATUS_HEADINGS:
        count = sum(1 for line in lines if line == f"## {heading}")
        if count != 1:
            errors.append(f"Expected exactly one ## {heading} heading, found {count}.")

    seen = set()
    for section, item_id, block in iter_items(lines):
        if item_id in seen:
            errors.append(f"Duplicate item id: {item_id}")
        seen.add(item_id)

        typ = parse_field(block, "Typ")
        status = parse_field(block, "Status")
        short = parse_field(block, "Kurzbeschreibung")
        area = parse_field(block, "Betroffener Bereich")

        if typ not in TYPES:
            target = warnings if status == "DONE" else errors
            target.append(f"{item_id}: invalid or missing Typ: {typ}")
        if status not in STATUSES:
            errors.append(f"{item_id}: invalid or missing Status: {status}")
        if status and section and status != section:
            target = warnings if status == "DONE" else errors
            target.append(f"{item_id}: Status {status} is under ## {section}.")
        if not short:
            target = warnings if status == "DONE" else errors
            target.append(f"{item_id}: missing Kurzbeschreibung.")
        if not area:
            target = warnings if status == "DONE" else errors
            target.append(f"{item_id}: missing Betroffener Bereich.")

        entry = parse_field(block, "Entry Point")
        handoff = parse_field(block, "Handoff")
        next_skill = parse_field(block, "Recommended next skill")

        if entry and entry not in ENTRY_POINTS:
            errors.append(f"{item_id}: invalid Entry Point: {entry}")
        is_legacy_done = status == "DONE"
        target = warnings if is_legacy_done else errors

        if next_skill and next_skill not in NEXT_SKILLS:
            target.append(f"{item_id}: invalid Recommended next skill: {next_skill}")
        if entry == "SPEC_PIPELINE_START" and handoff and handoff != "none":
            if not handoff.startswith("documentation/Planned Features/"):
                target.append(f"{item_id}: SPEC_PIPELINE_START handoff must be under documentation/Planned Features/.")
            if next_skill != "SKILL 1":
                target.append(f"{item_id}: SPEC_PIPELINE_START requires SKILL 1.")
        if entry == "PRE_IMPLEMENTATION_VERIFICATION" and handoff and handoff != "none":
            if not handoff.startswith("documentation/tasks/"):
                target.append(f"{item_id}: PRE_IMPLEMENTATION_VERIFICATION handoff must be under documentation/tasks/.")
            if next_skill != "SKILL 3":
                target.append(f"{item_id}: PRE_IMPLEMENTATION_VERIFICATION requires SKILL 3.")
        if entry == "ROUTING_BLOCKED" and next_skill and next_skill != "none":
            target.append(f"{item_id}: ROUTING_BLOCKED must use Recommended next skill none.")

    return errors, warnings


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_backlog.py <BACKLOG.md>")
        return 2
    path = Path(sys.argv[1])
    errors, warnings = validate(path)
    if errors:
        print("BACKLOG VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        if warnings:
            print("BACKLOG LEGACY WARNINGS")
            for warning in warnings:
                print(f"- {warning}")
        return 1
    if warnings:
        print("BACKLOG VALIDATION PASS WITH LEGACY WARNINGS")
        for warning in warnings:
            print(f"- {warning}")
        return 0
    print("BACKLOG VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
