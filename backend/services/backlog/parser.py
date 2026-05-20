from __future__ import annotations

import re
from pathlib import Path

from backend.services.backlog.schemas import BacklogCounts, BacklogItem, BacklogItemsResponse

DEFAULT_BACKLOG_PATH = Path(__file__).resolve().parents[3] / "documentation" / "backlog" / "BACKLOG.md"
ITEM_HEADING_PATTERN = re.compile(r"^###\s+(BACKLOG-\d+)\s+(?:–|â€“|-)\s+(.+?)\s*$")
SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
FIELD_PATTERN = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")

FIELD_ALIASES = {
    "Typ": "type",
    "Status": "status",
    "Quelle": "source",
    "Erstellt": "created_at",
    "Aktualisiert": "updated_at",
    "Kurzbeschreibung": "summary",
    "Erwartetes Verhalten": "expected_behavior",
    "Tatsächliches Verhalten": "actual_behavior",
    "TatsÃ¤chliches Verhalten": "actual_behavior",
    "Reproduktion / Kontext": "reproduction_context",
    "Betroffener Bereich": "affected_area",
    "Nachweise": "evidence",
    "Notizen": "notes",
    "Wichtigkeit": "importance",
    "Umsetzungsrisiko": "implementation_risk",
    "Aufwand": "effort",
    "Umsetzungsreife": "readiness",
    "Empfehlung": "recommendation",
    "Entry Point": "entry_point",
    "Routing reason": "routing_reason",
    "Routing confidence": "routing_confidence",
    "Routing decided by": "routing_decided_by",
    "Routing decided at": "routing_decided_at",
    "Routing blocker": "routing_blocker",
    "Handoff": "handoff",
    "Recommended next skill": "recommended_next_skill",
    "Handoff created": "handoff_created",
    "Precheck artifact": "precheck_artifact",
    "Target Task": "target_task",
    "Completed in version": "completed_in_version",
    "Completed by task": "completed_by_task",
    "Completed at": "completed_at",
    "Abgeschlossen": "completed_at",
    "Final audit": "final_audit",
    "Validation evidence": "validation_evidence",
    "Changelog": "changelog",
}

COUNT_KEYS = {
    "NEEDS INFO": "needs_info",
    "READY": "ready",
    "IN PROGRESS": "in_progress",
    "DONE": "done",
    "BLOCKED": "blocked",
}


def parse_backlog_file(path: str | Path = DEFAULT_BACKLOG_PATH) -> BacklogItemsResponse:
    backlog_path = Path(path)
    text = backlog_path.read_text(encoding="utf-8")
    return parse_backlog_text(text, source=str(backlog_path))


def parse_backlog_text(text: str, source: str = "documentation/backlog/BACKLOG.md") -> BacklogItemsResponse:
    items: list[BacklogItem] = []
    current_section: str | None = None
    current_item: BacklogItem | None = None
    current_field: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        section_match = SECTION_PATTERN.match(line)
        if section_match and not line.startswith("###"):
            current_section = section_match.group(1).strip()
            current_field = None
            continue

        item_match = ITEM_HEADING_PATTERN.match(line)
        if item_match:
            if current_item is not None:
                items.append(current_item)
            current_item = BacklogItem(
                id=item_match.group(1).strip(),
                title=item_match.group(2).strip(),
                section=current_section,
            )
            current_field = None
            continue

        if current_item is None:
            continue

        field_match = FIELD_PATTERN.match(line)
        if field_match:
            field_name = field_match.group(1).strip()
            value = field_match.group(2).strip()
            attr_name = FIELD_ALIASES.get(field_name)
            current_item.raw_fields[field_name] = value
            if attr_name is not None:
                setattr(current_item, attr_name, value)
                current_field = attr_name
            else:
                current_field = None
            continue

        if current_field and _is_continuation_line(line):
            previous = getattr(current_item, current_field) or ""
            continuation = line.strip()
            if continuation:
                joined = f"{previous}\n{continuation}" if previous else continuation
                setattr(current_item, current_field, joined)

    if current_item is not None:
        items.append(current_item)

    _normalize_items(items)
    return BacklogItemsResponse(source=source, items=items, counts=_build_counts(items))


def _is_continuation_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("###") or stripped.startswith("##"):
        return False
    if FIELD_PATTERN.match(stripped):
        return False
    return line.startswith(" ") or stripped.startswith("-")


def _normalize_items(items: list[BacklogItem]) -> None:
    for item in items:
        if item.status:
            item.status = item.status.upper()
        if item.section:
            item.section = item.section.upper()
        if item.status in COUNT_KEYS:
            item.section = item.status
        if item.entry_point:
            item.entry_point = item.entry_point.upper()
        if item.routing_confidence:
            item.routing_confidence = item.routing_confidence.upper()
        if item.recommended_next_skill:
            item.recommended_next_skill = item.recommended_next_skill.upper()
        # Mark items from TestRun as test blockers
        if item.source and item.source.upper() == "TESTRUN":
            item.is_test_blocker = True


def _build_counts(items: list[BacklogItem]) -> BacklogCounts:
    counts = BacklogCounts(total=len(items))
    for item in items:
        status = item.status or ""
        key = COUNT_KEYS.get(status)
        if key:
            setattr(counts, key, getattr(counts, key) + 1)
        if status == "DONE":
            counts.history += 1
        else:
            counts.active += 1
        if not item.entry_point and status != "DONE":
            counts.routing_missing += 1
        if item.entry_point == "ROUTING_BLOCKED":
            counts.routing_blocked += 1
    return counts
