from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.data import crud
from backend.data.models import Base, Cost
from backend.services.cost_service import create_cost_entry


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_cost_entry_persists_cached_and_total_tokens_for_deep_dive():
    db = _session()

    entry = create_cost_entry(
        db=db,
        amount=0.001,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=1000,
        output_tokens=120,
        cached_tokens=350,
        total_tokens=1120,
        context_details="tool_loop_iteration=1;tool_calls=1",
    )

    stored = db.query(Cost).filter(Cost.id == entry.id).one()
    assert stored.cached_tokens == 350
    assert stored.total_tokens == 1120
    assert "tool_calls=1" in stored.context


def test_monthly_deep_dive_aggregates_hidden_cached_tokens_and_context_breakdown():
    db = _session()
    create_cost_entry(
        db=db,
        amount=0.001,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=1000,
        output_tokens=120,
        cached_tokens=350,
        total_tokens=1120,
        context_details="tool_loop_iteration=1;tool_calls=1",
    )
    create_cost_entry(
        db=db,
        amount=0.0005,
        model="gpt-5.4-nano",
        provider="openai",
        source_type="conversation",
        input_tokens=200,
        output_tokens=50,
        cached_tokens=0,
        total_tokens=250,
        context_details="stream_final_usage=1",
    )

    now = datetime.utcnow()
    summary = crud.get_monthly_cost_summary_by_model(db, now.year, now.month)
    row = next(item for item in summary if item["model"] == "gpt-5.4-nano")

    assert row["total_input_tokens"] == 1200
    assert row["total_output_tokens"] == 170
    assert row["total_cached_tokens"] == 350
    assert row["total_tokens"] == 1370
    contexts = {item["context"]: item for item in row["context_breakdown"]}
    assert contexts["conversation (tool_loop_iteration=1;tool_calls=1)"]["cached_tokens"] == 350
    assert contexts["conversation (stream_final_usage=1)"]["total_tokens"] == 250


def test_websearch_costs_remain_separate_deep_dive_component():
    db = _session()
    create_cost_entry(
        db=db,
        amount=0.009,
        model="websearch",
        provider="openai",
        source_type="websearch",
        context_details="query_count=1",
    )

    now = datetime.utcnow()
    summary = crud.get_monthly_cost_summary_by_model(db, now.year, now.month)
    row = next(item for item in summary if item["model"] == "__WEB_SEARCHES__")

    assert row["display_name"] == "Web-Recherchen"
    assert row["search_count"] == 1
    assert row["search_cost"] == 0.009
