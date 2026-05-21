"""
Core logging pipeline with async RAM-Queue.
Provides non-blocking event ingestion with thread-safe queue operations.
"""
import asyncio
import logging
from contextvars import ContextVar
from datetime import datetime
from typing import Optional, List
from uuid import uuid4
import json
from pathlib import Path

from backend.data.schemas_logging import LogEventCreate, LogEvent, LogEventPayload
from backend.services.logging.supabase_client import get_supabase_client
from backend.utils.redaction import redact_sensitive_value


# Configure module logger
logger = logging.getLogger(__name__)


# Context variable for trace_id - enables automatic trace propagation
_trace_id: ContextVar[Optional[str]] = ContextVar("_trace_id", default=None)


def set_trace_id(trace_id: str) -> None:
    """
    Set the trace_id for the current async context.
    
    This enables automatic trace propagation across all logging calls
    within the same request/transaction context.
    
    Args:
        trace_id: The trace identifier to set (e.g., UUID or chat_id).
    """
    _trace_id.set(trace_id)


def get_trace_id() -> Optional[str]:
    """
    Get the trace_id for the current async context.
    
    Returns:
        The current trace_id if set, None otherwise.
    """
    return _trace_id.get()


def generate_trace_id() -> str:
    """
    Generate a new unique trace_id.
    
    Returns:
        A new UUID-based trace_id as string.
    """
    return str(uuid4())


# Global async queue for in-memory event buffering
# Max size of 5000 to prevent memory bloat in case of backpressure
_log_queue: asyncio.Queue[LogEventCreate] = asyncio.Queue(maxsize=5000)

# Worker task reference for graceful shutdown
_worker_task: Optional[asyncio.Task] = None

# Shutdown flag to signal worker to stop
_shutdown_requested: bool = False

# Metrics tracking
_successful_uploads: int = 0
_failed_uploads: int = 0
_total_retries: int = 0


async def log_event(event: LogEventCreate) -> None:
    """
    Asynchronously add a log event to the in-memory queue.
    
    This function is non-blocking and designed for high-throughput scenarios.
    Events are enriched with a current timestamp if not already provided.
    Trace ID is automatically populated from context if not provided in the event.
    A unique ID is generated for UPSERT idempotency.
    Payload is validated against strict schema before queuing.
    
    Queue Overflow Strategy: If queue is full, remove oldest event before adding new one.
    
    Args:
        event: The log event to be queued. If timestamp is None, it will be
               set to the current UTC time. If trace_id is None, it will be
               auto-populated from context.
               
    Raises:
        asyncio.QueueFull: If the queue is full (5000 events). This is a
                          backpressure signal that the consumer cannot keep up.
    """
    from backend.services.ops_kill_switches import telemetry_event_ingest_allowed

    if not telemetry_event_ingest_allowed(getattr(event, "event_type", None)):
        logger.info("Telemetry event dropped by JANUS_TELEMETRY_MODE. event_type=%s", event.event_type)
        return

    # Enrich with current timestamp if not provided
    if event.timestamp is None:
        event.timestamp = datetime.utcnow()
    
    # Auto-populate trace_id from context if not provided
    if event.trace_id is None:
        event.trace_id = get_trace_id()
    
    # Generate unique ID for UPSERT idempotency
    if event.id is None:
        event.id = str(uuid4())
    
    # Validate payload if present
    if event.payload is not None:
        try:
            # Validate against strict payload schema
            LogEventPayload(**event.payload)
        except Exception as e:
            # Reject event with schema violation
            logger.warning(
                "LOGGING-VALIDATION: Event rejected due to payload schema violation. "
                "event_type=%s, skill=%s, error=%s, payload=%s",
                event.event_type,
                event.skill,
                str(e),
                redact_sensitive_value(event.payload)
            )
            return  # Do not queue invalid events
    
    # Queue Overflow Strategy: Remove oldest if full
    if _log_queue.full():
        try:
            _log_queue.get_nowait()  # Remove oldest event
            logger.warning(
                "LOGGING-OVERFLOW: Queue full (5000). Removed oldest event to make room for new event. "
                "event_type=%s, skill=%s",
                event.event_type,
                event.skill
            )
        except asyncio.QueueEmpty:
            pass  # Should not happen, but handle gracefully
    
    # Add to queue
    await _log_queue.put(event)
    
    # Debug logging for monitoring queue size
    current_size = _log_queue.qsize()
    logger.debug("Event added to queue. Current size: %d / 5000", current_size)


