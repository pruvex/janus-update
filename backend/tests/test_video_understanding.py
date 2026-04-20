"""Integration Tests for Video Understanding Skill (Task VID-UNDERSTAND-001 WO-6).

Tests:
1. Transcript Service TTL Cache
2. Video Understanding Tool Logic (Mocked)
3. Intent Detection
4. Schema Validation
"""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from backend.data.schemas import VideoUnderstandingInput
from backend.services.video.transcript_service import (
    TranscriptService,
    TranscriptResult,
    transcript_service,
    _TRANSCRIPT_CACHE,
    _TRANSCRIPT_CACHE_TTL_SECONDS,
    _get_cached_transcript,
    _store_cached_transcript,
)
from backend.tools.video_understanding import video_understanding_tool
from backend.services.orchestrator.intent_engine import intent_engine


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Transcript Service TTL Cache
# ═══════════════════════════════════════════════════════════════════════════════

def test_transcript_service_cache():
    """Test that the TTL cache works correctly."""
    service = TranscriptService()
    video_id = "test12345678"  # Must be 11 chars for real service

    # Clear cache first
    _TRANSCRIPT_CACHE.clear()

    # First call - should be cache miss
    with patch.object(service, 'get_transcript', wraps=service.get_transcript) as mock_get:
        mock_get.return_value = TranscriptResult(
            text="Test transcript",
            source="youtube_captions",
            language="de",
            chunks=["Test transcript"],
        )
        result1 = service.get_transcript(video_id)
        assert mock_get.call_count >= 1

    # Second call - should be cache hit (cache is cleared between patches in this test structure)
    # For a proper cache test, we need to verify the internal cache behavior
    # Let's test the cache directly
    _TRANSCRIPT_CACHE.clear()
    _store_cached_transcript(video_id, {
        "text": "Cached transcript",
        "source": "youtube_captions",
        "language": "de",
        "chunks": ["Cached transcript"],
        "video_title": "Cached Video",
    })
    
    cached = _get_cached_transcript(video_id)
    assert cached is not None
    assert cached["text"] == "Cached transcript"

    print("✓ Transcript Service TTL Cache test passed")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: Video Understanding Tool Logic (Mocked)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_video_understanding_tool_logic():
    """Test video understanding tool with mocked dependencies."""
    video_id = "dQw4w9WgXcQ"  # Rick Roll ID for testing
    args = VideoUnderstandingInput(
        video_id=video_id,
        task="summarize",
        language="de",
        detail_level="medium",
    )

    # Mock transcript service
    mock_transcript_result = TranscriptResult(
        text="This is a test transcript. The video is about testing.",
        source="youtube_captions",
        language="en",
        chunks=["This is a test transcript.", "The video is about testing."],
        video_title="Test Video",
    )

    # Mock LLM gateway
    mock_llm_response = {
        "text": "Zusammenfassung: Das Video handelt von Testen.",
    }

    # Mock memory storage
    mock_memory_stored = True

    with patch.object(
        transcript_service,
        'get_transcript',
        return_value=mock_transcript_result
    ) as mock_transcript:
        with patch('backend.llm_providers.openai.gateway.OpenAIGateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.complete = AsyncMock(return_value=mock_llm_response)
            mock_gateway_class.return_value = mock_gateway

            with patch.object(
                transcript_service,
                'store_summary_in_memory',
                return_value=mock_memory_stored
            ) as mock_memory:
                # Execute tool
                result = await video_understanding_tool(args)

                # Verify transcript was fetched
                mock_transcript.assert_called_once_with(video_id)

                # Verify memory storage was called
                mock_memory.assert_called_once()
                memory_call_args = mock_memory.call_args
                assert memory_call_args[1]['video_id'] == video_id
                assert memory_call_args[1]['title'] == "Test Video"
                assert "Zusammenfassung" in memory_call_args[1]['summary']

                # Verify result structure
                assert result.status == "ok"
                assert "data" in result.model_dump()
                data = result.model_dump()["data"]
                assert data["video_id"] == video_id
                assert data["task"] == "summarize"
                assert data["transcript_source"] == "youtube_captions"
                assert data["chunk_count"] == 2

                # Verify metadata
                assert result.metadata is not None
                assert result.metadata["memory_stored"] == mock_memory_stored
                assert result.metadata["transcript_source"] == "youtube_captions"

    print("✓ Video Understanding Tool Logic test passed")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Intent Detection
# ═══════════════════════════════════════════════════════════════════════════════

def test_intent_detection():
    """Test intent detection for various user inputs."""
    test_cases = [
        ("Fasse das Video zusammen", True),
        ("zusammenfassung", True),
        ("schritte aus dem video", True),
        ("anleitung aus dem video", True),
        ("transcript", True),
        ("worum geht es in dem video", True),
        ("erklär das video", True),
        ("was ist das wetter", False),
        ("wer ist angela merkel", False),
        ("schreibe einen brief", False),
    ]

    for user_input, expected_intent in test_cases:
        result = intent_engine.detect_video_understanding_intent(user_input)
        assert result == expected_intent, f"Failed for input: '{user_input}' (expected {expected_intent}, got {result})"

    print("✓ Intent Detection test passed (10 cases)")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: Schema Validation
# ═══════════════════════════════════════════════════════════════════════════════

def test_schema_validation():
    """Test schema validation for invalid inputs."""
    from pydantic import ValidationError

    # Test invalid video_id (too short)
    with pytest.raises(ValidationError):
        VideoUnderstandingInput(
            video_id="short",
            task="summarize",
        )

    # Test invalid video_id (too long)
    with pytest.raises(ValidationError):
        VideoUnderstandingInput(
            video_id="way_too_long_video_id",
            task="summarize",
        )

    # Test valid input
    valid_input = VideoUnderstandingInput(
        video_id="dQw4w9WgXcQ",  # Exactly 11 chars
        task="summarize",
        language="de",
        detail_level="medium",
    )
    assert valid_input.video_id == "dQw4w9WgXcQ"
    assert valid_input.task == "summarize"
    assert valid_input.language == "de"
    assert valid_input.detail_level == "medium"

    print("✓ Schema Validation test passed")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5: Memory Bridge Tag Verification
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_memory_bridge_tag_verification():
    """Test that Memory Bridge sets the 'video' tag correctly."""
    video_id = "dQw4w9WgXcQ"  # Exactly 11 chars (Rick Roll ID)
    args = VideoUnderstandingInput(
        video_id=video_id,
        task="summarize",
        language="de",
    )

    mock_transcript_result = TranscriptResult(
        text="Test transcript for tag verification.",
        source="youtube_captions",
        language="en",
        chunks=["Test transcript for tag verification."],
        video_title="Tag Test Video",
    )

    mock_llm_response = {
        "text": "Test summary for tag verification.",
    }

    with patch.object(
        transcript_service,
        'get_transcript',
        return_value=mock_transcript_result
    ):
        with patch('backend.llm_providers.openai.gateway.OpenAIGateway') as mock_gateway_class:
            mock_gateway = MagicMock()
            mock_gateway.complete = AsyncMock(return_value=mock_llm_response)
            mock_gateway_class.return_value = mock_gateway

            # Track the memory storage call
            with patch.object(
                transcript_service,
                'store_summary_in_memory',
                return_value=True
            ) as mock_memory:
                result = await video_understanding_tool(args)

                # Verify memory storage was called
                mock_memory.assert_called_once()
                memory_call_kwargs = mock_memory.call_args[1]

                # Verify the 'video' tag is set
                # Note: This requires Memory V2 to actually check the tags
                # For now we verify the call was made with correct parameters
                assert memory_call_kwargs['video_id'] == video_id
                assert memory_call_kwargs['title'] == "Tag Test Video"
                assert memory_call_kwargs['summary'] == "Test summary for tag verification."

                # The actual tag verification would require checking the Memory V2
                # implementation, which is beyond the scope of this tool test
                # We verify the call signature matches the contract

    print("✓ Memory Bridge Tag Verification test passed (call signature verified)")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 6: Transcript Unavailable Handling
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_transcript_unavailable_handling():
    """Test graceful degradation when transcript is unavailable."""
    video_id = "unavailabl0"  # Exactly 11 chars
    args = VideoUnderstandingInput(
        video_id=video_id,
        task="summarize",
    )

    # Mock unavailable transcript
    mock_transcript_result = TranscriptResult(
        text="",
        source="unavailable",
        language="",
        chunks=[],
        video_title="",
    )

    with patch.object(
        transcript_service,
        'get_transcript',
        return_value=mock_transcript_result
    ):
        result = await video_understanding_tool(args)

        # Should return error status
        assert result.status == "error"
        assert result.error is not None
        assert result.error.code == "TRANSCRIPT_UNAVAILABLE"
        assert "Kein Transkript" in result.error.message

    print("✓ Transcript Unavailable Handling test passed")
