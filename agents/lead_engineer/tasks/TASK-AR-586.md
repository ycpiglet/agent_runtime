---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-586
display_id: TASK-AR-586
task_uid: 0896a0d3-a4b6-43df-97f4-400f4f7bc38e
work_id: TASK-AR-586
work_uid: 0896a0d3-a4b6-43df-97f4-400f4f7bc38e
kind: task
parent_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
registered_at: 2026-06-18T22:26:32+09:00
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-07-04T02:37:53+09:00
started_at: 2026-07-04T02:00:00+09:00
completed_at: 2026-07-04T02:37:53+09:00
verification_status: passed
title: Wire cadence-bound noncritical auto-release and correct the release-conductor doc
status: done
priority: P1
difficulty: L
est_hours: 8
est_tokens: 16000
owner: lead-engineer
team: risk-release
initiative_id: INIT-AR-RELEASE-AUTOMATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-586/UNIT-TASK-AR-586-001.md
reservation_id: RES-20260618-222632-7ac40299-02
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Add an automated path that, at the release cadence boundary on green main CI, executes a noncritical release end-to-end via the agent release council (no Owner approval), while major/breaking/critical releases stop for explicit Owner approval. Document the real tier rule.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-586 - Wire cadence-bound noncritical auto-release and correct the release-conductor doc

## Goal

- Add an automated path that, at the release cadence boundary on green main CI, executes a noncritical release end-to-end via the agent release council (no Owner approval), while major/breaking/critical releases stop for explicit Owner approval. Document the real tier rule.

## Scope

- Add an orchestration script and a scheduled workflow that gate strictly on noncritical + green CI + head-SHA pinning, run readiness summary -> agent-council decision (W4b independent) -> council gate -> execution gate -> bump/tag/push, and notify the Owner. Never auto-release when criticality is critical or any CRITICAL_FLAG (major_or_breaking_release, secret, destructive, etc.) is set. Correct skills/release-conductor/SKILL.md (and its template copy) which currently overstates that all execution is Owner-gated.

## Acceptance Criteria

- A noncritical release (criticality=noncritical, no CRITICAL_FLAGS, recommended bump=patch) can be executed end-to-end by the agent release council without Owner approval, producing a tag + push.
- Any critical / major_or_breaking_release / secret / destructive release halts before tag/push and requires explicit Owner approval (no auto-execution).
- Auto-release only fires on green main CI for the exact validated head SHA (reuse the auto-merge.yml safety pattern) and is bound to the cadence boundary (weekly cron / W6), not every merge.
- The Owner is notified on every auto-release execution.
- skills/release-conductor/SKILL.md and its template copy describe the real tier rule (noncritical -> agent council; critical/major-or-breaking -> Owner), replacing the 'always Owner-gated' wording.

## Verification

- `python -m pytest tests -q -k release`
- `python scripts/owner_governance_gate.py`
- `python scripts/release_cadence_trigger.py --check --json`

## Closeout (2026-07-04)

- Finding: the scoped work already landed on main via the release-automation
  redesign lane (PR #183: workflow_run trigger on green main test runs,
  green-SHA checkout, feat->minor / breaking->major semver, criticality
  tiering; PR #210: dedup owner-approval GitHub-issue notification). This
  closeout verifies acceptance rather than re-implementing.
- Verified: `scripts/release_auto_noncritical.py` + `.github/workflows/release-auto.yml`
  execute the noncritical tier end-to-end (readiness -> council -> gates ->
  tag/push) and halt critical / major_or_breaking / secret / destructive with
  `owner-approval-required` plus an Owner-visible dedup issue (issues: write).
- Verified: `python -m pytest tests -q -k release` -> `120 passed`.
- Verified: `python scripts/release_cadence_trigger.py --check --json` ->
  `triggered=true` (commits>=40 actual 72, feat>=5 actual 16) — trigger lane live.
- Verified: `skills/release-conductor/SKILL.md` and the template copy document
  the real tier rule (noncritical -> agent council executes; critical/major ->
  explicit Owner approval), not 'always Owner-gated'.
- Boundary: tier boundary itself is v0.3.0-era Owner policy — patch-level
  noncritical releases auto-execute; minor/major stop for Owner approval.