def get_metrics() -> dict:
    """
    Get current logging metrics.
    
    Returns:
        dict: Dictionary with successful_uploads, failed_uploads, total_retries, queue_size
    """
    return {
        "successful_uploads": _successful_uploads,
        "failed_uploads": _failed_uploads,
        "total_retries": _total_retries,
        "queue_size": _log_queue.qsize()
    }


def get_queue_size() -> int:
    """
    Get the current number of events in the queue.
    
    Returns:
        int: Current queue size (0 to 5000).
    """
    return _log_queue.qsize()


def is_queue_empty() -> bool:
    """
    Check if the queue is empty.

    Returns:
        bool: True if queue has no events, False otherwise.
    """
    return _log_queue.empty()


def _write_to_dlq(events: List[LogEventCreate], error: str) -> None:
    """
    Write failed events to Dead Letter Queue (DLQ) file.

    This is a lightweight DLQ implementation that writes failed batches
    to a JSONL file for manual inspection and recovery.

    Args:
        events: List of failed log events.
        error: Error message describing why the batch failed.
    """
    try:
        # Ensure logs directory exists
        logs_dir = Path(__file__).parent.parent.parent / "backend" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        dlq_path = logs_dir / "failed_batches.jsonl"

        # Write each event as a JSON line with error context
        with open(dlq_path, "a", encoding="utf-8") as f:
            for event in events:
                dlq_entry = {
                    "event": redact_sensitive_value(event.model_dump(mode="json")),
                    "error": error,
                    "failed_at": datetime.utcnow().isoformat(),
                }
                f.write(json.dumps(dlq_entry) + "\n")

        logger.warning(
            "DLQ: Wrote %d failed events to %s (error: %s)",
            len(events),
            dlq_path,
            error[:100],
        )
    except Exception as e:
        logger.error("DLQ: Failed to write to dead letter queue: %s", e)


async def get_next_event() -> LogEventCreate:
    """
    Get the next event from the queue (blocking).
    
    This is intended for the consumer/worker task that processes events
    and sends them to Supabase.
    
    Returns:
        LogEventCreate: The next event to process.
        
    Raises:
        asyncio.CancelledError: If the operation is cancelled.
    """
    return await _log_queue.get()


async def clear_queue() -> None:
    """
    Clear all events from the queue.
    
    This is primarily used for testing or emergency situations.
    """
    while not _log_queue.empty():
        try:
            _log_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
    
    logger.warning("Queue cleared. All pending events have been discarded.")


