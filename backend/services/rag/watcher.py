"""
RAG V2 Background Watchdog

File-system observer for automatic incremental re-indexing.

Features:
- OS-native events via watchdog library
- Debounce logic: 2s debounce per file to handle IDE auto-save bursts
- Coalesce: Group multiple events into single ingestion run
- Thread-safe: Runs in separate thread, graceful shutdown
- Error handling: Crashes don't affect main backend

Usage:
    watcher = RAGWatcher(
        workspace_root="/path/to/workspace",
        chroma_path="/path/to/chroma_v2",
        db_path="/path/to/index_v2.db",
    )
    watcher.start()
    # ... main application runs ...
    watcher.stop()
"""

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Set

import watchdog.events
import watchdog.observers

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")


class DebounceQueue:
    """
    Queue with debounce logic for file system events.

    Rules:
    - Events for the same file within 2s are coalesced
    - Multiple files changed within 1s are grouped into one batch
    - Only one ingestion run per batch
    """

    def __init__(self, debounce_seconds: float = 2.0, batch_seconds: float = 1.0):
        self.debounce_seconds = debounce_seconds
        self.batch_seconds = batch_seconds
        self._pending_files: Set[str] = set()
        self._last_event_time: float = 0
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._callback = None

    def set_callback(self, callback):
        """Set the callback function to call when debounce triggers."""
        self._callback = callback

    def add_event(self, file_path: str):
        """
        Add a file event to the queue.

        The event is debounced and coalesced with other events.
        """
        with self._lock:
            self._pending_files.add(file_path)
            now = time.time()
            self._last_event_time = now

            # Cancel existing timer if any
            if self._timer is not None:
                self._timer.cancel()

            # Schedule new timer for batch window
            self._timer = threading.Timer(self.batch_seconds, self._process_batch)
            self._timer.start()

    def _process_batch(self):
        """Process the batch of pending files."""
        with self._lock:
            if not self._pending_files:
                return

            # Check if more events came in during batch window
            time_since_last = time.time() - self._last_event_time
            if time_since_last < self.batch_seconds:
                # More events came in, reschedule
                if self._timer is not None:
                    self._timer.cancel()
                self._timer = threading.Timer(self.batch_seconds, self._process_batch)
                self._timer.start()
                return

            # Process the batch
            files_to_process = list(self._pending_files)
            self._pending_files.clear()
            self._timer = None

        # Call callback outside lock
        if self._callback:
            try:
                self._callback(files_to_process)
            except Exception as e:
                logger.error(f"[RAG Watcher] Callback failed: {e}", exc_info=True)

    def stop(self):
        """Stop the debounce queue and process any pending events."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

            # Process remaining events immediately
            if self._pending_files:
                files_to_process = list(self._pending_files)
                self._pending_files.clear()
                if self._callback:
                    try:
                        self._callback(files_to_process)
                    except Exception as e:
                        logger.error(f"[RAG Watcher] Final callback failed: {e}", exc_info=True)


class RAGEventHandler(watchdog.events.FileSystemEventHandler):
    """
    Event handler for file system changes.

    Filters events to only relevant files and forwards to debounce queue.
    """

    def __init__(self, debounce_queue: DebounceQueue, workspace_root: Path):
        super().__init__()
        self.debounce_queue = debounce_queue
        self.workspace_root = workspace_root

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if not self._is_relevant_file(file_path):
            return

        logger.debug(f"[RAG Watcher] File modified: {file_path}")
        self.debounce_queue.add_event(str(file_path))

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if not self._is_relevant_file(file_path):
            return

        logger.debug(f"[RAG Watcher] File created: {file_path}")
        self.debounce_queue.add_event(str(file_path))

    def on_moved(self, event):
        """Handle file move/rename events."""
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)
        if not self._is_relevant_file(dest_path):
            return

        logger.debug(f"[RAG Watcher] File moved: {event.src_path} -> {dest_path}")
        self.debounce_queue.add_event(str(dest_path))

    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if not self._is_relevant_file(file_path):
            return

        logger.debug(f"[RAG Watcher] File deleted: {file_path}")
        self.debounce_queue.add_event(str(file_path))

    def _is_relevant_file(self, file_path: Path) -> bool:
        """
        Check if a file is relevant for RAG indexing.

        Relevant files:
        - Within workspace root
        - Has supported extension (.py, .md, .txt, etc.)
        - Not in denylist (.env, .pem, node_modules, etc.)
        """
        # Must be within workspace
        try:
            file_path.resolve().relative_to(self.workspace_root.resolve())
        except ValueError:
            return False

        # Check extension (basic filter)
        supported_extensions = {".py", ".md", ".txt", ".rst", ".js", ".ts", ".json", ".yaml", ".yml"}
        if file_path.suffix.lower() not in supported_extensions:
            return False

        # Basic denylist (should align with path_policy.py)
        denylist_names = {".env", ".pem", ".key", ".crt", ".cert"}
        if file_path.name in denylist_names:
            return False

        return True


class RAGWatcher:
    """
    Background watcher for automatic RAG re-indexing.

    Runs in a separate thread and watches the workspace for file changes.
    Debounces and coalesces events to avoid excessive re-indexing.
    """

    def __init__(
        self,
        workspace_root: str,
        chroma_path: Optional[str] = None,
        db_path: Optional[str] = None,
        enable_path_policy: bool = True,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.chroma_path = chroma_path or str(Path(get_app_data_dir()) / "rag_chroma_db_v2")
        self.db_path = db_path or str(Path(get_app_data_dir()) / "knowledge_index_v2.db")
        self.enable_path_policy = enable_path_policy

        self._debounce_queue = DebounceQueue(debounce_seconds=2.0, batch_seconds=1.0)
        self._debounce_queue.set_callback(self._on_batch_ready)

        self._observer: Optional[watchdog.observers.Observer] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _on_batch_ready(self, file_paths: list):
        """
        Callback when a batch of file events is ready for processing.

        This runs in the debounce queue's timer thread, so we should
        offload the actual indexing to a separate thread or queue.
        """
        logger.info(f"[RAG Watcher] Processing batch of {len(file_paths)} files")

        # Offload indexing to a separate thread to avoid blocking the debounce queue
        indexing_thread = threading.Thread(
            target=self._run_partial_indexing,
            args=(file_paths,),
            daemon=True,
        )
        indexing_thread.start()

    def _run_partial_indexing(self, file_paths: list):
        """
        Run partial indexing in a separate thread.

        This prevents blocking the watchdog observer thread.
        """
        try:
            from .ingestion import IngestionRun

            ingest = IngestionRun(
                root_dir=str(self.workspace_root),
                chroma_path=self.chroma_path,
                db_path=self.db_path,
                enable_path_policy=self.enable_path_policy,
            )
            stats = ingest.run_partial(file_paths)
            logger.info(f"[RAG Watcher] Partial indexing completed: {stats}")
        except Exception as e:
            logger.error(f"[RAG Watcher] Partial indexing failed: {e}", exc_info=True)

    def start(self):
        """Start the watcher in a separate thread."""
        if self._running:
            logger.warning("[RAG Watcher] Already running")
            return

        logger.info(f"[RAG Watcher] Starting watcher for: {self.workspace_root}")

        # Create observer
        self._observer = watchdog.observers.Observer()
        event_handler = RAGEventHandler(self._debounce_queue, self.workspace_root)
        self._observer.schedule(event_handler, str(self.workspace_root), recursive=True)

        # Start observer in thread
        self._observer.start()
        self._running = True

        logger.info("[RAG Watcher] Started successfully")

    def stop(self):
        """Stop the watcher and clean up resources."""
        if not self._running:
            return

        logger.info("[RAG Watcher] Stopping...")

        # Stop debounce queue first (process pending events)
        self._debounce_queue.stop()

        # Stop observer
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        self._running = False
        logger.info("[RAG Watcher] Stopped successfully")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
