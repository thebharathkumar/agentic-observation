from __future__ import annotations

import sqlite3
from pathlib import Path

from trace_replay.storage import SCHEMA_SQL


class Database:
    def __init__(self, db_path: str | Path = "trace_replay.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        conn = self.connect()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
