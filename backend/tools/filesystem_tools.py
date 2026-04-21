"""Filesystem tools with Path Sentinel authentication."""

import os
from backend.services.path_sentinel.decorator import requires_path_auth
from backend.services.path_sentinel.models import PathOp


@requires_path_auth(op=PathOp.READ, path_arg="path")
def list_directory(path: str, **kwargs) -> dict:
    """
    List contents of a directory.

    Args:
        path: Path to the directory
        **kwargs: Additional arguments including session_id, user_id, sentinel, db, etc.

    Returns:
        Dict with status and directory contents
    """
    try:
        if not os.path.exists(path):
            return {"status": "error", "message": f"Directory not found: {path}"}

        if not os.path.isdir(path):
            return {"status": "error", "message": f"Path is not a directory: {path}"}

        contents = os.listdir(path)
        print(f"[DEBUG list_directory] Path: {path}, Files found: {len(contents)}, Files: {contents}")
        return {
            "status": "success",
            "data": {
                "path": path,
                "contents": contents,
                "count": len(contents),
            },
        }
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {path}"}
    except Exception as e:
        print(f"[DEBUG list_directory] Error: {str(e)}")
        return {"status": "error", "message": f"Error listing directory: {str(e)}"}


@requires_path_auth(op=PathOp.READ, path_arg="file_path")
def read_file(file_path: str, **kwargs) -> dict:
    """
    Read contents of a file.

    Args:
        file_path: Path to the file
        **kwargs: Additional arguments including session_id, user_id, sentinel, db, etc.

    Returns:
        Dict with status and file contents
    """
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}

        if not os.path.isfile(file_path):
            return {"status": "error", "message": f"Path is not a file: {file_path}"}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "status": "success",
            "data": {
                "path": file_path,
                "content": content,
                "size": os.path.getsize(file_path),
            },
        }
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {file_path}"}
    except UnicodeDecodeError:
        return {"status": "error", "message": f"File is not text-readable: {file_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error reading file: {str(e)}"}


@requires_path_auth(op=PathOp.WRITE, path_arg="file_path")
def create_file(file_path: str, content: str = "", **kwargs) -> dict:
    """
    Create a new file with content.

    Args:
        file_path: Path to the file to create
        content: Content to write to the file
        **kwargs: Additional arguments including session_id, user_id, sentinel, db, etc.

    Returns:
        Dict with status
    """
    try:
        # Check if file already exists
        if os.path.exists(file_path):
            return {"status": "error", "message": f"File already exists: {file_path}"}

        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "success",
            "data": {
                "path": file_path,
                "size": os.path.getsize(file_path),
            },
        }
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {file_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error creating file: {str(e)}"}


@requires_path_auth(op=PathOp.WRITE, path_arg="source_path")
def move_file(source_path: str, destination_path: str, **kwargs) -> dict:
    """
    Move a file to a new location.

    Args:
        source_path: Current path of the file
        destination_path: New path for the file
        **kwargs: Additional arguments including session_id, user_id, sentinel, db, etc.

    Returns:
        Dict with status
    """
    try:
        if not os.path.exists(source_path):
            return {"status": "error", "message": f"Source file not found: {source_path}"}

        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(destination_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        os.rename(source_path, destination_path)

        return {
            "status": "success",
            "data": {
                "source": source_path,
                "destination": destination_path,
            },
        }
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {source_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error moving file: {str(e)}"}


@requires_path_auth(op=PathOp.DELETE, path_arg="file_path")
def delete_file(file_path: str, **kwargs) -> dict:
    """
    Delete a file.

    Args:
        file_path: Path to the file to delete
        **kwargs: Additional arguments including session_id, user_id, sentinel, db, etc.

    Returns:
        Dict with status
    """
    try:
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}

        os.remove(file_path)

        return {
            "status": "success",
            "data": {
                "path": file_path,
            },
        }
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {file_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting file: {str(e)}"}


@requires_path_auth(op=PathOp.DELETE, path_arg="directory_path")
def delete_directory(directory_path: str, **kwargs) -> dict:
    """
    Delete a directory and all its contents.

    Args:
        directory_path: Path to the directory to delete
        **kwargs: Additional arguments including session_id, user_id, sentinel, db, etc.

    Returns:
        Dict with status
    """
    try:
        if not os.path.exists(directory_path):
            return {"status": "error", "message": f"Directory not found: {directory_path}"}

        if not os.path.isdir(directory_path):
            return {"status": "error", "message": f"Path is not a directory: {directory_path}"}

        import shutil
        shutil.rmtree(directory_path)

        return {
            "status": "success",
            "data": {
                "path": directory_path,
            },
        }
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {directory_path}"}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting directory: {str(e)}"}
