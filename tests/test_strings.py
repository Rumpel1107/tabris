from core.strings import msg

def test_msg_returns_spanish_string():
    assert msg("exit_command", "es") == "salir"

def test_msg_returns_english_string():
    assert msg("exit_command", "en") == "exit"

def test_msg_formats_kwargs():
    result = msg("startup", "en", agent="Tabris", exit_cmd="exit")
    assert result == "Tabris is active. Type 'exit' to end the session. How can I help you today?"