async def _upload_batch_to_supabase(events: List[LogEventCreate]) -> bool:
    """
    Upload a batch of events to Supabase with UPSERT support for idempotency.
    
    Uses upsert() with on_conflict='id' to ensure idempotent uploads.
    If an event with the same ID already exists, it will be updated instead of creating a duplicate.
    
    Args:
        events: List of events to upload.
        
    Returns:
        bool: True if upload succeeded, False otherwise.
    """
    global _successful_uploads, _failed_uploads, _total_retries
    
    try:
        client = get_supabase_client()
        
        # Convert LogEventCreate to dict for Supabase
        events_data = []
        for event in events:
            event_dict = {
                "id": getattr(event, 'id', None),  # Use generated event ID for idempotency
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "session_id": event.session_id,
                "provider": event.provider,
                "model": event.model,
                "skill": event.skill,
                "event_type": event.event_type,
                "status": event.status,
                "payload": redact_sensitive_value(event.payload),
                "latency_ms": event.latency_ms,
                "trace_id": event.trace_id  # New field for trace tracking
            }
            events_data.append(event_dict)
        
        # Batch upsert with idempotency via id
        response = client.table("logs_raw").upsert(
            events_data,
            on_conflict="id"  # Use 'id' as conflict resolution key
        ).execute()
        
        if response.data:
            logger.info("Successfully upserted %d events to Supabase (idempotent)", len(events))
            _successful_uploads += 1
            return True
        else:
            logger.error("Supabase returned no data for batch upsert of %d events", len(events))
            _failed_uploads += 1
            return False
            
    except Exception as e:
        error_msg = str(e)
        # Log PGRST204 (missing column) errors VERY clearly
        if "PGRST204" in error_msg or "column" in error_msg.lower():
            logger.error(
                "=== DATABASE SCHEMA MISMATCH DETECTED ===\n"
                "Error: %s\n"
                "This indicates a missing column in the Supabase logs_raw table.\n"
                "Please verify that the database schema matches the LogEventCreate model in schemas_logging.py.\n"
                "Required columns: id, timestamp, session_id, provider, model, skill, event_type, status, payload, latency_ms, trace_id\n"
                "==========================================",
                error_msg
            )
        else:
            logger.error("Failed to upsert batch to Supabase: %s", error_msg)
        _failed_uploads += 1
        _total_retries += 1
        return False


async def _batch_upload_worker() -> None:
    """
    Background worker that processes events from the queue in batches.
    
    Batches are uploaded when either:
    - 50 events are collected, OR
    - 2 seconds have passed since the first event in the batch
    
    Uses exponential backoff on upload failures (events stay in queue).
    Periodically logs system_health events to Supabase.
    """
    global _shutdown_requested
    
    BATCH_SIZE = 50
    BATCH_TIMEOUT = 2.0  # seconds
    MAX_RETRIES = 5
    SYSTEM_HEALTH_INTERVAL = 50  # batches between system health events
    batch_count = 0
    
    logger.info("Batch upload worker started")
    
    retry_count = 0  # Initialize retry_count at the beginning of the loop
    
    while not _shutdown_requested:
        try:
            batch: List[LogEventCreate] = []
            start_time = asyncio.get_event_loop().time()
            
            # Collect events until batch is full or timeout
            while len(batch) < BATCH_SIZE and not _shutdown_requested:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(
                        _log_queue.get(),
                        timeout=BATCH_TIMEOUT
                    )
                    batch.append(event)
                    
                    # Reset timeout on first event
                    if len(batch) == 1:
                        start_time = asyncio.get_event_loop().time()
                        
                except asyncio.TimeoutError:
                    # Timeout reached, upload what we have
                    break
            
            # Upload batch if not empty
            if batch and not _shutdown_requested:
                success = False
                retry_count = 0  # Reset retry_count for new batch
                backoff_delay = 1.0  # Initial backoff delay
                
                # Exponential backoff retry logic
                while retry_count < MAX_RETRIES and not success:
                    success = await _upload_batch_to_supabase(batch)
                    
                    if success:
                        retry_count = 0  # Reset retry_count on successful upload
                    else:
                        retry_count += 1
                        backoff_delay = min(2 ** retry_count, 60)  # Max 60 seconds
                        logger.warning(
                            "Upload failed (attempt %d/%d). Retrying in %d seconds...",
                            retry_count + 1, MAX_RETRIES, backoff_delay
                        )
                        await asyncio.sleep(backoff_delay)
                        global _total_retries
                        _total_retries += 1
                    
                    if retry_count < MAX_RETRIES and not _shutdown_requested:
                        await asyncio.sleep(backoff_delay)
                        backoff_delay *= 2  # Exponential backoff: 1s, 2s, 4s, 8s...
                        
                        # Re-collect events from queue for retry
                        batch = []
                        while len(batch) < BATCH_SIZE and not _log_queue.empty():
                            try:
                                event = _log_queue.get_nowait()
                                batch.append(event)
                            except asyncio.QueueEmpty:
                                break
            
            if retry_count >= MAX_RETRIES:
                logger.error("Max retries (%d) exceeded for batch of %d events", MAX_RETRIES, len(batch))
                # Write to DLQ instead of keeping in queue forever
                _write_to_dlq(batch, f"Max retries ({MAX_RETRIES}) exceeded")
                
        except asyncio.CancelledError:
            logger.info("Worker cancelled, shutting down gracefully")
            break
        except Exception as e:
            logger.error("Unexpected error in batch upload worker: %s", str(e))
            await asyncio.sleep(1)  # Prevent tight error loop
    
    logger.info("Batch upload worker stopped")


