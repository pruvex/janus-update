from unittest.mock import MagicMock, patch

import backend.data.database  # Added this import
import pytest
from backend.data.crud import (
    create_chat,
    create_message,
    delete_chat,
    get_monthly_cost_summary_by_model,
    get_all_chat_summaries,
    get_chat_by_id,
    get_chat_with_messages,
    get_chats,
    get_messages_by_chat_id,
    toggle_archive_chat,
    update_chat_summary,
    update_chat_title,
)


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_chat_model():
    mock_chat = MagicMock()
    mock_chat.id = 1
    mock_chat.title = "Test Chat"
    mock_chat.is_archived = False
    mock_chat.summary = None
    mock_chat.summary_embedding_json = None
    return mock_chat


@pytest.fixture
def mock_message_model():
    mock_msg = MagicMock()
    mock_msg.id = 1
    mock_msg.chat_id = 1
    mock_msg.sender = "user"
    mock_msg.content = "Hello"
    mock_msg.image_path = None
    mock_msg.timestamp = "2023-01-01T12:00:00"
    return mock_msg


@patch("backend.data.database.Chat")  # Patch the actual database.Chat
def test_create_chat(mock_chat_class, mock_db_session):
    mock_chat_instance = MagicMock()
    mock_chat_class.return_value = mock_chat_instance

    result = create_chat(mock_db_session, "New Chat Title")

    mock_chat_class.assert_called_once_with(
        title="New Chat Title", project_id=None, auto_generated=True
    )
    mock_db_session.add.assert_called_once_with(mock_chat_instance)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_chat_instance)
    assert result == mock_chat_instance


@patch("backend.data.database.Chat")  # Patch the actual database.Chat
def test_get_chats(mock_chat_class, mock_db_session, mock_chat_model):
    # query().filter().filter().order_by().all()
    tail = mock_db_session.query.return_value.filter.return_value.filter.return_value
    tail.order_by.return_value.all.return_value = [mock_chat_model]

    result = get_chats(mock_db_session)

    # Verify the query was built correctly
    mock_db_session.query.assert_called_once_with(mock_chat_class)
    
    # Verify the result
    assert len(result) == 1
    assert result[0] is mock_chat_model


def test_get_chats_include_archived(mock_db_session, mock_chat_model):
    # query().filter().order_by().all() (only project_id filter when include_archived=True)
    tail = mock_db_session.query.return_value.filter.return_value
    tail.order_by.return_value.all.return_value = [mock_chat_model]

    result = get_chats(mock_db_session, include_archived=True)
    
    # Verify the query was built correctly
    mock_db_session.query.assert_called_once_with(backend.data.database.Chat)
    
    # Verify the result
    assert len(result) == 1
    assert result[0] is mock_chat_model


def test_get_chats_no_chats(mock_db_session):
    tail = mock_db_session.query.return_value.filter.return_value.filter.return_value
    tail.order_by.return_value.all.return_value = []

    result = get_chats(mock_db_session)

    assert len(result) == 0


@patch("backend.data.database.Chat")  # Patch the actual database.Chat
def test_get_chat_by_id(mock_chat_class, mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model

    result = get_chat_by_id(mock_db_session, 1)

    mock_db_session.query.assert_called_once_with(mock_chat_class)
    mock_db_session.query.return_value.filter.assert_called_once_with(mock_chat_class.id == 1)
    assert result == mock_chat_model


def test_get_chat_by_id_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = get_chat_by_id(mock_db_session, 999)

    assert result is None


@patch("backend.data.database.Message")  # Patch the actual database.Message
def test_get_messages_by_chat_id(mock_message_class, mock_db_session, mock_message_model):
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_message_model
    ]

    result = get_messages_by_chat_id(mock_db_session, 1)

    mock_db_session.query.assert_called_once_with(mock_message_class)
    mock_db_session.query.return_value.filter.assert_called_once_with(
        mock_message_class.chat_id == 1
    )
    assert result == [mock_message_model]


@patch("backend.data.database.Message")  # Patch the actual database.Message
def test_create_message(mock_message_class, mock_db_session):
    mock_message_instance = MagicMock()
    mock_message_class.return_value = mock_message_instance
    result = create_message(mock_db_session, 1, "user", "Test Content")

    mock_message_class.assert_called_once_with(
        chat_id=1,
        role="user",
        content="Test Content",
    )
    mock_db_session.add.assert_called_once_with(mock_message_instance)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_message_instance)
    assert result == mock_message_instance


