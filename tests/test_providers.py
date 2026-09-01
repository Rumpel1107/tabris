import config
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from core import providers
from core.providers import chat
from unittest.mock import MagicMock, patch


class TestProvidersChat(unittest.TestCase):
    
    @patch("core.providers._call_provider")
    def test_primary_succeeds(self, mock_call):
        mock_call.return_value = "respuesta del primario"
        result = chat("router", [{"role": "user", "content": "hola"}])
        self.assertEqual(result, "respuesta del primario")
        mock_call.assert_called_once()
    
    @patch("core.providers._call_provider")
    def test_fallback_used_when_primary_fails(self, mock_call):
        mock_call.side_effect = [Exception("primario caido"), "respuesta del respaldo"]
        result = chat("router", [{"role": "user", "content": "hola"}])
        self.assertEqual(result, "respuesta del respaldo")
        self.assertEqual(mock_call.call_count, 2)
    
    @patch("core.providers._call_provider", side_effect=Exception("todos caidos"))
    def test_all_providers_fail(self, mock_call):
        with self.assertRaises(RuntimeError):
            chat("router", [{"role": "user", "content": "hola"}])

    @patch("core.providers._call_provider")
    def test_passes_the_role_temperature(self, mock_call):
        chat("router", [{"role": "user", "content": "hola"}])
        self.assertEqual(
            mock_call.call_args[1]["temperature"],
            config.AGENT_ROLES["router"]["temperature"],
        )

    @patch("core.providers._call_provider")
    def test_fallback_logs_warning(self, mock_call):
        mock_call.side_effect = [Exception("primario caido"), "respuesta del respaldo"]
        with self.assertLogs("core.providers", level="WARNING") as log:
            chat("router", [{"role": "user", "content": "hola"}])
        self.assertIn("primario caido", log.output[0])

class TestGetClient(unittest.TestCase):
    def setUp(self):
        providers._clients.clear()
    
    @patch("core.providers.OpenAI")
    def test_builds_client_with_timeout(self, mock_openai_class):
        providers._get_client("groq")
        mock_openai_class.assert_called_once_with(
            base_url=providers.PROVIDER_CONFIG["groq"]["base_url"],
            api_key=providers.PROVIDER_CONFIG["groq"]["api_key"],
            timeout=config.PROVIDER_TIMEOUT,
            max_retries=0,
        )
    
    @patch("core.providers.OpenAI")
    def test_reuses_cached_client(self, mock_openai_class):
        first = providers._get_client("groq")
        second = providers._get_client("groq")
        self.assertIs(first, second)
        mock_openai_class.assert_called_once()

class TestCallProvider(unittest.TestCase):
    
    @patch("core.providers._get_client")
    def test_returns_content_when_no_tool_calls(self, mock_get_client):
        mock_message = MagicMock(content="hola", tool_calls=None)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = providers._call_provider(
            "groq", "llama-3.3-70b-versatile", [{"role": "user", "content": "hola"}]
        )
        
        self.assertEqual(result, providers.ChatResponse(content="hola", tool_calls=None))
    
    @patch("core.providers._get_client")
    def test_passes_tools_to_api(self, mock_get_client):
        mock_message = MagicMock(content="ok", tool_calls=None)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        tools = [{"type": "function", "function": {"name": "web_search", "parameters": {}}}]
        providers._call_provider(
            "groq", "llama-3.3-70b-versatile", [{"role": "user", "content": "hola"}], tools=tools
        )
        
        mock_client.chat.completions.create.assert_called_once_with(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "hola"}],
            tools=tools,
        )


@patch("core.providers._call_provider")
def test_chat_passes_a_roles_own_timeout(mock_call):
    chat("vision", [{"role": "user", "content": "hola"}])
    assert mock_call.call_args[1]["timeout"] == config.AGENT_ROLES["vision"]["timeout"]


@patch("core.providers._call_provider")
def test_chat_leaves_the_timeout_unset_for_a_role_that_declares_none(mock_call):
    chat("router", [{"role": "user", "content": "hola"}])
    assert mock_call.call_args[1]["timeout"] is None


@patch("core.providers._get_client")
def test_call_provider_omits_the_timeout_rather_than_sending_null(mock_get_client):
    providers._call_provider("groq", "m", [{"role": "user", "content": "hola"}])
    assert "timeout" not in mock_get_client.return_value.chat.completions.create.call_args[1]


@patch("core.providers._get_client")
def test_call_provider_sends_the_timeout_it_was_given(mock_get_client):
    providers._call_provider("groq", "m", [{"role": "user", "content": "hola"}], timeout=40)
    assert mock_get_client.return_value.chat.completions.create.call_args[1]["timeout"] == 40


if __name__ == "__main__":
    unittest.main()