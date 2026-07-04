import argparse
import json
from pathlib import Path


TOP_LEVEL_FIELDS = (
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


def read_input(path: Path) -> dict:
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

    for field_name in TOP_LEVEL_FIELDS[:4]:
        require_text(payload, field_name)

    favorite = payload["recommended_favorite"]
    if not isinstance(favorite, dict):
        raise ValueError("recommended_favorite must be an object.")
    for field_name in FAVORITE_FIELDS:
        require_text(favorite, field_name)

    alternatives = payload["alternatives"]
    if not isinstance(alternatives, list):
        raise ValueError("alternatives must be a list.")
    if len(alternatives) < 1 or len(alternatives) > 2:
        raise ValueError("alternatives must contain exactly 1 or 2 entries.")
    for index, alternative in enumerate(alternatives, start=1):
        if not isinstance(alternative, dict):
            raise ValueError(f"Alternative {index} must be an object.")
        for field_name in ALTERNATIVE_FIELDS:
            require_text(alternative, field_name)

    decision_notes = payload["decision_notes"]
    if not isinstance(decision_notes, dict):
        raise ValueError("decision_notes must be an object.")
    for field_name in DECISION_NOTE_FIELDS:
        require_text(decision_notes, field_name)


def render_recommendation(payload: dict) -> str:
    favorite = payload["recommended_favorite"]
    alternatives = payload["alternatives"]
    decision_notes = payload["decision_notes"]

    lines = [
        "MCP PRE-RUN RECOMMENDATION",
        "",
        f"Task Class: {payload['task_class']}",
        f"Recommendation Time: {payload['recommendation_time']}",
        f"Live Data Freshness: {payload['live_data_freshness']}",
        f"Internal Evidence Freshness: {payload['internal_evidence_freshness']}",
        "",
        "Recommended Favorite:",
        f"- Model: {favorite['model']}",
        f"- Why it leads: {favorite['why_it_leads']}",
        f"- Best fit task type: {favorite['best_fit_task_type']}",
        f"- Main tradeoff: {favorite['main_tradeoff']}",
        f"- Suggested next action: {favorite['suggested_next_action']}",
        "",
        "Alternatives:",
    ]

    for index, alternative in enumerate(alternatives, start=1):
        lines.extend(
            [
                f"{index}. Model: {alternative['model']}",
                f"   Why it stays viable: {alternative['why_it_stays_viable']}",
                f"   Best fit task type: {alternative['best_fit_task_type']}",
                f"   Main tradeoff: {alternative['main_tradeoff']}",
            ]
        )

    lines.extend(
        [
            "",
            "Decision Notes:",
            f"- Price-performance signal: {decision_notes['price_performance_signal']}",
            f"- Benchmark/ranking signal: {decision_notes['benchmark_ranking_signal']}",
            f"- Internal evidence signal: {decision_notes['internal_evidence_signal']}",
            f"- Confidence level: {decision_notes['confidence_level']}",
            "",
            "Approval Boundary:",
            "- This is a recommendation only.",
            "- Codex/operator approval is required before any real OR candidate test continues.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a bounded MCP recommendation artifact.")
    parser.add_argument("--input", required=True, help="Path to the bounded recommendation input JSON.")
    parser.add_argument("--output", required=True, help="Path to the rendered markdown artifact.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = read_input(input_path)
    validate_payload(payload)
    rendered = render_recommendation(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
