# trace-replay SQLite storage schema (v0.1 stable)

Database file: `trace_replay.db`

## tables

### traces
- `id` TEXT PK
- `name` TEXT
- `started_at` TEXT (ISO-8601 UTC)
- `ended_at` TEXT (ISO-8601 UTC)
- `status` TEXT (`ok|error`)
- `root_span_id` TEXT
- `metadata_json` TEXT
- `created_at` TEXT

### spans
- `id` TEXT PK
- `trace_id` TEXT FK -> traces.id
- `parent_id` TEXT nullable
- `name` TEXT
- `function_name` TEXT
- `module` TEXT
- `status` TEXT
- `started_at` TEXT
- `ended_at` TEXT
- `duration_ms` REAL
- `input_json` TEXT
- `output_json` TEXT nullable
- `exception_json` TEXT nullable
- `metadata_json` TEXT nullable

### events
- `id` INTEGER PK AUTOINCREMENT
- `trace_id` TEXT FK
- `event_type` TEXT
- `timestamp` TEXT
- `payload_json` TEXT

### prompts
- `id` INTEGER PK AUTOINCREMENT
- `span_id` TEXT FK
- `role` TEXT
- `content` TEXT
- `metadata_json` TEXT

### completions
- `id` INTEGER PK AUTOINCREMENT
- `span_id` TEXT FK
- `content` TEXT
- `model` TEXT nullable
- `metadata_json` TEXT nullable

### errors
- `id` INTEGER PK AUTOINCREMENT
- `span_id` TEXT FK
- `error_type` TEXT
- `message` TEXT
- `traceback` TEXT nullable

### eval_results
- `id` INTEGER PK AUTOINCREMENT
- `trace_id` TEXT FK
- `task_id` TEXT
- `grader` TEXT nullable
- `status` TEXT (`pass|fail`)
- `score` REAL nullable
- `details_json` TEXT nullable
- `created_at` TEXT

This schema is intentionally sqlite3-friendly so users can inspect traces with:

```bash
sqlite3 trace_replay.db '.tables'
sqlite3 trace_replay.db 'select id,name,status from traces limit 10;'
```
