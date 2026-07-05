import argparse
import json
from pathlib import Path


TOP_LEVEL_FIELDS = (
    "comparison_context",
    "comparison_time",
    "approval_boundary_note",
    "entry_count",
    "entries",
)

ENTRY_FIELDS = (
    "label",
    "captured_at",
    "task_class",
    "favorite_model",
    "favorite_reason",
    "suggested_next_action",
    "alternatives",
    "decision_notes",
    "source_recommendation_time",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(container: dict, field_name: str) -> str:
    value = container.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or empty text field: {field_name}")
    return value.strip()


def validate_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Input payload must be a JSON object.")

    for field_name in TOP_LEVEL_FIELDS:
        if field_name not in payload:
            raise ValueError(f"Missing top-level field: {field_name}")

    for field_name in TOP_LEVEL_FIELDS[:3]:
        require_text(payload, field_name)

    entry_count = payload["entry_count"]
    if not isinstance(entry_count, int) or entry_count < 1:
        raise ValueError("entry_count must be a positive integer.")

    entries = payload["entries"]
    if not isinstance(entries, list) or len(entries) != entry_count:
        raise ValueError("entries must be a list matching entry_count.")

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {index} must be an object.")
        for field_name in ENTRY_FIELDS:
            if field_name not in entry:
                raise ValueError(f"Entry {index} is missing field: {field_name}")
        for field_name in (
            "label",
            "captured_at",
            "task_class",
            "favorite_model",
            "favorite_reason",
            "suggested_next_action",
            "source_recommendation_time",
        ):
            require_text(entry, field_name)
        if not isinstance(entry["alternatives"], list):
            raise ValueError(f"alternatives for entry {index} must be a list.")
        if not isinstance(entry["decision_notes"], dict):
            raise ValueError(f"decision_notes for entry {index} must be an object.")


def build_archive_view(payload: dict) -> str:
    lines = [
        "MCP RECOMMENDATION COMPARISON ARCHIVE",
        "",
        f"Comparison Context: {payload['comparison_context']}",
        f"Comparison Time: {payload['comparison_time']}",
        f"Entries: {payload['entry_count']}",
        "",
        "Archived Recommendations:",
    ]

    for index, entry in enumerate(payload["entries"], start=1):
        lines.extend(
            [
                f"{index}. Label: {entry['label']}",
                f"   Captured At: {entry['captured_at']}",
                f"   Source Recommendation Time: {entry['source_recommendation_time']}",
                f"   Task Class: {entry['task_class']}",
                f"   Favorite Model: {entry['favorite_model']}",
                f"   Favorite Reason: {entry['favorite_reason']}",
                f"   Suggested Next Action: {entry['suggested_next_action']}",
            ]
        )

        alternatives = entry["alternatives"]
        if alternatives:
            lines.append("   Alternatives:")
            for alternative in alternatives:
                lines.append(
                    f"   - {alternative['model']}: {alternative['main_tradeoff']}"
                )

        decision_notes = entry["decision_notes"]
        lines.extend(
            [
                "   Decision Notes:",
                f"   - Price-performance: {decision_notes['price_performance_signal']}",
                f"   - Benchmark/ranking: {decision_notes['benchmark_ranking_signal']}",
                f"   - Internal evidence: {decision_notes['internal_evidence_signal']}",
                f"   - Confidence: {decision_notes['confidence_level']}",
                "",
            ]
        )

    lines.extend(
        [
            "Approval Boundary:",
            f"- {payload['approval_boundary_note']}",
            "- This archive view does not decide winners or authorize any real OR candidate test.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a stable archive view from a bounded recommendation comparison artifact."
    )
    parser.add_argument("--input", required=True, help="Path to the comparison artifact JSON.")
    parser.add_argument("--output", required=True, help="Path to the archive-view markdown output.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = read_json(input_path)
    validate_payload(payload)
    archive_view = build_archive_view(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(archive_view, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
