---
id: TASK-AR-369
display_id: TASK-AR-369
task_uid: 9d171d09-6c3d-4d1c-a8e7-fdee77a75d2c
registered_at: 2026-06-12T08:17:54+09:00
created_at: 2026-06-12T08:17:54+09:00
started_at: 2026-06-12T08:42:59+09:00
updated_at: 2026-06-12T09:04:46+09:00
completed_at: 2026-06-12T09:04:46+09:00
title: Initiative vocabulary and PM contract migration
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 4000
owner: lead_engineer
initiative_id: INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
escalation_triggers:
  - ambiguity
  - cross_cutting
tags:
  - project-management
  - taxonomy
  - docs
---

# TASK-AR-369 - Initiative vocabulary and PM contract migration

## Goal

- Finish the terminology migration from ambiguous `project -> taskset -> task -> unit` language to `initiative -> taskset -> task -> unit` without breaking existing `project_id` routing.

## Scope

- Audit runtime docs, generated host templates, board copy, and task/unit templates for owner-facing hierarchy language.
- Keep `project_id` as host/repository/product identity and add `initiative_id` guidance for new taskset parents.
- Add compatibility notes where older records still use `project` as a planning parent.
- Update examples so Owner prompts map cleanly to `initiative`, `taskset`, `task`, or `unit`.

## Out Of Scope

- Renumbering old tasks.
- Changing completed taskset history.
- Removing `project_id` from current claims or board output.

## Acceptance Criteria

- New docs consistently explain `initiative -> taskset -> task -> unit`.
- Existing `project_id` metadata still parses and appears in generated boards.
- A future agent can answer "unit 작성해줘? taskset 작성해줘?" from local docs without chat history.

## Verification

- `rg -n "project -> taskset|initiative -> taskset|initiative_id|Owner request vocabulary" AGENTS.md src/agent_runtime/templates/project/AGENTS.md agents/project/PROJECT-MANAGEMENT-CONTRACT.md`
- `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`

## Handoff

- Report changed docs and any remaining legacy mentions that are intentionally preserved for historical review records.

## Completion Evidence

- Added generated work-item classification outputs under `agents/project/work-items/`.
- Recorded the hierarchy/numbering/planning-discussion decision in `reviews/MEETING-2026-06-12-work-hierarchy-numbering-and-recording.md`.
- Added planning-discussion prompt-hook guidance and owner-governance classifier checks.
- Verified with `python scripts\work_item_classifier.py --write --check`, focused pytest, `python scripts\taskset_work_gate.py --check`, and `python scripts\owner_governance_gate.py`.

