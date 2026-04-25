"""
Core logging pipeline with async RAM-Queue.
Provides non-blocking event ingestion with thread-safe queue operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from backend.data.schemas_logging import LogEventCreate


# Configure module logger
logger = logging.getLogger(__name__)


# Global async queue for in-memory event buffering
# Max size of 5000 to prevent memory bloat in case of backpressure
_log_queue: asyncio.Queue[LogEventCreate] = asyncio.Queue(maxsize=5000)


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
