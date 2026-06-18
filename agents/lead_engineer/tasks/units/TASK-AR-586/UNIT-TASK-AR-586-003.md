---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-586-003
work_uid: bb7bc606-f379-4267-bbb3-e0e327731259
kind: unit
parent_id: TASK-AR-586
unit_id: UNIT-TASK-AR-586-003
task_id: TASK-AR-586
task_set_id: TASKSET-AR-RELEASE-AUTO-NONCRITICAL
initiative_id: INIT-AR-RELEASE-AUTOMATION
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-06-18T22:26:32+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Correct the release-conductor skill doc
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: skills/release-conductor/SKILL.md states 'Tag, push, and publish are Owner-gated -- never run them without explicit approval', which overstates the code: release_council_gate + release_execution_gate allow agent_council_approved execution for noncritical releases.
inputs:
  - skills/release-conductor/SKILL.md
  - src/agent_runtime/templates/project/skills/release-conductor/SKILL.md
  - scripts/release_council_gate.py CRITICAL_FLAGS
target_files:
  - skills/release-conductor/SKILL.md
  - src/agent_runtime/templates/project/skills/release-conductor/SKILL.md
scope: Documentation only. State the tier rule: noncritical -> agent council can approve and execute without Owner; critical / major_or_breaking_release / secret / destructive -> explicit Owner approval required.
acceptance:
  - The skill doc no longer claims all execution is Owner-gated and accurately describes the noncritical agent-council path.
verification:
  - python scripts/lock_merge_driver.py post-merge
handoff: Doc matches code; close the taskset.
stop_condition: If the template change desyncs the host lock, regenerate it before closing.
---

# UNIT-TASK-AR-586-003 - Correct the release-conductor skill doc

## Context

skills/release-conductor/SKILL.md states 'Tag, push, and publish are Owner-gated -- never run them without explicit approval', which overstates the code: release_council_gate + release_execution_gate allow agent_council_approved execution for noncritical releases.

## Inputs

- skills/release-conductor/SKILL.md
- src/agent_runtime/templates/project/skills/release-conductor/SKILL.md
- scripts/release_council_gate.py CRITICAL_FLAGS

## Target Files

- skills/release-conductor/SKILL.md
- src/agent_runtime/templates/project/skills/release-conductor/SKILL.md

## Scope

Documentation only. State the tier rule: noncritical -> agent council can approve and execute without Owner; critical / major_or_breaking_release / secret / destructive -> explicit Owner approval required.

## Steps

1. Rewrite the Owner-gated-boundaries section to describe the two tiers and the criticality/CRITICAL_FLAGS trigger.
2. Keep the template copy in sync; regenerate the host lock if the template changed.

## Acceptance Criteria

- The skill doc no longer claims all execution is Owner-gated and accurately describes the noncritical agent-council path.

## Verification

- `python scripts/lock_merge_driver.py post-merge`

## Handoff

Doc matches code; close the taskset.

## Stop Boundary

If the template change desyncs the host lock, regenerate it before closing.
