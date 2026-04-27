from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(slots=True)
class EventRecord:
    event_type: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=utc_now_iso)


@dataclass(slots=True)
class SpanRecord:
    name: str
    function_name: str
    module: str
    status: str
    started_at: str
    ended_at: str
    duration_ms: float
    input_json: str
    output_json: str | None
    exception_json: str | None
    prompt_text: str | None = None
    completion_text: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))
    parent_id: str | None = None
    metadata_json: str | None = None


@dataclass(slots=True)
class TraceRecord:
    id: str
    name: str
    started_at: str
    ended_at: str
    status: str
    root_span_id: str | None
    metadata_json: str
    spans: list[SpanRecord]
    events: list[EventRecord]
