"""Unit tests for Path Sentinel utilities."""

import os
import pytest

from backend.services.path_sentinel.utils import PathNormalizer, SystemPathBlocklist
from backend.services.path_sentinel.models import PathOp, GrantScope, GrantRecord


class TestPathNormalizer:
    """Test suite for PathNormalizer."""

    def test_normalize_absolute_path(self):
        """Test normalization of absolute paths."""
        path = "C:\\Users\\Test\\..\\Test\\File.txt"
        normalized = PathNormalizer.normalize(path)
        expected = os.path.normpath(os.path.abspath(path)).lower() if os.name == "nt" else os.path.normpath(os.path.abspath(path))
        assert normalized == expected

    def test_normalize_case_folding_windows(self):
        """Test case folding on Windows."""
        if os.name != "nt":
            pytest.skip("Case folding test only applicable on Windows")
        
        path1 = "C:\\Users\\Test\\File.txt"
        path2 = "c:\\users\\test\\file.txt"
        assert PathNormalizer.normalize(path1) == PathNormalizer.normalize(path2)

    def test_is_subpath_exact_match(self):
        """Test is_subpath with exact match."""
        parent = "D:\\Geheim"
        child = "D:\\Geheim"
        assert PathNormalizer.is_subpath(parent, child) is True

    def test_is_subpath_child_file(self):
        """Test is_subpath with child file."""
        parent = "D:\\Geheim"
        child = "D:\\Geheim\\file.txt"
        assert PathNormalizer.is_subpath(parent, child) is True

    def test_is_subpath_child_directory(self):
        """Test is_subpath with child directory."""
        parent = "D:\\Geheim"
        child = "D:\\Geheim\\subdir"
        assert PathNormalizer.is_subpath(parent, child) is True

    def test_is_subpath_no_match_different_prefix(self):
        """Test is_subpath with different prefix (Geheim vs GeheimKram)."""
        parent = "D:\\Geheim"
        child = "D:\\GeheimKram\\file.txt"
        assert PathNormalizer.is_subpath(parent, child) is False

    def test_is_subpath_trailing_slash_parent(self):
        """Test is_subpath with trailing slash on parent."""
        parent = "D:\\Geheim\\"
        child = "D:\\Geheim\\file.txt"
        assert PathNormalizer.is_subpath(parent, child) is True

    def test_is_subpath_trailing_slash_child(self):
        """Test is_subpath with trailing slash on child."""
        parent = "D:\\Geheim"
        child = "D:\\Geheim\\subdir\\"
        assert PathNormalizer.is_subpath(parent, child) is True

    def test_is_subpath_path_traversal_attack(self):
        """Test is_subpath resists path traversal attacks."""
        parent = "D:\\Safe"
        child = "D:\\Safe\\..\\Unsafe\\file.txt"
        # Normalized child should not be considered subpath of Safe
        assert PathNormalizer.is_subpath(parent, child) is False

    def test_is_subpath_dots_normalization(self):
        """Test is_subpath with . and .. components."""
        parent = "D:\\Safe"
        child = "D:\\Safe\\.\\subdir\\..\\file.txt"
        assert PathNormalizer.is_subpath(parent, child) is True


