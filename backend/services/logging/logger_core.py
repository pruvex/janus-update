"""
Core logging pipeline with async RAM-Queue.
Provides non-blocking event ingestion with thread-safe queue operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, List

from backend.data.schemas_logging import LogEventCreate, LogEvent
from backend.services.logging.supabase_client import get_supabase_client


# Configure module logger
logger = logging.getLogger(__name__)


# Global async queue for in-memory event buffering
# Max size of 5000 to prevent memory bloat in case of backpressure
_log_queue: asyncio.Queue[LogEventCreate] = asyncio.Queue(maxsize=5000)

# Worker task reference for graceful shutdown
_worker_task: Optional[asyncio.Task] = None

# Shutdown flag to signal worker to stop
_shutdown_requested: bool = False


async def log_event(event: LogEventCreate) -> None:
    """
    Asynchronously add a log event to the in-memory queue.
    
    This function is non-blocking and designed for high-throughput scenarios.
    Events are enriched with a current timestamp if not already provided.
    
    Args:
        event: The log event to be queued. If timestamp is None, it will be
               set to the current UTC time.
               
    Raises:
        asyncio.QueueFull: If the queue is full (5000 events). This is a
                          backpressure signal that the consumer cannot keep up.
    """
    # Enrich with current timestamp if not provided
    if event.timestamp is None:
        event.timestamp = datetime.utcnow()
    
    # Add to queue - this will block only if queue is full
    await _log_queue.put(event)
    
    # Debug logging for monitoring queue size
    current_size = _log_queue.qsize()
    logger.debug("Event added to queue. Current size: %d / 5000", current_size)


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
    Upload a batch of events to Supabase.
    
    Args:
        events: List of events to upload.
        
    Returns:
        bool: True if upload succeeded, False otherwise.
    """
    try:
        client = get_supabase_client()
        
        # Convert LogEventCreate to dict for Supabase
        events_data = []
        for event in events:
            event_dict = {
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "session_id": event.session_id,
                "provider": event.provider,
                "model": event.model,
                "skill": event.skill,
                "event_type": event.event_type,
                "status": event.status,
                "payload": event.payload,
                "latency_ms": event.latency_ms
            }
            events_data.append(event_dict)
        
        # Batch insert
        response = client.table("logs_raw").insert(events_data).execute()
        
        if response.data:
            logger.info("Successfully uploaded %d events to Supabase", len(events))
            return True
        else:
            logger.error("Supabase returned no data for batch insert of %d events", len(events))
            return False
            
    except Exception as e:
        logger.error("Failed to upload batch to Supabase: %s", str(e))
        return False


async def _batch_upload_worker() -> None:
    """
    Background worker that processes events from the queue in batches.
    
    Batches are uploaded when either:
    - 50 events are collected, OR
    - 2 seconds have passed since the first event in the batch
    
    Uses exponential backoff on upload failures (events stay in queue).
    """
    global _shutdown_requested
    
    BATCH_SIZE = 50
    BATCH_TIMEOUT = 2.0  # seconds
    MAX_RETRIES = 5
    
    logger.info("Batch upload worker started")
    
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
                    # Timeout reached, process current batch
                    break
            
            # Skip if no events collected
            if not batch:
                continue
            
            logger.debug("Collected batch of %d events", len(batch))
            
            # Upload with exponential backoff
            retry_count = 0
            backoff_delay = 1.0  # Start with 1 second
            
            while retry_count < MAX_RETRIES and not _shutdown_requested:
                success = await _upload_batch_to_supabase(batch)
                
                if success:
                    # Upload succeeded, events are removed from queue (already got them)
                    retry_count = 0
                    break
                else:
                    # Upload failed, put events back in queue
                    logger.warning(
                        "Upload failed (attempt %d/%d). Retrying in %.1fs...",
                        retry_count + 1, MAX_RETRIES, backoff_delay
                    )
                    
                    # Put events back in queue (at the front)
                    for event in reversed(batch):
                        _log_queue.put_nowait(event)
                    
                    retry_count += 1
                    
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
                # Events are already back in queue
                
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