def test_create_message_with_image_path(mock_db_session):
    with patch("backend.data.database.Message") as mock_message_class:
        mock_message_instance = MagicMock()
        mock_message_class.return_value = mock_message_instance

        result = create_message(
            mock_db_session, 1, "user", "Image Content", image_path="/path/to/image.png"
        )

        mock_message_class.assert_called_once_with(
            chat_id=1,
            role="user",
            content="Image Content",
        )
        assert mock_message_instance.metadata_json is not None
        assert "/path/to/image.png" in mock_message_instance.metadata_json
        mock_db_session.add.assert_called_once_with(mock_message_instance)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_message_instance)
        assert result == mock_message_instance


def test_update_chat_title(mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model

    result = update_chat_title(mock_db_session, 1, "Updated Title")

    assert mock_chat_model.title == "Updated Title"
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_chat_model)
    assert result == mock_chat_model


def test_update_chat_title_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = update_chat_title(mock_db_session, 999, "Updated Title")

    assert result is None
    mock_db_session.commit.assert_not_called()


def test_toggle_archive_chat(mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model
    mock_chat_model.is_archived = False

    result = toggle_archive_chat(mock_db_session, 1)

    assert mock_chat_model.is_archived
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_chat_model)
    assert result == mock_chat_model


def test_toggle_archive_chat_from_archived(mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model
    mock_chat_model.is_archived = True

    result = toggle_archive_chat(mock_db_session, 1)

    assert not mock_chat_model.is_archived
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_chat_model)
    assert result == mock_chat_model


def test_get_monthly_cost_summary_by_model_includes_context_breakdown(mock_db_session):
    conversation_cost = MagicMock(
        model="gpt-5.4-nano",
        total_cost=0.0007,
        input_tokens=3000,
        output_tokens=900,
        context="conversation",
    )
    websearch_cost = MagicMock(
        model="gpt-5.4-nano",
        total_cost=0.0090,
        input_tokens=1,
        output_tokens=0,
        context="websearch (query_count=1)",
    )
    mock_db_session.query.return_value.filter.return_value.all.return_value = [conversation_cost, websearch_cost]

    result = get_monthly_cost_summary_by_model(mock_db_session, 2026, 3)

    assert len(result) == 1
    entry = result[0]
    assert entry["model"] == "gpt-5.4-nano"
    assert entry["total_cost"] == pytest.approx(0.0097)
    assert entry["total_input_tokens"] == 3001
    contexts = {item["context"]: item for item in entry["context_breakdown"]}
    assert contexts["websearch (query_count=1)"]["cost"] == pytest.approx(0.0090)
    assert contexts["websearch (query_count=1)"]["count"] == 1
    assert contexts["conversation"]["cost"] == pytest.approx(0.0007)


def test_toggle_archive_chat_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = toggle_archive_chat(mock_db_session, 999)

    assert result is None
    mock_db_session.commit.assert_not_called()


def test_get_chat_with_messages(mock_db_session, mock_chat_model, mock_message_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        mock_message_model
    ]

    chat, messages = get_chat_with_messages(mock_db_session, 1)

    assert chat == mock_chat_model
    assert messages == [mock_message_model]


def test_get_chat_with_messages_no_chat(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    chat, messages = get_chat_with_messages(mock_db_session, 999)

    assert chat is None
    assert messages == []


def test_get_chat_with_messages_no_messages(mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    chat, messages = get_chat_with_messages(mock_db_session, 1)

    assert chat == mock_chat_model
    assert messages == []


def test_delete_chat(mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model

    result = delete_chat(mock_db_session, 1)

    mock_db_session.delete.assert_called_once_with(mock_chat_model)
    mock_db_session.commit.assert_called_once()
    assert result


def test_delete_chat_not_found(mock_db_session):
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = delete_chat(mock_db_session, 999)

    assert not result
    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_update_chat_summary(mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chat_model

    result = update_chat_summary(mock_db_session, 1, "New Summary", "[0.1, 0.2]")

    assert mock_chat_model.summary == "New Summary"
    assert mock_chat_model.summary_embedding_json == "[0.1, 0.2]"
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_chat_model)
    assert result == mock_chat_model


@patch("backend.data.database.Chat")  # Patch the actual database.Chat
def test_get_all_chat_summaries(mock_chat_class, mock_db_session, mock_chat_model):
    mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_chat_model]
    result = get_all_chat_summaries(mock_db_session)

    mock_db_session.query.assert_called_once_with(mock_chat_class)
    mock_db_session.query.return_value.filter.assert_called_once()
    assert result == [mock_chat_model]
