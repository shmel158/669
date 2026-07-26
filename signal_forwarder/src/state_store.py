import sqlite3


class StateStore:
    def __init__(self, db_path: str = "forward_state.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_messages (
                source_chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                PRIMARY KEY (source_chat_id, message_id)
            )
            """
        )
        self.conn.commit()

    def has_seen(self, source_chat_id: int, message_id: int) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM seen_messages WHERE source_chat_id = ? AND message_id = ?",
            (source_chat_id, message_id),
        )
        return cur.fetchone() is not None

    def mark_seen(self, source_chat_id: int, message_id: int) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen_messages (source_chat_id, message_id) VALUES (?, ?)",
            (source_chat_id, message_id),
        )
        self.conn.commit()
