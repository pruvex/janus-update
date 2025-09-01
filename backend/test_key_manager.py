import os
import pytest
from backend.key_manager import get_api_key, Settings

@pytest.fixture(autouse=True)
def setup_and_teardown_env():
    # Store original environment variables
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    original_google_key = os.environ.get("GOOGLE_API_KEY")

    # Clear relevant environment variables before each test
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]

    yield

    # Restore original environment variables after each test
    if original_openai_key is not None:
        os.environ["OPENAI_API_KEY"] = original_openai_key
    else:
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

    if original_google_key is not None:
        os.environ["GOOGLE_API_KEY"] = original_google_key
    else:
        if "GOOGLE_API_KEY" in os.environ:
            del os.environ["GOOGLE_API_KEY"]

def test_get_openai_api_key_from_env(setup_and_teardown_env):
    os.environ["OPENAI_API_KEY"] = "test_openai_key_123"
    # Re-initialize settings to pick up new env var
    from importlib import reload
    import backend.key_manager
    reload(backend.key_manager)
    key = backend.key_manager.get_api_key("openai")
    assert key == "test_openai_key_123"

def test_get_google_api_key_from_env(setup_and_teardown_env):
    os.environ["GOOGLE_API_KEY"] = "test_google_key_456"
    # Re-initialize settings to pick up new env var
    from importlib import reload
    import backend.key_manager
    reload(backend.key_manager)
    key = backend.key_manager.get_api_key("google")
    assert key == "test_google_key_456"

def test_get_non_existent_api_key(setup_and_teardown_env):
    # Re-initialize settings to ensure no keys are loaded
    from importlib import reload
    import backend.key_manager
    reload(backend.key_manager)
    key = backend.key_manager.get_api_key("non_existent_provider")
    assert key is None

def test_get_api_key_when_env_var_not_set(setup_and_teardown_env):
    # Ensure env vars are not set for this test by fixture
    # Re-initialize settings to ensure no keys are loaded
    from importlib import reload
    import backend.key_manager
    reload(backend.key_manager)
    key = backend.key_manager.get_api_key("openai")
    assert key is None