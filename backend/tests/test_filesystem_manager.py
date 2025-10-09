import pytest
from pyfakefs.fake_filesystem_unittest import TestCase
import os
import shutil
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

# Assuming filesystem_manager is in the same directory or accessible via PYTHONPATH
from backend.services import filesystem_manager


class TestFilesystemManager(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

        # Patch get_app_data_dir within setUp
        self.mock_get_app_data_dir = patch(
            "backend.services.filesystem_manager.get_app_data_dir", return_value="/fake_app_data"
        ).start()
        self.addCleanup(patch.stopall)  # Ensure all patches are stopped after the test

        self.fake_app_data_dir = Path("/fake_app_data")
        self.fake_app_data_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.fake_app_data_dir / "config.json"
        self.default_workspace = self.fake_app_data_dir / "workspace"
        self.default_workspace.mkdir(parents=True, exist_ok=True)

        # Explicitly create the fake Desktop directory
        self.fake_desktop_dir = Path(os.path.expanduser("~")) / "Desktop"
        self.fake_desktop_dir.mkdir(parents=True, exist_ok=True)

        config_data = {
            "filesystem_workspaces": [
                str(self.default_workspace),
                str(
                    self.fake_desktop_dir
                ),  # Use the explicitly created fake desktop path
            ]
        }
        with open(self.config_file, "w") as f:
            json.dump(config_data, f)

        # Manually re-initialize ALLOWED_WORKSPACES and DEFAULT_WORKSPACE
        # This is crucial because they are module-level variables initialized on import.
        # We need to ensure they reflect our fake filesystem setup for each test.

        # Mock the _get_allowed_workspaces function to return our controlled list
        self.mock_get_allowed_workspaces = patch(
            "backend.services.filesystem_manager._get_allowed_workspaces",
            return_value=[
                self.default_workspace.resolve(),
                self.fake_desktop_dir.resolve(),  # Use the resolved fake desktop path
            ],
        ).start()
        self.addCleanup(patch.stopall)

        # Re-run the initialization logic in filesystem_manager to pick up the mocked values
        # This is a bit hacky, but necessary for module-level variables.
        # In a real scenario, you might refactor filesystem_manager to allow easier re-initialization.
        filesystem_manager.ALLOWED_WORKSPACES = (
            filesystem_manager._get_allowed_workspaces()
        )
        filesystem_manager.DEFAULT_WORKSPACE = (
            self.default_workspace
        )  # Ensure this points to the fake one

    def test_create_file_success(self):
        file_path = self.default_workspace / "test_file.txt"
        content = "Hello, world!"
        result = filesystem_manager.create_file(str(file_path), content)
        assert "erfolgreich erstellt" in result["output"]
        assert file_path.exists()
        assert file_path.read_text() == content

    def test_create_file_already_exists(self):
        file_path = self.default_workspace / "existing_file.txt"
        file_path.write_text("initial content")
        result = filesystem_manager.create_file(str(file_path), "new content")
        assert "existiert bereits" in result["output"]
        assert file_path.read_text() == "initial content"

    def test_read_file_success(self):
        file_path = self.default_workspace / "read_me.txt"
        content = "This is content to read."
        file_path.write_text(content)
        result = filesystem_manager.read_file(str(file_path))
        assert content in result["output"]

    def test_read_file_not_found(self):
        file_path = self.default_workspace / "non_existent.txt"
        result = filesystem_manager.read_file(str(file_path))
        assert "Fehler: Pfad" in result["output"]
        assert "existiert nicht." in result["output"]

    def test_delete_file_success(self):
        file_path = self.default_workspace / "delete_me.txt"
        file_path.write_text("content")
        result = filesystem_manager.delete_file(str(file_path))
        assert "erfolgreich gelöscht" in result["output"]
        assert not file_path.exists()

    def test_delete_file_not_found(self):
        file_path = self.default_workspace / "non_existent_to_delete.txt"
        result = filesystem_manager.delete_file(str(file_path))
        assert "Fehler: Pfad" in result["output"]
        assert "existiert nicht." in result["output"]

    def test_list_directory_success(self):
        (self.default_workspace / "dir1").mkdir()
        (self.default_workspace / "file1.txt").write_text("content")
        (self.default_workspace / "file2.log").write_text("content")
        result = filesystem_manager.list_directory(str(self.default_workspace))
        assert "dir1/" in result["items"]
        assert "file1.txt" in result["items"]
        assert "file2.log" in result["items"]
        assert result["count"] == 3

    def test_list_directory_with_pattern(self):
        (self.default_workspace / "image1.png").write_text("content")
        (self.default_workspace / "image2.jpg").write_text("content")
        (self.default_workspace / "document.txt").write_text("content")
        result = filesystem_manager.list_directory(
            str(self.default_workspace), pattern="*.png"
        )
        assert "image1.png" in result["items"]
        assert "image2.jpg" not in result["items"]
        assert result["count"] == 1

    def test_create_directory_success(self):
        dir_path = self.default_workspace / "new_dir"
        result = filesystem_manager.create_directory(str(dir_path))
        assert "erfolgreich erstellt" in result["output"]
        assert dir_path.is_dir()

    def test_create_directory_already_exists(self):
        dir_path = self.default_workspace / "existing_dir"
        dir_path.mkdir()
        result = filesystem_manager.create_directory(str(dir_path))
        assert "existiert bereits" in result["output"]

    def test_delete_directory_success(self):
        dir_path = self.default_workspace / "dir_to_delete"
        (dir_path / "sub_file.txt").mkdir(parents=True)
        result = filesystem_manager.delete_directory(str(dir_path))
        assert "gelöscht" in result["output"]
        assert not dir_path.exists()

    def test_delete_directory_not_found(self):
        dir_path = self.default_workspace / "non_existent_dir"
        result = filesystem_manager.delete_directory(str(dir_path))
        assert "Fehler: Pfad" in result["output"]
        assert "existiert nicht." in result["output"]

    def test_delete_directory_workspace_root_protected(self):
        result = filesystem_manager.delete_directory(str(self.default_workspace))
        assert (
            "Fehler: Ein Workspace-Stammverzeichnis darf nicht gelöscht werden."
            in result["output"]
        )
        assert self.default_workspace.exists()

    def test_move_file_success(self):
        source_file = self.default_workspace / "source.txt"
        source_file.write_text("content")
        destination_file = self.default_workspace / "destination.txt"
        result = filesystem_manager.move_file(str(source_file), str(destination_file))
        assert "erfolgreich nach" in result["output"]
        assert not source_file.exists()
        assert destination_file.exists()
        assert destination_file.read_text() == "content"

    def test_rename_file_success(self):
        old_name = self.default_workspace / "old_name.txt"
        old_name.write_text("content")
        new_name = self.default_workspace / "new_name.txt"
        result = filesystem_manager.rename_file(str(old_name), str(new_name))
        assert "erfolgreich nach" in result["output"]
        assert not old_name.exists()
        assert new_name.exists()
        assert new_name.read_text() == "content"

    def test_move_file_destination_exists(self):
        source_file = self.default_workspace / "source_exists.txt"
        source_file.write_text("source content")
        destination_file = self.default_workspace / "dest_exists.txt"
        destination_file.write_text("destination content")
        result = filesystem_manager.move_file(str(source_file), str(destination_file))
        assert "existiert bereits" in result["output"]
        assert source_file.exists()
        assert destination_file.read_text() == "destination content"

    def test_move_files_success(self):
        source_dir = self.default_workspace / "source_move_files"
        dest_dir = self.default_workspace / "dest_move_files"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("1")
        (source_dir / "file2.log").write_text("2")
        (source_dir / "file3.txt").write_text("3")

        result = filesystem_manager.move_files(str(source_dir), str(dest_dir), "*.txt")
        assert "Alle 2 Dateien" in result["output"]
        assert (dest_dir / "file1.txt").exists()
        assert (dest_dir / "file3.txt").exists()
        assert not (source_dir / "file1.txt").exists()
        assert not (source_dir / "file3.txt").exists()
        assert (source_dir / "file2.log").exists()
        assert result["moved_count"] == 2

    def test_move_files_no_match(self):
        source_dir = self.default_workspace / "source_no_match"
        dest_dir = self.default_workspace / "dest_no_match"
        source_dir.mkdir()
        (source_dir / "file1.log").write_text("1")
        result = filesystem_manager.move_files(str(source_dir), str(dest_dir), "*.txt")
        assert "Keine Dateien passend zum Muster" in result["output"]
        # The destination directory is created even if no files match, so no assertion for its non-existence.

    def test_resolve_and_validate_path_absolute_allowed(self):
        test_path = self.default_workspace / "abs_test.txt"
        test_path.write_text("content")
        resolved_path = filesystem_manager._resolve_and_validate_path(str(test_path))
        assert resolved_path == test_path.resolve()

    def test_resolve_and_validate_path_absolute_not_allowed(self):
        outside_path = Path("/outside_allowed/file.txt")
        with pytest.raises(PermissionError):
            filesystem_manager._resolve_and_validate_path(str(outside_path))

    def test_resolve_and_validate_path_relative_allowed(self):
        (self.default_workspace / "relative_test.txt").write_text("content")
        resolved_path = filesystem_manager._resolve_and_validate_path(
            "relative_test.txt"
        )
        assert resolved_path == (self.default_workspace / "relative_test.txt").resolve()

    def test_resolve_and_validate_path_relative_not_found(self):
        with pytest.raises(FileNotFoundError):
            filesystem_manager._resolve_and_validate_path("non_existent_relative.txt")

    def test_resolve_and_validate_path_placeholder_desktop(self):
        # The fake_desktop_dir is already created in setUp
        desktop_file = self.fake_desktop_dir / "desktop_file.txt"
        desktop_file.write_text("content")
        resolved_path = filesystem_manager._resolve_and_validate_path(str(desktop_file))
        assert resolved_path == desktop_file.resolve()

    def test_resolve_and_validate_path_placeholder_desktop_relative(self):
        # The fake_desktop_dir is already created in setUp
        relative_desktop_file = self.fake_desktop_dir / "relative_desktop_file.txt"
        relative_desktop_file.write_text("content")
        # Simulate a user providing "Desktop/relative_desktop_file.txt"
        resolved_path = filesystem_manager._resolve_and_validate_path(
            "Desktop/relative_desktop_file.txt"
        )
        assert resolved_path == relative_desktop_file.resolve()

    def test_resolve_and_validate_path_must_exist_false(self):
        non_existent_path = self.default_workspace / "new_file_to_create.txt"
        resolved_path = filesystem_manager._resolve_and_validate_path(
            str(non_existent_path), must_exist=False
        )
        assert resolved_path == non_existent_path.resolve()
        assert not non_existent_path.exists()
