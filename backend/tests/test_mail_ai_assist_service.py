from unittest.mock import AsyncMock, patch

import pytest

from backend.services.mail.mail_ai_assist_service import MailAiAssistService


@pytest.mark.asyncio
async def test_ai_analyze_returns_degraded_without_configured_provider():
    service = MailAiAssistService()
    detail = {"id": "m1", "date": "today", "body_text": "Bitte melden."}

    with patch.object(service, "_resolve_text_model", return_value=("", "")):
        result = await service.analyze_with_llm(detail)

    assert result.degraded is True
    assert result.reply_needed == "unknown"
    assert "not configured" in result.error_message


@pytest.mark.asyncio
async def test_ai_analyze_returns_degraded_on_provider_failure():
    service = MailAiAssistService()
    detail = {"id": "m1", "date": "today", "body_text": "Bitte melden."}

    with (
        patch.object(service, "_resolve_text_model", return_value=("openai", "gpt-test")),
        patch(
            "backend.services.mail.mail_ai_assist_service.llm_gateway.call_llm",
            new=AsyncMock(side_effect=RuntimeError("provider boom")),
        ),
    ):
        result = await service.analyze_with_llm(detail)

    assert result.degraded is True
    assert result.summary == "AI-Analyse ist aktuell nicht verfuegbar."
    assert "failed" in result.error_message


@pytest.mark.asyncio
async def test_ai_analyze_returns_degraded_on_invalid_provider_payload():
    service = MailAiAssistService()
    detail = {"id": "m1", "date": "today", "body_text": "Bitte melden."}

    with (
        patch.object(service, "_resolve_text_model", return_value=("openai", "gpt-test")),
        patch(
            "backend.services.mail.mail_ai_assist_service.llm_gateway.call_llm",
            new=AsyncMock(return_value={"text": '{"summary":"ok","reply_needed":"maybe","priority":"medium"}'}),
        ),
    ):
        result = await service.analyze_with_llm(detail)

    assert result.degraded is True
    assert result.reply_needed == "unknown"
    assert "invalid" in result.error_message


@pytest.mark.asyncio
async def test_ai_draft_returns_degraded_on_provider_failure():
    service = MailAiAssistService()
    detail = {"id": "m1", "subject": "Test", "body_text": "Hallo"}

    with (
        patch.object(service, "_resolve_text_model", return_value=("openai", "gpt-test")),
        patch(
            "backend.services.mail.mail_ai_assist_service.llm_gateway.call_llm",
            new=AsyncMock(side_effect=RuntimeError("provider boom")),
        ),
    ):
        result = await service.draft_with_llm(detail, "neutral")

    assert result.degraded is True
    assert result.draft == ""
    assert "failed" in result.error_message


@pytest.mark.asyncio
async def test_ai_draft_returns_degraded_on_empty_provider_payload():
    service = MailAiAssistService()
    detail = {"id": "m1", "subject": "Test", "body_text": "Hallo"}

    with (
        patch.object(service, "_resolve_text_model", return_value=("openai", "gpt-test")),
        patch(
            "backend.services.mail.mail_ai_assist_service.llm_gateway.call_llm",
            new=AsyncMock(return_value={"text": ""}),
        ),
    ):
        result = await service.draft_with_llm(detail, "neutral")

    assert result.degraded is True
    assert result.draft == ""
    assert "empty" in result.error_message
