"""
Unit tests for RAG V2 Security & Observability (P6).

Tests:
- Secret-Leak Gate: .env file must NOT be indexed
- Path-Escape Gate: /etc/passwd or ../config.json must throw SecurityError
- Observability Gate: Every query produces valid JSON log entry
- Denylist Coverage: All denylist patterns are rejected
"""

import json
import tempfile
from pathlib import Path

import pytest

from backend.services.rag.path_policy import (
    PathPolicy,
    SecurityError,
    set_global_policy,
    is_path_allowed,
    validate_path,
)
from backend.services.rag.retrieval_logger import RetrievalLogger, get_retrieval_logger
from backend.services.rag.ingestion import IngestionRun


# --- Secret-Leak Gate ---

class TestSecretLeakGate:
    """Test that secret files are not indexed."""

    def test_env_file_denied(self):
        """A .env file must be rejected by path policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("SECRET_KEY=abc123")

            assert not policy.is_allowed(env_file)
            reason = policy.get_denied_reason(env_file)
            assert "Denied name" in reason or "Denied extension" in reason

    def test_pem_file_denied(self):
        """A .pem file (private key) must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            pem_file = Path(tmpdir) / "private.pem"
            pem_file.write_text("-----BEGIN PRIVATE KEY-----")

            assert not policy.is_allowed(pem_file)
            reason = policy.get_denied_reason(pem_file)
            assert "Denied extension" in reason

    def test_key_file_denied(self):
        """A .key file must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            key_file = Path(tmpdir) / "api.key"
            key_file.write_text("SECRET")

            assert not policy.is_allowed(key_file)

    def test_db_file_denied(self):
        """Database files (.db, .sqlite) must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            db_file = Path(tmpdir) / "data.db"
            db_file.write_text("sqlite data")

            assert not policy.is_allowed(db_file)
            reason = policy.get_denied_reason(db_file)
            assert "Denied extension" in reason

    def test_secrets_json_denied(self):
        """secrets.json file must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            secrets_file = Path(tmpdir) / "secrets.json"
            secrets_file.write_text('{"api_key": "abc"}')

            assert not policy.is_allowed(secrets_file)
            reason = policy.get_denied_reason(secrets_file)
            assert "Denied name" in reason

    def test_ingestion_skips_env_file(self):
        """Ingestion must skip .env file and log [SKIP]."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            env_file = root / ".env"
            env_file.write_text("SECRET=xyz")

            # Create a normal file to verify ingestion works
            py_file = root / "test.py"
            py_file.write_text("def test(): pass")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "index_v2.db"

            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
                enable_path_policy=True,
            ) as ingest:
                stats = ingest.run()

            # .env should be denied, not indexed
            assert stats["denied"] >= 1

            # Verify .env is not in index
            store = ingest.store
            indexed = store.get_all()
            assert ".env" not in indexed
            assert "test.py" in indexed


# --- Path-Escape Gate ---

