"""
RAG V2 Retrieval Logger

JSON-Line logger for retrieval operations with rotation.
Logs queries, router decisions, latency breakdown, and top results for forensics.

Format: One JSON object per line (NDJSON).
Rotation: 10MB per file, 5 backups.
"""

import json
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

# Log file location
LOG_DIR = Path(get_app_data_dir()) / "logs"
LOG_FILE = LOG_DIR / "rag_retrieval.log"

# Rotation settings
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


class RetrievalLogger:
    """
    JSON-Line logger for retrieval operations.

    Usage:
        retrieval_logger = RetrievalLogger()
        retrieval_logger.log_query(
            query="test query",
            router_decision=decision,
            latency_breakdown={"vector": 50, "keyword": 10, "rrf": 5},
            top_result={"chunk_id": "1", "source_path": "/test/file.py"},
        )
    """

    _instance = None
    _handler = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._handler is not None:
            return  # Already initialized

        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        self._handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )

        # Create logger
        self._logger = logging.getLogger("rag_retrieval")
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(self._handler)

        # Prevent propagation to root logger (avoid duplicate logs)
        self._logger.propagate = False

        logger.info(f"[RetrievalLogger] Initialized: {LOG_FILE} (10MB, 5 backups)")

    def log_query(
        self,
        query: str,
        router_decision: Optional[Dict[str, Any]],
        latency_breakdown: Optional[Dict[str, float]],
        top_result: Optional[Dict[str, Any]],
        num_results: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """
        Log a retrieval query as a JSON line.

        Args:
            query: The search query string.
            router_decision: Router decision dict (mode, weights, etc.).
            latency_breakdown: Latency per component (ms).
            top_result: The top-1 result dict (chunk_id, source_path, etc.).
            num_results: Total number of results returned.
            error: Error message if query failed.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "query": query[:500],  # Truncate very long queries
            "router_decision": router_decision,
            "latency_breakdown": latency_breakdown,
            "top_result": top_result,
            "num_results": num_results,
            "error": error,
        }

        # Write as JSON line
        json_line = json.dumps(log_entry, ensure_ascii=False)
        self._logger.info(json_line)

    def log_ingestion_skip(
        self,
        file_path: str,
        reason: str,
    ) -> None:
        """
        Log a file skip during ingestion.

        Args:
            file_path: The file path being skipped.
            reason: Reason for skipping (e.g., "Denied extension: .env").
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "ingestion_skip",
            "file_path": file_path,
            "reason": reason,
        }

        json_line = json.dumps(log_entry, ensure_ascii=False)
        self._logger.info(json_line)

    def log_ingestion_success(
        self,
        file_path: str,
        num_chunks: int,
        collection: str,
    ) -> None:
        """
        Log a successful ingestion.

        Args:
            file_path: The file path ingested.
            num_chunks: Number of chunks created.
            collection: Target collection name.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "ingestion_success",
            "file_path": file_path,
            "num_chunks": num_chunks,
            "collection": collection,
        }

        json_line = json.dumps(log_entry, ensure_ascii=False)
        self._logger.info(json_line)


def get_retrieval_logger() -> RetrievalLogger:
    """Get the singleton retrieval logger."""
    return RetrievalLogger()
