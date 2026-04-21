"""Path Sentinel core decision engine."""

from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session
from time import time

from .utils import SystemPathBlocklist, PathNormalizer
from .stores import EphemeralGrantStore, PersistentGrantStore
from .models import PathOp, GrantScope, GrantRecord
from .auth import SignedConsentToken


class SentinelDecision(str, Enum):
    """Sentinel access control decision."""

    ALLOW = "allow"
    DENY_REQUIRES_CONSENT = "deny_requires_consent"
    DENY_SYSTEM_PROTECTED = "deny_system_protected"


class PathSentinel:
    """Core path access control sentinel."""

    def __init__(
        self,
        blocklist: SystemPathBlocklist,
        ephemeral_store: EphemeralGrantStore,
        db_session_factory,
    ):
        """Initialize the sentinel.

        Args:
            blocklist: SystemPathBlocklist instance
            ephemeral_store: EphemeralGrantStore instance
            db_session_factory: Callable that returns a SQLAlchemy Session
        """
        self.blocklist = blocklist
        self.ephemeral_store = ephemeral_store
        self.db_session_factory = db_session_factory

    def check(
        self,
        path: str,
        op: str,
        session_id: str,
        user_id: str,
        db: Optional[Session] = None,
    ) -> SentinelDecision:
        """
        Check if path access is allowed.

        Decision flow:
        1. Check blocklist -> DENY_SYSTEM_PROTECTED
        2. Check persistent store -> ALLOW
        3. Check ephemeral store -> ALLOW
        4. Otherwise -> DENY_REQUIRES_CONSENT

        Args:
            path: File path to check
            op: Operation type (read/write/delete)
            session_id: User session identifier
            user_id: User identifier
            db: Optional database session (if not provided, uses factory)

        Returns:
            SentinelDecision
        """
        # 1. Check blocklist
        if self.blocklist.is_blocked(path):
            return SentinelDecision.DENY_SYSTEM_PROTECTED

        # 2. Check persistent store
        if db is None:
            db = self.db_session_factory()
        persistent_store = PersistentGrantStore(db)
        if persistent_store.check_grant(user_id, path, op):
            return SentinelDecision.ALLOW

        # 3. Check ephemeral store (with prefix matching)
        normalized_path = PathNormalizer.normalize(path)
        # Get all grants for this user and operation
        all_grants = self.ephemeral_store._store
        for (uid, stored_path, stored_op), grant in all_grants.items():
            if uid == user_id and stored_op == op:
                # Check prefix match
                if PathNormalizer.is_subpath(stored_path, normalized_path):
                    return SentinelDecision.ALLOW

        # 4. No grant found
        return SentinelDecision.DENY_REQUIRES_CONSENT

    def grant(
        self,
        path: str,
        op: str,
        scope: str,
        session_id: str,
        user_id: str,
        consent_token: str,
        secret_key: str,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Grant path access after consent verification.

        Verifies the consent token and creates the appropriate grant:
        - ALWAYS: Persistent grant in database
        - SESSION/ONCE: Ephemeral grant in memory

        Args:
            path: File path to grant access to
            op: Operation type (read/write/delete)
            scope: Grant scope (once/session/always)
            session_id: User session identifier
            user_id: User identifier
            consent_token: Signed consent token
            secret_key: Secret key for token verification
            db: Optional database session (if not provided, uses factory)

        Returns:
            True if grant was created successfully, False otherwise
        """
        # Verify token
        token_auth = SignedConsentToken(secret_key)
        payload = token_auth.verify_token(consent_token)
        if payload is None:
            return False

        # Validate token matches request
        if payload.get("path") != path or payload.get("op") != op or payload.get("scope") != scope:
            return False

        # Create grant based on scope
        if scope == GrantScope.ALWAYS.value:
            # Persistent grant
            if db is None:
                db = self.db_session_factory()
            persistent_store = PersistentGrantStore(db)
            persistent_store.add_grant(user_id, path, op)
        else:
            # Ephemeral grant (SESSION or ONCE)
            grant_scope = GrantScope.SESSION if scope == GrantScope.SESSION.value else GrantScope.ONCE
            grant_op = PathOp.READ if op == "read" else (PathOp.WRITE if op == "write" else PathOp.DELETE)

            # Normalize path before storing
            normalized_path = PathNormalizer.normalize(path)

            record = GrantRecord(
                path=normalized_path,
                op=grant_op,
                scope=grant_scope,
                granted_at=time(),
                expires_at=None,
                consent_challenge_id=payload.get("challenge_id", ""),
                user_id=user_id,
            )
            self.ephemeral_store.add_grant(record)

        return True
