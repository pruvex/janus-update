"""Transcript Service for Video Understanding (Task VID-UNDERSTAND-001 WO-2).

Provides transcript retrieval with fallback chain (YouTube Captions API → yt-dlp → unavailable),
chunking for LLM processing, and Memory V2 integration for summary storage.
"""

import asyncio
import logging
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("janus_backend")

# turbo: Check yt-dlp availability
try:
    subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    _YT_DLP_AVAILABLE = True
except (FileNotFoundError, subprocess.CalledProcessError):
    _YT_DLP_AVAILABLE = False
    logger.warning("TRANSCRIPT-SERVICE: yt-dlp not available - fallback disabled")

# tiktoken for token counting (optional)
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    logger.warning("TRANSCRIPT-SERVICE: tiktoken not available - using char-based chunking")

# Memory V2 Bridge
try:
    from backend.services.memory import save_memory_snippet
    from backend.data.schemas import MemoryCategory
    _MEMORY_V2_AVAILABLE = True
except ImportError:
    _MEMORY_V2_AVAILABLE = False
    logger.warning("TRANSCRIPT-SERVICE: Memory V2 not available - summary storage disabled")

# YouTube Transcript API
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _YOUTUBE_TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    _YOUTUBE_TRANSCRIPT_API_AVAILABLE = False
    logger.warning("TRANSCRIPT-SERVICE: youtube-transcript-api not available - primary method disabled")

# faster-whisper for local STT
try:
    from faster_whisper import WhisperModel
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False
    logger.warning("TRANSCRIPT-SERVICE: faster-whisper not available - STT fallback disabled")


# ═══════════════════════════════════════════════════════════════════════════════
# CACHE (Pattern from video_tools.py)
# ═══════════════════════════════════════════════════════════════════════════════

_TRANSCRIPT_CACHE_TTL_SECONDS = 24 * 3600  # 24h
_TRANSCRIPT_CACHE_LOCK = threading.Lock()
_TRANSCRIPT_CACHE: Dict[str, Dict[str, Any]] = {}


def _transcript_cache_key(video_id: str) -> str:
    return f"transcript:{video_id}"


def _get_cached_transcript(video_id: str) -> Optional[Dict[str, Any]]:
    now = time.time()
    with _TRANSCRIPT_CACHE_LOCK:
        entry = _TRANSCRIPT_CACHE.get(_transcript_cache_key(video_id))
        if not entry:
            return None
        if float(entry.get("expires_at", 0.0)) <= now:
            _TRANSCRIPT_CACHE.pop(_transcript_cache_key(video_id), None)
            return None
        return entry


