# Disposable Pilot Isolation Contract

Consumer pilots must prove that Runtime-driven writes occurred only in a new,
disposable target checkout. A live primary checkout is an observation surface,
not a test target and not a byte-stability oracle.

The contract separates local physical proof from portable public evidence:

- raw v1 validates absolute checkout topology and write containment;
- sanitized v2 preserves the decision and non-secret identities without local
  paths.

## Required checkout roles

| Role | Required | May change? | Allowed attribution | Gate result |
| --- | --- | --- | --- | --- |
| `disposable_target` | at least one | yes | `authorized_target` when changed | pass |
| `frozen_control` | at least one | no | `none` | any snapshot change blocks |
| `live_observation` | optional | independently | `external_or_unattributed` when changed | watch, not block |

`pilot_caused` is never valid for a changed live observation. Pilot causality is
supported only by the declared disposable write surface.

## Raw v1: physical proof

Schema `agent-runtime-pilot-isolation/v1` contains canonical absolute `root`
values and `observed_write_roots`. Checkout roots must be absolute, canonical,
and pairwise disjoint. Equal or nested roots block. Every observed write must be
the disposable target root or a descendant of it.

Capture each checkout immediately before and after the pilot:

- `head`: the 40-hex Git commit ID;
- `status_sha256`: SHA-256 of the complete porcelain status observation; and
- `tracked_diff_sha256`: SHA-256 of the complete tracked diff observation.

Use the same commands and byte encoding on both sides. The gate evaluates the
recorded observations; it does not mutate or re-read a checkout.

Validate raw evidence before projection:

```text
python scripts/pilot_isolation_gate.py \
  --evidence <private-raw-v1.json> --check --json
```

## Sanitized v2: portable projection

Only a raw decision with zero blockers can produce schema
`agent-runtime-pilot-isolation/v2`. The projection:

- removes `root` and `observed_write_roots`;
- retains checkout IDs, roles, snapshots, and attribution;
- maps observed writes to `observed_write_checkout_ids`; and
- records the raw file's byte SHA-256, status, blocker/watch counts, and watch
  codes in `raw_proof`.

Generate it atomically:

```text
python scripts/pilot_isolation_gate.py \
  --evidence <private-raw-v1.json> \
  --sanitize-out <public-v2.json> \
  --check --json
```

The output is deterministic for the same raw JSON bytes. Keep raw v1 in the
local evidence boundary; commit or distribute only v2. An acceptance contract
can bind both the v2 semantic digest and the raw v1 byte digest.

The v2 gate rejects absolute paths, malformed or blocking raw decisions,
duplicate/unknown checkout identities, writes mapped outside a disposable
target, snapshot drift with invalid attribution, and unexpected fields.

A frozen-control change, overlapping raw root, write outside the disposable
target, or unsupported causality claim blocks. Unrelated live drift returns
`pass_with_watch`, preserving the observation without blaming the pilot.
