from __future__ import annotations

import functools
import inspect
import json
import traceback
from contextvars import ContextVar
from dataclasses import asdict
from time import perf_counter
from typing import Any, Callable, TypeVar
from uuid import uuid4

from .exporters import SQLiteExporter, TraceExporter
from .models import EventRecord, SpanRecord, TraceRecord, utc_now_iso

F = TypeVar("F", bound=Callable[..., Any])

_trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)
_span_id_ctx: ContextVar[str | None] = ContextVar("span_id", default=None)
_spans_ctx: ContextVar[list[SpanRecord] | None] = ContextVar("spans", default=None)
_events_ctx: ContextVar[list[EventRecord] | None] = ContextVar("events", default=None)
_trace_name_ctx: ContextVar[str | None] = ContextVar("trace_name", default=None)
_trace_started_ctx: ContextVar[str | None] = ContextVar("trace_started", default=None)


def _json_safe(value: Any) -> str:
    return json.dumps(value, default=str, ensure_ascii=False)


def trace(
    name: str | None = None,
    exporter: TraceExporter | None = None,
    capture_prompt_arg: str | None = None,
) -> Callable[[F], F]:
    """Trace any function and write spans to SQLite or OTel exporter.

    If nested traced functions are called, they become spans within one trace.
    """

    exporter_impl = exporter or SQLiteExporter()

    def decorator(fn: F) -> F:
        fn_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            is_root = _trace_id_ctx.get() is None
            if is_root:
                _trace_id_ctx.set(str(uuid4()))
                _spans_ctx.set([])
                _events_ctx.set([])
                _trace_name_ctx.set(fn_name)
                _trace_started_ctx.set(utc_now_iso())

            parent_span_id = _span_id_ctx.get()
            span_id = str(uuid4())
            token = _span_id_ctx.set(span_id)

            started_iso = utc_now_iso()
            started = perf_counter()
            status = "ok"
            output_json: str | None = None
            exception_json: str | None = None
            result: Any = None

            bound = inspect.signature(fn).bind_partial(*args, **kwargs)
            bound.apply_defaults()
            payload = dict(bound.arguments)
            prompt_text = None
            if capture_prompt_arg and capture_prompt_arg in payload:
                prompt_text = str(payload[capture_prompt_arg])

            try:
                result = fn(*args, **kwargs)
                output_json = _json_safe(result)
                return result
            except Exception as exc:  # noqa: BLE001
                status = "error"
                exception_json = _json_safe(
                    {
                        "type": exc.__class__.__name__,
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )
                raise
            finally:
                ended_iso = utc_now_iso()
                duration_ms = (perf_counter() - started) * 1000
                span = SpanRecord(
                    id=span_id,
                    parent_id=parent_span_id,
                    name=fn_name,
                    function_name=fn.__name__,
                    module=fn.__module__,
                    status=status,
                    started_at=started_iso,
                    ended_at=ended_iso,
                    duration_ms=duration_ms,
                    input_json=_json_safe(payload),
                    output_json=output_json,
                    exception_json=exception_json,
                    prompt_text=prompt_text,
                    completion_text=(None if result is None else str(result)),
                    metadata_json=_json_safe({"semconv": "genai.v1", "callable": fn.__qualname__}),
                )
                spans = _spans_ctx.get()
                events = _events_ctx.get()
                if spans is not None and events is not None:
                    spans.append(span)
                    events.append(EventRecord(event_type="span.closed", payload={"span_id": span_id, "status": status}))

                _span_id_ctx.reset(token)

                if is_root:
                    trace = TraceRecord(
                        id=_trace_id_ctx.get() or str(uuid4()),
                        name=_trace_name_ctx.get() or fn_name,
                        started_at=_trace_started_ctx.get() or started_iso,
                        ended_at=ended_iso,
                        status=("error" if any(s.status == "error" for s in spans or []) else "ok"),
                        root_span_id=span_id,
                        metadata_json=_json_safe({"semconv": "genai.v1"}),
                        spans=spans or [],
                        events=events or [],
                    )
                    exporter_impl.export(trace)
                    _trace_id_ctx.set(None)
                    _spans_ctx.set(None)
                    _events_ctx.set(None)
                    _trace_name_ctx.set(None)
                    _trace_started_ctx.set(None)

        return wrapper  # type: ignore[return-value]

    return decorator


def export_trace_jsonl(db_path: str = "trace_replay.db", output_path: str = "trace_export.jsonl") -> str:
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM traces ORDER BY created_at ASC").fetchall()
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
    conn.close()
    return output_path
