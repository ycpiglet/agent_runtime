# Disposable Pilot Isolation Contract

Consumer pilots must prove that Runtime-driven writes occurred only in a new,
disposable target checkout. A live primary checkout is an observation surface,
not a test target and not a byte-stability oracle.

## Required checkout roles

| Role | Required | May change? | Allowed attribution | Gate result |
| --- | --- | --- | --- | --- |
| `disposable_target` | at least one | yes | `authorized_target` when changed | pass |
| `frozen_control` | at least one | no | `none` | any snapshot change blocks |
| `live_observation` | optional | independently | `external_or_unattributed` when changed | watch, not block |

Checkout roots must be absolute, canonical, and pairwise disjoint. Equal or
nested roots block. Every entry in `observed_write_roots` must be the disposable
target root or a descendant of one.

`pilot_caused` is never valid for a changed live observation. Pilot causality is
supported only by the declared disposable write surface; claiming causality
outside it blocks.

## Snapshot fields

Capture the following immediately before and after the pilot window:

- `head`: the 40-hex Git commit ID.
- `status_sha256`: SHA-256 of the complete porcelain status observation.
- `tracked_diff_sha256`: SHA-256 of the complete tracked diff observation.

The same deterministic commands and byte encoding must be used for each side of
a comparison. The gate compares the recorded digests; it does not mutate or
re-read the checkouts.

## Evidence shape

Evidence uses schema `agent-runtime-pilot-isolation/v1`:

```json
{
  "schema": "agent-runtime-pilot-isolation/v1",
  "pilot_id": "bean-wiki-attempt-5",
  "observed_write_roots": ["/absolute/path/to/attempt-5"],
  "checkouts": [
    {
      "id": "attempt-5",
      "role": "disposable_target",
      "root": "/absolute/path/to/attempt-5",
      "before": {
        "head": "0000000000000000000000000000000000000000",
        "status_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        "tracked_diff_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
      },
      "after": {
        "head": "0000000000000000000000000000000000000000",
        "status_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
        "tracked_diff_sha256": "1111111111111111111111111111111111111111111111111111111111111111"
      },
      "change_attribution": "authorized_target"
    },
    {
      "id": "attempt-4",
      "role": "frozen_control",
      "root": "/absolute/path/to/attempt-4-frozen",
      "before": {
        "head": "2222222222222222222222222222222222222222",
        "status_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
        "tracked_diff_sha256": "2222222222222222222222222222222222222222222222222222222222222222"
      },
      "after": {
        "head": "2222222222222222222222222222222222222222",
        "status_sha256": "2222222222222222222222222222222222222222222222222222222222222222",
        "tracked_diff_sha256": "2222222222222222222222222222222222222222222222222222222222222222"
      },
      "change_attribution": "none"
    }
  ]
}
```

Run:

```text
python scripts/pilot_isolation_gate.py --evidence <evidence.json> --check --json
```

A frozen-control change, overlapping root, write outside the disposable target,
or unsupported causality claim returns a blocking exit status. Unrelated live
drift returns `pass_with_watch`, preserving evidence without blaming the pilot.
