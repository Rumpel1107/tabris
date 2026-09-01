import config
import contextlib
import os
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
    directory = os.path.dirname(db_path)
    if directory:
        os.makedirs(directory, mode=0o700, exist_ok=True)
        os.chmod(directory, 0o700)  # makedirs' mode only applies on creation; an existing directory keeps its own
    with contextlib.closing(_connect(db_path)) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                language   TEXT NOT NULL DEFAULT 'en',
                location   TEXT NOT NULL DEFAULT '',
                timezone   TEXT NOT NULL DEFAULT 'UTC',
                deactivated_at TEXT,
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
                attachment TEXT,
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
        if "deactivated_at" not in existing:
            conn.execute("ALTER TABLE users ADD COLUMN deactivated_at TEXT")
        conn.commit()
        facts_cols = {row[1] for row in conn.execute("PRAGMA table_info(facts)")}
        if "retired_at" not in facts_cols:
            conn.execute("ALTER TABLE facts ADD COLUMN retired_at TEXT")
        messages_cols = {row[1] for row in conn.execute("PRAGMA table_info(messages)")}
        if "attachment" not in messages_cols:
            conn.execute("ALTER TABLE messages ADD COLUMN attachment TEXT")
        conn.commit()
    os.chmod(db_path, 0o600)  # sqlite creates the file with the process umask, which is not restrictive enough for personal data

def create_user(db_path, name, language="en", location="", timezone="UTC"):
    with contextlib.closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, language, location, timezone) VALUES (?, ?, ?, ?)",
            (name, language, location, timezone)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id

def create_user_with_channel(db_path: str, name: str, channel: str, key: str, language: str = "en", location: str = "", timezone: str = "UTC") -> int:
    """Create a user and the channel that reaches them in one transaction: a user without a channel is unreachable."""
    with contextlib.closing(_connect(db_path)) as conn:
        with conn:
            cursor = conn.execute(
                "INSERT INTO users (name, language, location, timezone) VALUES (?, ?, ?, ?)",
                (name, language, location, timezone)
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO user_channels (user_id, channel, key) VALUES (?, ?, ?)",
                (user_id, channel, key)
            )
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
            "SELECT * FROM facts WHERE user_id=? AND is_active=1 ORDER BY created_at, id",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]

def save_message(db_path, user_id, role, content, attachment=None) -> int:
    with contextlib.closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO messages (user_id, role, content, attachment) VALUES (?, ?, ?, ?)",
            (user_id, role, content, attachment)
        )
        conn.commit()
        return cursor.lastrowid

def deactivate_message(db_path: str, user_id: int, message_id: int) -> None:
    """Retire a message so it no longer belongs to the conversation, scoped to its owner."""
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "UPDATE messages SET is_active=0 WHERE id=? AND user_id=?",
            (message_id, user_id)
        )
        conn.commit()

def delete_messages_before(db_path: str, cutoff: str) -> int:
    """Erase every message stored before `cutoff` and return how many were erased."""
    with contextlib.closing(_connect(db_path)) as conn:
        # Retired messages go too: is_active=0 says a turn left the conversation, not that its text did.
        cursor = conn.execute("DELETE FROM messages WHERE created_at < ?", (cutoff,))
        conn.commit()
        return cursor.rowcount

def get_messages(db_path, user_id, limit=20):
    with contextlib.closing(_connect(db_path)) as conn:
        rows = conn.execute(
            """SELECT * FROM messages WHERE user_id=? AND is_active=1
            ORDER BY id DESC LIMIT ?""",
            (user_id, limit)
        ).fetchall()
        return list(reversed([dict(row) for row in rows]))

def get_last_message_time(db_path: str, user_id: int) -> str | None:
    """Return when this user's newest message was stored (UTC), retired ones included."""
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT MAX(created_at) FROM messages WHERE user_id=?",
            (user_id,)
        ).fetchone()
        return row[0]

def update_user_profile(db_path, user_id, name=None, language=None, location=None, timezone=None):
    """Update only the fields given; anything left as None keeps its stored value."""
    updates = {
        column: value
        for column, value in (("name", name), ("language", language),
                              ("location", location), ("timezone", timezone))
        if value is not None
    }
    if not updates:
        return
    # Column names come from the tuple above, never from a caller's string.
    assignments = ", ".join(f"{column} = ?" for column in updates)
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            f"UPDATE users SET {assignments} WHERE id = ?",
            (*updates.values(), user_id)
        )
        conn.commit()

def deactivate_fact(db_path, user_id, fact_id):
    with contextlib.closing(_connect(db_path)) as conn:
        conn.execute(
            "UPDATE facts SET is_active=0, retired_at=datetime('now') WHERE id=? AND user_id=?",
            (fact_id, user_id)
        )
        conn.commit()

