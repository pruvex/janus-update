from backend.services.orchestrator.execution_engine import _build_dynamic_fallback_summary


def test_openai_authentication_error_gets_actionable_user_message():
    message = _build_dynamic_fallback_summary(
        exception=RuntimeError("AuthenticationError: status=401 invalid_api_key"),
        provider="openai",
        model="gpt-5.4-nano",
    )

    assert "OpenAI-API-Key" in message
    assert "neu eintragen" in message
    assert "robusten Neuaufbau" not in message