def _store_cached_transcript(video_id: str, data: Dict[str, Any]) -> None:
    expires_at = time.time() + _TRANSCRIPT_CACHE_TTL_SECONDS
    with _TRANSCRIPT_CACHE_LOCK:
        _TRANSCRIPT_CACHE[_transcript_cache_key(video_id)] = {
            "expires_at": expires_at,
            **data,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TranscriptResult:
    """Result of transcript retrieval with source tracking."""
    text: str
    source: str  # 'youtube_captions' | 'yt_dlp' | 'whisper_stt' | 'unavailable'
    language: str
    chunks: List[str]
    video_title: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSCRIPT SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TranscriptService:
    """Service for retrieving and processing video transcripts."""

    def __init__(self) -> None:
        self.cache_ttl = _TRANSCRIPT_CACHE_TTL_SECONDS

    async def get_transcript(self, video_id: str, languages: List[str] = None) -> TranscriptResult:
        """Retrieve transcript with fallback chain.

        Priority:
        1. YouTube Captions API (youtube-transcript-api)
        2. yt-dlp subtitle extraction
        3. yt-dlp audio download + faster-whisper STT (local fallback)
        4. Return unavailable (graceful degradation)

        Args:
            video_id: 11-character YouTube video ID
            languages: List of language codes to try (default: ['de', 'en'])

        Returns:
            TranscriptResult with text, source, language, chunks
        """
        # Set default languages if not provided
        if languages is None:
            languages = ['de', 'en']

        logger.info("💎 TRANSCRIPT: Attempting to fetch subtitles for languages: %s", languages)

        # Check cache
        cached = _get_cached_transcript(video_id)
        if cached:
            logger.info("💎 TRANSCRIPT: cache hit for video_id=%s", video_id)
            return TranscriptResult(
                text=cached["text"],
                source=cached["source"],
                language=cached["language"],
                chunks=cached["chunks"],
                video_title=cached.get("video_title", ""),
            )

        # Phase 1: YouTube Captions API
        if _YOUTUBE_TRANSCRIPT_API_AVAILABLE:
            try:
                result = await asyncio.to_thread(self._fetch_youtube_captions, video_id, languages)
                if result.text:
                    _store_cached_transcript(video_id, {
                        "text": result.text,
                        "source": result.source,
                        "language": result.language,
                        "chunks": result.chunks,
                        "video_title": result.video_title,
                    })
                    logger.info(
                        "💎 TRANSCRIPT: source=%s lang=%s chunks=%d video_id=%s",
                        result.source, result.language, len(result.chunks), video_id
                    )
                    return result
            except Exception as exc:
                logger.debug("YouTube Captions API failed: %s", exc)

        # Phase 2: yt-dlp subtitle extraction
        if _YT_DLP_AVAILABLE:
            try:
                result = await asyncio.to_thread(self._fetch_yt_dlp_subtitles, video_id, languages)
                if result.text:
                    _store_cached_transcript(video_id, {
                        "text": result.text,
                        "source": result.source,
                        "language": result.language,
                        "chunks": result.chunks,
                        "video_title": result.video_title,
                    })
                    logger.info(
                        "💎 TRANSCRIPT: source=%s lang=%s chunks=%d video_id=%s",
                        result.source, result.language, len(result.chunks), video_id
                    )
                    return result
            except Exception as exc:
                logger.debug("yt-dlp subtitle extraction failed: %s", exc)

        # Phase 3: yt-dlp audio download + faster-whisper STT
        if _YT_DLP_AVAILABLE and _WHISPER_AVAILABLE:
            try:
                result = await asyncio.to_thread(self._fetch_whisper_stt, video_id, languages)
                if result.text:
                    _store_cached_transcript(video_id, {
                        "text": result.text,
                        "source": result.source,
                        "language": result.language,
                        "chunks": result.chunks,
                        "video_title": result.video_title,
                    })
                    logger.info(
                        "💎 TRANSCRIPT: source=%s lang=%s chunks=%d video_id=%s",
                        result.source, result.language, len(result.chunks), video_id
                    )
                    return result
            except Exception as exc:
                logger.debug("Whisper STT fallback failed: %s", exc)

        # Phase 4: Unavailable (graceful degradation)
        logger.warning("💎 TRANSCRIPT: unavailable for video_id=%s", video_id)
        result = TranscriptResult(
            text="",
            source="unavailable",
            language="",
            chunks=[],
            video_title="",
        )
        _store_cached_transcript(video_id, {
            "text": result.text,
            "source": result.source,
            "language": result.language,
            "chunks": result.chunks,
            "video_title": result.video_title,
        })
        return result

    def _fetch_youtube_captions(self, video_id: str, languages: List[str] = None) -> TranscriptResult:
        """Fetch transcript using YouTube Transcript API."""
        if languages is None:
            languages = ["de", "en"]
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except Exception:
            # Fallback: any available language
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as exc:
                logger.debug("YouTube Transcript API failed completely: %s", exc)
                raise

        # Extract text
        text = " ".join([item["text"] for item in transcript_list])
        language = self._detect_language(text)

        # Chunk
        chunks = self._chunk_transcript(text)

        return TranscriptResult(
            text=text,
            source="youtube_captions",
            language=language,
            chunks=chunks,
        )

    def _fetch_yt_dlp_subtitles(self, video_id: str, languages: List[str] = None) -> TranscriptResult:
        """Fetch transcript using yt-dlp subtitle extraction."""
        if languages is None:
            languages = ["de", "en"]
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Use yt-dlp to write auto-generated subtitles
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-auto-sub",
                "--sub-lang", ",".join(languages),
                "--skip-download",
                "--sub-format", "vtt",
                "-o", "%(id)s.%(ext)s",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            # Check for HTTP 429 rate limit
            stderr = result.stderr or ""
            if "429" in stderr or "Too Many Requests" in stderr:
                logger.info("💎 Rate-Limit detected, skipping to Whisper STT fallback")
                raise RuntimeError("Rate limit exceeded")
            raise RuntimeError(f"yt-dlp failed: {result.stderr}")

        # Parse VTT file (simplified - in production would use proper VTT parser)
        # For now, return empty to trigger graceful degradation
        # TODO: Implement proper VTT parsing
        logger.warning("yt-dlp VTT parsing not yet implemented - returning unavailable")
        raise RuntimeError("VTT parsing not implemented")

    def _fetch_whisper_stt(self, video_id: str, languages: List[str] = None) -> TranscriptResult:
        """Fetch transcript using yt-dlp audio download + faster-whisper STT.

        Phase 2: Download audio only (.m4a/.mp3) to temp directory
        Phase 3: Run faster-whisper on downloaded audio
        Cleanup: Delete temporary audio file
        """
        if languages is None:
            languages = ["de", "en"]
        # Use first language for Whisper hint (prefer German if available)
        whisper_language = languages[0] if languages else "de"
        url = f"https://www.youtube.com/watch?v={video_id}"
        temp_dir = os.path.join(os.getcwd(), "workspace", "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        audio_file = os.path.join(temp_dir, f"{video_id}.m4a")

        try:
            # Phase 2: Download audio using yt-dlp
            logger.info("💎 TRANSCRIPT: Phase 2 - downloading audio for video_id=%s", video_id)
            result = subprocess.run(
                [
                    "yt-dlp",
                    "-f", "bestaudio[ext=m4a]/bestaudio/best",
                    "--extract-audio",
                    "--audio-format", "m4a",
                    "--audio-quality", "0",  # best quality
                    "-o", audio_file,
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"yt-dlp audio download failed: {result.stderr}")

            if not os.path.exists(audio_file):
                raise RuntimeError(f"Audio file not created: {audio_file}")

            logger.info("💎 TRANSCRIPT: Phase 2 - audio downloaded to %s", audio_file)

            # Phase 3: Run faster-whisper
            logger.info("💎 TRANSCRIPT: Phase 3 - running Whisper STT with language=%s", whisper_language)
            import time
            start_time = time.time()
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_file, language=whisper_language, beam_size=5)
            duration = time.time() - start_time

            # Build transcript from segments
            transcript_text = " ".join([segment.text for segment in segments])
            language = info.language if info.language else "de"

            # Chunk the transcript
            chunks = self._chunk_transcript(transcript_text)

            logger.info(
                "💎 TRANSCRIPT: Phase 3 - Whisper STT complete: lang=%s chunks=%d duration=%.2fs",
                language, len(chunks), duration
            )

            return TranscriptResult(
                text=transcript_text,
                source="whisper_stt",
                language=language,
                chunks=chunks,
            )

        except Exception as exc:
            logger.error("💎 TRANSCRIPT: Whisper STT failed: %s", exc)
            raise
        finally:
            # Cleanup: Delete temporary audio file
            if os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                    logger.info("💎 TRANSCRIPT: cleaned up temporary audio file: %s", audio_file)
                except Exception as exc:
                    logger.warning("💎 TRANSCRIPT: failed to cleanup audio file: %s", exc)

    def _chunk_transcript(self, text: str, max_tokens: int = 3000) -> List[str]:
        """Split transcript into chunks respecting sentence boundaries.

        Args:
            text: Full transcript text
            max_tokens: Maximum tokens per chunk (default 3000)

        Returns:
            List of text chunks
        """
        if not text:
            return []

        if _TIKTOKEN_AVAILABLE:
            return self._chunk_with_tiktoken(text, max_tokens)
        else:
            return self._chunk_by_characters(text, max_tokens * 4)  # ~4 chars per token

    def _chunk_with_tiktoken(self, text: str, max_tokens: int) -> List[str]:
        """Chunk using tiktoken for accurate token counting."""
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")

        chunks = []
        current_chunk = ""
        current_tokens = 0

        # Split by sentence boundaries
        sentences = re.split(r'([.!?]+)\s+', text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            sentence_tokens = len(encoding.encode(sentence))

            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                current_chunk += sentence
                current_tokens += sentence_tokens

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _chunk_by_characters(self, text: str, max_chars: int) -> List[str]:
        """Fallback: chunk by characters with sentence boundary awareness."""
        chunks = []
        current_chunk = ""

        sentences = re.split(r'([.!?]+)\s+', text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            if len(current_chunk) + len(sentence) > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common words."""
        if not text:
            return ""

        text_lower = text.lower()
        
        # German markers
        de_markers = ["und", "der", "die", "das", "ist", "sind", "haben", "werden", "mit", "für"]
        de_count = sum(1 for marker in de_markers if marker in text_lower)
        
        # English markers
        en_markers = ["the", "and", "is", "are", "have", "will", "with", "for", "of"]
        en_count = sum(1 for marker in en_markers if marker in text_lower)

        if de_count > en_count:
            return "de"
        elif en_count > de_count:
            return "en"
        else:
            return "unknown"

    def store_summary_in_memory(
        self,
        video_id: str,
        title: str,
        summary: str,
        chat_id: Optional[int] = None,
    ) -> bool:
        """Store video summary in Memory V2.

        Args:
            video_id: YouTube video ID
            title: Video title
            summary: Generated summary text
            chat_id: Optional chat ID for context

        Returns:
            True if successful, False otherwise
        """
        db = None  # Initialize db to None at the beginning

        if not _MEMORY_V2_AVAILABLE:
            logger.warning("TRANSCRIPT-SERVICE: Memory V2 not available - cannot store summary")
            return False

        # Create DB session if not provided
        should_close_db = False
        if db is None:
            from backend.data.database import SessionLocal
            db = SessionLocal()
            should_close_db = True

        try:
            # Build snippet
            snippet_text = f"Video: {title} (ID: {video_id})\n{summary}"

            # Store with core_priority=0.7, category="General Fact"
            save_memory_snippet(
                db=db,
                chat_id=chat_id,
                snippet_text=snippet_text,
                category="General Fact",
                source_type="video",
                source_metadata={"video_id": video_id, "title": title, "source_skill": "video.understand"},
                core_priority=0.7,
                is_core=False,
            )

            logger.info(
                "💎 TRANSCRIPT: stored summary in memory for video_id=%s title=%s",
                video_id, title
            )
            return True
        except Exception as exc:
            logger.error("TRANSCRIPT-SERVICE: failed to store summary: %s", exc, exc_info=True)
            return False
        finally:
            if db:
                db.close()


# Singleton instance
transcript_service = TranscriptService()
