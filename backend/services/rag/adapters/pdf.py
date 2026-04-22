"""
PDF Adapter for RAG V2

Parses PDF files into RawChunks using PyMuPDF (fitz).
Extracts text page-by-page and chunks it for embedding.
"""

import logging
from pathlib import Path
from typing import List

try:
    import fitz
except ImportError:
    fitz = None
    logging.warning("PyMuPDF (fitz) not installed. PDF adapter will not work.")

from .base import BaseAdapter, RawChunk

logger = logging.getLogger("janus_backend")

# Chunk size for PDF text (characters)
PDF_CHUNK_SIZE = 1000
PDF_CHUNK_OVERLAP = 200


class PdfAdapter(BaseAdapter):
    """
    Adapter for PDF files.

    Extracts text page-by-page using PyMuPDF (fitz).
    Chunks the text into manageable pieces for embedding.
    """

    @classmethod
    def supports(cls, path: Path) -> bool:
        if fitz is None:
            return False
        return path.suffix.lower() == ".pdf"

    def parse(self, path: Path) -> List[RawChunk]:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if fitz is None:
            raise RuntimeError("PyMuPDF (fitz) not installed")

        try:
            doc = fitz.open(path)
            chunks: List[RawChunk] = []
            page_number = 0

            for page in doc:
                page_number += 1
                # Extract text from page
                text = page.get_text()
                
                if not text.strip():
                    continue

                # Chunk the text
                page_chunks = self._chunk_text(text)
                
                for i, chunk_text in enumerate(page_chunks):
                    chunks.append(
                        RawChunk(
                            text=chunk_text,
                            start_line=None,  # PDFs don't have line numbers
                            end_line=None,
                            metadata={
                                "source_path": str(path),
                                "format": "pdf",
                                "page": page_number,
                                "chunk_index": i,
                            },
                        )
                    )

            doc.close()
            logger.info(f"PdfAdapter parsed {path}: {len(chunks)} chunks from {page_number} pages")
            return chunks

        except Exception as e:
            logger.error(f"Error parsing PDF {path}: {e}")
            raise

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of approximately PDF_CHUNK_SIZE characters
        with PDF_CHUNK_OVERLAP overlap between chunks.
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + PDF_CHUNK_SIZE
            chunk = text[start:end]
            
            # Try to break at a sentence boundary if possible
            if end < text_length:
                # Look for the last sentence terminator
                for i in range(min(100, len(chunk))):
                    if chunk[-i] in {'.', '!', '?', '\n'}:
                        chunk = chunk[:-i]
                        end = start + len(chunk)
                        break
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            # Move to next chunk with overlap
            start = end - PDF_CHUNK_OVERLAP
            if start < 0:
                start = 0

        return chunks
