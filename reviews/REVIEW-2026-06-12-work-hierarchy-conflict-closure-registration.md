---
type: review
id: REVIEW-2026-06-12-work-hierarchy-conflict-closure-registration
audience: owner
status: pass
signal: pass
score: 88
priority: High
tags: [taskset, registration, conflict-closure, project-management]
---

# Work Hierarchy Conflict Closure Registration Review

## Bottom Line

- Summary: registered `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` to close the
  remaining task-registration conflict surfaces raised in the Claude exchange.
- Result: `project` is no longer the recommended Owner-facing parent above
  taskset; use `initiative`.
- Boundary: this registration creates the plan and task records. The ID
  allocator, backlog deconfliction, and registration API remain planned work.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Trigger alias checked | watch | `python scripts/taskset_dispatcher.py plan task --json` returned `unknown task set alias: task` |
| Taxonomy decision | pass | `reviews/RESEARCH-2026-06-12-work-hierarchy-taxonomy.md` |
| Initiative record | pass | `agents/project/initiatives/INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE.md` |
| Plan recorded | pass | `docs/superpowers/plans/2026-06-12-work-hierarchy-conflict-closure.md` |
| Task records registered | pass | `TASK-AR-369` through `TASK-AR-374` |

## Insight

- Claude's two remaining conflict surfaces are real: `BACKLOG.md` still invites
  top-of-file shared edits, and task display IDs can be chosen concurrently
  before a claim exists.
- `task_uid` protects identity after file creation, but it does not reserve the
  human display number before file creation.
- The old hierarchy solved worker detail, but it left `project` ambiguous for
  Owner prompts. `initiative` closes that naming gap without breaking existing
  `project_id` metadata.

## Decision

- Decision: route "상위 묶음" prompts to `initiative`.
- Decision: route "백로그에 새 할 일 목록 작성/등록" prompts to `taskset`.
- Decision: route "실행 가능한 최소 단위로 쪼개줘" prompts to `unit` only after a
  task exists or is being created.
- Decision: keep the current next-session pointer unchanged; this registration
  does not claim implementation.

## Action Board

| Task | Action | Owner | Evidence |
| --- | --- | --- | --- |
| `TASK-AR-369` | Vocabulary migration | lead-engineer | PM contract and AGENTS docs |
| `TASK-AR-370` | Task ID reservation | agent-runtime-core | allocator/gate |
| `TASK-AR-371` | Backlog deconfliction | doc-steward | generated/changelog path |
| `TASK-AR-372` | Registration API | planning-office | CLI/API tests |
| `TASK-AR-373` | Unit readiness migration | lead-engineer | migration report |
| `TASK-AR-374` | Verification closeout | lead-engineer | named closeout gate |

## Risks / Blockers

- Risk: until `TASK-AR-370` lands, agents can still manually pick a colliding
  display ID.
- Risk: until `TASK-AR-371` lands, `BACKLOG.md` remains a shared manual intake
  surface.
- Blocker: none for registering the work.

## Next Steps

- Start `work-hierarchy-conflict-closure` through the dispatcher after this
  registration appears on the board.
- Implement `TASK-AR-370` before any broad multi-pane task-registration push.
- Implement `TASK-AR-371` before requiring all planners to update `BACKLOG.md`.

