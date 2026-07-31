import config
import contextlib
import secrets
import sqlite3

_LINK_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"   # no 0/O/1/I/L to avoid ambiguity when typed

def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute(f"PRAGMA busy_timeout = {config.DB_BUSY_TIMEOUT_MS}") # PRAGMA does not accept bound parameters, hence the interpolation; the value from the system, not user input
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    with contextlib.closing(_connect(db_path)) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                language   TEXT NOT NULL DEFAULT 'en',
                location   TEXT NOT NULL DEFAULT '',
                timezone   TEXT NOT NULL DEFAULT 'UTC',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            
            CREATE TABLE IF NOT EXISTS facts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                content    TEXT NOT NULL,
                is_active  INTEGER NOT NULL DEFAULT 1,
                retired_at TEXT,
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
            
            CREATE TABLE IF NOT EXISTS user_channels (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                channel    TEXT NOT NULL,
                key        TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(channel, key)
            );
            
            CREATE TABLE IF NOT EXISTS link_codes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                code       TEXT NOT NULL UNIQUE,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                expires_at TEXT NOT NULL,
                used       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_facts_active_content ON facts(user_id, content) WHERE is_active=1;
        """)
        existing = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "location" not in existing:
            conn.execute("ALTER TABLE users ADD COLUMN location TEXT NOT NULL DEFAULT ''")
        if "timezone" not in existing:
            conn.execute("ALTER TABLE users ADD COLUMN timezone TEXT NOT NULL DEFAULT 'UTC'")
        conn.commit()
        facts_cols = {row[1] for row in conn.execute("PRAGMA table_info(facts)")}
        if "retired_at" not in facts_cols:
            conn.execute("ALTER TABLE facts ADD COLUMN retired_at TEXT")

def create_user(db_path, name, language="en", location="", timezone="UTC"):
    with contextlib.closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, language, location, timezone) VALUES (?, ?, ?, ?)",
            (name, language, location, timezone)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id

def get_user(db_path, user_id):
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

def save_fact(db_path, user_id, content):
    with contextlib.closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO facts (user_id, content) VALUES (?, ?)",
            (user_id, content)
        )
        fact_id = cursor.lastrowid
        conn.commit()
        return fact_id

def get_facts(db_path, user_id):
    with contextlib.closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM facts WHERE user_id=? AND is_active=1 ORDER BY created_at",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]

def save_message(db_path, user_id, role, content):
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        conn.commit()

def get_messages(db_path, user_id, limit=20):
    with contextlib.closing(_connect(db_path)) as conn:
        rows = conn.execute(
            """SELECT * FROM messages WHERE user_id=?
            ORDER BY id DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return list(reversed([dict(row) for row in rows]))

def update_user_language(db_path, user_id, language):
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "UPDATE users SET language = ? WHERE id = ?",
            (language, user_id)
        )
        conn.commit()

def deactivate_fact(db_path, user_id, fact_id):
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "UPDATE facts SET is_active=0, retired_at=datetime('now') WHERE id=? AND user_id=?",
            (fact_id, user_id)
        )
        conn.commit()

def create_link_code(db_path: str, user_id: int) -> str:
    """Generate a short single-use code that links another channel to this user_id."""
    code = "".join(secrets.choice(_LINK_CODE_ALPHABET) for _ in range(8))
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO link_codes (code, user_id, expires_at) VALUES (?, ?, datetime('now', ?))",
            (code, user_id, f"{config.LINK_CODE_TTL_SECONDS} seconds"),
        )
        conn.commit()
    return code

def redeem_link_code(db_path: str, code: str, channel: str, key: str) -> int | None:
    """Redeem a link code: point (channel, key) to the code's user. Returns the user_id, or None if the code is invalid."""
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT user_id FROM link_codes WHERE code=? AND used=0 AND expires_at > datetime('now')",
            (code,),
        ).fetchone()
        if row is None:
            return None
        user_id = row["user_id"]
        conn.execute(
            "INSERT INTO user_channels (user_id, channel, key) VALUES (?, ?, ?)",
            (user_id, channel, key),
        )
        conn.execute("UPDATE link_codes SET used=1 WHERE code=?", (code,))
        conn.commit()
        return user_id

def register_user_channel(db_path, user_id, channel, key):
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO user_channels (user_id, channel, key) VALUES (?, ?, ?)",
            (user_id, channel, key)
        )
        conn.commit()

def find_user_by_key(db_path, channel, key):
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            """SELECT users.* FROM users
            JOIN user_channels ON user_channels.user_id = users.id
            WHERE user_channels.channel = ? AND user_channels.key = ?""",
            (channel, key)
        ).fetchone()
        return dict(row) if row else None
