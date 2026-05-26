"""TASK-067 mutation guard store + confirmation parsing."""

import uuid

import pytest

from backend.data.schemas import MutationProposal
from backend.services.calendar import mutation_guard_store as mgs
from backend.services.calendar_mutation_intent import classify_calendar_mutation_intent


@pytest.fixture(autouse=True)
def clear_store():
    for k in (909001, 909002):
        mgs.clear_pending_mutation_proposal(k)
    yield
    for k in (909001, 909002):
        mgs.clear_pending_mutation_proposal(k)


def test_confirmation_and_reject_classification():
    assert mgs.classify_confirmation_reply("Ja") == "confirm"
    assert mgs.classify_confirmation_reply("okay") == "confirm"
    assert mgs.classify_confirmation_reply("bestätige") == "confirm"
    assert mgs.classify_confirmation_reply("Nein") == "reject"
    assert mgs.classify_confirmation_reply("abbrechen") == "reject"
    assert mgs.classify_confirmation_reply("was steht heute an") is None


def test_pending_roundtrip():
    cid = 909001
    pid = str(uuid.uuid4())
    p = MutationProposal(
        proposal_id=pid,
        chat_id=cid,
        event_id="ev123",
        proposed_changes={"new_description": "Handtuch"},
        original_event={"summary": "Sport"},
        status="pending",
    )
    mgs.set_pending_mutation_proposal(cid, p)
    got = mgs.get_pending_mutation_proposal(cid)
    assert got is not None
    assert got.proposal_id == pid
    popped = mgs.pop_pending_mutation_proposal(cid)
    assert popped.proposal_id == pid
    assert mgs.get_pending_mutation_proposal(cid) is None


def test_tool_args_from_proposal_fills_title():
    pid = str(uuid.uuid4())
    p = MutationProposal(
        proposal_id=pid,
        chat_id=909002,
        event_id="gid@google.com",
        proposed_changes={"new_description": "x"},
        original_event={"summary": "Meeting A"},
    )
    args = mgs.tool_args_from_proposal(p)
    assert args["event_id"] == "gid@google.com"
    assert args["event_title_query"] == "Meeting A"
    assert args["new_description"] == "x"


def test_task_067_b_mutation_classification():
    assert classify_calendar_mutation_intent(
        new_description="Yogamatte mitnehmen",
    ) == "DATA_MUTATION"
    assert classify_calendar_mutation_intent(
        new_summary="Foo",
        new_location="Berlin",
    ) == "DATA_MUTATION"
    assert classify_calendar_mutation_intent(
        new_start_time="2026-05-03T18:00:00",
    ) == "TIME_MUTATION"
    assert classify_calendar_mutation_intent(
        cancel_event=True,
    ) == "TIME_MUTATION"
    assert classify_calendar_mutation_intent(
        new_description="x",
        new_start_time="morgen 10 Uhr",
    ) == "TIME_MUTATION"
    assert classify_calendar_mutation_intent() == "NONE"


def test_build_confirmation_prompt_message():
    p = MutationProposal(
        proposal_id="p1",
        chat_id=1,
        event_id="e1",
        proposed_changes={"new_start_time": "morgen 15:00"},
        original_event={"summary": "Frisör"},
    )
    msg = mgs.build_confirmation_prompt_message(p)
    assert "Frisör" in msg
    assert "15:00" in msg or "morgen" in msg
    assert "Ja" in msg
