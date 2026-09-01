import config
import contextlib
import os
import pytest
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import deactivate_fact, deactivate_message, deactivate_user, create_link_code, create_user, create_user_with_channel, delete_messages_before, delete_user_completely, find_link_code, find_user_by_key, get_deactivated_users, get_facts, get_last_message_time, get_messages, get_user, get_user_channels, get_user_records, init_db, reactivate_user, redeem_link_code, register_user_channel, save_fact, save_message, update_user_profile, _connect


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

    def test_creates_the_data_directory_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = os.path.join(tmp, "data")
            init_db(os.path.join(data_dir, "test.db"))
            self.assertTrue(os.path.isdir(data_dir))
            self.assertEqual(os.stat(data_dir).st_mode & 0o777, 0o700)

    def test_creates_the_database_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            self.assertEqual(os.stat(db_path).st_mode & 0o777, 0o600)

    def test_locks_down_a_data_directory_that_already_existed(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = os.path.join(tmp, "data")
            os.makedirs(data_dir, mode=0o755)
            init_db(os.path.join(data_dir, "test.db"))
            self.assertEqual(os.stat(data_dir).st_mode & 0o777, 0o700)

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


def test_users_has_deactivated_at_column():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        with contextlib.closing(_connect(db_path)) as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        assert "deactivated_at" in cols


def test_init_db_adds_deactivated_at_to_an_older_database():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        user_id = create_user(db_path, name="Ana")
        with contextlib.closing(_connect(db_path)) as conn:
            conn.execute("ALTER TABLE users DROP COLUMN deactivated_at")
            conn.commit()

        init_db(db_path)

        with contextlib.closing(_connect(db_path)) as conn:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        assert "deactivated_at" in cols
        assert get_user(db_path, user_id)["name"] == "Ana"


def test_get_user_records_returns_everything_stored():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        init_db(db_path)
        user_id = create_user_with_channel(db_path, "Ana", "discord", "key-123")
        retired_id = save_fact(db_path, user_id, "likes tea")
        deactivate_fact(db_path, user_id, retired_id)
        save_fact(db_path, user_id, "lives in Panama")
        undone_id = save_message(db_path, user_id, "assistant", "a reply never read")
        deactivate_message(db_path, user_id, undone_id)
        save_message(db_path, user_id, "user", "hola")

        records = get_user_records(db_path, user_id)

        assert records["user"]["name"] == "Ana"
        assert {fact["content"] for fact in records["facts"]} == {"likes tea", "lives in Panama"}
        assert {message["content"] for message in records["messages"]} == {"a reply never read", "hola"}
        assert records["channels"] == ["discord"]


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
        message_id = save_message(self.db_path, self.user_id, "user", "Hola Tabris")

        messages = get_messages(self.db_path, self.user_id)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hola Tabris")
        self.assertEqual(messages[0]["id"], message_id)

    def test_deactivated_message_is_not_returned(self):
        message_id = save_message(self.db_path, self.user_id, "user", "Hola Tabris")

        deactivate_message(self.db_path, self.user_id, message_id)

        self.assertEqual(get_messages(self.db_path, self.user_id), [])

    def _age(self, message_id, stamp):
        with contextlib.closing(_connect(self.db_path)) as conn:
            conn.execute("UPDATE messages SET created_at=? WHERE id=?", (stamp, message_id))
            conn.commit()

    def test_erases_only_what_predates_the_cutoff(self):
        old = save_message(self.db_path, self.user_id, "user", "de hace mucho")
        self._age(old, "2026-01-01 00:00:00")
        save_message(self.db_path, self.user_id, "user", "de ahora")

        delete_messages_before(self.db_path, "2026-06-01 00:00:00")

        remaining = [message["content"] for message in get_messages(self.db_path, self.user_id)]
        self.assertEqual(remaining, ["de ahora"])

    def test_reports_how_many_it_erased(self):
        for _ in range(3):
            self._age(save_message(self.db_path, self.user_id, "user", "vieja"), "2026-01-01 00:00:00")

        self.assertEqual(delete_messages_before(self.db_path, "2026-06-01 00:00:00"), 3)

    def test_erases_a_retired_message_too(self):
        # A turn undone by item 34g stays in the table with is_active=0; its text is still text.
        retired = save_message(self.db_path, self.user_id, "assistant", "nunca entregada")
        deactivate_message(self.db_path, self.user_id, retired)
        self._age(retired, "2026-01-01 00:00:00")

        delete_messages_before(self.db_path, "2026-06-01 00:00:00")

        with contextlib.closing(_connect(self.db_path)) as conn:
            left = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        self.assertEqual(left, 0)

    def test_erases_across_every_user(self):
        other_id = create_user(self.db_path, name="Ana")
        self._age(save_message(self.db_path, self.user_id, "user", "vieja"), "2026-01-01 00:00:00")
        self._age(save_message(self.db_path, other_id, "user", "vieja"), "2026-01-01 00:00:00")

        self.assertEqual(delete_messages_before(self.db_path, "2026-06-01 00:00:00"), 2)

    def test_deactivate_message_ignores_another_users_message(self):
        other_id = create_user(self.db_path, name="Ana")
        message_id = save_message(self.db_path, self.user_id, "user", "Hola Tabris")

        deactivate_message(self.db_path, other_id, message_id)

        self.assertEqual(len(get_messages(self.db_path, self.user_id)), 1)
    
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

class TestUpdateUserProfile(unittest.TestCase):
    def test_updates_only_the_given_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user(db, "Rumpel", "en", "Bogotá", "America/Bogota")
            update_user_profile(db, user_id, name="Mauricio")
            user = get_user(db, user_id)
            self.assertEqual(user["name"], "Mauricio")
            self.assertEqual(user["language"], "en")
            self.assertEqual(user["location"], "Bogotá")
            self.assertEqual(user["timezone"], "America/Bogota")

    def test_updates_several_fields_at_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user(db, "Rumpel", "en", "Bogotá", "America/Bogota")
            update_user_profile(db, user_id, location="Cali", timezone="America/Bogota", language="es")
            user = get_user(db, user_id)
            self.assertEqual(user["location"], "Cali")
            self.assertEqual(user["language"], "es")

    def test_does_not_affect_other_users(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            id1 = create_user(db, "Rumpel", "en")
            id2 = create_user(db, "Ana", "en")
            update_user_profile(db, id1, language="es")
            self.assertEqual(get_user(db, id2)["language"], "en")

    def test_no_fields_leaves_the_row_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user(db, "Rumpel", "en", "Bogotá", "America/Bogota")
            update_user_profile(db, user_id)
            self.assertEqual(get_user(db, user_id)["name"], "Rumpel")

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

    def test_create_user_with_channel_links_it_in_one_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            user_id = create_user_with_channel(db, "Rumpel", "discord", "42", language="es")
            user = find_user_by_key(db, "discord", "42")
            self.assertEqual(user["id"], user_id)
            self.assertEqual(user["language"], "es")

    def test_create_user_with_channel_leaves_no_user_when_the_channel_is_taken(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "test.db")
            init_db(db)
            create_user_with_channel(db, "Ana", "discord", "42")

            with self.assertRaises(sqlite3.IntegrityError):
                create_user_with_channel(db, "Rumpel", "discord", "42")

            with contextlib.closing(_connect(db)) as conn:
                names = [row[0] for row in conn.execute("SELECT name FROM users")]
            self.assertEqual(names, ["Ana"])

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


def test_deactivate_user_sets_deactivated_at(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")

    deactivate_user(db_path, user_id)

    assert get_user(db_path, user_id)["deactivated_at"] is not None


def test_deactivate_user_expires_active_link_codes(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    code = create_link_code(db_path, user_id)

    deactivate_user(db_path, user_id)

    assert redeem_link_code(db_path, code, "discord", "disc-key-1") is None


def test_reactivate_user_clears_the_deactivation_mark(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    deactivate_user(db_path, user_id)

    reactivate_user(db_path, user_id)

    assert get_user(db_path, user_id)["deactivated_at"] is None


def test_get_deactivated_users_returns_only_those_marked_with_their_date(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    create_user(db_path, "Ana", "es")
    leaving = create_user(db_path, "Rumpel", "es")
    deactivate_user(db_path, leaving)

    deactivated = get_deactivated_users(db_path)

    assert [row["id"] for row in deactivated] == [leaving]
    assert deactivated[0]["deactivated_at"] is not None


def _rows_of_user(db_path, user_id):
    with contextlib.closing(_connect(db_path)) as conn:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column}=?", (user_id,)).fetchone()[0]
            for table, column in (("users", "id"), ("facts", "user_id"), ("messages", "user_id"),
                                  ("user_channels", "user_id"), ("link_codes", "user_id"))
        }


def test_delete_user_completely_leaves_no_row_in_any_table(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user_with_channel(db_path, "Ana", "discord", "key-1")
    save_fact(db_path, user_id, "likes tea")
    save_message(db_path, user_id, "user", "hola")
    create_link_code(db_path, user_id)

    delete_user_completely(db_path, user_id)

    assert set(_rows_of_user(db_path, user_id).values()) == {0}


def test_delete_user_completely_touches_nobody_else(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    leaving = create_user_with_channel(db_path, "Ana", "discord", "key-1")
    staying = create_user_with_channel(db_path, "Rumpel", "cli", "key-2")
    save_fact(db_path, leaving, "likes tea")
    save_fact(db_path, staying, "likes coffee")
    save_message(db_path, staying, "user", "hola")

    delete_user_completely(db_path, leaving)

    assert _rows_of_user(db_path, staying) == {"users": 1, "facts": 1, "messages": 1, "user_channels": 1, "link_codes": 0}


class _ConnectionFailingOnTheUserRow:
    """A real connection that refuses the last statement, standing in for a crash mid-delete."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, *args):
        if sql.strip().upper().startswith("DELETE FROM USERS"):
            raise sqlite3.OperationalError("interrupted halfway")
        return self._conn.execute(sql, *args)

    def commit(self):
        self._conn.commit()

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, *exc_info):
        return self._conn.__exit__(*exc_info)

    def close(self):
        self._conn.close()


def test_delete_user_completely_is_all_or_nothing(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user_with_channel(db_path, "Ana", "discord", "key-1")
    save_fact(db_path, user_id, "likes tea")

    with patch("core.db._connect", lambda path: _ConnectionFailingOnTheUserRow(_connect(path))):
        with pytest.raises(sqlite3.OperationalError):
            delete_user_completely(db_path, user_id)

    assert _rows_of_user(db_path, user_id) == {"users": 1, "facts": 1, "messages": 0, "user_channels": 1, "link_codes": 0}


def test_redeem_rejects_deactivated_account_even_with_a_valid_code(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO link_codes (code, user_id, expires_at) VALUES (?, ?, datetime('now', '+5 minutes'))",
            ("TESTCOD3", user_id),
        )
        conn.execute("UPDATE users SET deactivated_at = datetime('now') WHERE id=?", (user_id,))
        conn.commit()

    result = redeem_link_code(db_path, "TESTCOD3", "discord", "disc-key-1")

    assert result is None


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


def test_get_last_message_time_returns_the_newest_of_that_user(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    other_id = create_user(db_path, "Ana", "en")
    older = save_message(db_path, user_id, "user", "ayer")
    newer = save_message(db_path, user_id, "assistant", "hoy")
    intruder = save_message(db_path, other_id, "user", "de otra persona")
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        conn.executemany(
            "UPDATE messages SET created_at=? WHERE id=?",
            [("2026-01-01 08:00:00", older),
             ("2026-01-02 08:00:00", newer),
             ("2026-01-03 08:00:00", intruder)],
        )
        conn.commit()

    assert get_last_message_time(db_path, user_id) == "2026-01-02 08:00:00"


def test_get_last_message_time_is_none_without_messages(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")

    assert get_last_message_time(db_path, user_id) is None


@pytest.mark.parametrize("pragma, expected", [
    ("journal_mode", "wal"),
    ("busy_timeout", config.DB_BUSY_TIMEOUT_MS),
])
def test_connect_sets_concurrency_pragmas(tmp_path, pragma, expected):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    with contextlib.closing(_connect(db_path)) as conn:
        assert conn.execute(f"PRAGMA {pragma}").fetchone()[0] == expected


def test_init_db_adds_the_attachment_column_to_a_messages_table_that_predates_it(tmp_path):
    db_path = str(tmp_path / "older.db")
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """CREATE TABLE messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                is_active  INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        conn.commit()
    init_db(db_path)
    init_db(db_path)
    with contextlib.closing(_connect(db_path)) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(messages)")}
    assert "attachment" in columns


@pytest.mark.parametrize("text", ["¿qué ves aquí?", "what do you see here?"])
def test_save_message_stores_the_typed_text_and_the_mark_that_an_image_came(tmp_path, text):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    save_message(db_path, user_id, "user", text, attachment="image")
    stored = get_messages(db_path, user_id)[-1]
    assert stored["content"] == text
    assert stored["attachment"] == "image"


def test_save_message_leaves_the_mark_empty_when_no_attachment_came(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    user_id = create_user(db_path, "Rumpel", "es")
    save_message(db_path, user_id, "user", "hola")
    assert get_messages(db_path, user_id)[-1]["attachment"] is None


if __name__ == "__main__":
    unittest.main()