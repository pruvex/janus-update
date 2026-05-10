"""
Startup Telemetry Logger Module

Provides structured logging for startup phases and IO events with error handling and log rotation.
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from .startup_config import StartupTelemetryConfig


@dataclass
class PhaseLog:
    """Represents a logged phase."""
    name: str
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IOEventLog:
    """Represents a logged IO event."""
    event_type: str
    path: str
    duration_ms: float


@dataclass
class StartupLogBlock:
    """Represents a complete startup log block."""
    run_id: str
    timestamp: str
    total_duration_ms: float
    phases: List[Dict[str, Any]] = field(default_factory=list)
    io_events: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class StartupTelemetryLogger:
    """
    Logger for startup telemetry with structured logging, error handling, and log rotation.
    """
    
    def __init__(self, config: StartupTelemetryConfig):
        """
        Initialize the logger with configuration.
        
        Args:
            config: StartupTelemetryConfig instance
        """
        self.config = config
        self.enabled = config.enabled
        self.log_file_path = config.log_file_path
        self.max_file_size_bytes = config.max_file_size_bytes
        self.max_backup_files = config.max_backup_files
        
        self._current_run_id: Optional[str] = None
        self._run_start_time: Optional[float] = None
        self._phases: List[PhaseLog] = []
        self._io_events: List[IOEventLog] = []
        self._logging_disabled: bool = False
    
    def start_run(self) -> str:
        """
        Start a new startup run.
        
        Returns:
            str: Unique run ID for this startup
        """
        if not self.enabled or self._logging_disabled:
            return ""
        
        self._current_run_id = str(uuid.uuid4())
        self._run_start_time = time.time()
        self._phases = []
        self._io_events = []
        
        return self._current_run_id
    
    def log_phase(self, phase_name: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a phase with duration and metadata.
        
        Args:
            phase_name: Name of the phase
            duration_ms: Duration of the phase in milliseconds
            metadata: Optional metadata dictionary
        """
        if not self.enabled or self._logging_disabled:
            return
        
        phase = PhaseLog(
            name=phase_name,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self._phases.append(phase)
    
    def log_io_event(self, event_type: str, path: str, duration_ms: float):
        """
        Log an IO event.
        
        Args:
            event_type: Type of IO event (e.g., "read", "write", "delete")
            path: File or directory path
            duration_ms: Duration of the IO operation in milliseconds
        """
        if not self.enabled or self._logging_disabled:
            return
        
        io_event = IOEventLog(
            event_type=event_type,
            path=path,
            duration_ms=duration_ms
        )
        self._io_events.append(io_event)
    
    def end_run(self, success: bool = True, error_message: Optional[str] = None):
        """
        End the current run and write the log block.
        
        Args:
            success: Whether the startup completed successfully
            error_message: Optional error message if startup failed
        """
        if not self.enabled or self._logging_disabled:
            return
        
        if self._current_run_id is None or self._run_start_time is None:
            return
        
        total_duration_ms = (time.time() - self._run_start_time) * 1000
        
        log_block = StartupLogBlock(
            run_id=self._current_run_id or "",
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_duration_ms=total_duration_ms,
            phases=[asdict(phase) for phase in self._phases],
            io_events=[asdict(event) for event in self._io_events],
            success=success,
            error_message=error_message
        )
        
        self._write_log_block(log_block)
        
        # Reset state
        self._current_run_id = None
        self._run_start_time = None
        self._phases = []
        self._io_events = []
    
    def _write_log_block(self, log_block: StartupLogBlock):
        """
        Write the log block to the log file with rotation.
        
        Args:
            log_block: StartupLogBlock to write
        """
        try:
            # Ensure directory exists
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except (OSError, PermissionError) as e:
                    self._logging_disabled = True
                    print(f"[Startup Telemetry] Failed to create log directory: {e}")
                    return
            
            # Check file size and rotate if needed
            if os.path.exists(self.log_file_path):
                try:
                    file_size = os.path.getsize(self.log_file_path)
                    if file_size >= self.max_file_size_bytes:
                        self._rotate_log_file()
                except (OSError, PermissionError) as e:
                    self._logging_disabled = True
                    print(f"[Startup Telemetry] Failed to check file size: {e}")
                    return
            
            # Write log block
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(log_block), ensure_ascii=False) + "\n")
                
        except (OSError, PermissionError, IOError) as e:
            self._logging_disabled = True
            print(f"[Startup Telemetry] Failed to write log block: {e}")
        except Exception as e:
            self._logging_disabled = True
            print(f"[Startup Telemetry] Unexpected error writing log: {e}")
    
    def _rotate_log_file(self):
        """
        Rotate the log file by renaming with timestamp and cleaning up old backups.
        """
        try:
            # Generate timestamp for backup filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            log_dir = os.path.dirname(self.log_file_path)
            log_name = os.path.basename(self.log_file_path)
            backup_name = f"{log_name}.{timestamp}"
            backup_path = os.path.join(log_dir, backup_name)
            
            # Rename current file to backup
            if os.path.exists(self.log_file_path):
                os.rename(self.log_file_path, backup_path)
            
            # Clean up old backup files
            self._cleanup_old_backups(log_dir, log_name)
            
        except (OSError, PermissionError) as e:
            self._logging_disabled = True
            print(f"[Startup Telemetry] Failed to rotate log file: {e}")
    
    def _cleanup_old_backups(self, log_dir: str, log_name: str):
        """
        Clean up old backup files, keeping only max_backup_files.
        
        Args:
            log_dir: Directory containing log files
            log_name: Base name of the log file
        """
        try:
            # List all backup files
            backup_pattern = f"{log_name}."
            backup_files = []
            
            for filename in os.listdir(log_dir):
                if filename.startswith(backup_pattern) and filename != log_name:
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: x[1])
            
            # Delete oldest files if we have too many
            while len(backup_files) >= self.max_backup_files:
                oldest_file, _ = backup_files.pop(0)
                try:
                    os.remove(oldest_file)
                except OSError as e:
                    print(f"[Startup Telemetry] Failed to delete old backup: {e}")
                    
        except (OSError, PermissionError) as e:
            print(f"[Startup Telemetry] Failed to cleanup old backups: {e}")
