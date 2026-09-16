import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

class Database:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create()

    def _create(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS guilds(
            guild_id INTEGER PRIMARY KEY,
            log_channel_id INTEGER,
            quarantine_role_id INTEGER,
            snapshot TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS actions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trusted(
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY(guild_id, user_id)
        );
        """)
        self.conn.commit()

    def get_guild(self, guild_id):
        return self.conn.execute(
            "SELECT * FROM guilds WHERE guild_id=?", (guild_id,)
        ).fetchone()

    def save_guild(self, guild_id, log_channel_id, quarantine_role_id, snapshot):
        self.conn.execute("""
        INSERT INTO guilds(guild_id, log_channel_id, quarantine_role_id, snapshot, created_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(guild_id) DO UPDATE SET
            log_channel_id=excluded.log_channel_id,
            quarantine_role_id=excluded.quarantine_role_id,
            snapshot=excluded.snapshot
        """, (
            guild_id, log_channel_id, quarantine_role_id,
            json.dumps(snapshot), datetime.now(timezone.utc).isoformat()
        ))
        self.conn.commit()

    def add_action(self, guild_id, user_id, action):
        self.conn.execute(
            "INSERT INTO actions(guild_id,user_id,action,created_at) VALUES(?,?,?,?)",
            (guild_id, user_id, action, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()

    def count_recent(self, guild_id, user_id, action, seconds):
        row = self.conn.execute("""
        SELECT COUNT(*) AS c FROM actions
        WHERE guild_id=? AND user_id=? AND action=?
        AND created_at >= datetime('now', ?)
        """, (guild_id, user_id, action, f"-{int(seconds)} seconds")).fetchone()
        return row["c"]

    def add_trusted(self, guild_id, user_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO trusted(guild_id,user_id) VALUES(?,?)",
            (guild_id, user_id)
        )
        self.conn.commit()

    def is_trusted(self, guild_id, user_id):
        row = self.conn.execute(
            "SELECT 1 FROM trusted WHERE guild_id=? AND user_id=?",
            (guild_id, user_id)
        ).fetchone()
        return bool(row)
