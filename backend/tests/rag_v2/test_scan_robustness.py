"""
Test for _scan_files() robustness with invalid folder names.

This test validates that the os.walk implementation with onerror callback
can handle invalid folder names (e.g., trailing dots) without stopping the
entire scan.
"""

import os
import tempfile
from pathlib import Path

from backend.services.rag.ingestion import IngestionRun


def test_scan_with_invalid_folder_name():
    """Test that _scan_files() handles invalid folder names gracefully."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        root = Path(tmpdir)

        # Create valid files
        valid_file = root / "test.py"
        valid_file.write_text("print('hello')")

        # Create a subdirectory with valid files
        subdir = root / "subdir"
        subdir.mkdir()
        subdir_file = subdir / "sub.py"
        subdir_file.write_text("print('sub')")

        # Try to create a folder with an invalid name (trailing dot)
        # Windows may prevent this, but we'll test the error handling
        invalid_folder = root / "invalid."
        try:
            invalid_folder.mkdir()
            invalid_file = invalid_folder / "bad.py"
            invalid_file.write_text("print('bad')")
        except (OSError, PermissionError) as e:
            # Expected on Windows - folder names cannot end with a dot
            print(f"Could not create invalid folder (expected): {e}")

        # Run ingestion scan
        ingest = IngestionRun(
            root_dir=root,
            chroma_path=str(root / "chroma"),
            db_path=str(root / "db.sqlite"),
            enable_path_policy=False,
        )

        files = ingest._scan_files()

        # Verify that valid files were found
        assert len(files) >= 2, f"Expected at least 2 files, found {len(files)}"
        assert valid_file in files, f"Valid file {valid_file} not found"
        assert subdir_file in files, f"Subdir file {subdir_file} not found"

        print(f"✅ Scan robustness test passed: found {len(files)} files")


if __name__ == "__main__":
    test_scan_with_invalid_folder_name()
