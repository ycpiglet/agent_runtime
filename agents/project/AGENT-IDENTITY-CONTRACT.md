---
title: Agent Identity Contract
status: active
owner: lead-engineer
updated_at: 2026-06-12T14:50:00+09:00
signal: pass
score: 90
tags: [agent-identity, runtime, attribution]
---

# Agent Identity Contract

## Bottom Line

Runtime attribution must distinguish an agent role from a live agent instance.
`qa`, `lead-engineer`, or `doc-steward` is a role/class. A spawned worker is an
instance identified by `agent_instance_id` and shown with a readable callsign.

## Signal

| Signal | Current Rule | Consumer |
| --- | --- | --- |
| Role-only attribution | Invalid for runtime artifacts | `agent_identity_gate.py` |
| Claim spawn record | Required for new task claims | `task_claim_dispatcher.py` |
| Claim-created event actor | `agent_instance_id` with role/callsign context | `pane_event_log.py` |

## Identity Layers

| Layer | Field | Meaning |
| --- | --- | --- |
| Role | `agent_role` / `role` | Durable skill or responsibility class |
| Instance | `agent_instance_id` | Unique live execution unit |
| Callsign | `display_name` / `callsign` | Human-readable runtime label |
| Callsite | `callsite_id` | Terminal, pane, launcher, or parent origin |

## Spawn Record

Every task claim created through `scripts/task_claim_dispatcher.py create` must
write an instance record under `agents/runtime/instances/<agent_instance_id>.json`
with schema `agent-runtime-agent-instance/v1`.

Required claim-derived fields:

- `role`
- `team_id`
- `agent_instance_id`
- `display_name`
- `callsign`
- `callsite_id`
- `pane_id`
- `spawned_at`
- `spawned_by`
- `task_id`
- `task_set_id`
- `worktree_path`
- `model_tier`
- `claim_refs`

`claim_refs` links the instance back to the claim JSON that caused the spawn
record. Re-recording the same claim is idempotent and must not duplicate refs.

## Attribution Rule

Role-only attribution is invalid for runtime artifacts. A record that says only
`actor: qa` or `agent_role: qa` is not enough to analyze when and why work
happened. Runtime artifacts should carry `agent_instance_id` directly or be
joinable to a claim/instance record that carries it.

## Gate

Run:

```powershell
python scripts/agent_identity_gate.py --check
```

The gate validates active claims against instance records and reports missing
or mismatched instance attribution. Historical/released claims can be audited
with:

```powershell
python scripts/agent_identity_gate.py --all --check
```

## Action

- Use `scripts/task_claim_dispatcher.py create` for new runtime claims so the
  instance record is created with the claim.
- Run `python scripts/agent_identity_gate.py --check` before closeout when claim
  attribution changed.
- Treat direct `actor: <role>` runtime writes as legacy data unless they are
  joinable through a claim record.

## Risk

- Historical released claims may not have instance records until backfilled.
- A2A messages, commit trailers, and analytics views still need separate
  migration work before they can rely on instance-level attribution everywhere.

## Decision

Instance-level attribution is the canonical runtime identity. Roles remain
routing and responsibility classes, not sufficient execution actors.

## Next

- Extend the same identity chain to A2A messages, evidence records, and commit
  trailers in separate work items.
- Add stats/export consumers after the instance records have stable coverage.

## Boundary

This contract establishes claim-created spawn records and claim-to-instance
validation. A2A message attribution, commit trailers, stats pivots, saved views,
and analytics exports should consume this identity model in separate work
items.
