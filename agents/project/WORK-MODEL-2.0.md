---
type: contract
id: WORK-MODEL-2.0
audience: owner
status: pass
signal: pass
score: 92
priority: High
tags: [work-model, 2.0, units, waves, verification, metadata, lifecycle]
---

# Work Model 2.0 (agent_runtime v0.2.0)

## Bottom Line

- v0.2.0 makes the parallel-execution work model the default. Every new work item
  flows through: register (T0 plan snapshot) -> decompose into units -> group
  footprint-disjoint units into waves -> claim-first dispatch -> implement ->
  W4a self-verify / W4b independent verify -> merge-queue integrate -> W5 cleanup
  -> W6 closeout. The gates that enforce this are wired into owner_governance_gate
  and run every commit/stop-hook.
- This document is the single rule reference for the 2.0 model: how to shape a
  task, what metadata it must carry, how to split it into units, how to register
  waves, and how verification and agent/skill attribution work.

## Signal

| Stage | Mechanism | Gate / Tool |
| --- | --- | --- |
| W0 visibility | session_dashboard hook + `work.py status` | session_dashboard (SessionStart) |
| Register (T0) | `work.py new` auto-records plan snapshot | plan_assumption_gate (record) |
| Decompose | units under agents/lead_engineer/tasks/units/<TASK>/ | task_unit_readiness_gate |
| Wave group | `wave_dispatcher.py --plan` (footprint-disjoint) | footprint_conflict_gate |
| Claim-first | `task_claim_dispatcher.py create` (T2 drift check) | parallel_worktree_gate + plan_assumption_gate |
| Implement | per-unit worktree | claim-first enforcement |
| Verify (W4a/W4b) | worker self-check + distinct-instance APPROVE | cross-verification gate (release --verified-by) |
| Integrate | `merge_queue.py` serial rebase-test-merge | (orchestrator tool) |
| Cleanup (W5) | `worktree_lifecycle_gate.py --clean` | worktree_lifecycle_gate |
| Closeout (W6) | claim release + record completion + closeout review | verification_freshness_gate, conversation_work_audit |

## Required Work Item Metadata (v2.0 envelope)

Every work item carrying `schema_version: agent-runtime-work-item/v1` must have the
minimum-required-by-kind fields validated by `work_schema_gate.py --items`:

- Identity: `schema_version, work_id, work_uid, kind, parent_id, status, owner,
  created_at, updated_at`
- Provenance: `origin_type` (owner_request | planning_proposal | doc_intake |
  idea_vault_revival | retro | automation_rule), `origin_ref`, `created_by`
- When closed: `resolution` (done | wontfix | duplicate | superseded |
  moved_to_vault), `completed_at`, `verification_status`

Optional catalog fields (relations, governance, measurement, display) are
documented in `WORK-SCHEMA.yml` with their source (generator|gate|human|runtime|
derived) and promotion policy (optional -> required only when a consuming tool
exists). Derived values (progress_pct, age, variance) are storage-forbidden;
they are computed by views, never stored.

Legacy records authored before v0.2.0 are migrated with
`scripts/migrate_work_metadata_v2.py --all-open`, which derives the v2.0 envelope
from existing frontmatter (idempotent; completed/archived records are left as
historical).

## How to Decompose a Task into Units

- A unit is the smallest independently-claimable, independently-verifiable slice.
  Units live in `agents/lead_engineer/tasks/units/<TASK-AR-NNN>/UNIT-...-NNN.md`
  and follow the unit template (see units/README.md + units/examples).
- Each unit declares `target_files` (its write footprint) and optional
  `depends_on` (unit/task ids it must follow). The footprint is what the
  claim-time conflict gate and the wave dispatcher use to parallelize safely.
- Sizing rule: a unit should be completable + verifiable by one worker instance
  in one sitting, with a verification command that proves it.

## How to Register Waves

- `wave_dispatcher.py --plan --taskset <id>` computes topological waves from
  `depends_on` and splits any footprint-overlapping units into later waves.
- `--dispatch --mode cascade` keeps the sequential default; `--mode parallel
  --max-panes N` batch-issues claim+worktree for up to N footprint-disjoint units
  of the next wave.
- A wave is execution-scheduling metadata, orthogonal to the taskset hierarchy:
  one wave may carry units from multiple tasksets.

## Verification (W4a / W4b)

- W4a (worker self-verification): the implementing instance runs the unit's
  declared verification commands + the focused/full test suite + the governance
  gate, and records the observed results.
- W4b (independent verification): a DISTINCT instance (not the worker) reviews and
  returns APPROVE / REQUEST-CHANGES. Release is refused unless `verified_by`
  differs from the worker instance (cross-verification gate). Evidence is required
  by default; freshness is enforced by verification_freshness_gate.

## Agent / Skill Attribution

- Every artifact's actor is an `agent_instance_id` (not a bare role). Spawn records
  in `agents/runtime/instances/` carry role/team/callsign/model/skill_versions.
  The attribution gate blocks role-only attribution on post-2026-06-12 artifacts.
- Trigger-based skills surface the tools: wave-conductor, merge-integrator,
  independent-verification, work-analytics, release-conductor, scm-steward,
  taskset-dispatch. See OPS-COMMAND-REFERENCE.md for the full command/skill map.

## Decision

- Decision: all NEW work uses the 2.0 model by default (units + waves +
  W4a/W4b + v2.0 metadata). Open legacy tasks are metadata-migrated now and
  unit/wave-decomposed when they are next picked up for execution.
- Decision: completed/archived tasks are NOT retro-migrated — they are historical
  evidence and re-modeling them adds no value.

## Action Board

| Status | Action | Owner | Evidence |
| --- | --- | --- | --- |
| Done | Migrate open tasks to v2.0 metadata envelope | lead-engineer | migrate_work_metadata_v2.py, work_schema_gate findings=0 |
| Done | Document the 2.0 work model (this contract) | lead-engineer | WORK-MODEL-2.0.md |
| Next | Unit/wave-decompose each open taskset when picked up | lead-engineer | per-taskset on execution |
| Watch | Generalize the v0.1.8-frozen release execution/readiness gates | release-steward | release pipeline follow-up |

## Risks / Blockers

- Risk: unit/wave decomposition for the ~35 open tasks is deferred to execution
  time (when each taskset is picked up) rather than done speculatively up front —
  speculative decomposition drifts before it is used. The metadata + verification
  + this rule are in place now; the structural decomposition attaches at dispatch.
- Blocker: none. Open tasks validate under the v2.0 schema gate and carry
  acceptance/verification sections.

## Next Steps

- When an open taskset is next executed, run `work.py status` (W0), decompose its
  tasks into units (units/README.md), `wave_dispatcher --plan`, then dispatch with
  claim-first + W4a/W4b per this model.
- Keep migrate_work_metadata_v2.py available for any future legacy intake.
