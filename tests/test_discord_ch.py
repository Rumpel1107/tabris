import asyncio
import config
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
import threading
from types import SimpleNamespace

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
        self.typing_entered = False

    async def send(self, content):
        self.attempts += 1
        if self.attempts == self.fail_on:
            raise RuntimeError("send failed")
        self.sent.append(content)

    def typing(self):
        channel = self

        class Typing:
            async def __aenter__(self):
                channel.typing_entered = True

            async def __aexit__(self, *details):
                return False

        return Typing()


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


def test_a_turn_shows_typing_while_the_work_happens():
    channel = FakeChannel()
    message = SimpleNamespace(
        author=SimpleNamespace(id=42),
        content="hola",
        channel=channel,
        flags=SimpleNamespace(voice=False),
        attachments=[],
    )
    discord_ch.db_path = ":memory:"
    discord_ch.persona = "persona"
    discord_ch.sessions = {("discord", "42"): Session(language="es")}
    with patch("channels.discord_ch.handle_message", return_value="lista"):
        asyncio.run(discord_ch.on_message(message))
    assert channel.typing_entered is True
    assert channel.sent == ["lista"]


class FakeAttachment:
    def __init__(self, duration):
        self.duration = duration
        self.filename = "voice-message.ogg"
        self.read_calls = 0

    async def read(self):
        self.read_calls += 1
        return b"audio-bytes"


def _voice_message(channel, duration=10, is_voice=True, content=""):
    return SimpleNamespace(
        author=SimpleNamespace(id=42),
        content=content,
        channel=channel,
        flags=SimpleNamespace(voice=is_voice),
        attachments=[FakeAttachment(duration)],
    )


def _prepare_adapter():
    discord_ch.db_path = ":memory:"
    discord_ch.persona = "persona"
    discord_ch.sessions = {}


@patch("channels.discord_ch.find_user_by_key", return_value={"id": 1, "language": "es"})
@patch("channels.discord_ch.handle_message", return_value="Listo, te lo recuerdo")
@patch("channels.discord_ch.transcribe", return_value="recordame comprar café")
def test_a_voice_message_is_transcribed_and_answered(mock_transcribe, mock_handle, mock_user):
    channel = FakeChannel()
    _prepare_adapter()

    asyncio.run(discord_ch.on_message(_voice_message(channel)))

    assert mock_handle.call_args[0][3] == "recordame comprar café"
    assert channel.sent == ["🎙️ recordame comprar café\n\nListo, te lo recuerdo"]


@patch("channels.discord_ch.find_user_by_key", return_value={"id": 1, "language": "es"})
@patch("channels.discord_ch.handle_message")
@patch("channels.discord_ch.transcribe")
def test_a_voice_message_over_the_limit_is_refused_before_being_read(mock_transcribe, mock_handle, mock_user):
    channel = FakeChannel()
    _prepare_adapter()
    message = _voice_message(channel, duration=config.AUDIO_MAX_SECONDS + 1)

    asyncio.run(discord_ch.on_message(message))

    assert channel.sent == [msg("audio_too_long", "es", minutes=config.AUDIO_MAX_SECONDS // 60)]
    assert message.attachments[0].read_calls == 0
    assert mock_transcribe.called is False
    assert mock_handle.called is False


@patch("channels.discord_ch.find_user_by_key", return_value={"id": 1, "language": "es"})
@patch("channels.discord_ch.handle_message")
@patch("channels.discord_ch.transcribe", return_value=None)
def test_a_voice_message_that_cannot_be_transcribed_warns_the_user(mock_transcribe, mock_handle, mock_user):
    channel = FakeChannel()
    _prepare_adapter()

    asyncio.run(discord_ch.on_message(_voice_message(channel)))

    assert channel.sent == [msg("audio_not_understood", "es")]
    assert mock_handle.called is False


@patch("channels.discord_ch.handle_message", return_value="respuesta")
@patch("channels.discord_ch.transcribe")
def test_an_audio_attachment_that_is_not_a_voice_message_takes_the_text_path(mock_transcribe, mock_handle):
    channel = FakeChannel()
    _prepare_adapter()
    discord_ch.sessions = {("discord", "42"): Session(language="es")}

    asyncio.run(discord_ch.on_message(_voice_message(channel, is_voice=False, content="mira esto")))

    assert mock_transcribe.called is False
    assert mock_handle.call_args[0][3] == "mira esto"
    assert channel.sent == ["respuesta"]


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