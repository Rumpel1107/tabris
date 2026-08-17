import asyncio
import config
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
import threading

from channels import discord_ch
from core.db import create_user, find_user_by_key, get_messages, init_db, register_user_channel
from core.providers import ChatResponse
from core.session import Session
from core.strings import msg
from unittest.mock import patch


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


@patch("channels.discord_ch.route_message", return_value="general")
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


class FakeChannel:
    def __init__(self, fail_on=None):
        self.sent = []
        self.attempts = 0
        self.fail_on = fail_on

    async def send(self, content):
        self.attempts += 1
        if self.attempts == self.fail_on:
            raise RuntimeError("send failed")
        self.sent.append(content)


def test_run_locked_offloads_the_call_to_a_thread():
    calls = []

    def work(a, b):
        calls.append((a, b))
        return "done"

    result = asyncio.run(discord_ch._run_locked("some-key", work, "x", "y"))

    assert result == "done"
    assert calls == [("x", "y")]


def test_run_locked_serializes_calls_for_the_same_key_but_not_across_keys():
    order = []
    release_first = threading.Event()

    def first(key):
        order.append(f"{key}-start")
        release_first.wait(timeout=1)
        order.append(f"{key}-end")

    def other(key):
        order.append(f"{key}-start")
        order.append(f"{key}-end")

    async def scenario():
        blocked = asyncio.create_task(discord_ch._run_locked("alice", first, "alice"))
        await asyncio.sleep(0.05)  # let it acquire the lock and start blocking

        same_key = asyncio.create_task(discord_ch._run_locked("alice", other, "alice-2"))
        different_key = asyncio.create_task(discord_ch._run_locked("bob", other, "bob"))
        await asyncio.sleep(0.05)

        # bob doesn't wait on alice's lock; alice-2 does
        assert order == ["alice-start", "bob-start", "bob-end"]

        release_first.set()
        await asyncio.gather(blocked, same_key, different_key)

    asyncio.run(scenario())

    assert order == ["alice-start", "bob-start", "bob-end", "alice-end", "alice-2-start", "alice-2-end"]


def test_a_short_reply_is_sent_as_one_message():
    channel = FakeChannel()
    delivered = asyncio.run(discord_ch.send_reply(channel, "hola", Session(language="es")))
    assert channel.sent == ["hola"]
    assert delivered is True


@patch("config.DISCORD_MESSAGE_LIMIT", 20)
def test_a_long_reply_is_sent_in_pieces_in_order():
    channel = FakeChannel()
    asyncio.run(discord_ch.send_reply(channel, "primera línea\nsegunda línea", Session(language="es")))
    assert channel.sent == ["primera línea", "segunda línea"]


@patch("config.DISCORD_MESSAGE_LIMIT", 20)
def test_a_failed_piece_stops_the_send_and_warns_the_user():
    channel = FakeChannel(fail_on=2)
    reply = "primera línea\nsegunda línea\ntercera línea"
    delivered = asyncio.run(discord_ch.send_reply(channel, reply, Session(language="es")))
    assert channel.sent == ["primera línea", msg("send_failed", "es")]
    assert delivered is False