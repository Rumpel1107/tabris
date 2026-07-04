import unittest

from core.session import Session, get_or_create_session

def test_creates_new_session_with_defaults():
    sessions = {}
    session = get_or_create_session(sessions, "cli", "abc", user_id=1, language="es")
    assert session.user_id == 1
    assert session.language == "es"
    assert session.conversation_history == []
    assert session.exchange_count == 0
    assert session.last_analyzed_index == 0


def test_returns_same_session_for_same_key():
    sessions = {}
    first = get_or_create_session(sessions, "cli", "abc", user_id=1, language="es")
    first.conversation_history.append({"role": "user", "content": "hola"})
    second = get_or_create_session(sessions, "cli", "abc", user_id=1, language="es")
    assert second is first
    assert second.conversation_history == [{"role": "user", "content": "hola"}]


def test_different_keys_get_different_sessions():
    sessions = {}
    cli_session = get_or_create_session(sessions, "cli", "abc", user_id=1, language="es")
    telegram_session = get_or_create_session(sessions, "telegram", "xyz", user_id=2, language="en")
    assert cli_session is not telegram_session
    cli_session.exchange_count = 3
    assert telegram_session.exchange_count == 0
