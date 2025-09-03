import pytest
from backend.context_manager import ContextManager

mock_model_catalog = [
    {"id": "gpt-4o-mini", "context_window": 4000},
    {"id": "long-context-model", "context_window": 16000}
]

short_conversation = [
    {"role": "user", "content": "Hallo"},
    {"role": "assistant", "content": "Wie geht es Ihnen?"}
]

long_message_content = "Dies ist ein sehr langer Text mit vielen Wörtern und Zeichen, um die Token-Zählung realistischer zu gestalten. " * 100

long_conversation = [
    {"role": "user", "content": "Diese Nachricht sollte abgeschnitten werden."}, # Älteste
    {"role": "user", "content": long_message_content},
    {"role": "user", "content": long_message_content},
    {"role": "user", "content": long_message_content},
    {"role": "user", "content": "Das ist die neueste Nachricht."} # Neueste
]

@pytest.fixture
def context_manager():
    return ContextManager(model_catalog=mock_model_catalog)

def test_short_conversation_fits_completely(context_manager):
    model_id = "gpt-4o-mini"
    processed_history = context_manager.build_prompt_history(short_conversation, model_id)
    assert len(processed_history) == len(short_conversation)

def test_long_conversation_is_truncated_correctly(context_manager):
    model_id = "gpt-4o-mini" # Limit 4000, Puffer 1000 -> Nutzbar 3000 Tokens
    
    processed_history = context_manager.build_prompt_history(long_conversation, model_id)
    
    # Erwartung: Die neueste Nachricht ist immer dabei.
    # Die älteste Nachricht ("abgeschnitten") sollte NICHT dabei sein.
    assert len(processed_history) < len(long_conversation)
    assert processed_history[-1]["content"] == "Das ist die neueste Nachricht."
    assert "abgeschnitten" not in [msg["content"] for msg in processed_history]

def test_long_conversation_fits_in_large_model(context_manager):
    model_id = "long-context-model" # Limit 16000
    
    processed_history = context_manager.build_prompt_history(long_conversation, model_id)
    
    # Erwartung: Die gesamte Konversation passt.
    # Die älteste Nachricht ("abgeschnitten") muss die erste im Ergebnis sein.
    assert len(processed_history) == len(long_conversation)
    assert processed_history[0]["content"] == "Diese Nachricht sollte abgeschnitten werden."