"""
Unit tests for RAG V2 Ingestion Engine.

Tests idempotency, isolation, and orphan cleanup.
"""

import shutil
import tempfile
import time
from pathlib import Path

import pytest

from backend.services.rag.adapters.base import BaseAdapter
from backend.services.rag.ingestion import IngestionRun, FormatRouter, V2_CHROMA_PATH
from backend.services.rag.index_store import IndexStore


class TestFormatRouter:
    """Test format routing logic."""

    def test_routes_python(self):
        assert FormatRouter.is_supported(Path("test.py"))
        adapter = FormatRouter.get_adapter(Path("test.py"))
        assert adapter is not None
        assert FormatRouter.get_format(Path("test.py")) == "code"

    def test_routes_markdown(self):
        assert FormatRouter.is_supported(Path("test.md"))
        adapter = FormatRouter.get_adapter(Path("test.md"))
        assert adapter is not None
        assert FormatRouter.get_format(Path("test.md")) == "markdown"

    def test_ignores_txt(self):
        assert not FormatRouter.is_supported(Path("test.txt"))


class TestIsolationGuard:
    """Test that V2 ChromaDB path is isolated from legacy."""

    def test_v2_path_does_not_contain_legacy(self):
        from backend.utils.paths import get_app_data_dir
        import os
        legacy = os.path.join(get_app_data_dir(), "rag_chroma_db")
        assert V2_CHROMA_PATH != legacy
        assert not V2_CHROMA_PATH.startswith(legacy + os.sep)

    def test_ingestion_rejects_legacy_path(self):
        """IngestionRun should reject paths pointing to legacy collection."""
        from backend.utils.paths import get_app_data_dir
        import os
        legacy_path = os.path.join(get_app_data_dir(), "rag_chroma_db")

        with pytest.raises(RuntimeError) as exc_info:
            with IngestionRun("/tmp", chroma_path=legacy_path):
                pass
        assert "legacy" in str(exc_info.value).lower()


class TestIngestionIdempotency:
    """Test that re-running ingestion on unchanged files skips them."""

    def test_second_run_skips_unchanged(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test Python file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('hello')\n")

            # Use a temporary ChromaDB and DB path for isolation
            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "index_v2.db"

            # First run
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run1:
                stats1 = run1.run()
                assert stats1["indexed"] == 1
                assert stats1["skipped"] == 0

            # Second run - should skip
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run2:
                stats2 = run2.run()
                assert stats2["indexed"] == 0
                assert stats2["skipped"] == 1

    def test_detects_modified_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('hello')\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "index_v2.db"

            # First run
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run1:
                stats1 = run1.run()
                assert stats1["indexed"] == 1

            # Wait a moment then modify
            time.sleep(0.1)
            test_file.write_text("def hello():\n    print('world')\n")

            # Second run - should re-index
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run2:
                stats2 = run2.run()
                assert stats2["indexed"] == 1
                assert stats2["skipped"] == 0


class TestOrphanCleanup:
    """Test deletion of files no longer present on disk."""

    def test_deletes_missing_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello(): pass\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "index_v2.db"

            # First run
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run1:
                stats1 = run1.run()
                assert stats1["indexed"] == 1

            # Delete the file
            test_file.unlink()

            # Second run - should detect orphan and delete
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run2:
                stats2 = run2.run()
                assert stats2["deleted"] == 1
                assert stats2["indexed"] == 0

    def test_renames_detected_as_delete_and_add(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_file = Path(tmpdir) / "old.py"
            old_file.write_text("def hello(): pass\n")

            chroma_tmp = Path(tmpdir) / "chroma_v2"
            db_tmp = Path(tmpdir) / "index_v2.db"

            # First run
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run1:
                run1.run()

            # Rename
            new_file = Path(tmpdir) / "new.py"
            old_file.rename(new_file)

            # Second run
            with IngestionRun(
                tmpdir,
                chroma_path=str(chroma_tmp),
                db_path=str(db_tmp),
            ) as run2:
                stats2 = run2.run()
                assert stats2["deleted"] == 1  # old.py is orphan
                assert stats2["indexed"] == 1  # new.py is new
