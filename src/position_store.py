import sqlite3
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OpenTwap:
    id: int
    coin: str
    is_buy: bool
    size: float
    entry_price: float
    start_ts: float
    duration_min: float
    stop_loss_pct: float
    take_profit_pct: float
    protected: bool
    source_message_id: int


class PositionStore:
    def __init__(self, db_path: str = "bot_state.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS open_twaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin TEXT NOT NULL,
                is_buy INTEGER NOT NULL,
                size REAL NOT NULL,
                entry_price REAL NOT NULL,
                start_ts REAL NOT NULL,
                duration_min REAL NOT NULL,
                stop_loss_pct REAL NOT NULL,
                take_profit_pct REAL NOT NULL,
                protected INTEGER NOT NULL DEFAULT 0,
                source_message_id INTEGER NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_messages (
                message_id INTEGER PRIMARY KEY
            )
            """
        )
        self.conn.commit()

    def has_seen_message(self, message_id: int) -> bool:
        cur = self.conn.execute("SELECT 1 FROM seen_messages WHERE message_id = ?", (message_id,))
        return cur.fetchone() is not None

    def mark_message_seen(self, message_id: int) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen_messages (message_id) VALUES (?)", (message_id,)
        )
        self.conn.commit()

    def count_open_unprotected(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM open_twaps WHERE protected = 0")
        return cur.fetchone()[0]

    def add_open_twap(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        entry_price: float,
        duration_min: float,
        stop_loss_pct: float,
        take_profit_pct: float,
        source_message_id: int,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO open_twaps
                (coin, is_buy, size, entry_price, start_ts, duration_min,
                 stop_loss_pct, take_profit_pct, protected, source_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                coin,
                int(is_buy),
                size,
                entry_price,
                time.time(),
                duration_min,
                stop_loss_pct,
                take_profit_pct,
                source_message_id,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_due_unprotected(self, now: Optional[float] = None) -> List[OpenTwap]:
        now = now if now is not None else time.time()
        cur = self.conn.execute(
            "SELECT id, coin, is_buy, size, entry_price, start_ts, duration_min, "
            "stop_loss_pct, take_profit_pct, protected, source_message_id "
            "FROM open_twaps WHERE protected = 0"
        )
        rows = cur.fetchall()
        due = []
        for row in rows:
            twap = OpenTwap(
                id=row[0],
                coin=row[1],
                is_buy=bool(row[2]),
                size=row[3],
                entry_price=row[4],
                start_ts=row[5],
                duration_min=row[6],
                stop_loss_pct=row[7],
                take_profit_pct=row[8],
                protected=bool(row[9]),
                source_message_id=row[10],
            )
            if now >= twap.start_ts + twap.duration_min * 60:
                due.append(twap)
        return due

    def mark_protected(self, twap_id: int) -> None:
        self.conn.execute("UPDATE open_twaps SET protected = 1 WHERE id = ?", (twap_id,))
        self.conn.commit()
