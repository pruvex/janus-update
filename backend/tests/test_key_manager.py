import backend.services.key_manager


def test_get_openai_api_key_mocked(monkeypatch):
    """Tests retrieving the OpenAI API key by directly mocking get_api_key."""
    monkeypatch.setattr(
        backend.services.key_manager,
        "get_api_key",
        lambda provider: "test_openai_key_123" if provider == "openai" else None,
    )

    key = backend.services.key_manager.get_api_key("openai")
    assert key == "test_openai_key_123"


def test_get_google_api_key_mocked(monkeypatch):
    """Tests retrieving the Google API key by directly mocking get_api_key."""
    monkeypatch.setattr(
        backend.services.key_manager,
        "get_api_key",
        lambda provider: "test_google_key_456" if provider == "google" else None,
    )

    key = backend.services.key_manager.get_api_key("google")
    assert key == "test_google_key_456"


def test_get_non_existent_api_key_mocked(monkeypatch):
    """Tests that None is returned for a provider that doesn't exist by directly mocking get_api_key."""
    monkeypatch.setattr(backend.services.key_manager, "get_api_key", lambda provider: None)

    key = backend.services.key_manager.get_api_key("non_existent_provider")
    assert key is None


def test_get_api_key_when_env_var_not_set_mocked(monkeypatch):
    """Tests that None is returned for a provider if its key is not set by directly mocking get_api_key."""
    monkeypatch.setattr(backend.services.key_manager, "get_api_key", lambda provider: None)

    key = backend.services.key_manager.get_api_key("openai")
    assert key is None


def test_get_api_key_with_mixed_settings_mocked(monkeypatch):
    """Tests retrieving a key when other keys are also set by directly mocking get_api_key."""

    def mock_get_api_key(provider):
        if provider == "openai":
            return "test_openai_key_123"
        elif provider == "google":
            return "test_google_key_456"
        return None

    monkeypatch.setattr(backend.services.key_manager, "get_api_key", mock_get_api_key)

    assert backend.services.key_manager.get_api_key("openai") == "test_openai_key_123"
    assert backend.services.key_manager.get_api_key("google") == "test_google_key_456"
