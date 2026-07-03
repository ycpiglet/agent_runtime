---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-585
display_id: TASK-AR-585
task_uid: 57774268-cd3d-46ce-b280-9190ad6f808e
work_id: TASK-AR-585
work_uid: 57774268-cd3d-46ce-b280-9190ad6f808e
kind: task
parent_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
registered_at: 2026-06-18T22:26:32+09:00
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-07-04T02:37:53+09:00
started_at: 2026-07-04T02:00:00+09:00
completed_at: 2026-07-04T02:37:53+09:00
verification_status: passed
title: Parameterize the release execution gate (remove hardcoded v0.1.8)
status: done
priority: P1
difficulty: S
est_hours: 2
est_tokens: 6000
owner: lead-engineer
team: risk-release
initiative_id: INIT-AR-RELEASE-AUTOMATION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-585/UNIT-TASK-AR-585-001.md
reservation_id: RES-20260618-222632-7ac40299-01
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Make scripts/release_execution_gate.py version-parametric like release_council_gate.py so any target version can pass, instead of blocking every release after v0.1.8.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-585 - Parameterize the release execution gate (remove hardcoded v0.1.8)

## Goal

- Make scripts/release_execution_gate.py version-parametric like release_council_gate.py so any target version can pass, instead of blocking every release after v0.1.8.

## Scope

- Replace the hardcoded target_version=='0.1.8' / target_tag=='v0.1.8' checks with parametric resolution from pyproject.toml (target_version must equal the package version; target_tag must equal 'v'+target_version). Do NOT change the approval-route logic (approved / agent_council_approved routes stay as-is). Update DEFAULT_* paths if pinned to v0.1.8 and update the gate's tests.

## Acceptance Criteria

- scripts/release_execution_gate.py contains no hardcoded '0.1.8' / 'v0.1.8' in its evaluation logic; target_version/target_tag are validated against the live pyproject.toml version (mirroring release_council_gate.py _pyproject_version).
- The approved and agent_council_approved execution routes are unchanged in behavior.
- Tests cover a parametric version (e.g. a fixture at the current pyproject version) passing and a mismatched version blocking.

## Verification

- `python -m pytest tests/test_release_execution_gate.py -q`
- `python scripts/owner_governance_gate.py`
- `rg -n "0\.1\.8" scripts/release_execution_gate.py || echo no-hardcoded-version`

## Closeout (2026-07-04)

- Finding: the scoped work already landed on main via the release-automation
  redesign lane (PR #183 era); this closeout verifies acceptance rather than
  re-implementing.
- Verified: `rg "0\.1\.8" scripts/release_execution_gate.py` -> no hardcoded
  version; the gate resolves the live version via `_pyproject_version`
  (scripts/release_execution_gate.py) mirroring release_council_gate.py.
- Verified: `python -m pytest tests/test_release_execution_gate.py -q` -> `8 passed`
  (includes parametric current-version pass and mismatch block coverage via
  `CURRENT_VERSION`).
- Approval-route logic (approved / agent_council_approved) unchanged.
