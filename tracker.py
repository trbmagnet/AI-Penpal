import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class ReplyTracker:
    def __init__(self, db_path: str = "replied.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS replied (
                message_id TEXT PRIMARY KEY,
                replied_at TIMESTAMP NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                subject TEXT,
                timestamp TIMESTAMP NOT NULL,
                message_id TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_summary (
                sender TEXT PRIMARY KEY,
                summary_text TEXT NOT NULL,
                up_to_count INTEGER NOT NULL,
                updated_at TIMESTAMP
            )
            """
        )
        self._conn.commit()

    def has_replied(self, message_id: str) -> bool:
        cursor = self._conn.execute(
            "SELECT 1 FROM replied WHERE message_id = ?", (message_id,)
        )
        return cursor.fetchone() is not None

    def mark_replied(self, message_id: str):
        self._conn.execute(
            "INSERT OR IGNORE INTO replied (message_id, replied_at) VALUES (?, ?)",
            (message_id, datetime.now().isoformat()),
        )
        self._conn.commit()

    def store_exchange(self, sender: str, role: str, content: str,
                       subject: str = "", message_id: str = ""):
        self._conn.execute(
            """
            INSERT INTO conversation_history (sender, role, content, subject, timestamp, message_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sender, role, content, subject, datetime.now().isoformat(), message_id),
        )
        self._conn.commit()

    def get_history(self, sender: str, limit: int = 10) -> list[dict]:
        cursor = self._conn.execute(
            """
            SELECT role, content, subject, timestamp, message_id
            FROM conversation_history
            WHERE sender = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (sender, limit),
        )
        rows = cursor.fetchall()
        rows.reverse()
        return [
            {
                "role": row[0],
                "content": row[1],
                "subject": row[2],
                "timestamp": row[3],
                "message_id": row[4],
            }
            for row in rows
        ]

    def get_exchange_count(self, sender: str) -> int:
        cursor = self._conn.execute(
            "SELECT COUNT(*) FROM conversation_history WHERE sender = ?",
            (sender,),
        )
        return cursor.fetchone()[0]

    def get_summary(self, sender: str) -> dict | None:
        cursor = self._conn.execute(
            "SELECT summary_text, up_to_count, updated_at FROM conversation_summary WHERE sender = ?",
            (sender,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "summary_text": row[0],
            "up_to_count": row[1],
            "updated_at": row[2],
        }

    def update_summary(self, sender: str, summary_text: str, up_to_count: int):
        self._conn.execute(
            """
            INSERT OR REPLACE INTO conversation_summary (sender, summary_text, up_to_count, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (sender, summary_text, up_to_count, datetime.now().isoformat()),
        )
        self._conn.commit()

    def get_old_messages_for_sender(self, sender: str, exclude_recent: int = 10) -> list[dict]:
        cursor = self._conn.execute(
            """
            SELECT role, content, subject, timestamp, message_id
            FROM (
                SELECT role, content, subject, timestamp, message_id, id,
                       ROW_NUMBER() OVER (ORDER BY id DESC) as rn
                FROM conversation_history
                WHERE sender = ?
            )
            WHERE rn > ?
            ORDER BY id ASC
            """,
            (sender, exclude_recent),
        )
        rows = cursor.fetchall()
        return [
            {
                "role": row[0],
                "content": row[1],
                "subject": row[2],
                "timestamp": row[3],
                "message_id": row[4],
            }
            for row in rows
        ]

    def cleanup(self, days: int = 30):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        self._conn.execute("DELETE FROM replied WHERE replied_at < ?", (cutoff,))
        self._conn.commit()

    def close(self):
        self._conn.close()
