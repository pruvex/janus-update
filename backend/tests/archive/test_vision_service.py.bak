import pytest
from unittest.mock import MagicMock, patch
import io
import torch
from PIL import Image

# Import the service and profile directly for testing
from backend.services.vision_service import LocalVisionService
from backend.services.vision.profiles.openai_profile import CLIP_LABELS, LABEL_GROUPS, get_threshold

@pytest.fixture
def mock_clip_model():
    """Mocks the CLIP model and preprocess function."""
    with patch('clip.load') as mock_load:
        mock_model = MagicMock()
        mock_preprocess = MagicMock()
        mock_load.return_value = (mock_model, mock_preprocess)
        yield mock_model, mock_preprocess

@pytest.fixture
def mock_vision_service(mock_clip_model):
    """Provides an instance of LocalVisionService with mocked CLIP."""
    mock_model, mock_preprocess = mock_clip_model
    # Configure mock_preprocess to return a dummy tensor
    mock_preprocess.return_value.unsqueeze.return_value.to.return_value = torch.zeros(1, 3, 224, 224)
    return LocalVisionService()

@pytest.fixture
def mock_openai_profile():
    """Provides a mock profile object with CLIP_LABELS and get_threshold."""
    mock_profile = MagicMock()
    mock_profile.CLIP_LABELS = CLIP_LABELS
    mock_profile.LABEL_GROUPS = LABEL_GROUPS # Needed for CLIP_LABELS generation, though not directly used in the new vision service logic
    mock_profile.get_threshold.side_effect = get_threshold # Use the actual get_threshold logic
    return mock_profile

@pytest.fixture
def dummy_image_bytes():
    """Generates dummy image bytes."""
    # Create a simple black image
    img = Image.new('RGB', (100, 100), color = 'black')
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='PNG')
    return byte_arr.getvalue()

@pytest.mark.asyncio
async def test_process_image_aggressive_thresholds(
    mock_vision_service, mock_openai_profile, dummy_image_bytes, mock_clip_model
):
    mock_model, mock_preprocess = mock_clip_model

    # The service now builds a dynamic label pool across all plugins.
    # Match logits length to the actual tokenized label count to avoid index errors.
    def _dynamic_logits(_image_input, text_tokens):
        label_count = int(text_tokens.shape[0])
        return torch.full((1, label_count), -100.0, dtype=torch.float32), None

    mock_model.side_effect = _dynamic_logits

    # Mock db session (not directly used by vision_service for process_image logic)
    mock_db_session = MagicMock()

    result = mock_vision_service.process_image(
        dummy_image_bytes, mock_db_session, mock_openai_profile
    )

    assert isinstance(result, dict)
    assert "local_description" in result
    assert isinstance(result["local_description"], str)
    assert "feature_report" in result
    assert isinstance(result["feature_report"], dict)

    # Test case for no matches
    result_no_match = mock_vision_service.process_image(
        dummy_image_bytes, mock_db_session, mock_openai_profile
    )
    assert isinstance(result_no_match["local_description"], str)