class TestSystemPathBlocklist:
    """Test suite for SystemPathBlocklist."""

    def test_blocked_windows_directory(self):
        """Test blocking of Windows directory."""
        if os.name != "nt":
            pytest.skip("Windows path test only applicable on Windows")
        
        assert SystemPathBlocklist.is_blocked("C:\\Windows\\System32") is True

    def test_blocked_program_files(self):
        """Test blocking of Program Files."""
        if os.name != "nt":
            pytest.skip("Windows path test only applicable on Windows")
        
        assert SystemPathBlocklist.is_blocked("C:\\Program Files\\App") is True

    def test_blocked_git_directory(self):
        """Test blocking of .git directory."""
        assert SystemPathBlocklist.is_blocked(".git") is True
        assert SystemPathBlocklist.is_blocked(".git\\config") is True
        assert SystemPathBlocklist.is_blocked("subdir\\.git\\objects") is True

    def test_blocked_node_modules(self):
        """Test blocking of node_modules."""
        assert SystemPathBlocklist.is_blocked("node_modules") is True
        assert SystemPathBlocklist.is_blocked("frontend\\node_modules\\package") is True

    def test_blocked_python_cache(self):
        """Test blocking of Python cache directories."""
        assert SystemPathBlocklist.is_blocked("__pycache__") is True
        assert SystemPathBlocklist.is_blocked(".pytest_cache") is True
        assert SystemPathBlocklist.is_blocked(".ruff_cache") is True

    def test_blocked_venv_directories(self):
        """Test blocking of virtual environment directories."""
        assert SystemPathBlocklist.is_blocked(".venv") is True
        assert SystemPathBlocklist.is_blocked("venv") is True
        assert SystemPathBlocklist.is_blocked("env") is True

    def test_allowed_safe_path(self):
        """Test that safe paths are not blocked."""
        assert SystemPathBlocklist.is_blocked("C:\\Users\\Test\\Documents") is False
        assert SystemPathBlocklist.is_blocked("D:\\Projects\\MyProject") is False

    def test_blocked_case_insensitive_windows(self):
        """Test case-insensitive blocking on Windows."""
        if os.name != "nt":
            pytest.skip("Case-insensitive test only applicable on Windows")
        
        assert SystemPathBlocklist.is_blocked("C:\\WINDOWS\\SYSTEM32") is True
        assert SystemPathBlocklist.is_blocked("c:\\program files\\app") is True


class TestModels:
    """Test suite for Path Sentinel models."""

    def test_pathop_enum_values(self):
        """Test PathOp enum values."""
        assert PathOp.READ.value == "read"
        assert PathOp.WRITE.value == "write"
        assert PathOp.DELETE.value == "delete"

    def test_grantscope_enum_values(self):
        """Test GrantScope enum values."""
        assert GrantScope.ONCE.value == "once"
        assert GrantScope.SESSION.value == "session"
        assert GrantScope.ALWAYS.value == "always"

    def test_grantrecord_creation(self):
        """Test GrantRecord creation."""
        from time import time
        
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
        )
        
        assert record.path == "D:\\Test\\file.txt"
        assert record.op == PathOp.READ
        assert record.scope == GrantScope.ONCE
        assert record.consumed is False

    def test_grantrecord_immutable(self):
        """Test that GrantRecord is frozen/immutable."""
        from time import time
        
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            record.consumed = True


class TestSignedConsentToken:
    """Test suite for SignedConsentToken."""

    def test_create_and_verify_token_valid(self):
        """Test successful token creation and verification."""
        from backend.services.path_sentinel.auth import SignedConsentToken

        token_auth = SignedConsentToken(secret_key="test-secret-key")
        token = token_auth.create_token(
            challenge_id="challenge-123",
            path="D:\\Test\\file.txt",
            op="read",
            scope="once",
        )

        payload = token_auth.verify_token(token)
        assert payload is not None
        assert payload["challenge_id"] == "challenge-123"
        assert payload["path"] == "D:\\Test\\file.txt"
        assert payload["op"] == "read"
        assert payload["scope"] == "once"
        assert "iat" in payload

    def test_verify_token_wrong_secret(self):
        """Test token verification fails with wrong secret."""
        from backend.services.path_sentinel.auth import SignedConsentToken

        token_auth = SignedConsentToken(secret_key="test-secret-key")
        token = token_auth.create_token(
            challenge_id="challenge-123",
            path="D:\\Test\\file.txt",
            op="read",
            scope="once",
        )

        wrong_auth = SignedConsentToken(secret_key="wrong-secret-key")
        payload = wrong_auth.verify_token(token)
        assert payload is None

    def test_verify_token_manipulated_payload(self):
        """Test token verification fails with manipulated payload."""
        from backend.services.path_sentinel.auth import SignedConsentToken

        token_auth = SignedConsentToken(secret_key="test-secret-key")
        token = token_auth.create_token(
            challenge_id="challenge-123",
            path="D:\\Test\\file.txt",
            op="read",
            scope="once",
        )

        # Manipulate the token by changing a character
        manipulated_token = token[:-5] + "XXXXX"
        payload = token_auth.verify_token(manipulated_token)
        assert payload is None

    def test_verify_token_invalid_format(self):
        """Test token verification fails with invalid format."""
        from backend.services.path_sentinel.auth import SignedConsentToken

        token_auth = SignedConsentToken(secret_key="test-secret-key")
        assert token_auth.verify_token("invalid-token") is None
        assert token_auth.verify_token("only-one-part") is None
        assert token_auth.verify_token("") is None


