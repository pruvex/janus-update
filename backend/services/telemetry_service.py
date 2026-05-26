"""Telemetry Service — Beta-Reporting Implementation.

Provides async feedback submission to Discord webhooks with log attachment
and system metadata collection.
"""

import asyncio
import logging
import os
import platform
from datetime import datetime
from typing import Optional

import aiohttp

from backend.utils.paths import get_app_data_dir
from backend.utils.redaction import redact_sensitive_text
from backend.version import APP_VERSION

logger = logging.getLogger("janus_backend")

# Webhook URL from environment variable. No default webhook is embedded in code.
FEEDBACK_WEBHOOK_URL = os.getenv("FEEDBACK_WEBHOOK_URL", "").strip()

# Log file path in AppData directory (works in both dev and .exe)
LOG_FILE_PATH = os.path.join(get_app_data_dir(), "logs", "janus_backend.log")

# Ensure logs directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)


def _get_system_metadata() -> dict:
    """Collect system metadata for feedback reports."""
    return {
        "os": platform.system(),
        "os_version": platform.release(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "Unknown",
    }


def _read_last_log_lines(lines: int = 200) -> str:
    """Read the last N lines from the log file.
    
    Args:
        lines: Number of lines to read from end of file.
        
    Returns:
        Log content as string, or error message if file not found.
    """
    try:
        if not os.path.exists(LOG_FILE_PATH):
            return f"[Log file not found at {LOG_FILE_PATH}]"
        
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            # Get last N lines
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return redact_sensitive_text("".join(last_lines))
    except Exception as e:
        logger.error("Failed to read log file: %s", e)
        return f"[Error reading log file: {e}]"


def _build_discord_embed(
    feedback_type: str,
    description: str,
    include_logs: bool,
    system_meta: dict,
) -> dict:
    """Build Discord webhook payload with embeds.
    
    Args:
        feedback_type: Type of feedback (bug, feature, etc.)
        description: User description of the feedback
        include_logs: Whether logs were included
        system_meta: System metadata dictionary
        
    Returns:
        Discord webhook payload dictionary.
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Color based on feedback type
    color_map = {
        "bug": 0xFF4444,  # Red
        "feature": 0x44FF44,  # Green
        "feedback": 0x4444FF,  # Blue
        "crash": 0xFF8800,  # Orange
    }
    color = color_map.get(feedback_type.lower(), 0x808080)  # Default gray
    
    embed = {
        "title": f"📝 Beta Feedback: {feedback_type.upper()}",
        "description": redact_sensitive_text(description or "No description provided")[:2000],
        "color": color,
        "timestamp": timestamp,
        "fields": [
            {
                "name": "📦 App Version",
                "value": f"`{APP_VERSION}`",
                "inline": True,
            },
            {
                "name": "💻 OS",
                "value": f"{system_meta['os']} {system_meta['os_version']}",
                "inline": True,
            },
            {
                "name": "🐍 Python",
                "value": f"`{system_meta['python_version']}`",
                "inline": True,
            },
            {
                "name": "🏗️ Architecture",
                "value": f"`{system_meta['architecture']}`",
                "inline": True,
            },
            {
                "name": "📎 Logs Attached",
                "value": "Sanitized" if include_logs else "No",
                "inline": True,
            },
        ],
        "footer": {
            "text": f"Janus Beta Reporter • {timestamp[:10]}"
        },
    }
    
    payload = {
        "embeds": [embed],
    }
    
    return payload


async def send_feedback(
    feedback_type: str,
    description: str,
    include_logs: bool = False,
) -> dict:
    """Send feedback to Discord webhook asynchronously.
    
    This function is non-blocking and will not crash the app if the
    webhook call fails.
    
    Args:
        feedback_type: Type of feedback (bug, feature, crash, etc.)
        description: User's description of the feedback
        include_logs: If True, attaches last 200 lines of log file
        
    Returns:
        Dictionary with success status and message.
    """
    from backend.services.ops_kill_switches import telemetry_remote_upload_allowed

    if not telemetry_remote_upload_allowed():
        logger.warning("[TELEMETRY] Feedback submission skipped by JANUS_TELEMETRY_MODE")
        return {
            "success": False,
            "message": "Telemetry remote upload disabled",
        }

    if not FEEDBACK_WEBHOOK_URL:
        logger.warning("[TELEMETRY] FEEDBACK_WEBHOOK_URL not set, skipping feedback submission")
        return {
            "success": False,
            "message": "Webhook URL not configured",
        }
    
    # Collect system metadata
    system_meta = _get_system_metadata()
    
    # Read logs if requested
    log_content = ""
    if include_logs:
        log_content = _read_last_log_lines(200)
    
    # Build Discord payload
    payload = _build_discord_embed(feedback_type, description, include_logs, system_meta)
    
    # If logs included and not too long, add as a field
    if include_logs and log_content:
        # Discord field value limit is 1024 chars
        log_snippet = log_content[-1000:] if len(log_content) > 1000 else log_content
        payload["embeds"][0]["fields"].append({
            "name": "🪵 Recent Log Entries",
            "value": f"```\n{log_snippet}\n```",
            "inline": False,
        })
    
    # Send asynchronously (non-blocking to caller)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                FEEDBACK_WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (200, 204):
                    logger.info("[TELEMETRY] Feedback sent successfully: %s", feedback_type)
                    return {
                        "success": True,
                        "message": "Feedback submitted successfully",
                    }
                else:
                    error_text = await response.text()
                    logger.warning(
                        "[TELEMETRY] Webhook returned %s: %s",
                        response.status,
                        error_text[:200],
                    )
                    return {
                        "success": False,
                        "message": f"Webhook error: HTTP {response.status}",
                    }
    except asyncio.TimeoutError:
        logger.warning("[TELEMETRY] Feedback submission timed out")
        return {
            "success": False,
            "message": "Request timeout",
        }
    except Exception as e:
        logger.error("[TELEMETRY] Failed to send feedback: %s", e, exc_info=True)
        return {
            "success": False,
            "message": f"Exception: {str(e)}",
        }


def submit_feedback_async(
    feedback_type: str,
    description: str,
    include_logs: bool = False,
) -> None:
    """Fire-and-forget wrapper for send_feedback.
    
    This is the recommended way to submit feedback from synchronous code.
    The call returns immediately and the webhook submission happens in the
    background.
    
    Args:
        feedback_type: Type of feedback
        description: User description
        include_logs: Whether to include recent logs
    """
    try:
        # Create task without awaiting (fire and forget)
        asyncio.create_task(
            send_feedback(feedback_type, description, include_logs)
        )
        logger.info("[TELEMETRY] Feedback submission queued: %s", feedback_type)
    except Exception as e:
        logger.error("[TELEMETRY] Failed to queue feedback: %s", e)
