---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-602-001
work_uid: 84ffe575-403e-4360-b246-6481085544f2
kind: unit
parent_id: TASK-AR-602
unit_id: UNIT-TASK-AR-602-001
task_id: TASK-AR-602
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
initiative_id: INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-19T10:28:06+09:00
updated_at: 2026-07-19T10:28:06+09:00
origin_type: owner_request
origin_ref: chat:2026-07-19-all-open-intake; github:#274,#279,#280,#285,#287,#289,#290; pr:#277
created_by: codex-root-planner
summary: Close state and publish v0.7.0
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - external_effect
  - high_risk
  - cross_cutting
  - release
context: GitHub #280 approved v0.7.0 from an older SHA; current main has additional fixes, so the candidate must be rebuilt and verified only after every open intake item is integrated.
inputs:
  - https://github.com/ycpiglet/agent_runtime/issues/280
  - scripts/release_version_cascade.py
  - agents/project/RELEASE-GATE-TEMPLATE.yml
  - STATUS.md
  - BACKLOG-BOARD.md
target_files:
  - pyproject.toml
  - src/agent_runtime/__init__.py
  - src/agent_runtime/cli.py
  - src/agent_runtime/publish_tag_smoke.py
  - src/agent_runtime/publish_github_plan.py
  - src/agent_runtime/publish_github_execute.py
  - src/agent_runtime/release_preflight.py
  - .github/workflows/test.yml
  - agents/project/RELEASE-GATE-TEMPLATE.yml
  - tests/fixtures/host/agent_runtime.yml
  - tests/fixtures/host/agent_runtime.lock.json
  - tests/test_inventory_sync_sanitize.py
  - tests/test_release_execution_gate.py
  - BACKLOG-BOARD.md
  - ARCHIVE-INDEX.md
  - STATUS.md
  - reviews/INDEX.md
scope: Reconcile state, bump the deterministic cascade to 0.7.0, run full validation and release preflight, integrate through the repository release workflow, publish the annotated tag/release, close issues, and remove transient claims/worktrees/branches.
acceptance:
  - Version 0.7.0 is consistent across every CASCADE path and the host fixture lock.
  - The release tag points to the verified release commit and the GitHub release is visible.
  - GitHub open intake is reconciled and W0 reports no residual worktree/claim divergence.
verification:
  - python scripts/release_version_cascade.py --check
  - python scripts/owner_governance_gate.py
  - python -m pytest -q
  - python scripts/work.py status
  - git tag -v v0.7.0
handoff: Provide release URL, tag/commit SHA, full gate/test results, closed issue list, current W0 status, and rollback notes.
stop_condition: Stop before release if any required test/gate is red, current main differs from the verified release commit, or a secret/credential boundary is unclear.
---

# UNIT-TASK-AR-602-001 - Close state and publish v0.7.0

## Context

GitHub #280 approved v0.7.0 from an older SHA; current main has additional fixes, so the candidate must be rebuilt and verified only after every open intake item is integrated.

## Inputs

- https://github.com/ycpiglet/agent_runtime/issues/280
- scripts/release_version_cascade.py
- agents/project/RELEASE-GATE-TEMPLATE.yml
- STATUS.md
- BACKLOG-BOARD.md

## Target Files

- pyproject.toml
- src/agent_runtime/__init__.py
- src/agent_runtime/cli.py
- src/agent_runtime/publish_tag_smoke.py
- src/agent_runtime/publish_github_plan.py
- src/agent_runtime/publish_github_execute.py
- src/agent_runtime/release_preflight.py
- .github/workflows/test.yml
- agents/project/RELEASE-GATE-TEMPLATE.yml
- tests/fixtures/host/agent_runtime.yml
- tests/fixtures/host/agent_runtime.lock.json
- tests/test_inventory_sync_sanitize.py
- tests/test_release_execution_gate.py
- BACKLOG-BOARD.md
- ARCHIVE-INDEX.md
- STATUS.md
- reviews/INDEX.md

## Scope

Reconcile state, bump the deterministic cascade to 0.7.0, run full validation and release preflight, integrate through the repository release workflow, publish the annotated tag/release, close issues, and remove transient claims/worktrees/branches.

## Steps

1. Confirm all predecessor tasks are independently verified, merged, and reflected in GitHub state.
2. Regenerate backlog/evidence/state surfaces and run the full governance/test suite.
3. Bump the release cascade to 0.7.0, verify the current-head candidate, commit/merge, create and push the annotated tag, publish the GitHub release, and close remaining intake records.
4. Run W5/W6 status checks and publish final closeout/retro evidence.

## Acceptance Criteria

- Version 0.7.0 is consistent across every CASCADE path and the host fixture lock.
- The release tag points to the verified release commit and the GitHub release is visible.
- GitHub open intake is reconciled and W0 reports no residual worktree/claim divergence.

## Verification

- `python scripts/release_version_cascade.py --check`
- `python scripts/owner_governance_gate.py`
- `python -m pytest -q`
- `python scripts/work.py status`
- `git tag -v v0.7.0`

## Handoff

Provide release URL, tag/commit SHA, full gate/test results, closed issue list, current W0 status, and rollback notes.

## Stop Boundary

Stop before release if any required test/gate is red, current main differs from the verified release commit, or a secret/credential boundary is unclear.
