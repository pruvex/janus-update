import argparse
import json
from pathlib import Path


TOP_LEVEL_FIELDS = (
    "task_class",
    "recommendation_time",
    "live_data_freshness",
    "internal_evidence_freshness",
    "favorite_candidate",
    "alternative_candidates",
    "signals",
)

FAVORITE_FIELDS = (
    "model",
    "lead_reason",
    "best_fit_task_type",
    "main_tradeoff",
    "next_action",
)

ALTERNATIVE_FIELDS = (
    "model",
    "viability_reason",
    "best_fit_task_type",
    "main_tradeoff",
)

SIGNAL_FIELDS = (
    "price_performance",
    "benchmark_ranking",
    "internal_evidence",
    "confidence",
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

    for field_name in TOP_LEVEL_FIELDS[:4]:
        require_text(payload, field_name)

    favorite = payload["favorite_candidate"]
    if not isinstance(favorite, dict):
        raise ValueError("favorite_candidate must be an object.")
    for field_name in FAVORITE_FIELDS:
        require_text(favorite, field_name)

    alternatives = payload["alternative_candidates"]
    if not isinstance(alternatives, list):
        raise ValueError("alternative_candidates must be a list.")
    if len(alternatives) < 1 or len(alternatives) > 2:
        raise ValueError("alternative_candidates must contain exactly 1 or 2 entries.")
    for index, alternative in enumerate(alternatives, start=1):
        if not isinstance(alternative, dict):
            raise ValueError(f"Alternative {index} must be an object.")
        for field_name in ALTERNATIVE_FIELDS:
            require_text(alternative, field_name)

    signals = payload["signals"]
    if not isinstance(signals, dict):
        raise ValueError("signals must be an object.")
    for field_name in SIGNAL_FIELDS:
        require_text(signals, field_name)


def build_renderer_payload(payload: dict) -> dict:
    favorite = payload["favorite_candidate"]
    alternatives = payload["alternative_candidates"]
    signals = payload["signals"]

    return {
        "task_class": payload["task_class"],
        "recommendation_time": payload["recommendation_time"],
        "live_data_freshness": payload["live_data_freshness"],
        "internal_evidence_freshness": payload["internal_evidence_freshness"],
        "recommended_favorite": {
            "model": favorite["model"],
            "why_it_leads": favorite["lead_reason"],
            "best_fit_task_type": favorite["best_fit_task_type"],
            "main_tradeoff": favorite["main_tradeoff"],
            "suggested_next_action": favorite["next_action"],
        },
        "alternatives": [
            {
                "model": candidate["model"],
                "why_it_stays_viable": candidate["viability_reason"],
                "best_fit_task_type": candidate["best_fit_task_type"],
                "main_tradeoff": candidate["main_tradeoff"],
            }
            for candidate in alternatives
        ],
        "decision_notes": {
            "price_performance_signal": signals["price_performance"],
            "benchmark_ranking_signal": signals["benchmark_ranking"],
            "internal_evidence_signal": signals["internal_evidence"],
            "confidence_level": signals["confidence"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a renderer-ready recommendation package from a bounded local evidence bundle.")
    parser.add_argument("--input", required=True, help="Path to the source evidence bundle JSON.")
    parser.add_argument("--output", required=True, help="Path to the renderer-ready recommendation JSON.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    payload = read_json(input_path)
    validate_payload(payload)
    prepared_payload = build_renderer_payload(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(prepared_payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