class TestConsentChallengeStore:
    """Test suite for ConsentChallengeStore."""

    def test_create_and_retrieve_challenge(self):
        """Test successful challenge creation and retrieval."""
        from backend.services.path_sentinel.stores import ConsentChallengeStore

        store = ConsentChallengeStore()
        challenge_id = store.create_challenge(
            session_id="session-123",
            path="D:\\Test\\file.txt",
            op="read",
        )

        challenge_data = store.get_and_validate(challenge_id, "session-123")
        assert challenge_data is not None
        assert challenge_data["session_id"] == "session-123"
        assert challenge_data["path"] == "D:\\Test\\file.txt"
        assert challenge_data["op"] == "read"

    def test_retrieve_challenge_wrong_session(self):
        """Test challenge retrieval fails with wrong session ID."""
        from backend.services.path_sentinel.stores import ConsentChallengeStore

        store = ConsentChallengeStore()
        challenge_id = store.create_challenge(
            session_id="session-123",
            path="D:\\Test\\file.txt",
            op="read",
        )

        challenge_data = store.get_and_validate(challenge_id, "wrong-session")
        assert challenge_data is None

    def test_retrieve_challenge_nonexistent(self):
        """Test challenge retrieval fails for nonexistent challenge."""
        from backend.services.path_sentinel.stores import ConsentChallengeStore

        store = ConsentChallengeStore()
        challenge_data = store.get_and_validate("nonexistent-id", "session-123")
        assert challenge_data is None

    def test_challenge_ttl_expiration(self):
        """Test challenge expires after TTL."""
        from backend.services.path_sentinel.stores import ConsentChallengeStore
        import time

        store = ConsentChallengeStore()
        # Manually set a challenge with old timestamp
        store._store["old-challenge"] = {
            "session_id": "session-123",
            "path": "D:\\Test\\file.txt",
            "op": "read",
            "created_at": time.time() - 130,  # 130 seconds ago (past 120s TTL)
        }

        challenge_data = store.get_and_validate("old-challenge", "session-123")
        assert challenge_data is None
        assert "old-challenge" not in store._store

    def test_cleanup_expired_challenges(self):
        """Test cleanup of expired challenges."""
        from backend.services.path_sentinel.stores import ConsentChallengeStore
        import time

        store = ConsentChallengeStore()
        # Add expired challenge
        store._store["expired"] = {
            "session_id": "session-123",
            "path": "D:\\Test\\file.txt",
            "op": "read",
            "created_at": time.time() - 130,
        }
        # Add valid challenge
        store._store["valid"] = {
            "session_id": "session-123",
            "path": "D:\\Test\\file2.txt",
            "op": "write",
            "created_at": time.time() - 10,
        }

        removed = store.cleanup_expired()
        assert removed == 1
        assert "expired" not in store._store
        assert "valid" in store._store


