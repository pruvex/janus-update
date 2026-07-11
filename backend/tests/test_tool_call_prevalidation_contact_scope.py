import json

from backend.llm_providers.shared import utils as shared_utils


def _memory_read_call(query: str) -> dict:
    return {
        "id": "call_1",
        "type": "function",
        "function": {
            "name": "memory.read",
            "arguments": json.dumps({"query": query, "limit": 10}, ensure_ascii=False),
        },
    }


def test_prevalidate_memory_read_rebinds_conflicting_contact_scope_to_user_prompt():
    result = shared_utils._prevalidate_tool_calls(
        [_memory_read_call("Vorlieben und Abneigungen von Oli")],
        user_prompt="was mag olix?",
    )

    valid_call = result["valid_calls"][0]
    parsed_args = json.loads(valid_call["function"]["arguments"])

    assert parsed_args["query"] == "was mag olix?"
    assert result["system_hints"]


def test_prevalidate_memory_read_rebinds_scope_less_followup_to_user_prompt():
    result = shared_utils._prevalidate_tool_calls(
        [_memory_read_call("Vorlieben und Interessen")],
        user_prompt="was mag olix?",
    )

    valid_call = result["valid_calls"][0]
    parsed_args = json.loads(valid_call["function"]["arguments"])

    assert parsed_args["query"] == "was mag olix?"


def test_prevalidate_memory_read_keeps_multi_person_query_unchanged():
    result = shared_utils._prevalidate_tool_calls(
        [_memory_read_call("Vorlieben von Chris und Oli")],
        user_prompt="was mögen chris und oli?",
    )

    valid_call = result["valid_calls"][0]
    parsed_args = json.loads(valid_call["function"]["arguments"])

    assert parsed_args["query"] == "Vorlieben von Chris und Oli"


def test_prevalidate_memory_read_rebinds_overpacked_mixed_contact_scope_to_user_prompt():
    result = shared_utils._prevalidate_tool_calls(
        [_memory_read_call("Vorlieben von Oli Chris Gier Olix Quarz")],
        user_prompt="was mag olix?",
    )

    valid_call = result["valid_calls"][0]
    parsed_args = json.loads(valid_call["function"]["arguments"])

    assert parsed_args["query"] == "was mag olix?"
