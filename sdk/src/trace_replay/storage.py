from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import TraceRecord


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS traces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  status TEXT NOT NULL,
  root_span_id TEXT,
  metadata_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spans (
  id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  parent_id TEXT,
  name TEXT NOT NULL,
  function_name TEXT NOT NULL,
  module TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  duration_ms REAL NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT,
  exception_json TEXT,
  metadata_json TEXT,
  FOREIGN KEY(trace_id) REFERENCES traces(id)
);
CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trace_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY(trace_id) REFERENCES traces(id)
);
CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events(trace_id);

CREATE TABLE IF NOT EXISTS prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  span_id TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  content TEXT NOT NULL,
  metadata_json TEXT,
  FOREIGN KEY(span_id) REFERENCES spans(id)
);
CREATE INDEX IF NOT EXISTS idx_prompts_span_id ON prompts(span_id);

CREATE TABLE IF NOT EXISTS completions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  span_id TEXT NOT NULL,
  content TEXT NOT NULL,
  model TEXT,
  metadata_json TEXT,
  FOREIGN KEY(span_id) REFERENCES spans(id)
);
CREATE INDEX IF NOT EXISTS idx_completions_span_id ON completions(span_id);

CREATE TABLE IF NOT EXISTS errors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  span_id TEXT NOT NULL,
  error_type TEXT NOT NULL,
  message TEXT NOT NULL,
  traceback TEXT,
  FOREIGN KEY(span_id) REFERENCES spans(id)
);
CREATE INDEX IF NOT EXISTS idx_errors_span_id ON errors(span_id);

CREATE TABLE IF NOT EXISTS eval_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trace_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  grader TEXT,
  status TEXT NOT NULL,
  score REAL,
  details_json TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(trace_id) REFERENCES traces(id)
);
CREATE INDEX IF NOT EXISTS idx_eval_results_trace_id ON eval_results(trace_id);
"""


class SQLiteTraceStore:
    def __init__(self, db_path: str | Path = "trace_replay.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.executescript(SCHEMA_SQL)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def write_trace(self, trace: TraceRecord) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO traces (id, name, started_at, ended_at, status, root_span_id, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.id,
                    trace.name,
                    trace.started_at,
                    trace.ended_at,
                    trace.status,
                    trace.root_span_id,
                    trace.metadata_json,
                ),
            )
            for span in trace.spans:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO spans
                    (id, trace_id, parent_id, name, function_name, module, status, started_at, ended_at, duration_ms,
                     input_json, output_json, exception_json, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        span.id,
                        trace.id,
                        span.parent_id,
                        span.name,
                        span.function_name,
                        span.module,
                        span.status,
                        span.started_at,
                        span.ended_at,
                        span.duration_ms,
                        span.input_json,
                        span.output_json,
                        span.exception_json,
                        span.metadata_json,
                    ),
                )
                if span.prompt_text:
                    conn.execute(
                        "INSERT INTO prompts (span_id, role, content, metadata_json) VALUES (?, 'user', ?, ?)",
                        (span.id, span.prompt_text, json.dumps({"source": "decorator"})),
                    )
                if span.completion_text:
                    conn.execute(
                        "INSERT INTO completions (span_id, content, model, metadata_json) VALUES (?, ?, ?, ?)",
                        (span.id, span.completion_text, None, json.dumps({"source": "decorator"})),
                    )
                if span.exception_json:
                    exc = json.loads(span.exception_json)
                    conn.execute(
                        "INSERT INTO errors (span_id, error_type, message, traceback) VALUES (?, ?, ?, ?)",
                        (span.id, exc.get("type", "Exception"), exc.get("message", ""), exc.get("traceback")),
                    )

            for event in trace.events:
                conn.execute(
                    "INSERT INTO events (trace_id, event_type, timestamp, payload_json) VALUES (?, ?, ?, ?)",
                    (trace.id, event.event_type, event.timestamp, json.dumps(event.payload)),
                )