async def flush_log_queue() -> None:
    """
    Flush all remaining events from the queue to Supabase.
    
    This function is called during graceful shutdown to ensure no data loss.
    It processes all remaining events without batching or timeout.
    """
    from backend.services.ops_kill_switches import telemetry_remote_upload_allowed

    if not telemetry_remote_upload_allowed():
        await clear_queue()
        logger.warning("Telemetry remote upload disabled by JANUS_TELEMETRY_MODE; queue discarded during flush.")
        return

    logger.info("Flushing log queue before shutdown...")
    
    remaining_events = []
    while not _log_queue.empty():
        try:
            event = _log_queue.get_nowait()
            remaining_events.append(event)
        except asyncio.QueueEmpty:
            break
    
    if remaining_events:
        logger.info("Flushing %d remaining events to Supabase", len(remaining_events))
        
        # Upload in batches of 50 (same as worker)
        BATCH_SIZE = 50
        for i in range(0, len(remaining_events), BATCH_SIZE):
            batch = remaining_events[i:i + BATCH_SIZE]
            
            retry_count = 0
            MAX_RETRIES = 3  # Fewer retries during shutdown
            backoff_delay = 1.0
            
            while retry_count < MAX_RETRIES:
                success = await _upload_batch_to_supabase(batch)
                
                if success:
                    break
                else:
                    retry_count += 1
                    if retry_count < MAX_RETRIES:
                        await asyncio.sleep(backoff_delay)
                        backoff_delay *= 2
            
            if retry_count >= MAX_RETRIES:
                logger.error(
                    "Failed to flush batch of %d events after %d retries",
                    len(batch), MAX_RETRIES
                )
    else:
        logger.info("No events to flush")
    
    logger.info("Log queue flush complete")


async def start_worker() -> None:
    """Start the batch upload worker as a background task."""
    global _worker_task, _shutdown_requested

    from backend.services.ops_kill_switches import telemetry_remote_upload_allowed

    if not telemetry_remote_upload_allowed():
        _shutdown_requested = True
        logger.warning("Telemetry batch upload worker not started because JANUS_TELEMETRY_MODE disables remote upload.")
        return

    # Ensure logging schema is valid before starting worker
    try:
        from backend.services.logging.supabase_client import ensure_logging_schema
        ensure_logging_schema()
        logger.info("Logging schema validation completed")
    except Exception as e:
        logger.warning(f"Schema validation failed (continuing anyway): {e}")

    _shutdown_requested = False
    _worker_task = asyncio.create_task(_batch_upload_worker())
    logger.info("Batch upload worker task started")


async def stop_worker() -> None:
    """Stop the batch upload worker gracefully."""
    global _shutdown_requested, _worker_task
    
    if _worker_task is not None and not _worker_task.done():
        logger.info("Stopping batch upload worker...")
        _shutdown_requested = True
        
        # Wait for worker to finish with timeout
        try:
            await asyncio.wait_for(_worker_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Worker did not stop gracefully, cancelling...")
            _worker_task.cancel()
            try:
                await _worker_task
            except asyncio.CancelledError:
                pass
        
        _worker_task = None
        logger.info("Batch upload worker stopped")
