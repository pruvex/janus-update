"""
Tests for startup telemetry logger module.
"""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from backend.services.telemetry.startup_logger import (
    StartupTelemetryLogger,
    StartupLogBlock,
    PhaseLog,
    IOEventLog
)
from backend.services.telemetry.startup_config import StartupTelemetryConfig


class TestStartupTelemetryLogger:
    """Tests for StartupTelemetryLogger."""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create a temporary log file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    @pytest.fixture
    def enabled_config(self, temp_log_file):
        """Create an enabled configuration for testing."""
        return StartupTelemetryConfig(
            enabled=True,
            log_file_path=temp_log_file,
            max_file_size_bytes=1024,  # Small size for rotation testing
            max_backup_files=3
        )
    
    @pytest.fixture
    def disabled_config(self):
        """Create a disabled configuration for testing."""
        return StartupTelemetryConfig(
            enabled=False,
            log_file_path="",
            max_file_size_bytes=0,
            max_backup_files=0
        )
    
    def test_logger_initialization(self, enabled_config):
        """Test logger initialization with enabled config."""
        logger = StartupTelemetryLogger(enabled_config)
        assert logger.enabled is True
        assert logger.log_file_path == enabled_config.log_file_path
        assert logger._current_run_id is None
        assert logger._run_start_time is None
    
    def test_logger_initialization_disabled(self, disabled_config):
        """Test logger initialization with disabled config."""
        logger = StartupTelemetryLogger(disabled_config)
        assert logger.enabled is False
    
    def test_start_run(self, enabled_config):
        """Test starting a new run."""
        logger = StartupTelemetryLogger(enabled_config)
        run_id = logger.start_run()
        
        assert run_id is not None
        assert len(run_id) > 0
        assert logger._current_run_id == run_id
        assert logger._run_start_time is not None
    
    def test_start_run_disabled(self, disabled_config):
        """Test starting a run when logger is disabled."""
        logger = StartupTelemetryLogger(disabled_config)
        run_id = logger.start_run()
        
        assert run_id == ""
        assert logger._current_run_id is None
    
    def test_log_phase(self, enabled_config):
        """Test logging a phase."""
        logger = StartupTelemetryLogger(enabled_config)
        logger.start_run()
        
        logger.log_phase("initialization", 150.5, {"key": "value"})
        
        assert len(logger._phases) == 1
        assert logger._phases[0].name == "initialization"
        assert logger._phases[0].duration_ms == 150.5
        assert logger._phases[0].metadata == {"key": "value"}
    
    def test_log_phase_disabled(self, disabled_config):
        """Test logging a phase when logger is disabled."""
        logger = StartupTelemetryLogger(disabled_config)
        logger.start_run()
        
        logger.log_phase("initialization", 150.5)
        
        assert len(logger._phases) == 0
    
    def test_log_io_event(self, enabled_config):
        """Test logging an IO event."""
        logger = StartupTelemetryLogger(enabled_config)
        logger.start_run()
        
        logger.log_io_event("read", "/path/to/file", 50.2)
        
        assert len(logger._io_events) == 1
        assert logger._io_events[0].event_type == "read"
        assert logger._io_events[0].path == "/path/to/file"
        assert logger._io_events[0].duration_ms == 50.2
    
    def test_log_io_event_disabled(self, disabled_config):
        """Test logging an IO event when logger is disabled."""
        logger = StartupTelemetryLogger(disabled_config)
        logger.start_run()
        
        logger.log_io_event("read", "/path/to/file", 50.2)
        
        assert len(logger._io_events) == 0
    
    def test_end_run_success(self, enabled_config, temp_log_file):
        """Test ending a run successfully."""
        logger = StartupTelemetryLogger(enabled_config)
        logger.start_run()
        logger.log_phase("initialization", 150.5)
        logger.log_io_event("read", "/path/to/file", 50.2)
        
        logger.end_run(success=True)
        
        # Verify log file was written
        assert os.path.exists(temp_log_file)
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            log_block = json.loads(content)
            
            assert log_block["success"] is True
            assert log_block["run_id"] is not None
            assert len(log_block["phases"]) == 1
            assert len(log_block["io_events"]) == 1
            assert log_block["total_duration_ms"] >= 0  # Can be 0 in fast tests
    
    def test_end_run_failure(self, enabled_config, temp_log_file):
        """Test ending a run with failure."""
        logger = StartupTelemetryLogger(enabled_config)
        logger.start_run()
        
        logger.end_run(success=False, error_message="Test error")
        
        with open(temp_log_file, 'r') as f:
            content = f.read()
            log_block = json.loads(content)
            
            assert log_block["success"] is False
            assert log_block["error_message"] == "Test error"
    
    def test_end_run_without_start(self, enabled_config, temp_log_file):
        """Test ending a run without starting it."""
        logger = StartupTelemetryLogger(enabled_config)
        
        logger.end_run(success=True)
        
        # Should not write to file (file should be empty since fixture creates it)
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert content == ""  # File should be empty
    
    def test_log_rotation(self, enabled_config, temp_log_file):
        """Test log rotation when file size exceeds limit."""
        logger = StartupTelemetryLogger(enabled_config)
        
        # Write initial content to exceed size limit
        with open(temp_log_file, 'w') as f:
            f.write("x" * 2000)  # Exceeds 1024 byte limit
        
        logger.start_run()
        logger.log_phase("test", 100.0)
        logger.end_run(success=True)
        
        # Verify backup file was created
        log_dir = os.path.dirname(temp_log_file)
        log_name = os.path.basename(temp_log_file)
        backup_files = [f for f in os.listdir(log_dir) if f.startswith(log_name + ".")]
        
        assert len(backup_files) >= 1
    
    def test_logging_disabled_on_error(self, enabled_config, temp_log_file):
        """Test that logging is disabled on file errors."""
        import platform as plt
        
        # Skip on Windows as path handling differs
        if plt.system() == "Windows":
            pytest.skip("Error handling test skipped on Windows")
        
        logger = StartupTelemetryLogger(enabled_config)
        
        # Simulate error by making parent directory non-existent
        logger.log_file_path = "/nonexistent/path/log.log"
        
        logger.start_run()
        logger.log_phase("test", 100.0)
        logger.end_run(success=True)
        
        # Logging should be disabled
        assert logger._logging_disabled is True


class TestPhaseLog:
    """Tests for PhaseLog dataclass."""
    
    def test_phase_log_creation(self):
        """Test creating a PhaseLog."""
        phase = PhaseLog(name="test", duration_ms=100.0, metadata={"key": "value"})
        assert phase.name == "test"
        assert phase.duration_ms == 100.0
        assert phase.metadata == {"key": "value"}


class TestIOEventLog:
    """Tests for IOEventLog dataclass."""
    
    def test_io_event_log_creation(self):
        """Test creating an IOEventLog."""
        event = IOEventLog(event_type="read", path="/path", duration_ms=50.0)
        assert event.event_type == "read"
        assert event.path == "/path"
        assert event.duration_ms == 50.0


class TestStartupLogBlock:
    """Tests for StartupLogBlock dataclass."""
    
    def test_startup_log_block_creation(self):
        """Test creating a StartupLogBlock."""
        block = StartupLogBlock(
            run_id="test-id",
            timestamp="2024-01-01T00:00:00Z",
            total_duration_ms=1000.0,
            success=True
        )
        assert block.run_id == "test-id"
        assert block.success is True
        assert len(block.phases) == 0
