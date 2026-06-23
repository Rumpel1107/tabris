import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import patch
from core.providers import chat


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

if __name__ == "__main__":
    unittest.main()