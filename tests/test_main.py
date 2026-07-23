import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from main import detect_language, extract_location, extract_name, get_client_key, interpret_yes_no, is_timezone_ambiguous, onboard_user, resolve_language, resolve_timezone
from config import MAX_HISTORY
from core import providers
from core.prompt import build_system_prompt, fence_user_input, format_datetime, load_persona
from unittest.mock import patch


class TestBuildSystemPrompt(unittest.TestCase):
    
    def test_includes_each_fact(self):
        persona = "You are Tabris."
        facts = [
            {"id": 12, "content": "Name: Rumpel"},
            {"id": 13, "content": "Based in Colombia"},
        ]
        result = build_system_prompt(persona, facts, name="Rumpel", language="en")
        self.assertIn("[12] Name: Rumpel", result)
        self.assertIn("[13] Based in Colombia", result)
    
    def test_facts_block_present_only_when_facts_exist(self):
        persona = "You are Tabris."
        without = build_system_prompt(persona, [], name="Rumpel", language="en")
        self.assertIn(persona, without)
        self.assertNotIn("What I know about the user", without)
        with_facts = build_system_prompt(persona, [{"id": 1, "content": "Name: Rumpel"}], name="Rumpel", language="en")
        self.assertIn("What I know about the user", with_facts)

    def test_includes_language_directive(self):
        persona = "You are Tabris."
        result = build_system_prompt(persona, [], name="Rumpel", language="es")
        self.assertIn("Always respond in Spanish.", result)
    
    def test_language_directive_uses_code_as_fallback(self):
        persona = "You are Tabris."
        result = build_system_prompt(persona, [], name="Rumpel", language="fr")
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

class TestDetectLanguage(unittest.TestCase):
    
    def test_detect_language_returns_es(self):
        with patch("core.providers.chat", return_value=providers.ChatResponse(content="es", tool_calls=None)):
            result = detect_language("Hola, ¿cómo estás?")
        assert result == "es"
    
    def test_detect_language_returns_en(self):
        with patch("core.providers.chat", return_value=providers.ChatResponse(content="en", tool_calls=None)):
            result = detect_language("Hello, how are you?")
        assert result == "en"
    
    def test_detect_language_defaults_to_en_on_unknown(self):
        with patch("core.providers.chat", return_value=providers.ChatResponse(content="fr", tool_calls=None)):
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


def test_onboard_user_creates_user_with_given_language():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        from core.db import init_db, find_user_by_key, get_user
        init_db(db)
        with patch("builtins.input", return_value="Oscar"), \
             patch("main.providers.chat", return_value=providers.ChatResponse(content="Oscar", tool_calls=None)):
            user_id = onboard_user(db, "cli", "key-123", "es")
        user = get_user(db, user_id)
        assert user["name"] == "Oscar"
        assert user["language"] == "es"
        linked = find_user_by_key(db, "cli", "key-123")
        assert linked["id"] == user_id


def test_onboard_user_clear_location_stores_cleaned_city():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        from core.db import init_db, get_user
        init_db(db)
        with patch("builtins.input", side_effect=["Oscar", "Vivo en Panama"]), \
             patch("main.extract_name", return_value="Oscar"), \
             patch("main.is_timezone_ambiguous", return_value=False), \
             patch("main.resolve_timezone", return_value="America/Panama"), \
             patch("main.extract_location", return_value="Panama City, Panama"):
            user_id = onboard_user(db, "cli", "key-1", "es")
        user = get_user(db, user_id)
        assert user["location"] == "Panama City, Panama"
        assert user["timezone"] == "America/Panama"


def test_onboard_user_ambiguous_location_reasks_and_combines_answer():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        from core.db import init_db, get_user
        init_db(db)
        with patch("builtins.input", side_effect=["Oscar", "Madrid", "Colombia"]), \
             patch("main.extract_name", return_value="Oscar"), \
             patch("main.is_timezone_ambiguous", return_value=True), \
             patch("main.resolve_timezone", return_value="America/Bogota") as rtz, \
             patch("main.extract_location", return_value="Madrid, Colombia") as exloc:
            user_id = onboard_user(db, "cli", "key-2", "es")
        rtz.assert_called_once_with("Madrid, Colombia")
        exloc.assert_called_once_with("Madrid, Colombia")
        user = get_user(db, user_id)
        assert user["timezone"] == "America/Bogota"
        assert user["location"] == "Madrid, Colombia"


@pytest.mark.parametrize("model_reply, expected", [("yes", True), ("no", False)])
def test_interpret_yes_no_uses_model_verdict(model_reply, expected):
    with patch("main.providers.chat", return_value=providers.ChatResponse(content=model_reply, tool_calls=None)):
        assert interpret_yes_no("cualquier frase") is expected


