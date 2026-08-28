import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch

from core.transcribe import transcribe


class FakeResponse:
    def __init__(self, text):
        self._text = text

    def raise_for_status(self):
        return None

    def json(self):
        return {"text": self._text}


@patch("core.transcribe.httpx.post", return_value=FakeResponse(" recordame comprar café "))
def test_transcribe_returns_the_text_without_surrounding_spaces(mock_post):
    assert transcribe(b"audio-bytes", "voice.ogg", "es") == "recordame comprar café"


@patch("core.transcribe.httpx.post", return_value=FakeResponse("remind me to buy coffee"))
def test_transcribe_passes_the_language_to_the_provider(mock_post):
    transcribe(b"audio-bytes", "voice.ogg", "en")

    assert mock_post.call_args[1]["data"]["language"] == "en"


@patch("core.transcribe.httpx.post", return_value=FakeResponse("hola"))
def test_transcribe_omits_the_language_when_it_is_unknown(mock_post):
    transcribe(b"audio-bytes", "voice.ogg", None)

    assert "language" not in mock_post.call_args[1]["data"]


@patch("config.TRANSCRIBE_PROVIDERS", ["nonexistent", "groq"])
@patch("core.transcribe.httpx.post", return_value=FakeResponse("hola"))
def test_transcribe_falls_through_to_the_next_provider(mock_post):
    assert transcribe(b"audio-bytes", "voice.ogg", "es") == "hola"


@patch("core.transcribe.httpx.post", side_effect=RuntimeError("provider down"))
def test_transcribe_returns_none_when_every_provider_fails(mock_post):
    assert transcribe(b"audio-bytes", "voice.ogg", "es") is None
