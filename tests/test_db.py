import sys
import os
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db import init_db, create_user, get_user, find_user_by_name, save_fact, get_facts, deactivate_fact, save_message, get_messages, get_or_create_user


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
    
    def test_duplicate_user_raises_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "test.db")
            init_db(db_path)
            create_user(db_path, name="Rumpel")
            with self.assertRaises(Exception):
                create_user(db_path, name="Rumpel")

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

class TestFindUserByName(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
    
    def tearDown(self):
        self.tmp.cleanup()
    
    def test_finds_existing_user(self):
        user_id = create_user(self.db_path, name="Rumpel", language="es")
        user = find_user_by_name(self.db_path, "Rumpel")
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], user_id)
    
    def test_returns_none_if_not_found(self):
        user = find_user_by_name(self.db_path, "Ana")
        self.assertIsNone(user)

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
        
        deactivate_fact(self.db_path, fact_id)
        
        facts = get_facts(self.db_path, self.user_id)
        contents = [f["content"] for f in facts]
        self.assertIn("Hecho activo", contents)
        self.assertNotIn("Hecho a desactivar", contents)
    
    def test_deactivate_does_not_delete_from_db(self):
        fact_id = save_fact(self.db_path, self.user_id, "Hecho importante")
        deactivate_fact(self.db_path, fact_id)
        
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT is_active FROM facts WHERE id=?", (fact_id,)).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 0)

class TestGetOrCreateUser(unittest.TestCase):
    
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        init_db(self.db_path)
    
    def tearDown(self):
        self.tmp.cleanup()
    
    def test_creates_user_when_absent(self):
        user_id = get_or_create_user(self.db_path, "Rumpel", "es")
        self.assertIsNotNone(user_id)
        self.assertIsNotNone(find_user_by_name(self.db_path, "Rumpel"))
    
    def test_returns_existing_id_without_duplicating(self):
        first_id = get_or_create_user(self.db_path, "Rumpel", "es")
        second_id = get_or_create_user(self.db_path, "Rumpel", "es")
        self.assertEqual(first_id, second_id)

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


if __name__ == "__main__":
    unittest.main()