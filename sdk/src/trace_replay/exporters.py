from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from pathlib import Path
from urllib import request

from .models import TraceRecord
from .storage import SQLiteTraceStore


class TraceExporter(ABC):
    @abstractmethod
    def export(self, trace: TraceRecord) -> None:
        raise NotImplementedError


class SQLiteExporter(TraceExporter):
    def __init__(self, db_path: str | Path = "trace_replay.db") -> None:
        self.store = SQLiteTraceStore(db_path)

    def export(self, trace: TraceRecord) -> None:
        self.store.write_trace(trace)


class OTelHTTPExporter(TraceExporter):
    """Minimal OTLP/HTTP JSON exporter wrapper.

    This exporter forwards the normalized trace payload to a configurable endpoint,
    enabling compatibility with OpenTelemetry collector ingestion pipelines.
    """

    def __init__(self, endpoint: str = "http://localhost:4318/v1/traces", timeout: float = 2.0) -> None:
        self.endpoint = endpoint
        self.timeout = timeout

    def export(self, trace: TraceRecord) -> None:
        body = json.dumps({"trace": asdict(trace)}).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=self.timeout):  # noqa: S310
            return
