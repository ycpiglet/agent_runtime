---
title: Agent Identity Contract
status: active
owner: lead-engineer
updated_at: 2026-06-13T07:40:43+09:00
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
| Stored artifact attribution | Watch before, block after 2026-06-12 cutoff | `attribution_gate.py` |
| Instance lifecycle census | `instance_spawned`/`heartbeat`/`terminated` events | `pane_event_log.py census` |

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

Optional traceability fields link instance behavior back to the class (skill)
version that spawned it and to its causal chain:

- `skill_versions`: dict of skill/persona name to version.
- `prompt_config_hash`: hash of the prompt/config bundle used at spawn.
- `parent_instance_id`: spawning instance, when spawned by another agent.
- `on_behalf_of`: claim/task/unit the instance acts for.
- `decision_cycle_id`: planning/decision cycle context, when applicable.

Creating a new instance record also appends an `instance_spawned` pane event
carrying `agent_instance_id` plus join keys (claim/task/task-set) only, so the
pane event log supports point-in-time census queries
(`python scripts/pane_event_log.py census --at <ts>`) without duplicating claim
payloads. Long-lived instances should append `instance_heartbeat` and
`instance_terminated` events through `pane_event_log.py census-record`.

## Commit Trailer

Worker commits made on behalf of a live instance should carry a short trailer
block after the regular message body so commit history can be grouped by
instance, not only by author:

```text
Agent-Instance: <agent_instance_id>
Agent-Role: <agent_role>
On-Behalf-Of: <claim_id>
```

`Agent-Instance:` is the canonical trailer and should reference an instance
record under `agents/runtime/instances/`. `Agent-Role:` and `On-Behalf-Of:`
are optional context. Historical commits are not rewritten.

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

Stored artifacts (claims, pane events, A2A messages, evidence records) are
checked by the attribution gate, which treats artifacts dated on or before the
2026-06-12 identity-contract cutoff as watch-level and blocks role-only
attribution after it:

```powershell
python scripts/attribution_gate.py --check
```

## Action

- Use `scripts/task_claim_dispatcher.py create` for new runtime claims so the
  instance record is created with the claim.
- Run `python scripts/agent_identity_gate.py --check` and
  `python scripts/attribution_gate.py --check` before closeout when claim or
  runtime-artifact attribution changed.
- Treat direct `actor: <role>` runtime writes as legacy data unless they are
  joinable through a claim record.
- Append `instance_terminated` (and periodic `instance_heartbeat`) census
  events via `pane_event_log.py census-record` for long-lived instances.
- Add the `Agent-Instance:` trailer to new worker commits.

## Risk

- Historical released claims may not have instance records until backfilled.
- Artifacts dated on or before the 2026-06-12 cutoff stay watch-level in
  `attribution_gate.py` until backfilled; analytics over that window must
  tolerate role-only actors.
- Commit trailers are convention-checked in review, not yet machine-enforced.

## Decision

Instance-level attribution is the canonical runtime identity. Roles remain
routing and responsibility classes, not sufficient execution actors.

## Next

- Add stats/export consumers after the instance records have stable coverage.
- Backfill or annotate pre-cutoff artifacts so attribution-gate watch counts
  trend to zero.
- Consider machine-enforcing the `Agent-Instance:` commit trailer once worker
  tooling writes it automatically.

## Boundary

This contract establishes claim-created spawn records, claim-to-instance
validation, stored-artifact attribution gating (claims, pane events, A2A,
evidence), lifecycle census events, and the commit-trailer convention. Stats
pivots, saved views, and analytics exports should consume this identity model
in separate work items.
