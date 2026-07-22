---
title: TASK-AR-604 Skeptic High-Risk Review
date: 2026-07-22
signal: pass
task_id: TASK-AR-604
verified_head: efefcd785fb446a480fe910e76d445ef162531a6
verified_by: codex-task-ar-604-skeptic-20260722
role: skeptic
verdict: APPROVE
tags: [task-ar-604, skeptic, high-risk, status-persistence, taskset-dispatch]
---

# TASK-AR-604 Skeptic High-Risk Review

## Verdict

**APPROVE** at exact HEAD
`efefcd785fb446a480fe910e76d445ef162531a6`.

The implementation separates normalized transition/event status from the
localized value persisted to task frontmatter without changing the global
status schema or task selection state machine. No blocking regression or
in-scope counterexample was found.

## Adversarial `cmd_start` Matrix

The real `cmd_start` function was invoked through isolated temporary fixtures
for 32 current-status cases. Each invocation used a persisted claim and an
existing valid worktree, then checked the task file, emitted JSON, and write
flag.

Start transitions passed:

- `제안`, `계획`, `계획됨`, `준비`, `준비됨`, `활성`, and `대기` persisted
  `진행 중`, emitted `task_status: in_progress`, and reported
  `task_status_updated: true`.
- English `planned`, `PLANNED`, `worker_ready`, `active`, `proposed`, and an
  empty status persisted `in_progress` and emitted normalized `in_progress`.

Protected/already-started states passed without a task-file write:

- `in_progress`, `진행`, `진행중`, `진행 중`
- `completed`, `done`, `완료`, `완료됨`, `완결`
- `blocked`, `차단`, `차단됨`
- `hold`, `hold_pending`, `보류`, `보류됨`
- `review`, `waiting_review`, `ready_for_governance_review`

All 32 cases matched the expected stored value, normalized emitted status, and
`task_status_updated` flag.

## Independent Verification

- `python -m pytest tests/test_taskset_dispatcher.py -q`
  -> `82 passed in 27.40s`
- `python scripts/taskset_work_gate.py --check`
  -> pass, findings 0
- `python scripts/work_item_classifier.py --check`
  -> pass, findings 0
- `python scripts/conversation_work_audit.py --check`
  -> pass, findings 0, block 0, watch 0
- `python scripts/regen_host_lock_if_needed.py --check`
  -> pass, host lock current
- `python -m pytest tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py tests/test_owner_governance_chain_parity.py -q`
  -> `21 passed in 21.90s`
- `git diff --check 112c37d..efefcd7`
  -> pass

## Scope And Parity

- The implementation commit changes only live/template
  `taskset_dispatcher.py`, focused tests, and the generated-host fixture lock.
- `scripts/taskset_dispatcher.py` is byte-identical to its template mirror.
- `status_alias.py`, `WORK-SCHEMA.yml`, and other status consumers were not
  changed; the global vocabulary and selection/readiness normalization remain
  outside this focused persistence correction.
- The host lock is current and the additional template/parity suite passes.

## Failure-First And W4a Lineage

Commit `a389f8bd38495ff0b3e8ec7c6326dfca6368a5ac` was independently extracted
to a disposable directory. Running the new parameterized regression against
that pre-fix commit reproduced `1 failed, 1 passed`: localized `대기` was
incorrectly stored as `in_progress`, while English `planned` retained its
expected behavior.

The history is linear:

```text
a389f8b failure-first regression
  -> f04daf2 localized persistence fix
  -> efefcd7 task/unit W4a evidence
```

Both latest W4a records contain successful 82-test and host-lock commands:

- `reviews/VERIFY-2026-07-22-task-ar-604-20260722212421.json`
- `reviews/VERIFY-2026-07-22-unit-task-ar-604-001-20260722212349.json`

## Non-Blocking Residual Observation

The pre-existing start-target function treats `closed`/`released` and their
Korean aliases as startable rather than terminal. That behavior exists before
`a389f8b`; TASK-AR-604 neither changes eligibility nor the status schema, and
its unit stop condition explicitly forbids redesigning unrelated state-machine
behavior. The exact direct-call observations were `closed -> in_progress`,
`released -> in_progress`, `종결`/`종료 -> 진행 중`, and
`릴리스됨`/`배포됨 -> 진행 중`. A separate intake registration is required
to decide and correct that eligibility; it must not be fixed under TASK-AR-604.
