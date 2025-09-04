import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.tool_registry import TOOL_REGISTRY
from backend import filesystem_manager
from backend.llm_gateway import reason_and_respond # Import the function directly
from pathlib import Path
import json
import os

# Mock the get_app_data_dir for filesystem_manager during tests
class TestLLMIntegrationFilesystem:

    @pytest.fixture(autouse=True)
    def setup_fake_filesystem(self, fs, monkeypatch):
        # Use monkeypatch to mock get_app_data_dir
        monkeypatch.setattr('backend.filesystem_manager.get_app_data_dir', lambda: '/fake_app_data')
        # Mock Path.home() to return a path within the fake filesystem
        fake_home_dir = Path('/fake_home')
        fs.create_dir(fake_home_dir) # Create the fake home directory
        monkeypatch.setattr(Path, 'home', lambda: fake_home_dir) # Mock Path.home()

        self.fake_app_data_dir = Path('/fake_app_data')
        self.fake_app_data_dir.mkdir(parents=True, exist_ok=True)

        self.default_workspace = self.fake_app_data_dir / "workspace"
        self.default_workspace.mkdir(parents=True, exist_ok=True)

        # Explicitly create the fake Desktop directory within the fake home
        self.fake_desktop_dir = fake_home_dir / "Desktop" # Use fake_home_dir
        self.fake_desktop_dir.mkdir(parents=True, exist_ok=True)

        config_data = {
            "filesystem_workspaces": [
                str(self.default_workspace),
                str(self.fake_desktop_dir)
            ]
        }
        config_file = self.fake_app_data_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Mock _get_allowed_workspaces to return our controlled list of fake paths
        monkeypatch.setattr('backend.filesystem_manager._get_allowed_workspaces', lambda: [
            self.default_workspace.resolve(),
            self.fake_desktop_dir.resolve()
        ])
        
        # Mock DEFAULT_WORKSPACE directly
        monkeypatch.setattr('backend.filesystem_manager.DEFAULT_WORKSPACE', self.default_workspace)

        # Re-initialize ALLOWED_WORKSPACES in filesystem_manager
        # This will now call our mocked _get_allowed_workspaces
        filesystem_manager.ALLOWED_WORKSPACES = filesystem_manager._get_allowed_workspaces()

    @pytest.mark.asyncio
    async def test_llm_calls_create_file_tool(self, setup_fake_filesystem):
        # Simulate LLM suggesting to call create_file_tool
        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "create_file_tool",
            "tool_args": {"path": str(self.default_workspace / "llm_test_file.txt"), "content": "LLM created this."}, "usage": {}, # Mock usage/cost data
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            # Patch the actual tool function to observe its call
            with patch.object(filesystem_manager, 'create_file', wraps=filesystem_manager.create_file) as mock_create_file:
                # Call the function that would normally interact with the LLM
                # In a real scenario, this would be part of your main application logic
                # For testing, we directly call reason_and_respond and then process its output
                
                # Simulate the tool execution logic that would happen after reason_and_respond
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                
                # Execute the tool function with the mocked arguments
                # Note: Some tool functions might require additional arguments like 'db' or 'api_key'
                # For filesystem tools, they typically only need the arguments from tool_args
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_create_file.assert_called_once_with(str(self.default_workspace / "llm_test_file.txt"), "LLM created this.")
                assert "Datei '" + str(self.default_workspace / "llm_test_file.txt") + "' wurde erfolgreich erstellt." in tool_result["output"]
                assert (self.default_workspace / "llm_test_file.txt").exists()
                assert (self.default_workspace / "llm_test_file.txt").read_text() == "LLM created this."

    @pytest.mark.asyncio
    async def test_llm_calls_read_file_tool(self, setup_fake_filesystem):
        test_file = self.default_workspace / "read_by_llm.txt"
        test_file.write_text("Content to be read by LLM.")

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "read_file_tool",
            "tool_args": {"path": str(test_file)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'read_file', wraps=filesystem_manager.read_file) as mock_read_file:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_read_file.assert_called_once_with(str(test_file))
                assert "Inhalt von '" + str(test_file) + "':\n---\nContent to be read by LLM.\n---" in tool_result["output"]

    @pytest.mark.asyncio
    async def test_llm_calls_list_directory_tool(self, setup_fake_filesystem):
        (self.default_workspace / "dir_for_llm").mkdir()
        (self.default_workspace / "file_in_llm_dir.txt").write_text("content")

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "list_directory_tool",
            "tool_args": {"path": str(self.default_workspace)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'list_directory', wraps=filesystem_manager.list_directory) as mock_list_directory:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_list_directory.assert_called_once_with(str(self.default_workspace), None)
                assert "dir_for_llm/" in tool_result["output"]
                assert "file_in_llm_dir.txt" in tool_result["output"]

    @pytest.mark.asyncio
    async def test_llm_calls_delete_file_tool(self, setup_fake_filesystem):
        file_to_delete = self.default_workspace / "delete_me_llm.txt"
        file_to_delete.write_text("content")

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "delete_file_tool",
            "tool_args": {"path": str(file_to_delete)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'delete_file', wraps=filesystem_manager.delete_file) as mock_delete_file:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_delete_file.assert_called_once_with(str(file_to_delete))
                assert "Datei '" + str(file_to_delete) + "' wurde erfolgreich gelöscht." in tool_result["output"]
                assert not file_to_delete.exists()

    @pytest.mark.asyncio
    async def test_llm_calls_create_directory_tool(self, setup_fake_filesystem):
        dir_to_create = self.default_workspace / "new_dir_llm"

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "create_directory_tool",
            "tool_args": {"path": str(dir_to_create)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'create_directory', wraps=filesystem_manager.create_directory) as mock_create_directory:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_create_directory.assert_called_once_with(str(dir_to_create))
                assert "Ordner '" + str(dir_to_create) + "' wurde erfolgreich erstellt." in tool_result["output"]
                assert dir_to_create.is_dir()

    @pytest.mark.asyncio
    async def test_llm_calls_delete_directory_tool(self, setup_fake_filesystem):
        dir_to_delete = self.default_workspace / "dir_to_delete_llm"
        dir_to_delete.mkdir()

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "delete_directory_tool",
            "tool_args": {"path": str(dir_to_delete)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'delete_directory', wraps=filesystem_manager.delete_directory) as mock_delete_directory:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_delete_directory.assert_called_once_with(str(dir_to_delete))
                assert "Ordner '" + str(dir_to_delete) + "' und sein Inhalt wurden gelöscht." in tool_result["output"]
                assert not dir_to_delete.exists()

    @pytest.mark.asyncio
    async def test_llm_calls_move_file_tool(self, setup_fake_filesystem):
        source_file = self.default_workspace / "source_llm.txt"
        source_file.write_text("content")
        destination_file = self.default_workspace / "destination_llm.txt"

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "move_file_tool",
            "tool_args": {"source_path": str(source_file), "destination_path": str(destination_file)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'move_file', wraps=filesystem_manager.move_file) as mock_move_file:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_move_file.assert_called_once_with(str(source_file), str(destination_file))
                assert "'" + str(source_file) + "' wurde erfolgreich nach '" + str(destination_file) + "' verschoben/umbenannt." in tool_result["output"]
                assert not source_file.exists()
                assert destination_file.exists()

    @pytest.mark.asyncio
    async def test_llm_calls_rename_file_tool(self, setup_fake_filesystem):
        old_name = self.default_workspace / "old_name_llm.txt"
        old_name.write_text("content")
        new_name = self.default_workspace / "new_name_llm.txt"

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "rename_file_tool",
            "tool_args": {"old_path": str(old_name), "new_path": str(new_name)},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'rename_file', wraps=filesystem_manager.rename_file) as mock_rename_file:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_rename_file.assert_called_once_with(str(old_name), str(new_name))
                assert "'" + str(old_name) + "' wurde erfolgreich nach '" + str(new_name) + "' verschoben/umbenannt." in tool_result["output"]
                assert not old_name.exists()
                assert new_name.exists()

    @pytest.mark.asyncio
    async def test_llm_calls_move_files_tool(self, setup_fake_filesystem):
        source_dir = self.default_workspace / "source_move_files_llm"
        dest_dir = self.default_workspace / "dest_move_files_llm"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("1")
        (source_dir / "file2.log").write_text("2")
        (source_dir / "file3.txt").write_text("3")

        mock_reason_and_respond_return = {
            "type": "tool_code",
            "tool_name": "move_files_tool",
            "tool_args": {"source_directory": str(source_dir), "destination_directory": str(dest_dir), "pattern": "*.txt"},
            "usage": {},
            "cost": {}
        }

        with patch('backend.llm_gateway.reason_and_respond', new_callable=AsyncMock) as mock_reason_and_respond:
            mock_reason_and_respond.return_value = mock_reason_and_respond_return
            
            with patch.object(filesystem_manager, 'move_files', wraps=filesystem_manager.move_files) as mock_move_files:
                tool_info = mock_reason_and_respond_return
                tool_func = TOOL_REGISTRY[tool_info["tool_name"]].func
                tool_result = tool_func(**tool_info["tool_args"])
                
                mock_move_files.assert_called_once_with(str(source_dir), str(dest_dir), "*.txt")
                assert "Alle 2 Dateien passend zu '*.txt' wurden erfolgreich nach '" + str(dest_dir) + "' verschoben." in tool_result["output"]
                assert (dest_dir / "file1.txt").exists()
                assert (dest_dir / "file3.txt").exists()
                assert not (source_dir / "file1.txt").exists()
                assert not (source_dir / "file3.txt").exists()
                assert (source_dir / "file2.log").exists()