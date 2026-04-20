import os
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests
from backend.services.image_manager import (
    migrate_image_paths,
    save_image_from_bytes,
    save_image_from_url,
)


# Mock the logger to prevent actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch("backend.services.image_manager.logger") as mock_log:
        yield mock_log


# Mock get_images_dir to control the base path
@pytest.fixture(autouse=True)
def mock_get_images_dir():
    with patch("backend.services.image_manager.get_images_dir") as mock_func:
        mock_func.return_value = "/mock/images"
        yield mock_func


@patch("os.makedirs")
@patch("backend.services.image_manager._find_unique_filename", return_value="test-image.jpg")
@patch("builtins.open", new_callable=mock_open)
def test_save_image_from_bytes_success(mock_open_func, mock_find_unique_filename, mock_makedirs):
    image_bytes = b"test_image_data"
    description = "test image"
    file_extension = "jpg"
    expected_dir = "/mock/images"
    expected_filename = "test-image.jpg"
    expected_file_path = os.path.join(expected_dir, expected_filename)
    expected_web_path = f"/user_images/{expected_filename}"

    result = save_image_from_bytes(
        image_bytes, description=description, file_extension=file_extension
    )

    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
    mock_find_unique_filename.assert_called_once()
    mock_open_func.assert_called_once_with(expected_file_path, "wb")
    mock_open_func().write.assert_called_once_with(image_bytes)
    assert result == expected_web_path


@patch("os.makedirs")
@patch("backend.services.image_manager._find_unique_filename", return_value="untitled.png")
@patch("builtins.open", new_callable=mock_open)
def test_save_image_from_bytes_default_values(
    mock_open_func, mock_find_unique_filename, mock_makedirs
):
    image_bytes = b"test_image_data_default"
    expected_dir = "/mock/images"
    expected_filename = "untitled.png"
    expected_file_path = os.path.join(expected_dir, expected_filename)
    expected_web_path = f"/user_images/{expected_filename}"

    result = save_image_from_bytes(image_bytes)

    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
    mock_find_unique_filename.assert_called_once()
    mock_open_func.assert_called_once_with(expected_file_path, "wb")
    mock_open_func().write.assert_called_once_with(image_bytes)
    assert result == expected_web_path

    assert result == expected_web_path


@patch("os.makedirs")
@patch("backend.services.image_manager._find_unique_filename", return_value="collision-image-1.png")
@patch("builtins.open", new_callable=mock_open)
def test_save_image_from_bytes_collision(
    mock_open_func, mock_find_unique_filename, mock_makedirs
):
    image_bytes = b"test_image_data_collision"
    description = "collision image"
    file_extension = "png"
    expected_dir = "/mock/images"

    expected_filename = "collision-image-1.png"
    expected_file_path = os.path.join(expected_dir, expected_filename)
    expected_web_path = f"/user_images/{expected_filename}"

    result = save_image_from_bytes(
        image_bytes, description=description, file_extension=file_extension
    )

    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
    mock_find_unique_filename.assert_called_once()
    mock_open_func.assert_called_once_with(expected_file_path, "wb")
    mock_open_func().write.assert_called_once_with(image_bytes)
    assert result == expected_web_path


@patch("os.makedirs")
@patch("backend.services.image_manager._find_unique_filename", return_value="test-image-from-url.png")
@patch("builtins.open", new_callable=mock_open)
@patch("requests.get")
@patch("backend.services.image_manager.datetime")
def test_save_image_from_url_success(
    mock_datetime, mock_requests_get, mock_open_func, mock_find_unique_filename, mock_makedirs
):
    mock_datetime.now.return_value = datetime(2023, 1, 1)
    image_url = "http://example.com/image.png"
    title = "test image from url"
    expected_dir = "/mock/images"
    expected_filename = "test-image-from-url.png"
    expected_file_path = os.path.join(expected_dir, expected_filename)
    expected_web_path = f"/user_images/{expected_filename}"
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_requests_get.return_value = mock_response

    result = save_image_from_url(image_url, title=title)

    mock_requests_get.assert_called_once_with(image_url, stream=True)
    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
    mock_find_unique_filename.assert_called_once()
    mock_open_func.assert_called_once_with(expected_file_path, "wb")
    mock_open_func().write.assert_any_call(b"chunk1")
    mock_open_func().write.assert_any_call(b"chunk2")
    assert result == expected_web_path


@patch("requests.get")
def test_save_image_from_url_request_exception(mock_requests_get, mock_logger):
    image_url = "http://example.com/image.png"
    mock_requests_get.side_effect = requests.exceptions.RequestException("Network error")

    result = save_image_from_url(image_url)

    mock_logger.error.assert_called_once_with(
        f"Error downloading image from {image_url}: Network error"
    )
    assert result is None


@pytest.fixture
def mock_message_model_for_migration():
    mock_msg = MagicMock()
    mock_msg.id = 1
    mock_msg.image_path = "https://oaidalleapiprodscus.blob.core.windows.net/some_image.png"
    return mock_msg


@pytest.mark.asyncio
@patch(
    "backend.services.image_manager.save_image_from_url",
    return_value="/user_images/migrated.png",
)
async def test_migrate_image_paths_dalle_url(
    mock_save_image_from_url, mock_logger, mock_message_model_for_migration
):
    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_message_model_for_migration
    ]

    await migrate_image_paths(mock_db_session, MagicMock())

    mock_save_image_from_url.assert_called_once_with(
        "https://oaidalleapiprodscus.blob.core.windows.net/some_image.png",
        subdirectory=None,
    )
    assert mock_message_model_for_migration.image_path == "/user_images/migrated.png"
    mock_db_session.commit.assert_called_once()
    mock_logger.info.assert_called_with("Image path migration complete.")


@pytest.mark.asyncio
@patch("backend.services.image_manager.save_image_from_url")
async def test_migrate_image_paths_local_path(mock_save_image_from_url, mock_logger):
    mock_db_session = MagicMock()
    mock_msg = MagicMock()
    mock_msg.id = 2
    mock_msg.image_path = "/user_images/local_image.png"
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_msg]

    await migrate_image_paths(mock_db_session, MagicMock())

    mock_save_image_from_url.assert_not_called()
    assert mock_msg.image_path == "/user_images/local_image.png"
    mock_db_session.commit.assert_called_once()
    mock_logger.info.assert_called_with("Image path migration complete.")


@pytest.mark.asyncio
@patch("backend.services.image_manager.save_image_from_url", return_value=None)
async def test_migrate_image_paths_save_fails(
    mock_save_image_from_url, mock_logger, mock_message_model_for_migration
):
    mock_db_session = MagicMock()
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        mock_message_model_for_migration
    ]

    original_path = mock_message_model_for_migration.image_path
    await migrate_image_paths(mock_db_session, MagicMock())

    mock_save_image_from_url.assert_called_once()
    assert (
        mock_message_model_for_migration.image_path == original_path
    )  # Path should not change if save fails
    mock_db_session.commit.assert_called_once()
    mock_logger.info.assert_called_with("Image path migration complete.")
