"""
Markdown Adapter for RAG V2

Parses Markdown files into RawChunks based on heading boundaries.
Respects the document structure (headers as chunk boundaries) and
preserves metadata about headings for improved retrieval context.
"""

import logging
import re
from pathlib import Path
from typing import List

from .base import BaseAdapter, RawChunk

logger = logging.getLogger("janus_backend")

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class MarkdownAdapter(BaseAdapter):
    """
    Adapter for Markdown files.

    Splits on heading boundaries to preserve document structure.
    Each chunk includes its parent heading chain for context.
    """

    @classmethod
    def supports(cls, path: Path) -> bool:
        return path.suffix.lower() in {".md", ".markdown", ".mdown", ".mkd"}

    def parse(self, path: Path) -> List[RawChunk]:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        text = self.read_text_safe(path)
        lines = text.splitlines(keepends=False)

        chunks: List[RawChunk] = []
        current_lines: List[str] = []
        current_start = 1
        heading_stack: List[tuple] = []  # (level, title)

        def flush_chunk(end_line: int) -> None:
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if chunk_text:
                    # Build heading breadcrumb
                    headings = [h[1] for h in heading_stack]
                    chunks.append(
                        RawChunk(
                            text=chunk_text,
                            start_line=current_start,
                            end_line=end_line,
                            metadata={
                                "source_path": str(path),
                                "format": "markdown",
                                "headings": headings,
                                "heading_stack": [h[1] for h in heading_stack],
                            },
                        )
                    )
                current_lines.clear()

        for i, line in enumerate(lines, start=1):
            match = HEADING_RE.match(line)
            if match:
                # Heading boundary - flush current chunk
                flush_chunk(i - 1)
                current_start = i
                level = len(match.group(1))
                title = match.group(2).strip()
                # Pop headings with level >= current
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, title))
            else:
                current_lines.append(line)

        # Flush final chunk
        flush_chunk(len(lines))

        logger.info(f"MarkdownAdapter parsed {path}: {len(chunks)} chunks")
        return chunks

