import pytest

from backend.llm_providers.shared.tool_call_adapter import get_tool_call_adapter


@pytest.mark.parametrize("skill_id", ["system.weather", "system.websearch"])
def test_openai_and_gemini_keep_selected_skill_ids_canonical_roundtrip(skill_id):
    openai = get_tool_call_adapter("openai")
    gemini = get_tool_call_adapter("gemini")

    openai_outbound = openai.outbound_name(skill_id)
    gemini_outbound = gemini.outbound_name(skill_id)

    assert openai_outbound == gemini_outbound == skill_id.replace(".", "_")
    assert openai.inbound_name(openai_outbound) == skill_id
    assert gemini.inbound_name(gemini_outbound) == skill_id
