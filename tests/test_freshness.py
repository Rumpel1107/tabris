import os
import pytest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import freshness, providers
from core.prompt import fence_user_input
from unittest.mock import patch


def test_the_prompt_fences_the_message_as_data():
    messages = freshness.classifier_prompt("¿A cuánto está el dólar hoy?")
    assert "<user_message>" in messages[-1]["content"]
    assert "¿A cuánto está el dólar hoy?" in messages[-1]["content"]


@pytest.mark.parametrize("answer, verdict", [
    ("fresh", "fresh"),
    ("Stable.", "stable"),
    ("  FRESH\n", "fresh"),
    ("I think it is fresh", None),
    ("", None),
    (None, None),
])
def test_a_verdict_is_read_only_when_the_answer_is_one_word(answer, verdict):
    assert freshness.parse_verdict(answer) == verdict


@pytest.mark.parametrize("answer, verdict", [
    ("fresh", "fresh"),
    ("stable", "stable"),
    ("It depends on the day", "no verdict"),
    (None, "no verdict"),
])
@patch("core.freshness.providers.chat")
def test_classify_asks_the_router_role_and_names_what_it_read(mock_chat, answer, verdict):
    mock_chat.return_value = providers.ChatResponse(content=answer, tool_calls=None)

    assert freshness.classify("What is the exchange rate today?") == verdict

    role, prompt = mock_chat.call_args[0]
    assert role == "router"
    assert fence_user_input("What is the exchange rate today?") in prompt[-1]["content"]


@patch("core.freshness.providers.chat", side_effect=RuntimeError("all providers down"))
def test_classify_returns_no_verdict_when_the_call_fails(mock_chat):
    assert freshness.classify("¿Cuánto vale el dólar hoy?") == "no verdict"


@patch("core.freshness.providers.chat")
def test_classify_returns_no_verdict_when_the_answer_is_not_text(mock_chat):
    mock_chat.return_value = providers.ChatResponse(content=[{"type": "text", "text": "fresh"}], tool_calls=None)
    assert freshness.classify("What is the exchange rate today?") == "no verdict"


@pytest.mark.parametrize("user_input", ["", "   \n"])
@patch("core.freshness.providers.chat")
def test_a_turn_with_no_words_is_stable_without_asking(mock_chat, user_input):
    # a captionless photo, a voice note that transcribed to nothing: nothing in it can have changed
    assert freshness.classify(user_input) == "stable"
    mock_chat.assert_not_called()
