import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
import time
import unittest
from unittest.mock import patch

from config import MAX_HISTORY, MEMORY_TRIGGER_EXCHANGES, MEMORY_TRIGGER_SECONDS
from core import providers
from core.conversation import build_messages, handle_turn, route_message, run_with_tools, should_trigger_memory, WEB_FETCH_TOOL, WEB_SEARCH_TOOL
from core.db import create_user, get_messages, init_db, save_fact
from core.session import Session
from types import SimpleNamespace


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
    
    def test_triggers_at_exchanges_threshold(self):
        last_trigger = time.time()
        self.assertTrue(should_trigger_memory(MEMORY_TRIGGER_EXCHANGES, last_trigger))
    
    def test_does_not_trigger_below_exchanges_threshold(self):
        last_trigger = time.time()
        self.assertFalse(should_trigger_memory(MEMORY_TRIGGER_EXCHANGES - 1, last_trigger))
    
    def test_triggers_after_inactivity_threshold(self):
        last_trigger = time.time() - (MEMORY_TRIGGER_SECONDS + 1)
        self.assertTrue(should_trigger_memory(0, last_trigger))
    
    def test_does_not_trigger_before_inactivity_threshold(self):
        last_trigger = time.time() - (MEMORY_TRIGGER_SECONDS - 1)
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
    
    @patch("core.conversation.providers.chat")
    def test_offers_web_search_and_web_fetch_tools(self, mock_chat):
        mock_chat.return_value = providers.ChatResponse(content="Respuesta de Tabris", tool_calls=None)
        
        handle_turn(self.session, "Hola", "general", self.db_path)
        
        called_tools = mock_chat.call_args[1]["tools"]
        self.assertEqual(called_tools, [WEB_SEARCH_TOOL, WEB_FETCH_TOOL])


@patch("core.conversation.providers.chat")
def test_handle_turn_refreshes_system_prompt_each_turn(mock_chat):
    mock_chat.return_value = providers.ChatResponse(content="ok", tool_calls=None)
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "refresh.db")
        init_db(db_path)
        user_id = create_user(db_path, "Rumpel", "es")
        save_fact(db_path, user_id, "Le gusta el café")
        session = Session(
            user_id=user_id,
            language="es",
            conversation_history=[{"role": "system", "content": "sys"}],
        )

        handle_turn(session, "hola", "general", db_path, persona="PERSONA")
        save_fact(db_path, user_id, "Vive en Panama")
        handle_turn(session, "otra", "general", db_path, persona="PERSONA")

        assert "Vive en Panama" in session.conversation_history[0]["content"]


class TestRunWithTools(unittest.TestCase):
    
    @patch("core.conversation.web_search")
    @patch("core.conversation.providers.chat")
    def test_executes_tool_call_and_returns_final_answer(self, mock_chat, mock_search):
        tool_call = SimpleNamespace(
            id="call_1",
            function=SimpleNamespace(name="web_search", arguments='{"query": "clima en Panama"}'),
        )
        mock_chat.side_effect = [
            providers.ChatResponse(content=None, tool_calls=[tool_call]),
            providers.ChatResponse(content="Hace sol en Panama", tool_calls=None),
        ]
        mock_search.return_value = "resultado de busqueda"
        
        messages = [{"role": "user", "content": "como esta el clima en Panama?"}]
        result = run_with_tools("general", messages, tools=[WEB_SEARCH_TOOL])
        
        self.assertEqual(result, "Hace sol en Panama")
        mock_search.assert_called_once_with(query="clima en Panama")
        self.assertEqual(mock_chat.call_count, 2)
        
        second_call_messages = mock_chat.call_args_list[1][0][1]
        self.assertEqual(second_call_messages[-1]["role"], "tool")
        self.assertEqual(second_call_messages[-1]["content"], "resultado de busqueda")
        self.assertEqual(second_call_messages[-1]["tool_call_id"], "call_1")


@patch("core.conversation.web_fetch")
@patch("core.conversation.providers.chat")
def test_run_with_tools_dispatches_web_fetch(mock_chat, mock_fetch):
    tool_call = SimpleNamespace(
        id="call_2",
        function=SimpleNamespace(name="web_fetch", arguments='{"url": "https://example.com/a"}'),
    )
    mock_chat.side_effect = [
        providers.ChatResponse(content=None, tool_calls=[tool_call]),
        providers.ChatResponse(content="La pagina habla de X", tool_calls=None),
    ]
    mock_fetch.return_value = "contenido de la pagina"

    messages = [{"role": "user", "content": "que dice example.com/a?"}]
    result = run_with_tools("general", messages, tools=[WEB_SEARCH_TOOL, WEB_FETCH_TOOL])

    assert result == "La pagina habla de X"
    mock_fetch.assert_called_once_with(url="https://example.com/a")

    tool_message = mock_chat.call_args_list[1][0][1][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["content"] == "contenido de la pagina"
    assert tool_message["tool_call_id"] == "call_2"


if __name__ == "__main__":
    unittest.main()