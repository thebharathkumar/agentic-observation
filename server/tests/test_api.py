import json
from uuid import uuid4

from fastapi.testclient import TestClient

from trace_replay_server.app import app


client = TestClient(app)


def _sample_trace(trace_id: str) -> dict:
    return {
        "id": trace_id,
        "name": "agent.run",
        "started_at": "2026-04-27T00:00:00Z",
        "ended_at": "2026-04-27T00:00:01Z",
        "status": "ok",
        "root_span_id": "span-1",
        "metadata_json": "{}",
        "spans": [
            {
                "id": "span-1",
                "parent_id": None,
                "name": "agent.run",
                "function_name": "run",
                "module": "example",
                "status": "ok",
                "started_at": "2026-04-27T00:00:00Z",
                "ended_at": "2026-04-27T00:00:01Z",
                "duration_ms": 100.0,
                "input_json": json.dumps({"prompt": "hello"}),
                "output_json": json.dumps({"answer": "world"}),
                "exception_json": None,
                "metadata_json": "{}",
                "prompt_text": "hello",
                "completion_text": "world",
            }
        ],
        "events": [{"event_type": "span.closed", "timestamp": "2026-04-27T00:00:01Z", "payload": {"span_id": "span-1"}}],
    }


def test_ingest_and_fetch_trace() -> None:
    trace_id = str(uuid4())
    payload = _sample_trace(trace_id)
    r = client.post("/traces", json=payload)
    assert r.status_code == 200

    listed = client.get("/traces")
    assert listed.status_code == 200
    assert any(t["id"] == trace_id for t in listed.json())

    detail = client.get(f"/traces/{trace_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == trace_id


def test_prompt_diff() -> None:
    left = str(uuid4())
    right = str(uuid4())
    l_payload = _sample_trace(left)
    r_payload = _sample_trace(right)
    r_payload["spans"][0]["prompt_text"] = "hello updated"

    assert client.post("/traces", json=l_payload).status_code == 200
    assert client.post("/traces", json=r_payload).status_code == 200

    diff = client.get(f"/traces/{left}/diff", params={"compare": right})
    assert diff.status_code == 200
    body = diff.json()
    assert body["left_trace_id"] == left
    assert len(body["prompt_changes"]) >= 1


def test_eval_import_and_failed_filter() -> None:
    trace_id = str(uuid4())
    payload = _sample_trace(trace_id)
    assert client.post("/traces", json=payload).status_code == 200

    evals = [
        {"trace_id": trace_id, "task_id": "task-1", "grader": "exact-match", "status": "fail", "score": 0.0, "details": {"reason": "wrong"}},
    ]
    imported = client.post("/evals/import", json=evals)
    assert imported.status_code == 200
    assert imported.json()[0]["status"] == "fail"

    filtered = client.get("/traces", params={"failed_only": "true"})
    assert filtered.status_code == 200
    assert any(row["id"] == trace_id for row in filtered.json())