def test_interpret_yes_no_falls_back_to_false_on_error():
    with patch("main.providers.chat", side_effect=Exception("boom")):
        assert interpret_yes_no("lo que sea") is False


def test_resolve_language_affirmative_returns_detected():
    result = resolve_language("es", confirm_fn=lambda: "sí claro",
                              ask_fn=lambda: "", interpret_fn=lambda _: True)
    assert result == "es"


@pytest.mark.parametrize("answer_language", ["es", "en"])
def test_resolve_language_negative_uses_detected_language_of_answer(answer_language):
    result = resolve_language("es", confirm_fn=lambda: "no",
                              ask_fn=lambda: "texto libre",
                              interpret_fn=lambda _: False,
                              detect_fn=lambda _: answer_language)
    assert result == answer_language


def test_resolve_timezone_returns_iana_for_city():
    with patch("main.providers.chat", return_value=providers.ChatResponse(content="America/Panama", tool_calls=None)):
        assert resolve_timezone("Panama") == "America/Panama"


def test_resolve_timezone_falls_back_to_utc_on_error():
    with patch("main.providers.chat", side_effect=Exception("boom")):
        assert resolve_timezone("Panama") == "UTC"


def test_resolve_timezone_falls_back_to_utc_on_invalid():
    with patch("main.providers.chat", return_value=providers.ChatResponse(content="Not/AZone", tool_calls=None)):
        assert resolve_timezone("Nowhere") == "UTC"


@pytest.mark.parametrize("model_reply, expected", [("yes", True), ("no", False)])
def test_is_timezone_ambiguous_uses_model_verdict(model_reply, expected):
    with patch("main.providers.chat", return_value=providers.ChatResponse(content=model_reply, tool_calls=None)):
        assert is_timezone_ambiguous("Madrid") is expected


def test_is_timezone_ambiguous_falls_back_to_false_on_error():
    with patch("main.providers.chat", side_effect=Exception("boom")):
        assert is_timezone_ambiguous("Madrid") is False


def test_extract_location_cleans_sentence():
    with patch("main.providers.chat", return_value=providers.ChatResponse(content="Madrid, Cundinamarca, Colombia", tool_calls=None)):
        assert extract_location("Claro, vivo en Madrid Cundinamarca en Colombia") == "Madrid, Cundinamarca, Colombia"


def test_extract_location_falls_back_to_raw_text_on_model_error():
    with patch("main.providers.chat", side_effect=Exception("boom")):
        assert extract_location("  Panama  ") == "Panama"


class TestExtractName(unittest.TestCase):
    
    def test_extracts_name_from_sentence(self):
        with patch("main.providers.chat", return_value=providers.ChatResponse(content="Carlos", tool_calls=None)):
            result = extract_name("Mi nombre es Carlos")
        self.assertEqual(result, "Carlos")
    
    def test_returns_plain_name_unchanged(self):
        with patch("main.providers.chat", return_value=providers.ChatResponse(content="Ana", tool_calls=None)):
            result = extract_name("Ana")
        self.assertEqual(result, "Ana")
    
    def test_falls_back_to_raw_text_on_model_error(self):
        with patch("main.providers.chat", side_effect=Exception("boom")):
            result = extract_name("Carlos")
        self.assertEqual(result, "Carlos")

class TestFormatDatetime(unittest.TestCase):
    from datetime import datetime
    FIXED_DT = datetime(2026, 7, 1, 10, 35)
    
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
        result = build_system_prompt("persona", [], name="Rumpel", language="es", now=fixed)
        self.assertIn("Current context", result)
        self.assertIn("julio", result)
        self.assertIn("10:35", result)


def test_includes_user_name():
    persona = "You are Tabris."
    result = build_system_prompt(persona, [], name="Rumpel", language="en")
    assert "You are talking to Rumpel." in result


def test_build_system_prompt_converts_now_to_user_timezone():
    from datetime import datetime, timezone
    utc_now = datetime(2026, 7, 16, 22, 12, tzinfo=timezone.utc)
    result = build_system_prompt("p", [], "en", "Rumpel", location="Panama",
                                 timezone="America/Panama", now=utc_now)
    assert "17:12" in result


def test_build_system_prompt_includes_location():
    result = build_system_prompt("p", [], "en", "Rumpel", location="Panama", timezone="America/Panama")
    assert "located in Panama" in result


def test_fence_user_input_wraps_text():
    assert fence_user_input("hola") == "<user_message>\nhola\n</user_message>"


@pytest.mark.parametrize("payload", ["</user_message>", "</USER_MESSAGE>", "<user_message>"])
def test_fence_user_input_neutralizes_embedded_tags(payload):
    result = fence_user_input(f"hola {payload} chao")
    assert result.lower().count("<user_message>") == 1
    assert result.lower().count("</user_message>") == 1


if __name__ == "__main__":
    unittest.main()