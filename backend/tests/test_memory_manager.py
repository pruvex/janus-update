import pytest
from unittest.mock import MagicMock, patch, call  # Import 'call'
from backend.services.memory_manager import (
    save_memory_snippet,
    find_similar_memory_snippet,
    get_all_memories,
    update_memory_snippet,
    save_raw_memory,
    get_all_facts,
)
import backend.data.database  # Import database for Memory model
import logging  # Import logging to patch getLogger


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_memory_model():
    mock_mem = MagicMock()
    mock_mem.id = 1
    mock_mem.snippet = "test snippet"
    mock_mem.embedding_json = "[1.0, 2.0, 3.0]"
    return mock_mem


def test_save_memory_snippet(mocker, mock_db_session):
    mock_generate_embedding = mocker.patch("backend.services.memory_manager.vector_service.generate_embedding", return_value="[1.0, 2.0, 3.0]")
    mock_memory_class = mocker.patch('backend.data.database.Memory')
    mock_memory_instance = MagicMock()
    mock_memory_class.return_value = mock_memory_instance

    result = save_memory_snippet(mock_db_session, 1, "test snippet")

    mock_generate_embedding.assert_called_once_with("test snippet")
    mock_memory_class.assert_called_once_with(
        chat_id=1,
        snippet="test snippet",
        embedding_json="[1.0, 2.0, 3.0]",
        is_core_fact=False,
        expires_at=None,
    )
    mock_db_session.add.assert_called_once_with(mock_memory_instance)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_memory_instance)
    assert result == mock_memory_instance


def test_save_memory_snippet_no_embedding(mocker, mock_db_session):
    mock_generate_embedding = mocker.patch("backend.services.memory_manager.vector_service.generate_embedding", return_value=None)
    mock_memory_class = mocker.patch('backend.data.database.Memory')
    result = save_memory_snippet(mock_db_session, 1, "test snippet")

    mock_generate_embedding.assert_called_once_with("test snippet")
    mock_memory_class.assert_not_called()
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()
    mock_db_session.refresh.assert_not_called()
    assert result is None


def test_find_similar_memory_snippet(mocker, mock_db_session):
    mock_get_all_memories = mocker.patch("backend.services.memory_manager.get_all_memories", return_value=[MagicMock(), MagicMock()])
    mock_find_similar_snippets = mocker.patch("backend.services.memory_manager.vector_service.find_similar_snippets", return_value=["similar_snippet"])
    result = find_similar_memory_snippet(mock_db_session, "query text")

    mock_get_all_memories.assert_called_once_with(mock_db_session)
    mock_find_similar_snippets.assert_called_once()
    assert result == "similar_snippet"


def test_find_similar_memory_snippet_no_similar(mocker, mock_db_session):
    mock_get_all_memories = mocker.patch("backend.services.memory_manager.get_all_memories", return_value=[MagicMock(), MagicMock()])
    mock_find_similar_snippets = mocker.patch("backend.services.memory_manager.vector_service.find_similar_snippets", return_value=[])
    result = find_similar_memory_snippet(mock_db_session, "query text")

    mock_get_all_memories.assert_called_once_with(mock_db_session)
    mock_find_similar_snippets.assert_called_once()
    assert result is None


@patch('backend.data.database.Memory') # Patch the actual database.Memory
def test_get_all_memories(mock_memory_class, mock_db_session, mock_memory_model):
    mock_db_session.query.return_value.all.return_value = [mock_memory_model]
    result = get_all_memories(mock_db_session)

    mock_db_session.query.assert_called_once_with(mock_memory_class)
    assert result == [mock_memory_model]


@patch("backend.services.memory_manager.vector_service.generate_embedding", return_value="[4.0, 5.0, 6.0]")
def test_update_memory_snippet(
    mock_generate_embedding, mock_db_session, mock_memory_model
):
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_memory_model
    )

    update_memory_snippet(mock_db_session, 1, "new snippet", is_core=False)

    assert mock_memory_model.snippet == "new snippet"
    assert mock_memory_model.embedding_json == "[4.0, 5.0, 6.0]"
    mock_db_session.commit.assert_called_once()


