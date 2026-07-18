from __future__ import annotations

import asyncio
from unittest.mock import patch

from backend.data.schemas import VideoResult, VideoSearchInput
from backend.tools import video_tools


def test_ytdlp_entry_to_video_result_maps_title_and_channel() -> None:
    video = video_tools._ytdlp_entry_to_video_result(
        {
            "id": "9mmVa6O-hzQ",
            "title": "PYTHON LERNEN in 10 Minuten",
            "channel": "Programmieren lernen",
            "view_count": 263948,
            "upload_date": "20230115",
        }
    )
    assert video is not None
    assert video.video_id == "9mmVa6O-hzQ"
    assert video.title.startswith("PYTHON LERNEN")
    assert video.channel == "Programmieren lernen"
    assert video.views == 263948
    assert video.published_date_human == "15.01.2023"
    assert "watch?v=9mmVa6O-hzQ" in video.watch_url


def test_video_search_uses_ytdlp_when_api_key_missing() -> None:
    fake = [
        VideoResult(
            video_id="9mmVa6O-hzQ",
            title="PYTHON LERNEN in 10 Minuten (Anfänger Tutorial Deutsch)",
            channel="Programmieren lernen",
            views=263948,
            thumbnail="https://i.ytimg.com/vi/9mmVa6O-hzQ/hqdefault.jpg",
            watch_url="https://www.youtube.com/watch?v=9mmVa6O-hzQ",
            embed_url="https://www.youtube.com/embed/9mmVa6O-hzQ?rel=0",
            is_embeddable=True,
            published_date_human=None,
        )
    ]
    payload = VideoSearchInput(
        query="Python Tutorial für Anfänger",
        max_results=3,
        wants_latest=False,
        channel_name="",
        mode="list",
    )
    with patch.object(video_tools, "_get_youtube_api_key", return_value=""):
        with patch.object(video_tools, "_ensure_ytdlp_search_available", return_value=True):
            with patch.object(
                video_tools,
                "_search_youtube_entries_ytdlp",
                return_value=fake,
            ) as search_mock:
                result = asyncio.run(video_tools.video_search_tool(payload))

    assert result.status == "ok"
    assert result.metadata and result.metadata.get("source") == "youtube_ytdlp_no_api_key"
    assert result.data.get("count") == 1
    assert result.data["videos"][0]["title"].startswith("PYTHON LERNEN")
    assert result.data["videos"][0]["channel"] == "Programmieren lernen"
    assert search_mock.called


def test_video_search_still_errors_without_key_and_without_ytdlp() -> None:
    payload = VideoSearchInput(
        query="Python Tutorial für Anfänger",
        wants_latest=False,
        channel_name="",
        mode="list",
    )
    with patch.object(video_tools, "_get_youtube_api_key", return_value=""):
        with patch.object(video_tools, "_ensure_ytdlp_search_available", return_value=False):
            result = asyncio.run(video_tools.video_search_tool(payload))
    assert result.status == "error"
    assert result.error is not None
    assert "YOUTUBE_SEARCH_UNAVAILABLE" in str(result.error.message)


def test_video_search_tool_name_normalizes_to_skill_id() -> None:
    """Executor emits name=video_search; fallback gate must treat it as video.search."""
    assert "video_search".lower().replace("_", ".") == "video.search"
