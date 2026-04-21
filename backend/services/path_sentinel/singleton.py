"""Path Sentinel Singleton - shared state across decorator, API routes, and tool executor.

This module provides a process-wide singleton sentinel so that:
- ConsentChallenges created in the decorator can be resolved by the consent API route.
- EphemeralGrants granted by the user persist between tool calls within the session.
- The real application database is used for PersistentGrants (not in-memory).

IMPORTANT: The database import happens at module import time (not lazily inside
``get_sentinel``) because the sentinel is first created from a worker thread
(``asyncio.to_thread`` in the tool executor). Importing a new module from a
worker thread while the main thread holds ``importlib._ModuleLock`` produces a
hard deadlock - the classic CPython import-lock bug.
"""

import logging
import os
import threading
from typing import Optional

# Imported eagerly to pre-load the module lock on the main thread at startup.
from backend.data.database import SessionLocal

from .sentinel import PathSentinel
from .stores import ConsentChallengeStore, EphemeralGrantStore
from .utils import SystemPathBlocklist

logger = logging.getLogger("janus_backend")

# Process-wide singletons - created once, shared across all threads/requests.
_lock = threading.Lock()
_sentinel: Optional[PathSentinel] = None
_challenge_store: Optional[ConsentChallengeStore] = None
_ephemeral_store: Optional[EphemeralGrantStore] = None


def get_secret_key() -> str:
    """Return the consent-token secret key (env-override possible)."""
    return os.getenv(
        "JANUS_CONSENT_SECRET_KEY",
        "default-secret-key-change-in-production",
    )


def get_challenge_store() -> ConsentChallengeStore:
    """Return the process-wide ConsentChallengeStore singleton."""
    global _challenge_store
    if _challenge_store is None:
        with _lock:
            if _challenge_store is None:
                _challenge_store = ConsentChallengeStore()
    return _challenge_store


def get_ephemeral_store() -> EphemeralGrantStore:
    """Return the process-wide EphemeralGrantStore singleton."""
    global _ephemeral_store
    if _ephemeral_store is None:
        with _lock:
            if _ephemeral_store is None:
                _ephemeral_store = EphemeralGrantStore()
    return _ephemeral_store


def get_sentinel() -> PathSentinel:
    """Return the process-wide PathSentinel singleton, wired to the real app DB."""
    global _sentinel
    if _sentinel is None:
        with _lock:
            if _sentinel is None:
                blocklist = SystemPathBlocklist()
                ephemeral = get_ephemeral_store()
                _sentinel = PathSentinel(
                    blocklist=blocklist,
                    ephemeral_store=ephemeral,
                    db_session_factory=SessionLocal,
                )
                logger.info("[PATH-SENTINEL] Singleton initialized with real app DB.")
    return _sentinel


# ---------------------------------------------------------------------------
# Eagerly initialize all singletons on the main thread at module-import time.
# This guarantees the first tool call, which runs via ``asyncio.to_thread``
# in a worker thread, does NOT have to create any Python objects that might
# trigger lazy imports or acquire the importlib lock.
# ---------------------------------------------------------------------------
get_challenge_store()
get_ephemeral_store()
get_sentinel()
