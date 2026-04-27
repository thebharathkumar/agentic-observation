# trace-replay build report

## Phase 1: Repository skeleton
- Built monorepo layout: `server/`, `sdk/`, `web/`, `examples/`.
- Added Python package metadata (`server/pyproject.toml`, `sdk/pyproject.toml`), web package metadata (`web/package.json`), top-level `Makefile`, and root `README.md`.
- End-to-end: project has runnable entrypoints and test/build commands.

## Phase 2: SDK and storage
- Implemented `@trace` decorator in `sdk/src/trace_replay/decorator.py` capturing args/return/exception/duration.
- Added pluggable exporters (`SQLiteExporter`, `OTelHTTPExporter`).
- Added stable SQLite schema and docs in `docs/STORAGE_SCHEMA.md`.
- Added unit tests and runnable examples in `examples/*`.
- End-to-end: calling a decorated function writes real trace rows to SQLite.

## Phase 3: FastAPI ingestion server
- Implemented POST/GET trace endpoints, diff endpoint, websocket stream endpoint.
- Added Pydantic request/response models and integration tests.
- Added JSONL export endpoint.
- End-to-end: ingest + list + fetch + diff flows covered in tests.

## Phase 4: Trace timeline UI
- Added `TraceTimeline.tsx` with scrub bar and transport controls: play/pause/step/rewind.
- Added keyboard shortcuts: space, arrows, j/k.
- End-to-end: UI demonstrates timeline replay over span sequence.

## Phase 5: Prompt diff view
- Added `PromptDiff.tsx` token diff via `diff-match-patch` with side-by-side rendering.
- End-to-end: changed tokens are highlighted across runs.

## Phase 6: Eval-aware tracing
- Added `eval_results` table.
- Added `/evals/import` + `/evals` endpoints and `failed_only` trace filtering.
- Added simple `EvalHeatmap.tsx` visualization.
- End-to-end: failed eval traces can be filtered from API.

## Phase 7: Polish and ship (partial)
- Added CLI entrypoint `trace-replay serve` and quickstart docs.
- Added demo plan file.
- Divergence: actual PyPI publish/tag cannot be executed in this environment.

## Phase 8: Launch artifact (partial)
- Added blog draft placeholder and demo script plan.
- Divergence: external posting cannot be executed in this environment.
