from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SpanIn(BaseModel):
    id: str
    parent_id: str | None = None
    name: str
    function_name: str
    module: str
    status: str
    started_at: str
    ended_at: str
    duration_ms: float
    input_json: str
    output_json: str | None = None
    exception_json: str | None = None
    metadata_json: str | None = None
    prompt_text: str | None = None
    completion_text: str | None = None


class EventIn(BaseModel):
    event_type: str
    timestamp: str
    payload: dict[str, Any] = Field(default_factory=dict)


class TraceIn(BaseModel):
    id: str
    name: str
    started_at: str
    ended_at: str
    status: str
    root_span_id: str | None = None
    metadata_json: str = "{}"
    spans: list[SpanIn] = Field(default_factory=list)
    events: list[EventIn] = Field(default_factory=list)


class TraceSummary(BaseModel):
    id: str
    name: str
    status: str
    started_at: str
    ended_at: str
    created_at: str


class TraceDetail(TraceIn):
    pass


class PromptDiffOut(BaseModel):
    left_trace_id: str
    right_trace_id: str
    model_version_changed: bool
    prompt_changes: list[dict[str, Any]]
    summary: str


class EvalResultIn(BaseModel):
    trace_id: str
    task_id: str
    grader: str | None = None
    status: str
    score: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class EvalResultOut(EvalResultIn):
    id: int
