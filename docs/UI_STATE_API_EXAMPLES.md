---
id: UI-STATE-API-EXAMPLES
task: TASK-AR-227
status: completed
owner: lead-engineer
updated_at: 2026-06-10
tags: [ui-console, runtime-api, examples]
---

# UI State API Examples

`TASK-AR-227` exposes a read-only local adapter that is shaped like the future
HTTP API. The UI can call this adapter now and later swap the transport to
`GET /api/*` without changing the response contract.

## Local Adapter Commands

```powershell
$env:PYTHONPATH='src'
python -m agent_runtime.cli ui-state --root . --resource state --json
python -m agent_runtime.cli ui-state --root . --resource tasks --json
python -m agent_runtime.cli ui-state --root . --resource agents --json
python -m agent_runtime.cli ui-state --root . --resource messages --json
python -m agent_runtime.cli ui-state --root . --resource events --json
python -m agent_runtime.cli ui-state --root . --resource goals --json
python -m agent_runtime.cli ui-state --root . --resource sources --json
```

## Endpoint Equivalents

| Future endpoint | Local adapter resource | Notes |
|---|---|---|
| `GET /api/state` | `--resource state` | Full aggregate state |
| `GET /api/tasks` | `--resource tasks` | Normalized task cards/detail source |
| `GET /api/agents` | `--resource agents` | Session-derived agent status |
| `GET /api/messages` | `--resource messages` | Inbox/archive markdown messages |
| `GET /api/events` | `--resource events` | Runtime JSONL timeline |
| `GET /api/goals` | `--resource goals` | `STATUS.md`-derived MVP goal record |
| `GET /api/sources` | `--resource sources` | Source freshness and mutation boundary map |

## `/api/state` Shape

```json
{
  "generated_at": "2026-06-10T12:05:00+09:00",
  "sources": [
    {
      "id": "tasks",
      "path": "agents/lead_engineer/tasks",
      "kind": "task_directory",
      "fresh": true,
      "last_updated": "2026-06-10T12:00:00+09:00",
      "last_read_at": "2026-06-10T12:05:00+09:00",
      "freshness": "present",
      "mutation_boundary": "api_or_outbox"
    }
  ],
  "tasks": [],
  "agents": [],
  "messages": [],
  "events": [],
  "goals": [],
  "gaps": [],
  "warnings": []
}
```

## Task Record Shape

```json
{
  "id": "TASK-AR-227",
  "title": "ui state api",
  "status": "completed",
  "lane": "Done",
  "priority": "P0",
  "order": 0,
  "owner_agent": "lead-engineer",
  "team": null,
  "labels": ["ui-console", "runtime-api"],
  "description": "Expose a safe, read-first backend interface.",
  "blocked_reason": null,
  "created_at": "2026-06-10",
  "updated_at": null,
  "completed_at": null,
  "audit_log": ["BACKLOG.md"],
  "source_path": "agents/lead_engineer/tasks/TASK-AR-227.md",
  "source_kind": "task_markdown",
  "source": {
    "path": "agents/lead_engineer/tasks/TASK-AR-227.md",
    "kind": "task_markdown",
    "last_updated": "2026-06-10T12:00:00+09:00",
    "last_read_at": "2026-06-10T12:05:00+09:00",
    "freshness": "present"
  },
  "last_updated": "2026-06-10T12:00:00+09:00",
  "freshness": "present"
}
```

## Missing Source Behavior

Missing optional runtime directories do not fail the response. They return empty
collections and explicit gap records:

```json
{
  "kind": "missing_optional_source",
  "source_id": "messages_inbox",
  "path": "agents/messages/inbox",
  "detail": "optional runtime source is not present"
}
```

Malformed JSONL/session files return warning records and the rest of the state
continues to load.

## Mutation Boundary

All `ui-state` reads are side-effect-free. Task edits, message sends, stop files,
claim files, and event appends remain outside this adapter and must go through a
future runtime API or command outbox.