def deactivate_user(db_path: str, user_id: int) -> None:
    """Mark a user as deactivated and expire any unused link code of theirs, atomically."""
    with contextlib.closing(_connect(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET deactivated_at = datetime('now') WHERE id=?",
                (user_id,)
            )
            conn.execute(
                "UPDATE link_codes SET expires_at = datetime('now') WHERE user_id=? AND used=0",
                (user_id,)
            )

def reactivate_user(db_path: str, user_id: int) -> None:
    """Clear a user's deactivation mark so the account is served again."""
    with contextlib.closing(_connect(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE users SET deactivated_at = NULL WHERE id=?",
                (user_id,)
            )


def get_deactivated_users(db_path: str) -> list[dict]:
    """Return the id and deactivation date of every deactivated account, oldest request first."""
    with contextlib.closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, deactivated_at FROM users WHERE deactivated_at IS NOT NULL ORDER BY deactivated_at, id"
        ).fetchall()
        return [dict(row) for row in rows]


def delete_user_completely(db_path: str, user_id: int) -> None:
    """Erase every row belonging to one user, all of it or none of it.

    The only hard delete in the project (see CONTRIBUTING.md): a privacy deletion that
    only marked rows inactive would leave the data exactly where it was. Children go
    before the user row because the foreign keys point that way.
    """
    with contextlib.closing(_connect(db_path)) as conn:
        with conn:
            conn.execute("DELETE FROM link_codes WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM user_channels WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM messages WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM facts WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))


def find_link_code(text: str) -> str | None:
    """Return the link code contained in the text, or None if no word in it is shaped like one."""
    for word in text.split():
        code = word.strip(".,;:!?()[]{}<>\"'").upper()
        if len(code) != 8 or any(char not in _LINK_CODE_ALPHABET for char in code):
            continue
        if any(char.isdigit() for char in code):
            return code
    return None


def create_link_code(db_path: str, user_id: int) -> str:
    """Generate a short single-use code that links another channel to this user_id, expiring any previous unused code of that user."""
    # Retries the rare all-letter draw so a code can never be mistaken for a name.
    while True:
        code = "".join(secrets.choice(_LINK_CODE_ALPHABET) for _ in range(8))
        if any(char.isdigit() for char in code):
            break
    with contextlib.closing(_connect(db_path)) as conn:
        # Runs before the INSERT so the new code is not caught by its own expiry.
        conn.execute(
            "UPDATE link_codes SET expires_at = datetime('now') WHERE user_id=? AND used=0",
            (user_id,),
        )
        conn.execute(
            "INSERT INTO link_codes (code, user_id, expires_at) VALUES (?, ?, datetime('now', ?))",
            (code, user_id, f"{config.LINK_CODE_TTL_SECONDS} seconds"),
        )
        conn.commit()
    return code

def redeem_link_code(db_path: str, code: str, channel: str, key: str) -> int | None:
    """Redeem a link code: point (channel, key) to the code's user. Returns the user_id, or None if the code is invalid or the account is deactivated."""
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            """SELECT link_codes.user_id FROM link_codes
            JOIN users ON users.id = link_codes.user_id
            WHERE link_codes.code=? AND link_codes.used=0
            AND link_codes.expires_at > datetime('now')
            AND users.deactivated_at IS NULL""",
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

def get_user_channels(db_path: str, user_id: int) -> list[str]:
    """Return the names of the channels linked to a user, never their keys."""
    with contextlib.closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT channel FROM user_channels WHERE user_id=? ORDER BY id",
            (user_id,)
        ).fetchall()
        return [row["channel"] for row in rows]

def get_user_records(db_path: str, user_id: int) -> dict:
    """Return everything stored about one user, retired facts and inactive messages included.

    Unlike get_facts/get_messages, which answer what the assistant should see, this answers
    what the database actually holds. Channel keys are deliberately left out.
    """
    with contextlib.closing(_connect(db_path)) as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        channels = conn.execute(
            "SELECT channel FROM user_channels WHERE user_id=? ORDER BY id", (user_id,)
        ).fetchall()
        facts = conn.execute(
            "SELECT * FROM facts WHERE user_id=? ORDER BY id", (user_id,)
        ).fetchall()
        messages = conn.execute(
            "SELECT * FROM messages WHERE user_id=? ORDER BY id", (user_id,)
        ).fetchall()
        return {
            "user": dict(user) if user else None,
            "channels": [row["channel"] for row in channels],
            "facts": [dict(row) for row in facts],
            "messages": [dict(row) for row in messages],
        }

def find_user_by_key(db_path, channel, key):
    with contextlib.closing(_connect(db_path)) as conn:
        row = conn.execute(
            """SELECT users.* FROM users
            JOIN user_channels ON user_channels.user_id = users.id
            WHERE user_channels.channel = ? AND user_channels.key = ?""",
            (channel, key)
        ).fetchone()
        return dict(row) if row else None