class TestPathEscapeGate:
    """Test path-traversal protection."""

    def test_etc_passwd_rejected(self):
        """Attempt to index /etc/passwd must raise SecurityError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            passwd_path = Path("/etc/passwd")

            with pytest.raises(SecurityError) as exc_info:
                policy.validate(passwd_path)

            assert "outside allowed workspace root" in str(exc_info.value).lower()

    def test_parent_directory_traversal_rejected(self):
        """Attempt to use ../ to escape must raise SecurityError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            escape_path = Path(tmpdir) / ".." / "config.json"

            with pytest.raises(SecurityError) as exc_info:
                policy.validate(escape_path)

            assert "outside allowed workspace root" in str(exc_info.value).lower()

    def test_symlink_outside_root_rejected(self):
        """Symlinks pointing outside root must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            policy = PathPolicy(root)

            # Create a file outside root
            outside_dir = Path(tmpdir) / "outside"
            outside_dir.mkdir()
            outside_file = outside_dir / "secret.txt"
            outside_file.write_text("SECRET")

            # Create symlink inside root pointing outside
            symlink = root / "link_to_secret"
            try:
                symlink.symlink_to(outside_file)

                with pytest.raises(SecurityError) as exc_info:
                    policy.validate(symlink)

                assert "outside allowed workspace root" in str(exc_info.value).lower()
            except OSError:
                # Symlink creation not supported (Windows admin required)
                pytest.skip("Symlink creation requires admin privileges on Windows")


# --- Observability Gate ---

class TestObservabilityGate:
    """Test retrieval logging produces valid JSON."""

    def test_retrieval_logger_singleton(self):
        """RetrievalLogger must be a singleton."""
        logger1 = get_retrieval_logger()
        logger2 = get_retrieval_logger()
        assert logger1 is logger2

    def test_log_query_produces_valid_json(self):
        """log_query must produce valid JSON in log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir()

            # Override log location for test
            from backend.services.rag import retrieval_logger
            original_log_file = retrieval_logger.LOG_FILE
            retrieval_logger.LOG_FILE = log_dir / "test.log"

            try:
                logger = RetrievalLogger()

                logger.log_query(
                    query="test query",
                    router_decision={"mode": "code_heavy", "vector_weight": 0.25},
                    latency_breakdown={"vector_ms": 50, "keyword_ms": 10},
                    top_result={"chunk_id": "1", "source_path": "/test.py"},
                    num_results=5,
                )

                # Read log file and verify JSON
                log_content = (log_dir / "test.log").read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                assert len(lines) == 1
                entry = json.loads(lines[0])

                assert entry["query"] == "test query"
                assert entry["router_decision"]["mode"] == "code_heavy"
                assert entry["latency_breakdown"]["vector_ms"] == 50
                assert entry["num_results"] == 5
                assert "timestamp" in entry

            finally:
                retrieval_logger.LOG_FILE = original_log_file

    def test_log_ingestion_skip_produces_valid_json(self):
        """log_ingestion_skip must produce valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir()

            from backend.services.rag import retrieval_logger
            original_log_file = retrieval_logger.LOG_FILE
            retrieval_logger.LOG_FILE = log_dir / "test.log"

            try:
                logger = RetrievalLogger()
                logger.log_ingestion_skip("/path/to/.env", "Denied name: .env")

                log_content = (log_dir / "test.log").read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                assert len(lines) == 1
                entry = json.loads(lines[0])

                assert entry["event"] == "ingestion_skip"
                assert entry["file_path"] == "/path/to/.env"
                assert entry["reason"] == "Denied name: .env"

            finally:
                retrieval_logger.LOG_FILE = original_log_file

    def test_log_ingestion_success_produces_valid_json(self):
        """log_ingestion_success must produce valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir()

            from backend.services.rag import retrieval_logger
            original_log_file = retrieval_logger.LOG_FILE
            retrieval_logger.LOG_FILE = log_dir / "test.log"

            try:
                logger = RetrievalLogger()
                logger.log_ingestion_success("/path/to/file.py", 5, "kb_code_v2")

                log_content = (log_dir / "test.log").read_text(encoding="utf-8")
                lines = log_content.strip().split("\n")

                assert len(lines) == 1
                entry = json.loads(lines[0])

                assert entry["event"] == "ingestion_success"
                assert entry["file_path"] == "/path/to/file.py"
                assert entry["num_chunks"] == 5
                assert entry["collection"] == "kb_code_v2"

            finally:
                retrieval_logger.LOG_FILE = original_log_file


# --- Denylist Coverage ---

class TestDenylistCoverage:
    """Test that all denylist patterns are rejected."""

    def test_node_modules_denied(self):
        """node_modules directory must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            node_modules = Path(tmpdir) / "node_modules" / "package.json"
            node_modules.parent.mkdir(parents=True)
            node_modules.write_text("{}")

            assert not policy.is_allowed(node_modules)

    def test_venv_denied(self):
        """venv directory must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            venv_file = Path(tmpdir) / "venv" / "lib" / "python.py"
            venv_file.parent.mkdir(parents=True)
            venv_file.write_text("code")

            assert not policy.is_allowed(venv_file)

    def test_git_denied(self):
        """.git directory must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            git_file = Path(tmpdir) / ".git" / "config"
            git_file.parent.mkdir(parents=True)
            git_file.write_text("[core]")

            assert not policy.is_allowed(git_file)

    def test_pycache_denied(self):
        """__pycache__ directory must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            pycache = Path(tmpdir) / "__pycache__" / "module.pyc"
            pycache.parent.mkdir(parents=True)
            pycache.write_text("bytecode")

            assert not policy.is_allowed(pycache)

    def test_hidden_file_denied(self):
        """Hidden files (except allowlisted) must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            hidden_file = Path(tmpdir) / ".hidden"
            hidden_file.write_text("secret")

            assert not policy.is_allowed(hidden_file)

    def test_gitignore_allowed(self):
        """.gitignore should be allowed (allowlisted)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            gitignore = Path(tmpdir) / ".gitignore"
            gitignore.write_text("node_modules")

            assert policy.is_allowed(gitignore)

    def test_env_example_allowed(self):
        """.env.example should be allowed (allowlisted)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = PathPolicy(Path(tmpdir))
            env_example = Path(tmpdir) / ".env.example"
            env_example.write_text("SECRET_KEY=your_key_here")

            assert policy.is_allowed(env_example)


# --- Global Policy ---

class TestGlobalPolicy:
    """Test global path policy functions."""

    def test_set_global_policy(self):
        """set_global_policy should set the global policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            set_global_policy(Path(tmpdir))

            # Should now reject files outside tmpdir
            outside = Path("/etc/passwd")
            assert not is_path_allowed(outside)

    def test_validate_path_uses_global_policy(self):
        """validate_path should use global policy if set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            set_global_policy(Path(tmpdir))

            outside = Path("/etc/passwd")
            with pytest.raises(SecurityError):
                validate_path(outside)
