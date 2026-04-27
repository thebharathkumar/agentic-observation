import json
import sqlite3
from pathlib import Path

import pytest

from trace_replay import SQLiteExporter, trace


def test_trace_decorator_captures_success(tmp_path: Path) -> None:
    db_path = tmp_path / "trace.db"

    @trace(exporter=SQLiteExporter(db_path=db_path), capture_prompt_arg="prompt")
    def fake_agent(prompt: str) -> str:
        return f"Echo: {prompt}"

    out = fake_agent("hello")
    assert out == "Echo: hello"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    traces = conn.execute("SELECT * FROM traces").fetchall()
    spans = conn.execute("SELECT * FROM spans").fetchall()
    prompts = conn.execute("SELECT * FROM prompts").fetchall()
    conn.close()

    assert len(traces) == 1
    assert len(spans) == 1
    assert len(prompts) == 1
    assert prompts[0]["content"] == "hello"


def test_trace_decorator_captures_exception(tmp_path: Path) -> None:
    db_path = tmp_path / "trace.db"

    @trace(exporter=SQLiteExporter(db_path=db_path))
    def broken() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        broken()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    span = conn.execute("SELECT * FROM spans").fetchone()
    err = conn.execute("SELECT * FROM errors").fetchone()
    conn.close()

    assert span["status"] == "error"
    payload = json.loads(span["exception_json"])
    assert payload["type"] == "ValueError"
    assert err["error_type"] == "ValueError"
