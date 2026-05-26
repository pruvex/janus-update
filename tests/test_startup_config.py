"""
Tests for startup telemetry configuration module.
"""

import os
import pytest
from backend.services.telemetry.startup_config import (
    is_dev_context,
    get_documents_folder_path,
    get_startup_telemetry_config,
    StartupTelemetryConfig
)


class TestDevContextDetection:
    """Tests for dev context detection."""
    
    def test_dev_context_with_janus_dev_mode_true(self, monkeypatch):
        """Test dev context detection with JANUS_DEV_MODE=true."""
        monkeypatch.setenv("JANUS_DEV_MODE", "true")
        assert is_dev_context() is True
    
    def test_dev_context_with_janus_dev_mode_false(self, monkeypatch):
        """Test dev context detection with JANUS_DEV_MODE=false."""
        monkeypatch.setenv("JANUS_DEV_MODE", "false")
        assert is_dev_context() is False
    
    def test_dev_context_with_node_env_development(self, monkeypatch):
        """Test dev context detection with NODE_ENV=development."""
        monkeypatch.delenv("JANUS_DEV_MODE", raising=False)
        monkeypatch.setenv("NODE_ENV", "development")
        assert is_dev_context() is True
    
    def test_dev_context_with_node_env_production(self, monkeypatch):
        """Test dev context detection with NODE_ENV=production."""
        monkeypatch.delenv("JANUS_DEV_MODE", raising=False)
        monkeypatch.setenv("NODE_ENV", "production")
        assert is_dev_context() is False
    
    def test_dev_context_without_env_vars(self, monkeypatch):
        """Test dev context detection without environment variables."""
        monkeypatch.delenv("JANUS_DEV_MODE", raising=False)
        monkeypatch.delenv("NODE_ENV", raising=False)
        assert is_dev_context() is False


class TestDocumentsFolderPath:
    """Tests for documents folder path resolution."""
    
    def test_documents_folder_path_exists(self):
        """Test that documents folder path is returned."""
        path = get_documents_folder_path()
        assert isinstance(path, str)
        assert len(path) > 0
        # Path should contain "Documents" (production fallback) or "documentation" (dev path)
        assert "Documents" in path or "documents" in path.lower() or "documentation" in path.lower()
    
    def test_documents_folder_path_is_absolute(self):
        """Test that documents folder path is absolute."""
        path = get_documents_folder_path()
        assert os.path.isabs(path)


class TestStartupTelemetryConfig:
    """Tests for startup telemetry configuration."""
    
    def test_config_with_dev_context_enabled(self, monkeypatch):
        """Test configuration when dev context is enabled."""
        monkeypatch.setenv("JANUS_DEV_MODE", "true")
        
        config = get_startup_telemetry_config()
        
        assert isinstance(config, StartupTelemetryConfig)
        assert config.enabled is True
        assert config.log_file_path.endswith("janus_startup_telemetry.log")
        assert config.max_file_size_bytes == 10 * 1024 * 1024  # 10 MB
        assert config.max_backup_files == 5
    
    def test_config_with_dev_context_disabled(self, monkeypatch):
        """Test configuration when dev context is disabled."""
        monkeypatch.delenv("JANUS_DEV_MODE", raising=False)
        monkeypatch.delenv("NODE_ENV", raising=False)
        
        config = get_startup_telemetry_config()
        
        assert isinstance(config, StartupTelemetryConfig)
        assert config.enabled is False
        assert config.log_file_path == ""
        assert config.max_file_size_bytes == 0
    
    def test_config_with_custom_parameters(self, monkeypatch):
        """Test configuration with custom parameters."""
        monkeypatch.setenv("JANUS_DEV_MODE", "true")
        
        config = get_startup_telemetry_config(
            log_file_name="custom_log.log",
            max_file_size_mb=20,
            max_backup_files=10
        )
        
        assert config.enabled is True
        assert config.log_file_path.endswith("custom_log.log")
        assert config.max_file_size_bytes == 20 * 1024 * 1024  # 20 MB
        assert config.max_backup_files == 10
    
    def test_config_contains_all_required_fields(self, monkeypatch):
        """Test that configuration contains all required fields."""
        monkeypatch.setenv("JANUS_DEV_MODE", "true")
        
        config = get_startup_telemetry_config()
        
        assert hasattr(config, "enabled")
        assert hasattr(config, "log_file_path")
        assert hasattr(config, "max_file_size_bytes")
        assert hasattr(config, "max_backup_files")
