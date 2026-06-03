"""
Request Logger
==============
Saves every request to a SQLite database.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = "data/guardrail_logs.db"


class RequestLogger:

    def __init__(self):
        Path("data").mkdir(exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_table()
        print(f"[Logger] Database ready at {DB_PATH}")

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT    NOT NULL,
                user_id       TEXT    NOT NULL,
                message       TEXT    NOT NULL,
                blocked       INTEGER NOT NULL,
                block_reason  TEXT,
                block_stage   TEXT,
                latency_ms    REAL,
                checks        TEXT
            )
        """)
        self.conn.commit()

    def log(
        self,
        user_id: str,
        message: str,
        blocked: bool,
        block_reason: str | None,
        latency_ms: float,
        checks: list[str]
    ):
        block_stage = None
        if blocked:
            checks_str = " ".join(checks)
            if "llm_call" not in checks_str:
                block_stage = "input"
            else:
                block_stage = "output"

        self.conn.execute("""
            INSERT INTO request_logs
            (timestamp, user_id, message, blocked, block_reason, block_stage, latency_ms, checks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_id,
            message[:500],
            1 if blocked else 0,
            block_reason,
            block_stage,
            latency_ms,
            " | ".join(checks)
        ))
        self.conn.commit()

    def get_stats(self) -> dict:
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM request_logs")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM request_logs WHERE blocked = 1")
        blocked = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(latency_ms) FROM request_logs WHERE blocked = 0")
        avg_latency = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT block_reason, COUNT(*) as count
            FROM request_logs
            WHERE blocked = 1
            GROUP BY block_reason
            ORDER BY count DESC
            LIMIT 5
        """)
        top_reasons = cursor.fetchall()

        cursor.execute("""
            SELECT timestamp, message, blocked, block_reason, latency_ms
            FROM request_logs
            ORDER BY id DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()

        cursor.execute("""
            SELECT strftime('%H:00', timestamp) as hour, COUNT(*) as count
            FROM request_logs
            WHERE date(timestamp) = date('now')
            GROUP BY hour
            ORDER BY hour
        """)
        hourly = cursor.fetchall()

        return {
            "total":       total,
            "blocked":     blocked,
            "passed":      total - blocked,
            "block_rate":  round((blocked / total * 100), 1) if total > 0 else 0,
            "avg_latency": round(avg_latency, 1),
            "top_reasons": top_reasons,
            "recent":      recent,
            "hourly":      hourly
        }

    def get_all_logs(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, user_id, message, blocked, block_reason, latency_ms
            FROM request_logs
            ORDER BY id DESC
            LIMIT 100
        """)
        return cursor.fetchall()