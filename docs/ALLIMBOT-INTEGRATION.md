# Optional allimbot notifications

Agent Runtime ships an optional, standard-library-only allimbot client for
long-running work that benefits from a phone or dashboard alert. Notification
delivery is never part of the success criteria for the host operation.

## Delivery contract

The client tries these routes in order:

1. The local allimbot dashboard at `ALLIMBOT_URL/trigger` when
   `ALLIMBOT_TOKEN` is set.
2. The fixed `https://ntfy.sh` endpoint when `ALLIMBOT_NTFY_TOPIC` is set.

Missing configuration returns `False` without output or a network request.
Network and serialization errors are swallowed, and each network attempt is
capped at three seconds. A dashboard failure may therefore add at most one
three-second attempt before the ntfy fallback. Notifications must not contain
credentials, account data, private prompts, or other sensitive context.

## Configuration

Copy the blank template values into an untracked `.env` or the process
environment. Never commit real values.

```dotenv
ALLIMBOT_URL=http://127.0.0.1:8787
ALLIMBOT_TOKEN=
ALLIMBOT_NTFY_TOPIC=
ALLIMBOT_PROVIDER=
```

- `ALLIMBOT_TOKEN` enables the local dashboard path and its guardrails/history.
- `ALLIMBOT_NTFY_TOPIC` enables the direct fallback.
- `ALLIMBOT_PROVIDER` optionally selects a dashboard provider.
- `ALLIMBOT_URL` defaults to loopback and is only read when a token is set.

## Wired lifecycle events

| Event | Surface | Message policy |
| --- | --- | --- |
| Task completion/failure | template `agent_orchestrator.py` | explicit `/kill --outcome completed|failed`; task ID only |
| Owner governance block | root and template governance gates | exit code only |
| Session stop request | template Codex Stop hook | static message |
| Upstream update notice | package `update_notify.py` | the public version notice |
| CI failure | GitHub Actions test workflow | workflow, ref, and run URL |

The CI path is disabled by default. It runs once from the Python 3.12 matrix
only when repository variable `ALLIMBOT_CI_NOTIFY_ENABLED` equals `true`; the
ntfy topic must be stored as an `ALLIMBOT_NTFY_TOPIC` Actions secret.

## Direct use

```python
from agent_runtime.allimbot import notify, notify_on_complete

notify("TASK-123 completed", title="agent_runtime")

@notify_on_complete(title="nightly maintenance")
def maintain() -> None:
    ...
```

Generated hosts can use `scripts/allimbot.py` with the same API. Its CLI is
silent and exits zero by default even when delivery is disabled or fails;
`--verbose` is available only for an explicit operator diagnostic.
