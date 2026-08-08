import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
from unittest.mock import patch

import config
from core.db import create_user, find_user_by_key, get_messages, init_db, register_user_channel
from core.providers import ChatResponse
from core.strings import msg
import discord_ch


@patch("core.onboarding.detect_language", return_value="es")
def test_handle_message_onboards_an_unknown_person_instead_of_creating_a_user(mock_detect):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        sessions = {}
        reply = discord_ch.handle_message(
            db_path, sessions, key="42", user_input="hola", persona="PERSONA"
        )
        assert find_user_by_key(db_path, "discord", "42") is None
        assert reply == msg("language_detected", "es", agent=config.AGENT_NAME)


@patch("discord_ch.route_message", return_value="general")
@patch("core.conversation.providers.chat", return_value=ChatResponse(content="Hola, soy Tabris"))
def test_handle_message_replies_to_a_known_person(mock_chat, mock_route):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        user_id = create_user(db_path, "Carlos", "es")
        register_user_channel(db_path, user_id, "discord", "42")
        sessions = {}
        reply = discord_ch.handle_message(
            db_path, sessions, key="42", user_input="hola", persona="PERSONA"
        )
        assert reply == "Hola, soy Tabris"
        assert len(get_messages(db_path, user_id)) == 2