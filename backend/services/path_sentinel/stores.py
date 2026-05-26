"""Path Sentinel in-memory stores for challenges and grants."""

import threading
import time
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from .models import GrantRecord
from .utils import PathNormalizer


class ConsentChallengeStore:
    """RAM-based store for consent challenges with TTL."""

    TTL_SECONDS = 120

    def __init__(self):
        """Initialize the challenge store."""
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def create_challenge(self, session_id: str, path: str, op: str) -> str:
        """
        Create a new consent challenge.

        Args:
            session_id: User session identifier
            path: File path requesting access
            op: Operation type (read/write/delete)

        Returns:
            Unique challenge ID (UUID4)
        """
        challenge_id = str(uuid.uuid4())
        challenge_data = {
            "session_id": session_id,
            "path": path,
            "op": op,
            "created_at": time.time(),
        }

        with self._lock:
            self._store[challenge_id] = challenge_data

        return challenge_id

    def get_and_validate(self, challenge_id: str, session_id: str) -> Optional[dict]:
        """
        Retrieve and validate a challenge.

        Args:
            challenge_id: Challenge identifier
            session_id: User session identifier to validate ownership

        Returns:
            Challenge data dict if valid and not expired, None otherwise
        """
        with self._lock:
            challenge_data = self._store.get(challenge_id)
            if challenge_data is None:
                return None

            # Check TTL
            age = time.time() - challenge_data["created_at"]
            if age > self.TTL_SECONDS:
                # Expired, remove it
                del self._store[challenge_id]
                return None

            # Validate session ownership
            if challenge_data["session_id"] != session_id:
                return None

            return challenge_data

    def cleanup_expired(self) -> int:
        """
        Clean up expired challenges (utility method).

        Returns:
            Number of challenges removed
        """
        current_time = time.time()
        removed = 0

        with self._lock:
            expired_ids = [
                cid
                for cid, data in self._store.items()
                if current_time - data["created_at"] > self.TTL_SECONDS
            ]
            for cid in expired_ids:
                del self._store[cid]
                removed += 1

        return removed


class EphemeralGrantStore:
    """Thread-safe in-memory store for ephemeral grants."""

    def __init__(self):
        """Initialize the grant store."""
        self._store: dict[tuple[str, str, str], GrantRecord] = {}
        self._lock = threading.Lock()

    def add_grant(self, record: GrantRecord) -> None:
        """
        Add a grant record to the store.

        Args:
            record: GrantRecord to store
        """
        # Normalize path before storing
        normalized_path = PathNormalizer.normalize(record.path)
        key = (record.user_id, normalized_path, record.op.value)
        with self._lock:
            self._store[key] = record

    def get_grant(
        self, session_id: str, path: str, op: str
    ) -> Optional[GrantRecord]:
        """
        Retrieve a grant record.

        Args:
            session_id: User session identifier
            path: File path
            op: Operation type

        Returns:
            GrantRecord if found, None otherwise
        """
        normalized_path = PathNormalizer.normalize(path)
        key = (session_id, normalized_path, op)
        with self._lock:
            return self._store.get(key)

    def consume_once_grant(self, record: GrantRecord) -> bool:
        """
        Consume an ONCE grant (mark as consumed and remove from store).

        Args:
            record: GrantRecord to consume

        Returns:
            True if successfully consumed, False otherwise
        """
        if record.scope.value != "once":
            return False

        normalized_path = PathNormalizer.normalize(record.path)
        key = (record.user_id, normalized_path, record.op.value)

        with self._lock:
            stored = self._store.get(key)
            if stored is None:
                return False

            # Check if already consumed
            if stored.consumed:
                return False

            # Check if it's the same grant (by challenge_id)
            if stored.consent_challenge_id != record.consent_challenge_id:
                return False

            # Remove from store (ONCE grants are single-use)
            del self._store[key]
            return True

    def remove_grant(self, session_id: str, path: str, op: str) -> bool:
        """
        Remove a grant from the store.

        Args:
            session_id: User session identifier
            path: File path
            op: Operation type

        Returns:
            True if grant was removed, False if not found
        """
        normalized_path = PathNormalizer.normalize(path)
        key = (session_id, normalized_path, op)
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear_session(self, session_id: str) -> int:
        """
        Clear all grants for a session.

        Args:
            session_id: User session identifier

        Returns:
            Number of grants removed
        """
        removed = 0
        with self._lock:
            keys_to_remove = [k for k in self._store.keys() if k[0] == session_id]
            for key in keys_to_remove:
                del self._store[key]
                removed += 1
        return removed


class PersistentGrantStore:
    """Persistent store for path permissions in database."""

    def __init__(self, db: Session):
        """Initialize with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def add_grant(self, user_id: str, path: str, op: str) -> None:
        """
        Add a persistent grant to the database.

        Args:
            user_id: User identifier
            path: Normalized file path
            op: Operation type (read/write/delete)
        """
        from backend.data.models import PathPermission

        # Normalize path before storing
        normalized_path = PathNormalizer.normalize(path)

        permission = PathPermission(
            user_id=user_id,
            path_raw=normalized_path,
            op=op,
        )
        self.db.add(permission)
        self.db.commit()

    def check_grant(self, user_id: str, requested_path: str, op: str) -> bool:
        """
        Check if user has a grant for the requested path and operation.

        Uses prefix matching: if user has grant for 'D:\\Geheim',
        they can access 'D:\\Geheim\\file.txt'.

        Args:
            user_id: User identifier
            requested_path: File path to check
            op: Operation type (read/write/delete)

        Returns:
            True if access is allowed, False otherwise
        """
        from backend.data.models import PathPermission

        # Normalize requested path
        normalized_requested = PathNormalizer.normalize(requested_path)

        # Query all permissions for user and operation
        permissions = (
            self.db.query(PathPermission)
            .filter(PathPermission.user_id == user_id)
            .filter(PathPermission.op == op)
            .all()
        )

        # Check if any permission matches (prefix semantics)
        for perm in permissions:
            if PathNormalizer.is_subpath(perm.path_raw, normalized_requested):
                return True

        return False