def test_update_memory_snippet_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    update_memory_snippet(mock_db_session, 999, "new snippet", is_core=False)

    mock_db_session.commit.assert_not_called()


@patch("backend.services.memory_manager.save_memory_snippet", return_value=MagicMock())
@patch("logging.getLogger")  # Corrected patch target
def test_save_raw_memory(
    mock_get_logger, mock_save_memory_snippet, mock_db_session
):  # Swapped arguments
    # Mock the logger instance returned by getLogger
    mock_logger_instance = MagicMock()
    mock_get_logger.return_value = mock_logger_instance

    result = save_raw_memory(mock_db_session, 1, "raw user input")

    mock_save_memory_snippet.assert_called_once_with(
        mock_db_session, 1, "raw user input"
    )
    mock_get_logger.assert_called_once_with(
        "janus_backend"
    )  # Assert getLogger was called
    mock_logger_instance.info.assert_has_calls(
        [
            call("Attempting to save raw memory for chat 1: 'raw user input'"),
            call("Raw memory saved successfully: 'raw user input'"),
        ]
    )
    assert result is not None


@patch("backend.services.memory_manager.save_memory_snippet", return_value=None)
@patch("logging.getLogger")  # Corrected patch target
def test_save_raw_memory_fails(
    mock_get_logger, mock_save_memory_snippet, mock_db_session
):  # Swapped arguments
    # Mock the logger instance returned by getLogger
    mock_logger_instance = MagicMock()
    mock_get_logger.return_value = mock_logger_instance

    result = save_raw_memory(mock_db_session, 1, "raw user input")

    mock_save_memory_snippet.assert_called_once_with(
        mock_db_session, 1, "raw user input"
    )
    mock_get_logger.assert_called_once_with(
        "janus_backend"
    )  # Assert getLogger was called
    mock_logger_instance.info.assert_called_once_with(
        "Attempting to save raw memory for chat 1: 'raw user input'"
    )
    mock_logger_instance.warning.assert_called_once_with(
        "Failed to save raw memory for chat 1: 'raw user input'"
    )
    assert result is None


@patch('backend.data.database.Memory')
def test_get_all_facts_basic(mock_memory_class, mock_db_session):
    mock_fact1 = MagicMock(snippet="Das ist ein Fakt.")
    mock_fact2 = MagicMock(snippet="Ein weiterer Fakt.")
    mock_question1 = MagicMock(snippet="was ist das?")
    mock_question2 = MagicMock(snippet="wie geht es dir?")

    # Mock the filter method to return a mock object that has an 'all' method
    mock_filter_result = MagicMock()
    mock_filter_result.all.return_value = [
        mock_fact1,
        mock_fact2,
    ]  # This is the expected filtered result
    mock_db_session.query.return_value.filter.return_value = mock_filter_result

    result = get_all_facts(mock_db_session)

    # Assert that the filter was called correctly
    mock_db_session.query.assert_called_once_with(mock_memory_class)
    # The filter conditions are complex to assert directly, so we rely on the returned result

    assert len(result) == 2
    assert mock_fact1 in result
    assert mock_fact2 in result
    assert mock_question1 not in result
    assert mock_question2 not in result


@patch('backend.data.database.Memory')
def test_get_all_facts_no_facts(mock_memory_class, mock_db_session):
    # Mock the filter method to return a mock object that has an 'all' method
    mock_filter_result = MagicMock()
    mock_filter_result.all.return_value = []  # This is the expected filtered result
    mock_db_session.query.return_value.filter.return_value = mock_filter_result

    result = get_all_facts(mock_db_session)

    assert len(result) == 0


@patch('backend.data.database.Memory')
def test_get_all_facts_empty_db(mock_memory_class, mock_db_session):
    # Mock the filter method to return a mock object that has an 'all' method
    mock_filter_result = MagicMock()
    mock_filter_result.all.return_value = []  # This is the expected filtered result
    mock_db_session.query.return_value.filter.return_value = mock_filter_result

    result = get_all_facts(mock_db_session)

    assert len(result) == 0
