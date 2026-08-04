---
title: v0.8 Operability Dependency Preservation T0 Replan
date: 2026-07-30
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
status: approved
signal: pass
priority: P1
reviewer: codex-root-task-ar-650-planner
tags: [t0, replan, work-registration, dependency, wave]
---

# v0.8 Operability Dependency Preservation T0 Replan

## Trigger

The registered input declared TASK-AR-657 dependent on TASK-AR-654/656 and
TASK-AR-658 dependent on TASK-AR-652 through TASK-AR-656. Generated task and
unit records omitted those fields, and the read-only wave plan incorrectly
placed both downstream tasks in wave 1.

This changed the plan anchor `scripts/work.py` and the design record after the
initial registration snapshot. The assumption gate must therefore reject the
old snapshot until this review and a new recording exist.

## Classification

The silent dependency drop is a P1 planning-integrity defect:

- it changes approved execution order;
- it makes a dependent consumer skill or UI eligible before its schemas exist;
- replay previously reported success without comparing dependency identity.

Repair is within TASK-AR-650's registered work-order and shared-harness scope.
It does not authorize dispatch, a new taskset boundary, consumer product work,
or any external effect.

## Bounded repair

1. Preserve task `depends_on` in task frontmatter.
2. Inherit task dependencies into every generated worker unit so the wave DAG
   observes them.
3. Reject missing, malformed, duplicate, self, and cyclic task dependencies
   before any registration write.
4. Include dependency identity in already-exists replay checks.
5. Keep root and packaged-template `work.py` byte-identical.
6. Repair only the generated TASK-AR-657/658 task and unit records from this
   registration.

## Revalidated result

- Work registration dependency tests: pass.
- Taskset and wave regressions: pass.
- Registration replay: `already_exists`.
- Template mirror: zero findings.
- Wave plan: TASK-AR-652 begins wave 1; TASK-AR-657 and TASK-AR-658 occur only
  in wave 4 after every declared prerequisite.

## Decision

Accept the bounded repair and re-record the design, model-routing,
task-claim, and work-registration anchors. The next eligible task remains
TASK-AR-652. No claim, worktree, version, tag, push, package, publication,
deployment, or release action is approved.
