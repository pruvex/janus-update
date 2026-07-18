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
    assert record["model"] == MODEL
    assert record["prompt_tokens"] == 0
    assert record["completion_tokens"] is None
    assert record["credits_cost"] == 0.0
    assert record["upstream_inference_cost"] == 0.25
    assert record["entry_count"] == 1
    assert record["turn_count"] == 1
    assert "turn_id" not in record

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


def test_deep_dive_aggregates_openrouter_telemetry_by_model():
    db = _session()
    create_openrouter_telemetry_entry(
        db,
        telemetry=normalize_openrouter_telemetry(
            {
                "prompt_tokens": 100,
                "completion_tokens": 10,
                "total_tokens": 110,
                "prompt_tokens_details": {"cached_tokens": 40},
                "cost": 0.01,
            },
            response_model="z-ai/glm-5.2",
        ),
        turn_id="turn-a",
        chat_id=1,
        round_number=1,
    )
    create_openrouter_telemetry_entry(
        db,
        telemetry=normalize_openrouter_telemetry(
            {
                "prompt_tokens": 200,
                "completion_tokens": 20,
                "total_tokens": 220,
                "prompt_tokens_details": {"cached_tokens": 50},
                "cost": 0.02,
            },
            response_model="z-ai/glm-5.2",
        ),
        turn_id="turn-a",
        chat_id=1,
        round_number=2,
    )
    create_openrouter_telemetry_entry(
        db,
        telemetry=normalize_openrouter_telemetry(
            {
                "prompt_tokens": 50,
                "completion_tokens": 5,
                "total_tokens": 55,
                "cost": 0.005,
            },
            response_model="deepseek/deepseek-v4-pro",
        ),
        turn_id="turn-b",
        chat_id=2,
        round_number=1,
    )

    first = db.query(Cost).filter(Cost.provider == "openrouter").first()
    summary = crud.get_costs_deep_dive_summary(
        db,
        first.timestamp.year,
        first.timestamp.month,
    )
    rows = summary["openrouter_telemetry"]
    assert len(rows) == 2
    by_model = {row["model"]: row for row in rows}
    glm = by_model["z-ai/glm-5.2"]
    assert glm["entry_count"] == 2
    assert glm["turn_count"] == 1
    assert glm["prompt_tokens"] == 300
    assert glm["completion_tokens"] == 30
    assert glm["total_tokens"] == 330
    assert glm["cached_tokens"] == 90
    assert abs(float(glm["credits_cost"]) - 0.03) < 1e-9
    deepseek = by_model["deepseek/deepseek-v4-pro"]
    assert deepseek["entry_count"] == 1
    assert deepseek["turn_count"] == 1
    assert deepseek["prompt_tokens"] == 50

    assert abs(float(summary["cross_provider_summary"]["api_key_total_cost"]) - 0.0) < 1e-9
    assert abs(float(summary["cross_provider_summary"]["openrouter_total_cost"]) - 0.035) < 1e-9
    assert abs(float(summary["cross_provider_summary"]["combined_total_cost"]) - 0.035) < 1e-9
    assert abs(float(summary["cross_provider_summary"]["total_cost"]) - 0.035) < 1e-9
    assert summary["cross_provider_summary"]["openrouter_model_count"] == 2
    assert summary["cross_provider_summary"]["provider_count"] == 1


def test_costs_dashboard_totals_split_api_and_openrouter():
    db = _session()
    db.add(
        Cost(
            timestamp=__import__("datetime").datetime.utcnow(),
            provider="openai",
            model="gpt-test",
            input_tokens=10,
            output_tokens=5,
            cached_tokens=0,
            total_tokens=15,
            total_cost=1.26,
            context="conversation",
            tokens_saved=0,
            cost_saved=0.0,
        )
    )
    db.commit()
    create_openrouter_telemetry_entry(
        db,
        telemetry=normalize_openrouter_telemetry(
            {"prompt_tokens": 1, "cost": 0.5},
            response_model="z-ai/glm-5.2",
        ),
        turn_id="dash-1",
        chat_id=9,
        round_number=1,
    )

    now = __import__("datetime").datetime.utcnow()
    totals = crud.get_costs_dashboard_totals(db, now.year, now.month)
    assert abs(float(totals["api_key_total_cost"]) - 1.26) < 1e-9
    assert abs(float(totals["openrouter_total_cost"]) - 0.5) < 1e-9
    assert abs(float(totals["combined_total_cost"]) - 1.76) < 1e-9
    assert abs(float(totals["current_month_cost"]) - 1.76) < 1e-9
