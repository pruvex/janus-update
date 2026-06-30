from lean_precheck_eval import build_prompt


def test_build_prompt_uses_exact_needs_codex_review_token():
    prompt = build_prompt({"demo": "value"})
    assert "NEEDS_CODEX_REVIEW" in prompt
    assert "NEEDS_CODEx_REVIEW" not in prompt
