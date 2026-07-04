import argparse
import json
from pathlib import Path


TOP_LEVEL_FIELDS = (
    "comparison_context",
    "comparison_time",
    "approval_boundary_note",
    "entries",
)

ENTRY_FIELDS = (
    "label",
    "captured_at",
    "prepared_package",
)

PACKAGE_FIELDS = (
    "task_class",
    "recommendation_time",
    "live_data_freshness",
    "internal_evidence_freshness",
    "recommended_favorite",
    "alternatives",
    "decision_notes",
)

FAVORITE_FIELDS = (
    "model",
    "why_it_leads",
    "best_fit_task_type",
    "main_tradeoff",
    "suggested_next_action",
)

ALTERNATIVE_FIELDS = (
    "model",
    "why_it_stays_viable",
    "best_fit_task_type",
    "main_tradeoff",
)

DECISION_NOTE_FIELDS = (
    "price_performance_signal",
    "benchmark_ranking_signal",
    "internal_evidence_signal",
    "confidence_level",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(container: dict, field_name: str) -> str:
    value = container.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or empty text field: {field_name}")
    return value.strip()


def validate_prepared_package(package: dict, entry_label: str) -> None:
    if not isinstance(package, dict):
        raise ValueError(f"prepared_package for {entry_label} must be an object.")

    for field_name in PACKAGE_FIELDS:
        if field_name not in package:
            raise ValueError(f"prepared_package for {entry_label} is missing field: {field_name}")

    for field_name in PACKAGE_FIELDS[:4]:
        require_text(package, field_name)

    favorite = package["recommended_favorite"]
    if not isinstance(favorite, dict):
        raise ValueError(f"recommended_favorite for {entry_label} must be an object.")
    for field_name in FAVORITE_FIELDS:
        require_text(favorite, field_name)

    alternatives = package["alternatives"]
    if not isinstance(alternatives, list) or not alternatives:
        raise ValueError(f"alternatives for {entry_label} must be a non-empty list.")
    for index, alternative in enumerate(alternatives, start=1):
        if not isinstance(alternative, dict):
            raise ValueError(f"Alternative {index} for {entry_label} must be an object.")
        for field_name in ALTERNATIVE_FIELDS:
            require_text(alternative, field_name)

    decision_notes = package["decision_notes"]
    if not isinstance(decision_notes, dict):
        raise ValueError(f"decision_notes for {entry_label} must be an object.")
    for field_name in DECISION_NOTE_FIELDS:
        require_text(decision_notes, field_name)


def validate_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Input payload must be a JSON object.")

    for field_name in TOP_LEVEL_FIELDS:
        if field_name not in payload:
            raise ValueError(f"Missing top-level field: {field_name}")

    for field_name in TOP_LEVEL_FIELDS[:3]:
        require_text(payload, field_name)

    entries = payload["entries"]
    if not isinstance(entries, list) or len(entries) < 2:
        raise ValueError("entries must contain at least 2 comparison entries.")

    seen_labels = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"Entry {index} must be an object.")
        for field_name in ENTRY_FIELDS:
            if field_name not in entry:
                raise ValueError(f"Entry {index} is missing field: {field_name}")
        label = require_text(entry, "label")
        require_text(entry, "captured_at")
        if label in seen_labels:
            raise ValueError(f"Duplicate entry label detected: {label}")
        seen_labels.add(label)
        validate_prepared_package(entry["prepared_package"], label)


def build_comparison_artifact(payload: dict) -> dict:
    entries = []
    for entry in payload["entries"]:
        package = entry["prepared_package"]
        favorite = package["recommended_favorite"]
        entries.append(
            {
                "label": entry["label"],
                "captured_at": entry["captured_at"],
                "task_class": package["task_class"],
                "favorite_model": favorite["model"],
                "favorite_reason": favorite["why_it_leads"],
                "suggested_next_action": favorite["suggested_next_action"],
                "alternatives": package["alternatives"],
                "decision_notes": package["decision_notes"],
                "source_recommendation_time": package["recommendation_time"],
            }
        )

    return {
        "comparison_context": payload["comparison_context"],
        "comparison_time": payload["comparison_time"],
        "approval_boundary_note": payload["approval_boundary_note"],
        "entry_count": len(entries),
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a stable comparison artifact from bounded prepared recommendation packages."
    )
    parser.add_argument("--input", required=True, help="Path to the comparison input JSON.")
    parser.add_argument("--output", required=True, help="Path to the comparison artifact JSON.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = read_json(input_path)
    validate_payload(payload)
    artifact = build_comparison_artifact(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
