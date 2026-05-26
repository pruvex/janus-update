"""
Startup Telemetry Configuration Module

Provides dev-context detection and configuration for startup telemetry logging.
"""

import os
import platform
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class StartupTelemetryConfig:
    """Configuration object for startup telemetry logging."""
    
    enabled: bool
    log_file_path: str
    max_file_size_bytes: int
    max_backup_files: int


def is_dev_context() -> bool:
    """
    Detect if running in development context.
    
    Checks for JANUS_DEV_MODE environment variable or NODE_ENV.
    
    Returns:
        bool: True if in dev context, False otherwise
    """
    # Check for explicit dev mode flag
    if os.getenv("JANUS_DEV_MODE", "").lower() == "true":
        return True
    
    # Check for NODE_ENV (common in Electron/node environments)
    if os.getenv("NODE_ENV", "").lower() == "development":
        return True
    
    return False


def get_documents_folder_path() -> str:
    """
    Get custom log directory path based on environment.

    Returns:
        str: Path to the custom log directory
    """
    # Check if we're in production (packaged) or development
    is_production = os.getenv("JANUS_PRODUCTION", "").lower() == "true"

    if is_production:
        # Production: AppData\Roaming\Janus Projekt\logs
        appdata_roaming = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        prod_log_dir = os.path.join(appdata_roaming, "Janus Projekt", "logs")

        # Ensure directory exists
        if not os.path.exists(prod_log_dir):
            try:
                os.makedirs(prod_log_dir, exist_ok=True)
            except (OSError, PermissionError):
                # Fallback to documents folder
                system = platform.system()
                if system == "Windows":
                    return os.path.join(os.path.expanduser("~"), "Documents")
                elif system == "Darwin":
                    return os.path.join(os.path.expanduser("~"), "Documents")
                else:
                    return os.path.join(os.path.expanduser("~"), "Documents")

        return prod_log_dir
    else:
        # Development: C:\KI\Janus-Projekt\documentation\Startup log
        dev_log_dir = r"C:\KI\Janus-Projekt\documentation\Startup log"

        # Ensure directory exists
        if not os.path.exists(dev_log_dir):
            try:
                os.makedirs(dev_log_dir, exist_ok=True)
            except (OSError, PermissionError):
                # Fallback to documents folder
                system = platform.system()
                if system == "Windows":
                    return os.path.join(os.path.expanduser("~"), "Documents")
                elif system == "Darwin":
                    return os.path.join(os.path.expanduser("~"), "Documents")
                else:
                    return os.path.join(os.path.expanduser("~"), "Documents")

        return dev_log_dir


def get_startup_telemetry_config(
    log_file_name: str = "janus_startup_telemetry.log",
    max_file_size_mb: int = 10,
    max_backup_files: int = 5
) -> StartupTelemetryConfig:
    """
    Get startup telemetry configuration.

    Args:
        log_file_name: Name of the log file (default: janus_startup_telemetry.log)
        max_file_size_mb: Maximum file size in MB before rotation (default: 10)
        max_backup_files: Number of backup files to keep (default: 5)

    Returns:
        StartupTelemetryConfig: Configuration object
    """
    enabled = is_dev_context()

    log_file_path = ""
    max_file_size_bytes = 0

    if enabled:
        try:
            docs_path = get_documents_folder_path()
            log_file_path = os.path.join(docs_path, log_file_name)
            max_file_size_bytes = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        except Exception as e:
            print(f'[Startup Telemetry] Failed to get documents path: {e}')
            # Fall back to disabled state

    return StartupTelemetryConfig(
        enabled=enabled,
        log_file_path=log_file_path,
        max_file_size_bytes=max_file_size_bytes,
        max_backup_files=max_backup_files
    )


def write_telemetry_marker(marker_name: str, metadata: dict = None):
    """
    Write a telemetry marker to the log file.
    Used for cross-process synchronization between backend and electron.

    Args:
        marker_name: Name of the marker (e.g., "backend_startup_start", "backend_ready")
        metadata: Optional metadata dictionary
    """
    if not is_dev_context():
        return

    try:
        config = get_startup_telemetry_config()
        if not config.enabled or not config.log_file_path:
            return

        marker = {
            "marker": marker_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
        }

        # Ensure directory exists
        log_dir = os.path.dirname(config.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Write marker
        with open(config.log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(marker, ensure_ascii=False) + "\n")

    except Exception as e:
        print(f'[Startup Telemetry] Failed to write marker {marker_name}: {e}')
