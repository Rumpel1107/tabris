import sqlite3

def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    conn = _connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            language   TEXT NOT NULL DEFAULT 'en',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS facts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            content    TEXT NOT NULL,
            is_active  INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            is_active  INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

def create_user(db_path, name, language="en"):
    conn = _connect(db_path)
    cursor = conn.execute(
        "INSERT INTO users (name, language) VALUES (?, ?)",
        (name, language)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user(db_path, user_id):
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def save_fact(db_path, user_id, content):
    conn = _connect(db_path)
    cursor = conn.execute(
        "INSERT INTO facts (user_id, content) VALUES (?, ?)",
        (user_id, content)
    )
    fact_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return fact_id

def get_facts(db_path, user_id):
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM facts WHERE user_id=? AND is_active=1 ORDER BY created_at",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_message(db_path, user_id, role, content):
    conn = _connect(db_path)
    conn.execute(
        "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

def get_messages(db_path, user_id, limit=20):
    conn = _connect(db_path)
    rows = conn.execute(
        """SELECT * FROM messages WHERE user_id=?
        ORDER BY id DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return list(reversed([dict(row) for row in rows]))

def find_user_by_name(db_path, name):
    conn = _connect(db_path)
    row = conn.execute(
        "SELECT * FROM users WHERE name=?",
        (name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_or_create_user(db_path, name, language="en"):
    user = find_user_by_name(db_path, name)
    if user:
        return user["id"]
    return create_user(db_path, name, language)

def deactivate_fact(db_path, fact_id):
    conn = _connect(db_path)
    conn.execute(
        "UPDATE facts SET is_active=0 WHERE id=?",
        (fact_id,)
    )
    conn.commit()
    conn.close()