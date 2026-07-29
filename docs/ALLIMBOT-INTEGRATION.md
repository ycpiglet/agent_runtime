# Native Allimbot project events

Agent Runtime's `security-service` profile can enqueue a small, structured
event vocabulary into an installed Allimbot spool. Event delivery is advisory
and never changes the result of a host operation.

## Ownership boundary

- Agent Runtime validates the managed recipe, event type, exact fields, and
  bounded values. It renders the summary and always supplies an empty body.
- Installed Allimbot owns the SQLite spool, leases, retry/dead-letter policy,
  credentials, and network delivery.
- Runtime calls `ProjectEmitter.emit()` only. It never calls `flush()`, sends
  to `/trigger` or `/v1/events`, or falls back to ntfy.

The producer returns `spooled` with an event ID only after Allimbot confirms
the local enqueue. A missing dependency, configuration failure, or unwritable
spool returns a bounded `unavailable` reason and does not fail the host
operation. An unknown event, unexpected field, unsafe value, or managed-recipe
drift raises `EventPolicyError` before emitter construction.

## Event contract

| Event | Exact data fields |
| --- | --- |
| `attention.required` | `task_id`, `attention_kind`, `owner_role`, `state` |
| `task.state.changed` | `task_id`, `from_state`, `to_state`, `owner_role` |
| `release.gate.failed` | `gate`, `release`, `finding_count` |
| `turn.completed` | `task_id`, `result_state`, `duration_seconds` |

Callers cannot supply a summary or body. Prompts, arbitrary messages,
exception text, tracebacks, credentials, environment values, endpoints,
provider names, and destinations are outside the API.

State, result-state, attention-kind, and gate fields use Runtime-owned
allowlists. Non-system task IDs must name a regular canonical task file under
`agents/lead_engineer/tasks/`, and non-system owner roles must be canonical
IDs in `agents/project/ORG-MODEL.yml`. Release values are strict semantic
release tags. Session and turn correlations are canonical UUIDs, dedupe keys
are lowercase SHA-256 digests, and Allimbot must return a canonical UUID event
ID. Arbitrary display-safe strings therefore cannot cross the producer
boundary, even when they do not resemble a known credential or endpoint.

## Profile and configuration

Select `security-service` in `agent_runtime.yml`. Its managed projection adds:

- `.allimbot.json`;
- `scripts/allimbot.py`;
- `agents/project/SECURITY-SERVICE-POLICY.json`;
- `scripts/security_service_gate.py`; and
- `docs/security-service.md`.

The core profile excludes those assets and imports no optional Allimbot
module. Install Allimbot separately in the host's isolated environment, then
export configuration through the host's existing secret manager:

```dotenv
ALLIMBOT_ENDPOINT=
ALLIMBOT_PROJECT_TOKEN=
ALLIMBOT_SPOOL_PATH=
```

Do not commit values. `ALLIMBOT_SPOOL_PATH` must be an absolute path under the
installed Allimbot contract. A separate, intentionally operated Allimbot
worker performs delivery; Runtime does not start it.

## Usage

```python
from agent_runtime.allimbot import emit_event

result = emit_event(
    "task.state.changed",
    {
        "task_id": "TASK-123",
        "from_state": "review",
        "to_state": "completed",
        "owner_role": "lead-engineer",
    },
    root=repository_root,
)
```

Generated security-service hosts may call the thin `scripts/allimbot.py`
wrapper with the same structured event shape. The legacy
`notify(message, title, provider)` function remains for one release, but
ignores all supplied text and emits only a fixed compatibility signal.

## Wired lifecycle sites

| Runtime surface | Event |
| --- | --- |
| Owner governance block | `attention.required` |
| Available Runtime update | `attention.required` |
| Authoritative task completion or worker failure | `task.state.changed` |
| One portable stop boundary (`stop-closure`) | `turn.completed` |

GitHub Actions has no direct notification job. `notify_routing.py` remains a
separate dormant channel-recipe surface and is not an Allimbot transport.

## Safe diagnostics

`agent_runtime doctor --json` reports profile selection, recipe/policy/gate
presence and match status, optional dependency availability, boolean
configuration presence, risk-path counts, and stale legacy wiring. It does
not instantiate an emitter, open a spool, read a credential/keyring value, or
probe a network endpoint.
