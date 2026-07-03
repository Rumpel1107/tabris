import config
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from core import providers
from core.providers import chat
from unittest.mock import patch


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
        )
    
    @patch("core.providers.OpenAI")
    def test_reuses_cached_client(self, mock_openai_class):
        first = providers._get_client("groq")
        second = providers._get_client("groq")
        self.assertIs(first, second)
        mock_openai_class.assert_called_once()


if __name__ == "__main__":
    unittest.main()