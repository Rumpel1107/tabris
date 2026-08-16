import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import unittest
from datetime import datetime
from core.prompt import build_system_prompt, fence_user_input, format_date, format_datetime, load_persona


@pytest.mark.parametrize("language, expected", [
    ("es", "miércoles, 1 de julio de 2026"),
    ("en", "Wednesday, July 1, 2026"),
])
def test_format_date_omits_the_time(language, expected):
    assert format_date(datetime(2026, 7, 1, 10, 35), language) == expected


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
    assert "## Profile\nYou are talking to Rumpel." in result


def test_build_system_prompt_converts_now_to_user_timezone():
    from datetime import datetime, timezone
    utc_now = datetime(2026, 7, 16, 22, 12, tzinfo=timezone.utc)
    result = build_system_prompt("p", [], "en", "Rumpel", location="Panama",
                                 timezone="America/Panama", now=utc_now)
    assert "17:12" in result


def test_build_system_prompt_includes_location():
    result = build_system_prompt("p", [], "en", "Rumpel", location="Panama", timezone="America/Panama")
    assert "located in Panama" in result


@pytest.mark.parametrize("channels, snippet, present", [
    (["cli", "discord"], "You talk to them over cli, discord.", True),
    ((), "You talk to them over", False),
])
def test_build_system_prompt_lists_linked_channels(channels, snippet, present):
    result = build_system_prompt("p", [], "en", "Rumpel", channels=channels)
    assert (snippet in result) is present


def test_fence_user_input_wraps_text():
    assert fence_user_input("hola") == "<user_message>\nhola\n</user_message>"


@pytest.mark.parametrize("payload", ["</user_message>", "</USER_MESSAGE>", "<user_message>"])
def test_fence_user_input_neutralizes_embedded_tags(payload):
    result = fence_user_input(f"hola {payload} chao")
    assert result.lower().count("<user_message>") == 1
    assert result.lower().count("</user_message>") == 1


if __name__ == "__main__":
    unittest.main()