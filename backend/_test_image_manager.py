import pytest
from unittest.mock import MagicMock, patch, ANY
from backend.image_manager import save_image_from_url, migrate_image_paths
import os
import asyncio

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def mock_message_model():
    mock_msg = MagicMock()
    mock_msg.id = 1
    mock_msg.image_path = "http://example.com/image.png"
    return mock_msg

@patch('requests.get')
@patch('builtins.open', new_callable=MagicMock)
@patch('os.makedirs')
@patch('backend.image_manager.IMAGE_DIR', '/tmp/test_images')
def test_save_image_from_url(mock_makedirs, mock_open, mock_requests_get):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b"image_data"]
    mock_requests_get.return_value = mock_response

    # Configure mock_open to return a mock object with a write method
    mock_file_handle = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file_handle

    url = "http://example.com/test_image.png"
    result = save_image_from_url(url)

    mock_requests_get.assert_called_once_with(url, stream=True)
    mock_response.raise_for_status.assert_called_once()
    mock_open.assert_called_once_with(os.path.join('/tmp/test_images', result.split('/')[-1]), 'wb')
    mock_file_handle.write.assert_called_once_with(b"image_data")
    assert result.startswith("/static/images/")

@pytest.mark.asyncio
@patch('backend.database.Message') # Patch the actual Message model
@patch('asyncio.get_running_loop') # Patch get_running_loop
async def test_migrate_image_paths(mock_get_running_loop, mock_message_class, mock_message_model, mock_db_session):
    # Configure the mock for run_in_executor
    mock_loop = MagicMock()
    mock_get_running_loop.return_value = mock_loop
    mock_loop.run_in_executor.return_value = asyncio.Future() # Return a Future
    mock_loop.run_in_executor.return_value.set_result("/static/images/new_image.png") # Set the result of the Future

    # Ensure the image_path triggers the migration logic
    mock_message_model.image_path = "http://someurl.com/oaidalleapiprodscus/image.png"
    mock_db_session.query.return_value.filter.return_value.isnot.return_value.all.return_value = [mock_message_model]

    await migrate_image_paths(mock_db_session, mock_message_class) # Pass the patched Message class

    mock_db_session.query.assert_called_once()
    mock_loop.run_in_executor.assert_called_once_with(ANY, save_image_from_url, mock_message_model.image_path)
    assert mock_message_model.image_path == "/static/images/new_image.png"
    mock_db_session.add.assert_called_once_with(mock_message_model)
    mock_db_session.commit.assert_called_once()
