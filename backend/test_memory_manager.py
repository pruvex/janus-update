import pytest
from unittest.mock import MagicMock, patch
from backend.memory_manager import save_memory_snippet, find_similar_memory_snippet, get_all_memories, update_memory_snippet, save_raw_memory

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

@patch('backend.memory_manager.vector_service.generate_embedding', return_value="[1.0, 2.0, 3.0]")
@patch('backend.database.Memory') # Patch the actual database.Memory
def test_save_memory_snippet(mock_memory_class, mock_generate_embedding, mock_db_session):
    mock_memory_instance = MagicMock()
    mock_memory_class.return_value = mock_memory_instance

    result = save_memory_snippet(mock_db_session, 1, "test snippet")

    mock_generate_embedding.assert_called_once_with("test snippet")
    mock_memory_class.assert_called_once_with(chat_id=1, snippet="test snippet", embedding_json="[1.0, 2.0, 3.0]")
    mock_db_session.add.assert_called_once_with(mock_memory_instance)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_memory_instance)
    assert result == mock_memory_instance

@patch('backend.memory_manager.get_all_memories', return_value=[MagicMock(), MagicMock()])
@patch('backend.memory_manager.vector_service.find_similar_snippets', return_value=["similar_snippet"])
def test_find_similar_memory_snippet(mock_find_similar_snippets, mock_get_all_memories, mock_db_session):
    result = find_similar_memory_snippet(mock_db_session, "query text")

    mock_get_all_memories.assert_called_once_with(mock_db_session)
    mock_find_similar_snippets.assert_called_once()
    assert result == "similar_snippet"

@patch('backend.database.Memory') # Patch the actual database.Memory
def test_get_all_memories(mock_memory_class, mock_db_session, mock_memory_model):
    mock_db_session.query.return_value.all.return_value = [mock_memory_model]

    result = get_all_memories(mock_db_session)

    mock_db_session.query.assert_called_once_with(mock_memory_class)
    assert result == [mock_memory_model]

@patch('backend.memory_manager.vector_service.generate_embedding', return_value="[4.0, 5.0, 6.0]")
def test_update_memory_snippet(mock_generate_embedding, mock_db_session, mock_memory_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_memory_model

    update_memory_snippet(mock_db_session, 1, "new snippet")

    assert mock_memory_model.snippet == "new snippet"
    assert mock_memory_model.embedding_json == "[4.0, 5.0, 6.0]"
    mock_db_session.commit.assert_called_once()

@patch('backend.memory_manager.save_memory_snippet', return_value=MagicMock())
def test_save_raw_memory(mock_save_memory_snippet, mock_db_session):
    result = save_raw_memory(mock_db_session, 1, "raw user input")

    mock_save_memory_snippet.assert_called_once_with(mock_db_session, 1, "raw user input")
    assert result is not None