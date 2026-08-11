import config
import contextlib
import os
import pytest
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import deactivate_fact, create_link_code, create_user, find_link_code, find_user_by_key, get_facts, get_messages, get_user, get_user_channels, init_db, redeem_link_code, register_user_channel, save_fact, save_message, update_user_language, _connect


class TestInitDb(unittest.TestCase):
    
    def test_creates_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            conn.close()
            tables = {row[0] for row in rows}
            self.assertIn("users", tables)
            self.assertIn("facts", tables)
            self.assertIn("messages", tables)
    
    def test_facts_has_is_active_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            conn = sqlite3.connect(db_path)
            cols = [row[1] for row in conn.execute("PRAGMA table_info(facts)").fetchall()]
            conn.close()
            self.assertIn("is_active", cols)
    
    def test_messages_has_is_active_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            conn = sqlite3.connect(db_path)
            cols = [row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()]
            conn.close()
            self.assertIn("is_active", cols)

class TestCreateUser(unittest.TestCase):
    
    def test_creates_user_and_returns_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            
            user_id = create_user(db_path, name="Rumpel", language="es")
            
            self.assertIsNotNone(user_id)
            self.assertIsInstance(user_id, int)
            
    def test_default_language_is_english(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            
            user_id = create_user(db_path, name="Ana")
            
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT language FROM users WHERE id=?", (user_id,)).fetchone()
            conn.close()
            self.assertEqual(row[0], "en")


def test_create_user_stores_location_and_timezone():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        user_id = create_user(db_path, name="Rumpel", language="es",
                              location="Panama", timezone="America/Panama")
        user = get_user(db_path, user_id)
        assert user["location"] == "Panama"
        assert user["timezone"] == "America/Panama"


def test_create_user_defaults_location_and_timezone():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        user_id = create_user(db_path, name="Ana")
        user = get_user(db_path, user_id)
        assert user["location"] == ""
        assert user["timezone"] == "UTC"


class TestGetUser(unittest.TestCase):
    
    def test_returns_user_dict(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            user_id = create_user(db_path, name="Rumpel", language="es")
            
            user = get_user(db_path, user_id)
            
            self.assertEqual(user["name"], "Rumpel")
            self.assertEqual(user["language"], "es")
    
    def test_returns_none_if_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            
            user = get_user(db_path, 999)
            
            self.assertIsNone(user)

class TestFacts(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
        self.user_id = create_user(self.db_path, name="Rumpel", language="es")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    def test_save_and_retrieve_fact(self):
        save_fact(self.db_path, self.user_id, "Prefiere respuestas cortas")
        
        facts = get_facts(self.db_path, self.user_id)
        
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["content"], "Prefiere respuestas cortas")
        self.assertEqual(facts[0]["user_id"], self.user_id)
    
    def test_multiple_facts_same_user(self):
        save_fact(self.db_path, self.user_id, "Trabaja en TaxL")
        save_fact(self.db_path, self.user_id, "Es Scrum Master")
        
        facts = get_facts(self.db_path, self.user_id)
        
        self.assertEqual(len(facts), 2)
    
    def test_facts_isolated_by_user(self):
        other_id = create_user(self.db_path, name="Ana")
        save_fact(self.db_path, self.user_id, "Hecho de Rumpel")
        save_fact(self.db_path, other_id, "Hecho de Ana")
        
        facts = get_facts(self.db_path, self.user_id)
        
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["content"], "Hecho de Rumpel")
    
    def test_duplicate_active_fact_raises(self):
        save_fact(self.db_path, self.user_id, "Trabaja en TaxL")
        with self.assertRaises(sqlite3.IntegrityError):
            save_fact(self.db_path, self.user_id, "Trabaja en TaxL")

class TestMessages(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
        self.user_id = create_user(self.db_path, name="Rumpel", language="es")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    def test_save_and_retrieve_message(self):
        save_message(self.db_path, self.user_id, "user", "Hola Tabris")
        
        messages = get_messages(self.db_path, self.user_id)
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hola Tabris")
    
    def test_get_messages_respects_limit(self):
        for i in range(15):
            save_message(self.db_path, self.user_id, "user", f"mensaje {i}")
        
        messages = get_messages(self.db_path, self.user_id, limit=10)
        
        self.assertEqual(len(messages), 10)
    
    def test_get_messages_returns_most_recent(self):
        for i in range(15):
            save_message(self.db_path, self.user_id, "user", f"mensaje {i}")
        
        messages = get_messages(self.db_path, self.user_id, limit=5)
        
        self.assertEqual(messages[-1]["content"], "mensaje 14")
    
    def test_messages_isolated_by_user(self):
        other_id = create_user(self.db_path, name="Ana")
        save_message(self.db_path, self.user_id, "user", "Mensaje de Rumpel")
        save_message(self.db_path, other_id, "user", "Mensaje de Ana")
        
        messages = get_messages(self.db_path, self.user_id)
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "Mensaje de Rumpel")

class TestDeactivateFact(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
        self.user_id = create_user(self.db_path, name="Rumpel", language="es")
    
    def tearDown(self):
        self.tmp.cleanup()
    
    def test_deactivated_fact_not_returned_by_get_facts(self):
        save_fact(self.db_path, self.user_id, "Hecho activo")
        fact_id = save_fact(self.db_path, self.user_id, "Hecho a desactivar")
        
        deactivate_fact(self.db_path, self.user_id, fact_id)
        
        facts = get_facts(self.db_path, self.user_id)
        contents = [f["content"] for f in facts]
        self.assertIn("Hecho activo", contents)
        self.assertNotIn("Hecho a desactivar", contents)
    
    def test_deactivate_does_not_delete_from_db(self):
        fact_id = save_fact(self.db_path, self.user_id, "Hecho importante")
        deactivate_fact(self.db_path, self.user_id, fact_id)
        
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT is_active FROM facts WHERE id=?", (fact_id,)).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 0)
    
    def test_deactivate_does_not_affect_other_users_fact(self):
        other_user_id = create_user(self.db_path, name="Otro", language="es")
        fact_id = save_fact(self.db_path, other_user_id, "Hecho de otro usuario")
        
        deactivate_fact(self.db_path, self.user_id, fact_id)
        
        facts = get_facts(self.db_path, other_user_id)
        contents = [f["content"] for f in facts]
        self.assertIn("Hecho de otro usuario", contents)

class TestForeignKeyEnforcement(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
    
    def tearDown(self):
        self.tmp.cleanup()
    
    def test_save_fact_with_nonexistent_user_raises(self):
        with self.assertRaises(sqlite3.IntegrityError):
            save_fact(self.db_path, 999, "Hecho huérfano")

class TestUpdateUserLanguage(unittest.TestCase):
    def test_updates_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user(db, "Rumpel", "en")
            update_user_language(db, user_id, "es")
            user = get_user(db, user_id)
            self.assertEqual(user["language"], "es")
    
    def test_does_not_affect_other_users(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            id1 = create_user(db, "Rumpel", "en")
            id2 = create_user(db, "Ana", "en")
            update_user_language(db, id1, "es")
            self.assertEqual(get_user(db, id2)["language"], "en")

class TestUserChannels(unittest.TestCase):

    def test_find_returns_none_when_key_not_registered(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            self.assertIsNone(find_user_by_key(db, "cli", "abc-123"))

    def test_register_then_find_returns_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user(db, "Rumpel", "es")
            register_user_channel(db, user_id, "cli", "abc-123")
            user = find_user_by_key(db, "cli", "abc-123")
            self.assertEqual(user["id"], user_id)
            self.assertEqual(user["language"], "es")

    def test_same_key_different_channel_is_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user(db, "Rumpel", "es")
            register_user_channel(db, user_id, "cli", "shared-key")
            self.assertIsNone(find_user_by_key(db, "telegram", "shared-key"))
    
    def test_duplicate_channel_key_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            id1 = create_user(db, "Rumpel", "es")
            id2 = create_user(db, "Ana", "en")
            register_user_channel(db, id1, "cli", "dup-key")
            with self.assertRaises(sqlite3.IntegrityError):
                register_user_channel(db, id2, "cli", "dup-key")

def test_create_link_code_returns_unique_codes(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")

    code1 = create_link_code(db_path, user_id)
    code2 = create_link_code(db_path, user_id)

    assert isinstance(code1, str) and code1
    assert code1 != code2


@pytest.mark.parametrize("text, expected", [
    ("A2CD4FGH", "A2CD4FGH"),
    ("  a2cd4fgh  ", "A2CD4FGH"),
    ("Tengo este codigo A2CD4FGH", "A2CD4FGH"),
    ("mi codigo es a2cd4fgh, gracias", "A2CD4FGH"),
    ("Me llamo Carlos", None),
    ("MARGARET", None),
    ("A2CD4FG", None),
    ("A2CD4FGHJ", None),
    ("A2CD4F$H", None),
    ("A2CD4FG0", None),
    ("", None),
])
def test_find_link_code(text, expected):
    assert find_link_code(text) == expected


def test_find_link_code_accepts_what_create_link_code_produces(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")

    code = create_link_code(db_path, user_id)

    assert find_link_code(code) == code


def test_create_link_code_always_contains_a_digit(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")

    codes = [create_link_code(db_path, user_id) for _ in range(50)]

    assert all(any(char.isdigit() for char in code) for code in codes)


def test_create_link_code_invalidates_previous_unused_codes(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")

    old_code = create_link_code(db_path, user_id)
    new_code = create_link_code(db_path, user_id)

    assert redeem_link_code(db_path, old_code, "discord", "disc-key-1") is None
    assert redeem_link_code(db_path, new_code, "discord", "disc-key-2") == user_id


def test_create_link_code_leaves_other_users_codes_active(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    other_id = create_user(db_path, "Ana", "en")
    other_code = create_link_code(db_path, other_id)

    create_link_code(db_path, user_id)

    assert redeem_link_code(db_path, other_code, "discord", "disc-key-1") == other_id


def test_redeem_link_code_links_new_channel(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    code = create_link_code(db_path, user_id)

    result = redeem_link_code(db_path, code, "discord", "disc-key-1")
    linked = find_user_by_key(db_path, "discord", "disc-key-1")

    assert result == user_id
    assert linked is not None and linked["id"] == user_id


def test_redeem_rejects_expired_code(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    monkeypatch.setattr(config, "LINK_CODE_TTL_SECONDS", -60)   # code is born already expired
    code = create_link_code(db_path, user_id)

    result = redeem_link_code(db_path, code, "discord", "disc-key-1")

    assert result is None
    assert find_user_by_key(db_path, "discord", "disc-key-1") is None


def test_redeem_code_is_single_use(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    code = create_link_code(db_path, user_id)

    first = redeem_link_code(db_path, code, "discord", "disc-key-1")
    second = redeem_link_code(db_path, code, "telegram", "tg-key-1")

    assert first == user_id
    assert second is None
    assert find_user_by_key(db_path, "telegram", "tg-key-1") is None


class TestNonUniqueNames(unittest.TestCase):
    
    def test_two_users_can_share_a_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            id1 = create_user(db, "Oscar", "es")
            id2 = create_user(db, "Oscar", "en")
            self.assertNotEqual(id1, id2)


def test_deactivate_fact_sets_retired_at(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    save_fact(db_path, user_id, "Trabaja en TaxL")
    fact_id = get_facts(db_path, user_id)[0]["id"]

    deactivate_fact(db_path, user_id, fact_id)

    import sqlite3
    conn = sqlite3.connect(db_path)
    retired_at = conn.execute("SELECT retired_at FROM facts WHERE id=?", (fact_id,)).fetchone()[0]
    conn.close()
    assert retired_at is not None


def test_get_facts_orders_by_id_when_timestamps_tie(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    saved_ids = [save_fact(db_path, user_id, f"Hecho {n}") for n in range(12)]

    assert [fact["id"] for fact in get_facts(db_path, user_id)] == saved_ids


def test_get_user_channels_returns_channel_names(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    register_user_channel(db_path, user_id, "cli", "cli-key-1")
    register_user_channel(db_path, user_id, "discord", "disc-key-1")

    assert get_user_channels(db_path, user_id) == ["cli", "discord"]


def test_get_user_channels_excludes_other_users(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    other_id = create_user(db_path, "Ana", "en")
    register_user_channel(db_path, user_id, "cli", "cli-key-1")
    register_user_channel(db_path, other_id, "discord", "disc-key-1")

    assert get_user_channels(db_path, user_id) == ["cli"]


@pytest.mark.parametrize("pragma, expected", [
    ("journal_mode", "wal"),
    ("busy_timeout", config.DB_BUSY_TIMEOUT_MS),
])
def test_connect_sets_concurrency_pragmas(tmp_path, pragma, expected):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    with contextlib.closing(_connect(db_path)) as conn:
        assert conn.execute(f"PRAGMA {pragma}").fetchone()[0] == expected


if __name__ == "__main__":
    unittest.main()