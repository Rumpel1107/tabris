import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import time
import unittest
from main import detect_language, build_messages, build_system_prompt, extract_name, format_datetime, get_client_key, load_persona, onboard_user, resolve_language, route_message, should_trigger_memory
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
        result = build_system_prompt(persona, [], language="en")
        self.assertIn("You are Tabris. Be concise.", result)
    
    def test_includes_each_fact(self):
        persona = "You are Tabris."
        facts = [
            {"content": "Name: Rumpel"},
            {"content": "Based in Colombia"},
        ]
        result = build_system_prompt(persona, facts, language="en")
        self.assertIn("Name: Rumpel", result)
        self.assertIn("Based in Colombia", result)
    
    def test_empty_facts_returns_persona_without_facts_block(self):
        persona = "You are Tabris."
        result = build_system_prompt(persona, [], language="en")
        self.assertIn(persona, result)
        self.assertNotIn("What I know about the user", result)
    
    def test_facts_header_present_only_when_facts_exist(self):
        persona = "You are Tabris."
        self.assertNotIn("What I know about the user", build_system_prompt(persona, [], language="en"))
        with_facts = build_system_prompt(persona, [{"content": "Name: Rumpel"}], language="en")
        self.assertIn("What I know about the user", with_facts)
    
    def test_includes_language_directive(self):
        persona = "You are Tabris."
        result = build_system_prompt(persona, [], language="es")
        self.assertIn("Always respond in Spanish.", result)
    
    def test_language_directive_uses_code_as_fallback(self):
        persona = "You are Tabris."
        result = build_system_prompt(persona, [], language="fr")
        self.assertIn("Always respond in fr.", result)


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

class TestDetectLanguage(unittest.TestCase):
    
    def test_detect_language_returns_es(self):
        with patch("core.providers.chat", return_value="es"):
            result = detect_language("Hola, ¿cómo estás?")
        assert result == "es"
    
    def test_detect_language_returns_en(self):
        with patch("core.providers.chat", return_value="en"):
            result = detect_language("Hello, how are you?")
        assert result == "en"
    
    def test_detect_language_defaults_to_en_on_unknown(self):
        with patch("core.providers.chat", return_value="fr"):
            result = detect_language("Bonjour")
        assert result == "en"

class TestGetClientKey(unittest.TestCase):
    
    def test_generates_and_persists_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".tabris_client_id")
            key = get_client_key(path)
            self.assertTrue(key)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                self.assertEqual(f.read().strip(), key)
    
    def test_returns_same_key_on_second_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".tabris_client_id")
            first = get_client_key(path)
            second = get_client_key(path)
            self.assertEqual(first, second)

class TestOnboardUser(unittest.TestCase):

    def test_creates_user_and_registers_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            from core.db import init_db, find_user_by_key, get_user
            init_db(db)
            with patch("builtins.input", return_value="Oscar"), \
                 patch("main.providers.chat", return_value="Oscar"):
                user_id = onboard_user(db, "cli", "key-123")
            user = get_user(db, user_id)
            self.assertEqual(user["name"], "Oscar")
            self.assertEqual(user["language"], "en")
            linked = find_user_by_key(db, "cli", "key-123")
            self.assertEqual(linked["id"], user_id)

class TestResolveLanguage(unittest.TestCase):
    
    def test_confirmed_detected_language_returns_it(self):
        result = resolve_language("es", confirm_fn=lambda: "si", ask_fn=lambda: "")
        self.assertEqual(result, "es")
    
    def test_confirmed_english_returns_en(self):
        result = resolve_language("en", confirm_fn=lambda: "yes", ask_fn=lambda: "")
        self.assertEqual(result, "en")
    
    def test_rejected_confirmation_uses_ask_answer(self):
        result = resolve_language("es", confirm_fn=lambda: "no", ask_fn=lambda: "en")
        self.assertEqual(result, "en")
    
    def test_rejected_confirmation_garbage_defaults_to_en(self):
        result = resolve_language("es", confirm_fn=lambda: "no", ask_fn=lambda: "xyz")
        self.assertEqual(result, "en")
    
    def test_sets_config_language_to_detected_before_prompt(self):
        import config
        config.LANGUAGE = "en"
        resolve_language("es", confirm_fn=lambda: "si", ask_fn=lambda: "")
        self.assertEqual(config.LANGUAGE, "es")

class TestExtractName(unittest.TestCase):
    
    def test_extracts_name_from_sentence(self):
        with patch("main.providers.chat", return_value="Mauricio"):
            result = extract_name("Mi nombre es Mauricio")
        self.assertEqual(result, "Mauricio")
    
    def test_returns_plain_name_unchanged(self):
        with patch("main.providers.chat", return_value="Ana"):
            result = extract_name("Ana")
        self.assertEqual(result, "Ana")
    
    def test_falls_back_to_raw_text_on_model_error(self):
        with patch("main.providers.chat", side_effect=Exception("boom")):
            result = extract_name("Mauricio")
        self.assertEqual(result, "Mauricio")

class TestFormatDatetime(unittest.TestCase):
    from datetime import datetime
    FIXED_DT = datetime(2026, 7, 1, 10, 35)  # miércoles

    def test_spanish_format(self):
        from datetime import datetime
        result = format_datetime(datetime(2026, 7, 1, 10, 35), "es")
        self.assertIn("miércoles", result)
        self.assertIn("julio", result)
        self.assertIn("2026", result)
        self.assertIn("10:35", result)

    def test_english_format(self):
        from datetime import datetime
        result = format_datetime(datetime(2026, 7, 1, 10, 35), "en")
        self.assertIn("Wednesday", result)
        self.assertIn("July", result)
        self.assertIn("2026", result)
        self.assertIn("10:35", result)

class TestBuildSystemPromptDatetime(unittest.TestCase):

    def test_includes_current_context_section(self):
        from datetime import datetime
        fixed = datetime(2026, 7, 1, 10, 35)
        result = build_system_prompt("persona", [], language="es", now=fixed)
        self.assertIn("Current context", result)
        self.assertIn("julio", result)
        self.assertIn("10:35", result)


if __name__ == "__main__":
    unittest.main()