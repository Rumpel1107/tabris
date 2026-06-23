import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import unittest
from main import route_message, build_messages, should_trigger_memory
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


class TestRouteMessage(unittest.TestCase):

    def test_routes_code_keyword_english(self):
        self.assertEqual(route_message("I have a bug in my code"), "code")

    def test_routes_code_keyword_spanish(self):
        self.assertEqual(route_message("Tengo un error en mi función"), "code")

    def test_routes_general_message(self):
        self.assertEqual(route_message("what is machine learning?"), "general")


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