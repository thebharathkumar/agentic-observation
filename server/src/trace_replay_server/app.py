from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect

from .db import Database
from .schemas import EvalResultIn, EvalResultOut, PromptDiffOut, TraceDetail, TraceIn, TraceSummary

app = FastAPI(title="trace-replay server", version="0.1.0")
db = Database()
watchers: dict[str, list[WebSocket]] = defaultdict(list)


async def notify(trace_id: str, payload: dict[str, Any]) -> None:
    stale: list[WebSocket] = []
    for ws in watchers[trace_id]:
        try:
            await ws.send_json(payload)
        except Exception:  # noqa: BLE001
            stale.append(ws)
    for ws in stale:
        watchers[trace_id].remove(ws)


@app.post("/traces", response_model=TraceDetail)
async def ingest_trace(trace: TraceIn) -> TraceDetail:
    conn = db.connect()
    conn.execute(
        """
        INSERT OR REPLACE INTO traces (id, name, started_at, ended_at, status, root_span_id, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (trace.id, trace.name, trace.started_at, trace.ended_at, trace.status, trace.root_span_id, trace.metadata_json),
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
                (span.id, span.prompt_text, json.dumps({"source": "api"})),
            )
        if span.completion_text:
            conn.execute(
                "INSERT INTO completions (span_id, content, model, metadata_json) VALUES (?, ?, ?, ?)",
                (span.id, span.completion_text, None, json.dumps({"source": "api"})),
            )
    for event in trace.events:
        conn.execute(
            "INSERT INTO events (trace_id, event_type, timestamp, payload_json) VALUES (?, ?, ?, ?)",
            (trace.id, event.event_type, event.timestamp, json.dumps(event.payload)),
        )
    conn.commit()
    conn.close()

    await notify(trace.id, {"type": "trace.updated", "trace_id": trace.id, "span_count": len(trace.spans)})
    return TraceDetail(**trace.model_dump())


@app.get("/traces", response_model=list[TraceSummary])
def list_traces(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    failed_only: bool = False,
) -> list[TraceSummary]:
    conn = db.connect()
    params: list[Any] = []
    filters: list[str] = []
    if status:
        filters.append("status = ?")
        params.append(status)
    if failed_only:
        filters.append("id IN (SELECT DISTINCT trace_id FROM eval_results WHERE status = 'fail')")
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = conn.execute(
        f"SELECT id, name, status, started_at, ended_at, created_at FROM traces {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()
    conn.close()
    return [TraceSummary(**dict(row)) for row in rows]


@app.get("/traces/{trace_id}", response_model=TraceDetail)
def get_trace(trace_id: str) -> TraceDetail:
    conn = db.connect()
    trace = conn.execute("SELECT * FROM traces WHERE id = ?", (trace_id,)).fetchone()
    if trace is None:
        conn.close()
        raise HTTPException(status_code=404, detail="trace not found")
    spans = conn.execute("SELECT * FROM spans WHERE trace_id = ? ORDER BY started_at ASC", (trace_id,)).fetchall()
    events = conn.execute("SELECT event_type, timestamp, payload_json FROM events WHERE trace_id = ? ORDER BY timestamp ASC", (trace_id,)).fetchall()
    conn.close()

    span_payload = [
        {
            **dict(row),
            "prompt_text": None,
            "completion_text": None,
        }
        for row in spans
    ]
    event_payload = [
        {"event_type": row["event_type"], "timestamp": row["timestamp"], "payload": json.loads(row["payload_json"])}
        for row in events
    ]

    return TraceDetail(
        **dict(trace),
        spans=span_payload,
        events=event_payload,
    )


@app.get("/traces/{trace_id}/diff", response_model=PromptDiffOut)
def diff_traces(trace_id: str, compare: str) -> PromptDiffOut:
    conn = db.connect()
    left = conn.execute(
        """
        SELECT p.content
        FROM prompts p JOIN spans s ON p.span_id = s.id
        WHERE s.trace_id = ? ORDER BY p.id ASC
        """,
        (trace_id,),
    ).fetchall()
    right = conn.execute(
        """
        SELECT p.content
        FROM prompts p JOIN spans s ON p.span_id = s.id
        WHERE s.trace_id = ? ORDER BY p.id ASC
        """,
        (compare,),
    ).fetchall()
    conn.close()
    if not left and not right:
        raise HTTPException(status_code=404, detail="no prompts found for compared traces")

    left_lines = [r["content"] for r in left]
    right_lines = [r["content"] for r in right]
    max_len = max(len(left_lines), len(right_lines))
    changes = []
    for i in range(max_len):
        l = left_lines[i] if i < len(left_lines) else ""
        r = right_lines[i] if i < len(right_lines) else ""
        if l != r:
            changes.append({"index": i, "left": l, "right": r})

    return PromptDiffOut(
        left_trace_id=trace_id,
        right_trace_id=compare,
        model_version_changed=False,
        prompt_changes=changes,
        summary=("No prompt differences detected" if not changes else f"{len(changes)} prompt segment(s) changed"),
    )


@app.websocket("/traces/{trace_id}/stream")
async def stream_trace(trace_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    watchers[trace_id].append(websocket)
    await websocket.send_json({"type": "connected", "trace_id": trace_id})
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "trace_id": trace_id})
    except WebSocketDisconnect:
        if websocket in watchers[trace_id]:
            watchers[trace_id].remove(websocket)


@app.post("/evals/import", response_model=list[EvalResultOut])
def import_eval_results(items: list[EvalResultIn]) -> list[EvalResultOut]:
    conn = db.connect()
    inserted: list[EvalResultOut] = []
    for item in items:
        cur = conn.execute(
            """
            INSERT INTO eval_results (trace_id, task_id, grader, status, score, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item.trace_id, item.task_id, item.grader, item.status, item.score, json.dumps(item.details)),
        )
        inserted.append(EvalResultOut(id=cur.lastrowid, **item.model_dump()))
    conn.commit()
    conn.close()
    return inserted


@app.get("/evals", response_model=list[EvalResultOut])
def list_eval_results(status: str | None = None) -> list[EvalResultOut]:
    conn = db.connect()
    if status:
        rows = conn.execute("SELECT * FROM eval_results WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM eval_results ORDER BY id DESC").fetchall()
    conn.close()
    return [
        EvalResultOut(
            id=row["id"],
            trace_id=row["trace_id"],
            task_id=row["task_id"],
            grader=row["grader"],
            status=row["status"],
            score=row["score"],
            details=json.loads(row["details_json"] or "{}"),
        )
        for row in rows
    ]


@app.get("/export/jsonl")
def export_jsonl() -> dict[str, str]:
    conn = db.connect()
    rows = conn.execute("SELECT * FROM traces ORDER BY created_at ASC").fetchall()
    output = "trace_export.jsonl"
    with open(output, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
    conn.close()
    return {"path": output}
