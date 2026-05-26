"""
Base Adapter Interface for RAG V2 Format Routing
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("janus_backend")


@dataclass
class RawChunk:
    """
    A raw text chunk extracted from a document, before embedding.

    Fields:
        text:       The chunk text content.
        start_line: 1-based start line in the source file (if applicable).
        end_line:   1-based end line in the source file (if applicable).
        metadata:   Extra metadata (e.g. language, section headers).
    """
    text: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAdapter(ABC):
    """
    Abstract base class for all RAG V2 format adapters.

    Responsibilities:
    - Check if a file path matches the adapter's supported formats.
    - Parse the file into RawChunk objects.
    - Provide a fast SHA-256 hash of file content for incremental indexing.
    """

    @classmethod
    @abstractmethod
    def supports(cls, path: Path) -> bool:
        """Return True if this adapter can handle the given file path."""
        ...

    @abstractmethod
    def parse(self, path: Path) -> List[RawChunk]:
        """
        Parse the file at `path` into a list of RawChunk objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed.
        """
        ...

    @classmethod
    def compute_sha256(cls, path: Path) -> str:
        """
        Compute SHA-256 hash of file content with streaming (memory-safe for large files).

        Returns:
            Hex digest of the file's SHA-256 hash.
        """
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    @classmethod
    def get_file_stats(cls, path: Path) -> tuple:
        """
        Return (mtime, size_bytes) for the file.

        Used by the incremental indexer as a fast pre-filter before SHA-256.
        """
        stat = path.stat()
        return stat.st_mtime, stat.st_size

    @classmethod
    def read_text_safe(cls, path: Path, encoding: str = "utf-8") -> str:
        """
        Read file as text with encoding fallback.

        Tries the specified encoding first, then latin-1 as fallback.
        """
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {path}, falling back to latin-1")
            return path.read_text(encoding="latin-1")
