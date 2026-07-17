from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.data import crud
from backend.data.models import Base, Cost
from backend.llm_providers.openrouter.service import normalize_openrouter_telemetry
from backend.services.cost_service import create_openrouter_telemetry_entry


MODEL = "vendor/model-2026-07-17"


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_normalizer_preserves_complete_zero_and_missing_values():
    telemetry = normalize_openrouter_telemetry(
        {
            "prompt_tokens": 10,
            "completion_tokens": 0,
            "total_tokens": 10,
            "prompt_tokens_details": {
                "cached_tokens": 0,
                "cache_write_tokens": 3,
            },
            "completion_tokens_details": {"reasoning_tokens": 2},
            "cost": 0.0,
            "cost_details": {"upstream_inference_cost": 0.125},
        },
        response_model=MODEL,
    )

    assert telemetry == {
        "response_model": MODEL,
        "prompt_tokens": 10,
        "completion_tokens": 0,
        "total_tokens": 10,
        "cached_tokens": 0,
        "cache_write_tokens": 3,
        "reasoning_tokens": 2,
        "credits_cost": 0.0,
        "upstream_inference_cost": 0.125,
    }

    missing = normalize_openrouter_telemetry({}, response_model=MODEL)
    assert missing["response_model"] == MODEL
    assert all(value is None for key, value in missing.items() if key != "response_model")

    invalid = normalize_openrouter_telemetry(
        {
            "prompt_tokens": 1.5,
            "completion_tokens": True,
            "total_tokens": float("inf"),
            "cost": float("nan"),
            "cost_details": {"upstream_inference_cost": "0.25"},
        },
        response_model=MODEL,
    )
    assert all(value is None for key, value in invalid.items() if key != "response_model")


def test_persistence_and_deep_dive_keep_units_and_nullability_separate():
    db = _session()
    entry = create_openrouter_telemetry_entry(
        db,
        telemetry=normalize_openrouter_telemetry(
            {
                "prompt_tokens": 0,
                "cost": 0.0,
                "cost_details": {"upstream_inference_cost": 0.25},
            },
            response_model=MODEL,
        ),
        turn_id="turn-1",
        chat_id=7,
        round_number=1,
    )

    stored = db.query(Cost).filter(Cost.id == entry.id).one()
    assert stored.openrouter_prompt_tokens == 0
    assert stored.openrouter_completion_tokens is None
    assert stored.openrouter_credits_cost == 0.0
    assert stored.openrouter_upstream_inference_cost == 0.25
    assert stored.total_cost == 0.0
    assert stored.attribution_request_id == "turn-1"
    assert stored.model == MODEL

    summary = crud.get_costs_deep_dive_summary(
        db,
        stored.timestamp.year,
        stored.timestamp.month,
    )
    assert summary["cross_provider_summary"]["total_cost"] == 0.0
    record = summary["openrouter_telemetry"][0]
    assert record["prompt_tokens"] == 0
    assert record["completion_tokens"] is None
    assert record["credits_cost"] == 0.0
    assert record["upstream_inference_cost"] == 0.25
    assert record["turn_id"] == "turn-1"

    duplicate = create_openrouter_telemetry_entry(
        db,
        telemetry={"response_model": MODEL, "prompt_tokens": 999},
        turn_id="turn-1",
        chat_id=7,
        round_number=1,
    )
    assert duplicate.id == stored.id
    assert db.query(Cost).filter(Cost.provider == "openrouter").count() == 1
    assert duplicate.openrouter_prompt_tokens == 0
