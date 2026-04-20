from backend.services.prompting.runtime.builder import PromptBuilder


def test_prompt_builder_uses_gemini_compiler_with_xml_dialect():
    builder = PromptBuilder()
    builder.add_block("system_role", "Du bist Janus.", priority=1, required=True)
    builder.add_block("memory", "Rechercheblock A", priority=2, required=True)
    builder.add_block("grounding_rules", "Nutze nur den Kontext.", priority=1, required=True)
    builder.add_block("output_contract", "Antworte als Liste.", priority=1, required=True)
    builder.add_block("user_prompt", "Beantworte die Frage.", priority=1, required=True)

    compiled = builder.compile(provider="gemini", model_id="gemini-3-pro-preview", max_tokens=400)

    assert compiled.startswith("<role>")
    assert "<context>" in compiled
    assert "<constraints>" in compiled
    assert "<output_format>" in compiled
    assert compiled.endswith("</task>")


def test_prompt_builder_keeps_openai_compiler_behavior():
    builder = PromptBuilder()
    builder.add_block("system_role", "Du bist Janus.", priority=1, required=True)
    builder.add_block("user_prompt", "Hallo", priority=1, required=True)

    compiled = builder.compile(provider="openai", model_id="gpt-5", max_tokens=200)

    assert "ROLE: Du bist Janus." in compiled
    assert "### USER-INTENT:" in compiled
