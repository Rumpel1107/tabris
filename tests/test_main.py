import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import time
import unittest
from main import route_message, build_messages, should_trigger_memory, build_system_prompt, load_persona
from config import MAX_HISTORY
from unittest.mock import patch, MagicMock, mock_open


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

class TestBuildSystemPrompt(unittest.TestCase):

    def test_includes_persona(self):
        persona = "You are Tabris. Be concise."
        result = build_system_prompt(persona, [])
        self.assertIn("You are Tabris. Be concise.", result)

    def test_includes_each_fact(self):
        persona = "You are Tabris."
        facts = [
            {"content": "Name: Rumpel"},
            {"content": "Based in Colombia"},
        ]
        result = build_system_prompt(persona, facts)
        self.assertIn("Name: Rumpel", result)
        self.assertIn("Based in Colombia", result)

    def test_empty_facts_returns_persona_only(self):
        persona = "You are Tabris."
        result = build_system_prompt(persona, [])
        self.assertEqual(result, persona)

    def test_facts_header_present_only_when_facts_exist(self):
        persona = "You are Tabris."
        self.assertNotIn("What I know about the user", build_system_prompt(persona, []))
        with_facts = build_system_prompt(persona, [{"content": "Name: Rumpel"}])
        self.assertIn("What I know about the user", with_facts)

class TestLoadPersona(unittest.TestCase):

    def test_reads_file_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "persona.md")
            with open(path, "w") as f:
                f.write("You are an assistant. Be concise.")
            result = load_persona(path)
            self.assertIn("Be concise.", result)

    def test_substitutes_agent_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "persona.md")
            with open(path, "w") as f:
                f.write("You are {{AGENT_NAME}}.")
            result = load_persona(path)
            self.assertIn("You are Tabris.", result)
            self.assertNotIn("{{AGENT_NAME}}", result)

class TestRouteMessage(unittest.TestCase):

    @patch("main.providers.chat")
    def test_routes_to_code(self, mock_chat):
        mock_chat.return_value = "code"
        self.assertEqual(route_message("Fix this bug"), "code")

    @patch("main.providers.chat")
    def test_routes_to_general(self, mock_chat):
        mock_chat.return_value = "general"
        self.assertEqual(route_message("What is machine learning?"), "general")

    @patch("main.providers.chat")
    def test_routes_to_exit(self, mock_chat):
        mock_chat.return_value = "exit"
        self.assertEqual(route_message("quiero salir"), "exit")

    @patch("main.providers.chat")
    def test_unknown_response_falls_back_to_general(self, mock_chat):
        mock_chat.return_value = "algo inesperado"
        self.assertEqual(route_message("hola"), "general")

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


if __name__ == "__main__":
    unittest.main()