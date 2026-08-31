import os
import pytest
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


@pytest.mark.parametrize("transcript", ["", "   ", ".", "...", "¿? ¡!", "♪♪"])
@patch("core.transcribe.httpx.post")
def test_transcribe_returns_empty_text_when_the_transcript_holds_no_letter(mock_post, transcript):
    mock_post.return_value = FakeResponse(transcript)

    assert transcribe(b"audio-bytes", "voice.ogg", "es") == ""


@pytest.mark.parametrize("transcript, duration", [
    ("Gracias", 3),
    ("Gracias", 30),
    ("Gracias por ver el video", 30),
    ("Thanks for watching!", 30),
])
@patch("core.transcribe.httpx.post")
def test_transcribe_returns_empty_text_when_a_recording_yields_too_few_characters(mock_post, transcript, duration):
    mock_post.return_value = FakeResponse(transcript)

    assert transcribe(b"audio-bytes", "voice.ogg", "es", duration=duration) == ""


@pytest.mark.parametrize("transcript", [
    "recordame comprar café antes de las seis de la tarde",
    "remind me to buy coffee before six in the evening",
])
@patch("core.transcribe.httpx.post")
def test_transcribe_keeps_a_transcript_dense_enough_to_be_speech(mock_post, transcript):
    mock_post.return_value = FakeResponse(transcript)

    assert transcribe(b"audio-bytes", "voice.ogg", "es", duration=10) == transcript


@pytest.mark.parametrize("duration", [None, 0, 1])
@patch("core.transcribe.httpx.post", return_value=FakeResponse("Gracias"))
def test_transcribe_does_not_judge_density_without_enough_recording(mock_post, duration):
    assert transcribe(b"audio-bytes", "voice.ogg", "es", duration=duration) == "Gracias"
