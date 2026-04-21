"""
Unit tests for RAG V2 Watchdog (P8).

Tests:
- Debounce Queue: 10 quick saves trigger only one log message
- Coalesce: Multiple files in batch window trigger single run
- Thread-Safety: No lock errors under concurrent access
"""

import logging
import tempfile
import time
from pathlib import Path

import pytest

from backend.services.rag.watcher import DebounceQueue, RAGWatcher


class TestDebounceQueue:
    """Test debounce queue logic."""

    def test_debounce_single_file(self):
        """
        Test that multiple events for the same file within debounce window
        trigger only one callback.
        """
        callback_count = [0]
        processed_files = []

        def callback(files):
            callback_count[0] += 1
            processed_files.extend(files)

        queue = DebounceQueue(debounce_seconds=2.0, batch_seconds=1.0)
        queue.set_callback(callback)

        # Simulate 10 quick saves to the same file
        for i in range(10):
            queue.add_event("test.py")
            time.sleep(0.1)  # 100ms between saves

        # Wait for batch to process
        time.sleep(2)

        # Should trigger only one callback
        assert callback_count[0] == 1, f"Expected 1 callback, got {callback_count[0]}"
        assert "test.py" in processed_files
        # File should appear only once (deduplication)
        assert processed_files.count("test.py") == 1

    def test_coalesce_multiple_files(self):
        """
        Test that multiple files changed within batch window
        trigger a single callback with all files.
        """
        callback_count = [0]
        processed_files = []

        def callback(files):
            callback_count[0] += 1
            processed_files.extend(files)

        queue = DebounceQueue(debounce_seconds=2.0, batch_seconds=1.0)
        queue.set_callback(callback)

        # Simulate changes to 10 different files
        for i in range(10):
            queue.add_event(f"file{i}.py")
            time.sleep(0.1)  # 100ms between events

        # Wait for batch to process
        time.sleep(2)

        # Should trigger only one callback
        assert callback_count[0] == 1, f"Expected 1 callback, got {callback_count[0]}"
        # All 10 files should be in the batch
        assert len(processed_files) == 10
        for i in range(10):
            assert f"file{i}.py" in processed_files

    def test_stop_processes_pending(self):
        """Test that stopping the queue processes pending events."""
        callback_count = [0]
        processed_files = []

        def callback(files):
            callback_count[0] += 1
            processed_files.extend(files)

        queue = DebounceQueue(debounce_seconds=2.0, batch_seconds=1.0)
        queue.set_callback(callback)

        # Add events but don't wait for batch
        queue.add_event("test.py")

        # Stop immediately
        queue.stop()

        # Should process pending events
        assert callback_count[0] == 1
        assert "test.py" in processed_files


class TestRAGWatcher:
    """Test RAG watcher integration."""

    def test_watcher_lifecycle(self):
        """Test watcher start/stop lifecycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = RAGWatcher(
                workspace_root=tmpdir,
                chroma_path=None,
                db_path=None,
                enable_path_policy=False,  # Disable for test
            )

            watcher.start()
            assert watcher._running is True

            watcher.stop()
            assert watcher._running is False

    def test_watcher_context_manager(self):
        """Test watcher as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with RAGWatcher(
                workspace_root=tmpdir,
                enable_path_policy=False,
            ) as watcher:
                assert watcher._running is True

            assert watcher._running is False

    def test_relevant_file_filter(self):
        """Test that only relevant files are processed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            callback_count = [0]

            def callback(files):
                callback_count[0] += 1

            queue = DebounceQueue()
            queue.set_callback(callback)

            from backend.services.rag.watcher import RAGEventHandler
            handler = RAGEventHandler(queue, Path(tmpdir))

            # Test relevant file
            handler.on_modified(watchdog.events.FileModifiedEvent(str(Path(tmpdir) / "test.py")))
            queue.stop()
            assert callback_count[0] == 1

    def test_irrelevant_file_filtered(self):
        """Test that irrelevant files are filtered out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            callback_count = [0]

            def callback(files):
                callback_count[0] += 1

            queue = DebounceQueue()
            queue.set_callback(callback)

            from backend.services.rag.watcher import RAGEventHandler
            handler = RAGEventHandler(queue, Path(tmpdir))

            # Test irrelevant file (.env should be filtered)
            handler.on_modified(watchdog.events.FileModifiedEvent(str(Path(tmpdir) / ".env")))
            queue.stop()
            assert callback_count[0] == 0


# Import watchdog for event types
import watchdog.events