class TestEphemeralGrantStore:
    """Test suite for EphemeralGrantStore."""

    def test_add_and_retrieve_grant(self):
        """Test successful grant addition and retrieval."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time

        store = EphemeralGrantStore()
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
        )

        store.add_grant(record)
        retrieved = store.get_grant("user-456", "D:\\Test\\file.txt", "read")
        assert retrieved is not None
        assert retrieved.path == "D:\\Test\\file.txt"
        assert retrieved.consent_challenge_id == "challenge-123"

    def test_retrieve_grant_nonexistent(self):
        """Test grant retrieval fails for nonexistent grant."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore

        store = EphemeralGrantStore()
        retrieved = store.get_grant("user-456", "D:\\Test\\file.txt", "read")
        assert retrieved is None

    def test_consume_once_grant_success(self):
        """Test successful consumption of ONCE grant."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time

        store = EphemeralGrantStore()
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
        )

        store.add_grant(record)
        result = store.consume_once_grant(record)
        assert result is True

        # Grant should be removed
        retrieved = store.get_grant("user-456", "D:\\Test\\file.txt", "read")
        assert retrieved is None

    def test_consume_once_grant_wrong_scope(self):
        """Test consume fails for non-ONCE grant."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time

        store = EphemeralGrantStore()
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.SESSION,  # Not ONCE
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
        )

        store.add_grant(record)
        result = store.consume_once_grant(record)
        assert result is False

    def test_consume_once_grant_already_consumed(self):
        """Test consume fails for already consumed grant."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time

        store = EphemeralGrantStore()
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
            consumed=True,  # Already consumed
        )

        store.add_grant(record)
        result = store.consume_once_grant(record)
        assert result is False

    def test_remove_grant(self):
        """Test grant removal."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time

        store = EphemeralGrantStore()
        record = GrantRecord(
            path="D:\\Test\\file.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-456",
        )

        store.add_grant(record)
        result = store.remove_grant("user-456", "D:\\Test\\file.txt", "read")
        assert result is True

        retrieved = store.get_grant("user-456", "D:\\Test\\file.txt", "read")
        assert retrieved is None

    def test_clear_session(self):
        """Test clearing all grants for a session."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time

        store = EphemeralGrantStore()
        record1 = GrantRecord(
            path="D:\\Test\\file1.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-1",
            user_id="user-123",
        )
        record2 = GrantRecord(
            path="D:\\Test\\file2.txt",
            op=PathOp.WRITE,
            scope=GrantScope.SESSION,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-2",
            user_id="user-123",
        )
        record3 = GrantRecord(
            path="D:\\Test\\file3.txt",
            op=PathOp.READ,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-3",
            user_id="user-456",  # Different user
        )

        store.add_grant(record1)
        store.add_grant(record2)
        store.add_grant(record3)

        removed = store.clear_session("user-123")
        assert removed == 2

        assert store.get_grant("user-123", "D:\\Test\\file1.txt", "read") is None
        assert store.get_grant("user-123", "D:\\Test\\file2.txt", "write") is None
        assert store.get_grant("user-456", "D:\\Test\\file3.txt", "read") is not None

    def test_thread_safety_concurrent_access(self):
        """Test thread safety with concurrent access."""
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from time import time
        import threading

        store = EphemeralGrantStore()
        results = []

        def add_grant_thread(user_id_suffix):
            for i in range(10):
                record = GrantRecord(
                    path=f"D:\\Test\\file{i}.txt",
                    op=PathOp.READ,
                    scope=GrantScope.ONCE,
                    granted_at=time(),
                    expires_at=None,
                    consent_challenge_id=f"challenge-{i}",
                    user_id=f"user-{user_id_suffix}",
                )
                store.add_grant(record)
                results.append(f"user-{user_id_suffix}")

        # Create multiple threads
        threads = [threading.Thread(target=add_grant_thread, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All operations should have completed without errors
        assert len(results) == 50


class TestPersistentGrantStore:
    """Test suite for PersistentGrantStore."""

    def test_add_and_check_grant(self):
        """Test adding and checking persistent grants."""
        from backend.services.path_sentinel.stores import PersistentGrantStore
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base
        from backend.data.models import PathPermission

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            store = PersistentGrantStore(db)
            store.add_grant("user-123", "D:\\Safe", "read")

            # Check exact match
            assert store.check_grant("user-123", "D:\\Safe", "read") is True

            # Check prefix match
            assert store.check_grant("user-123", "D:\\Safe\\file.txt", "read") is True

            # Check no match for different user
            assert store.check_grant("user-456", "D:\\Safe", "read") is False

            # Check no match for different operation
            assert store.check_grant("user-123", "D:\\Safe", "write") is False

        finally:
            db.close()

    def test_check_grant_no_permissions(self):
        """Test check_grant returns False when no permissions exist."""
        from backend.services.path_sentinel.stores import PersistentGrantStore
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            store = PersistentGrantStore(db)
            assert store.check_grant("user-123", "D:\\Safe", "read") is False
        finally:
            db.close()


class TestPathSentinel:
    """Test suite for PathSentinel core."""

    def test_check_deny_system_protected(self):
        """Test check returns DENY_SYSTEM_PROTECTED for blocked paths."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, lambda: None)

        decision = sentinel.check("C:\\Windows\\System32", "read", "session-123", "user-123")
        assert decision == SentinelDecision.DENY_SYSTEM_PROTECTED

    def test_check_deny_requires_consent(self):
        """Test check returns DENY_REQUIRES_CONSENT when no grant exists."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123")
        assert decision == SentinelDecision.DENY_REQUIRES_CONSENT

    def test_check_allow_ephemeral_grant(self):
        """Test check returns ALLOW with ephemeral grant."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.models import GrantRecord, PathOp, GrantScope
        from time import time
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # Add ephemeral grant
        record = GrantRecord(
            path="D:\\Safe",
            op=PathOp.READ,
            scope=GrantScope.SESSION,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-123",
        )
        ephemeral_store.add_grant(record)

        decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123")
        assert decision == SentinelDecision.ALLOW

    def test_check_allow_persistent_grant(self):
        """Test check returns ALLOW with persistent grant."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore, PersistentGrantStore
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            blocklist = SystemPathBlocklist()
            ephemeral_store = EphemeralGrantStore()
            sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

            # Add persistent grant
            persistent_store = PersistentGrantStore(db)
            persistent_store.add_grant("user-123", "D:\\Safe", "read")

            decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123", db)
            assert decision == SentinelDecision.ALLOW
        finally:
            db.close()

    def test_grant_ephemeral_session(self):
        """Test granting ephemeral SESSION grant."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.auth import SignedConsentToken
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # Create token
        token_auth = SignedConsentToken("test-secret")
        token = token_auth.create_token("challenge-123", "D:\\Safe", "read", "session")

        # Grant access
        result = sentinel.grant(
            path="D:\\Safe",
            op="read",
            scope="session",
            session_id="session-123",
            user_id="user-123",
            consent_token=token,
            secret_key="test-secret",
        )
        assert result is True

        # Check access is now allowed
        decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123")
        assert decision == SentinelDecision.ALLOW

    def test_grant_persistent_always(self):
        """Test granting persistent ALWAYS grant."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.auth import SignedConsentToken
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            blocklist = SystemPathBlocklist()
            ephemeral_store = EphemeralGrantStore()
            sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

            # Create token
            token_auth = SignedConsentToken("test-secret")
            token = token_auth.create_token("challenge-123", "D:\\Safe", "read", "always")

            # Grant access
            result = sentinel.grant(
                path="D:\\Safe",
                op="read",
                scope="always",
                session_id="session-123",
                user_id="user-123",
                consent_token=token,
                secret_key="test-secret",
                db=db,
            )
            assert result is True

            # Check access is now allowed (even without ephemeral grant)
            decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123", db)
            assert decision == SentinelDecision.ALLOW
        finally:
            db.close()

    def test_grant_invalid_token(self):
        """Test grant fails with invalid token."""
        from backend.services.path_sentinel.sentinel import PathSentinel
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # Try to grant with invalid token
        result = sentinel.grant(
            path="D:\\Safe",
            op="read",
            scope="session",
            session_id="session-123",
            user_id="user-123",
            consent_token="invalid-token",
            secret_key="test-secret",
        )
        assert result is False

    def test_complete_flow_deny_to_allow(self):
        """Test complete flow: check (Deny) -> ConsentChallengeStore.create -> SignedConsentToken.create -> grant -> check (Allow)."""
        from backend.services.path_sentinel.sentinel import PathSentinel, SentinelDecision
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore, ConsentChallengeStore
        from backend.services.path_sentinel.auth import SignedConsentToken
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        challenge_store = ConsentChallengeStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # Step 1: Check access - should require consent
        decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123")
        assert decision == SentinelDecision.DENY_REQUIRES_CONSENT

        # Step 2: Create consent challenge
        challenge_id = challenge_store.create_challenge("session-123", "D:\\Safe", "read")
        assert challenge_id is not None

        # Step 3: Verify challenge
        challenge_data = challenge_store.get_and_validate(challenge_id, "session-123")
        assert challenge_data is not None
        assert challenge_data["path"] == "D:\\Safe"
        assert challenge_data["op"] == "read"

        # Step 4: Create signed token
        token_auth = SignedConsentToken("test-secret")
        token = token_auth.create_token(challenge_id, "D:\\Safe", "read", "session")
        assert token is not None

        # Step 5: Grant access with token
        result = sentinel.grant(
            path="D:\\Safe",
            op="read",
            scope="session",
            session_id="session-123",
            user_id="user-123",
            consent_token=token,
            secret_key="test-secret",
        )
        assert result is True

        # Step 6: Check access again - should now be allowed
        decision = sentinel.check("D:\\Safe\\file.txt", "read", "session-123", "user-123")
        assert decision == SentinelDecision.ALLOW


class TestRequiresPathAuthDecorator:
    """Test suite for @requires_path_auth decorator."""

    def test_decorator_deny_system_protected(self):
        """Test decorator returns error for system protected paths."""
        from backend.services.path_sentinel.decorator import requires_path_auth
        from backend.services.path_sentinel.models import PathOp
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.sentinel import PathSentinel
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        @requires_path_auth(op=PathOp.READ, path_arg="path")
        def test_func(path: str, **kwargs):
            return {"status": "success", "data": path}

        result = test_func(path="C:\\Windows\\System32", sentinel=sentinel)
        assert result["status"] == "error"
        assert "System path protected" in result["message"]

    def test_decorator_permission_required(self):
        """Test decorator returns permission_required for mutating ops without grant.

        Policy: READ is auto-allowed (no consent). Only mutating ops (write/delete)
        trigger the consent flow.
        """
        from backend.services.path_sentinel.decorator import requires_path_auth
        from backend.services.path_sentinel.models import PathOp
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore, ConsentChallengeStore
        from backend.services.path_sentinel.sentinel import PathSentinel
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        challenge_store = ConsentChallengeStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # DELETE requires consent under the new policy.
        @requires_path_auth(op=PathOp.DELETE, path_arg="path")
        def test_func(path: str, **kwargs):
            return {"status": "success", "data": path}

        result = test_func(
            path="D:\\Safe\\file.txt",
            sentinel=sentinel,
            ephemeral_store=ephemeral_store,
            challenge_store=challenge_store,
        )
        assert result["status"] == "permission_required"
        assert "challenge_id" in result["data"]
        assert result["data"]["path"] == "D:\\Safe\\file.txt"
        assert result["data"]["op"] == "delete"

    def test_decorator_read_auto_allowed(self):
        """Test decorator auto-allows READ without grant (new policy)."""
        from backend.services.path_sentinel.decorator import requires_path_auth
        from backend.services.path_sentinel.models import PathOp
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.sentinel import PathSentinel
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        @requires_path_auth(op=PathOp.READ, path_arg="path")
        def test_func(path: str, **kwargs):
            return {"status": "success", "data": path}

        result = test_func(path="D:\\Safe\\file.txt", sentinel=sentinel)
        assert result["status"] == "success"
        assert result["data"] == "D:\\Safe\\file.txt"

    def test_decorator_allow_with_grant(self):
        """Test decorator allows execution when grant exists."""
        from backend.services.path_sentinel.decorator import requires_path_auth
        from backend.services.path_sentinel.models import PathOp, GrantScope, GrantRecord
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.sentinel import PathSentinel
        from time import time
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # Add grant
        record = GrantRecord(
            path="D:\\Safe",
            op=PathOp.READ,
            scope=GrantScope.SESSION,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-123",
        )
        ephemeral_store.add_grant(record)

        @requires_path_auth(op=PathOp.READ, path_arg="path")
        def test_func(path: str, **kwargs):
            return {"status": "success", "data": path}

        result = test_func(path="D:\\Safe\\file.txt", sentinel=sentinel, user_id="user-123", ephemeral_store=ephemeral_store)
        assert result["status"] == "success"
        assert result["data"] == "D:\\Safe\\file.txt"

    def test_decorator_missing_path_arg(self):
        """Test decorator returns error when path argument is missing."""
        from backend.services.path_sentinel.decorator import requires_path_auth
        from backend.services.path_sentinel.models import PathOp

        @requires_path_auth(op=PathOp.READ, path_arg="path")
        def test_func(wrong_arg: str, **kwargs):
            return {"status": "success", "data": wrong_arg}

        result = test_func(wrong_arg="D:\\Safe")
        assert result["status"] == "error"
        assert "Path argument" in result["message"]

    def test_decorator_consumes_once_grant(self):
        """Test decorator consumes ONCE grants after successful mutating op.

        Uses DELETE (mutating) because under the new policy READ is auto-allowed
        and therefore never consults grants.
        """
        from backend.services.path_sentinel.decorator import requires_path_auth
        from backend.services.path_sentinel.models import PathOp, GrantScope, GrantRecord
        from backend.services.path_sentinel.utils import SystemPathBlocklist
        from backend.services.path_sentinel.stores import EphemeralGrantStore
        from backend.services.path_sentinel.sentinel import PathSentinel
        from time import time
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.data.database import Base

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)

        blocklist = SystemPathBlocklist()
        ephemeral_store = EphemeralGrantStore()
        sentinel = PathSentinel(blocklist, ephemeral_store, SessionLocal)

        # Add ONCE grant for DELETE
        record = GrantRecord(
            path="D:\\Safe",
            op=PathOp.DELETE,
            scope=GrantScope.ONCE,
            granted_at=time(),
            expires_at=None,
            consent_challenge_id="challenge-123",
            user_id="user-123",
        )
        ephemeral_store.add_grant(record)

        @requires_path_auth(op=PathOp.DELETE, path_arg="path")
        def test_func(path: str, **kwargs):
            return {"status": "success", "data": path}

        # First call should succeed
        result1 = test_func(path="D:\\Safe\\file.txt", sentinel=sentinel, user_id="user-123", ephemeral_store=ephemeral_store)
        assert result1["status"] == "success"

        # Grant should be consumed (use normalized path)
        from backend.services.path_sentinel.utils import PathNormalizer
        normalized_path = PathNormalizer.normalize("D:\\Safe")
        grant_after = ephemeral_store.get_grant("user-123", normalized_path, "delete")
        assert grant_after is None


