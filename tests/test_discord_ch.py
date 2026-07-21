import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
from unittest.mock import patch

from core.db import find_user_by_key, get_messages, init_db
from core.providers import ChatResponse
import discord_ch


@patch("discord_ch.route_message", return_value="general")
@patch("core.conversation.providers.chat", return_value=ChatResponse(content="Hola, soy Tabris"))
def test_handle_message_provisions_new_user_and_replies(mock_chat, mock_route):
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        sessions = {}
        reply = discord_ch.handle_message(
            db_path, sessions, key="42", name="Carlos", user_input="hola", persona="PERSONA"
        )
        assert reply == "Hola, soy Tabris"
        user = find_user_by_key(db_path, "discord", "42")
        assert user is not None
        assert len(get_messages(db_path, user["id"])) == 2