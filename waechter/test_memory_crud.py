import pytest
from backend import crud

def test_save_memory_snippet(db_session):
    """Testet, ob ein neuer Memory-Snippet korrekt gespeichert wird."""
    snippet_text = "Der Benutzer heißt Klaus."
    
    saved_memory = crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text=snippet_text)
    
    assert saved_memory is not None
    assert saved_memory.id is not None
    assert saved_memory.snippet == snippet_text
    assert saved_memory.chat_id == db_session.dummy_chat_id

def test_search_memory_by_text(db_session):
    """Testet, ob die Textsuche in den Memory-Snippets funktioniert."""
    crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text="Der Benutzer heißt Klaus.")
    crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text="Die Lieblingsfarbe des Benutzers ist Blau.")
    crud.save_memory_snippet(db_session, chat_id=db_session.dummy_chat_id, snippet_text="Das Projekt heißt Janus.")

    search_results_klaus = crud.search_memory_by_text(db_session, search_term="Klaus")
    assert len(search_results_klaus) == 1
    assert search_results_klaus[0].snippet == "Der Benutzer heißt Klaus."

    search_results_farbe = crud.search_memory_by_text(db_session, search_term="farbe")
    assert len(search_results_farbe) == 1
    assert "Blau" in search_results_farbe[0].snippet

    search_results_none = crud.search_memory_by_text(db_session, search_term="Berlin")
    assert len(search_results_none) == 0