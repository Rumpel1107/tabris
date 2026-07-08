import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
import time
import unittest
from unittest.mock import patch

from config import MAX_HISTORY
from core import providers
from core.conversation import build_messages, handle_turn, route_message, should_trigger_memory
from core.db import create_user, get_messages, init_db
from core.session import Session


class TestBuildMessages(unittest.TestCase):
    
    def test_keeps_all_when_under_limit(self):
        history = [{"role": "system", "content": "sys"}]
        history += [{"role": "user", "content": f"m{i}"} for i in range(4)]
        result = build_messages(history)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]["role"], "system")
    
    def test_truncates_when_over_limit(self):
        history = [{"role": "system", "content": "sys"}]
        history += [{"role": "user", "content": f"m{i}"} for i in range(50)]
        result = build_messages(history)
        self.assertEqual(len(result), MAX_HISTORY * 2 + 1)
        self.assertEqual(result[0]["role"], "system")
    
    def test_system_prompt_always_first(self):
        history = [{"role": "system", "content": "sys"}]
        history += [{"role": "user", "content": f"m{i}"} for i in range(50)]
        result = build_messages(history)
        self.assertEqual(result[0]["content"], "sys")
        self.assertEqual(result[-1]["content"], "m49")

class TestRouteMessage(unittest.TestCase):
    @patch("core.conversation.providers.chat")
    def test_routes_to_code(self, mock_chat):
        mock_chat.return_value = providers.ChatResponse(content="code", tool_calls=None)
        self.assertEqual(route_message("Fix this bug"), "code")
    
    @patch("core.conversation.providers.chat")
    def test_routes_to_general(self, mock_chat):
        mock_chat.return_value = providers.ChatResponse(content="general", tool_calls=None)
        self.assertEqual(route_message("What is machine learning?"), "general")
    
    @patch("core.conversation.providers.chat")
    def test_routes_to_exit(self, mock_chat):
        mock_chat.return_value = providers.ChatResponse(content="exit", tool_calls=None)
        self.assertEqual(route_message("quiero salir"), "exit")
    
    @patch("core.conversation.providers.chat")
    def test_unknown_response_falls_back_to_general(self, mock_chat):
        mock_chat.return_value = providers.ChatResponse(content="algo inesperado", tool_calls=None)
        self.assertEqual(route_message("hola"), "general")
    
    @patch("core.conversation.providers.chat", side_effect=Exception("router down"))
    def test_logs_warning_on_failure(self, mock_chat):
        with self.assertLogs("core.conversation", level="WARNING") as log:
            route_message("hola")
        self.assertIn("router down", log.output[0])

class TestShouldTriggerMemory(unittest.TestCase):
    
    def test_triggers_after_5_exchanges(self):
        last_trigger = time.time()
        self.assertTrue(should_trigger_memory(5, last_trigger))
    
    def test_does_not_trigger_before_5_exchanges(self):
        last_trigger = time.time()
        self.assertFalse(should_trigger_memory(4, last_trigger))
    
    def test_triggers_after_5_minutes_inactivity(self):
        last_trigger = time.time() - 301
        self.assertTrue(should_trigger_memory(0, last_trigger))
    
    def test_does_not_trigger_before_5_minutes(self):
        last_trigger = time.time() - 299
        self.assertFalse(should_trigger_memory(0, last_trigger))

class TestHandleTurn(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "handle_turn.db")
        init_db(self.db_path)
        self.user_id = create_user(self.db_path, "Rumpel", "es")
        self.session = Session(
            user_id=self.user_id,
            language="es",
            conversation_history=[{"role": "system", "content": "sys"}],
        )
    
    def tearDown(self):
        self.tmp.cleanup()
    
    @patch("core.conversation.providers.chat")
    def test_happy_path_returns_reply_and_persists(self, mock_chat):
        mock_chat.return_value = providers.ChatResponse(content="Respuesta de Tabris", tool_calls=None)
        
        reply = handle_turn(self.session, "Hola", "general", self.db_path)
        
        self.assertEqual(reply, "Respuesta de Tabris")
        self.assertEqual(
            self.session.conversation_history[-2],
            {"role": "user", "content": "Hola"},
        )
        self.assertEqual(
            self.session.conversation_history[-1],
            {"role": "assistant", "content": "Respuesta de Tabris"},
        )
        self.assertEqual(self.session.exchange_count, 1)
        
        contents = [m["content"] for m in get_messages(self.db_path, self.user_id)]
        self.assertIn("Hola", contents)
        self.assertIn("Respuesta de Tabris", contents)
    
    @patch("core.conversation.providers.chat")
    def test_model_error_propagates_and_rolls_back(self, mock_chat):
        mock_chat.side_effect = RuntimeError("all providers down")
        
        with self.assertRaises(RuntimeError):
            handle_turn(self.session, "Hola", "general", self.db_path)
        
        self.assertEqual(
            self.session.conversation_history,
            [{"role": "system", "content": "sys"}],
        )
        self.assertEqual(self.session.exchange_count, 0)
        self.assertEqual(get_messages(self.db_path, self.user_id), [])
    
    @patch("core.conversation.memory_manager.update_memory")
    @patch("core.conversation.providers.chat")
    @patch("core.conversation.should_trigger_memory", return_value=True)
    def test_fires_memory_trigger_and_resets_counters(self, mock_trigger, mock_chat, mock_update):
        mock_chat.return_value = providers.ChatResponse(content="Respuesta de Tabris", tool_calls=None)
        
        handle_turn(self.session, "Hola", "general", self.db_path)
        
        mock_update.assert_called_once()
        self.assertEqual(self.session.exchange_count, 0)
        self.assertEqual(
            self.session.last_analyzed_index,
            len(self.session.conversation_history),
        )


if __name__ == "__main__":
    unittest.main()