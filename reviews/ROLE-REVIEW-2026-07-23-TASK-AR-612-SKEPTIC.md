---
title: TASK-AR-612 Skeptic and Adversarial W4b Review
date: 2026-07-23
signal: pass
score: 98
task_id: TASK-AR-612
verified_head: caeeb795b590ff098878f9cee56b05effb1669e7
implementation_sha: 3c1df97a829febf1081bebeb42e17183f908d6a3
failure_first_sha: 61eaab67ca013df0aacdfb9e54d6101b65001ee5
verified_by: codex-task-ar-612-skeptic-20260723
worker: codex-root-task-ar-612
role: skeptic
verdict: APPROVE
tags: [task-ar-612, skeptic, adversarial, w4b, terminal-status, taskset-dispatch]
---

# TASK-AR-612 Skeptic and Adversarial W4b Review

## Verdict

**APPROVE** at exact W4a HEAD
`caeeb795b590ff098878f9cee56b05effb1669e7`.

No blocking counterexample was found. Implementation
`3c1df97a829febf1081bebeb42e17183f908d6a3` makes the dispatcher-local
terminal classification agree across start transitions, task selection, task
dependencies, unit selection, and unit dependencies. The shared status schema
and shared alias module remain unchanged.

## Adversarial Status Matrix

Both the live dispatcher and generated-host template passed the same direct
matrix:

| Input | Normalized | Start target | Task selection | Task dependency | Unit selection/dependency |
|---|---|---|---|---|---|
| `closed` | `closed` | `None` | skipped | complete | skipped / complete |
| `released` | `released` | `None` | skipped | complete | skipped / complete |
| `종결` | `closed` | `None` | skipped | complete | skipped / complete |
| `종료` | `closed` | `None` | skipped | complete | skipped / complete |
| `릴리스됨` | `released` | `None` | skipped | complete | skipped / complete |
| `배포됨` | `released` | `None` | skipped | complete | skipped / complete |

For selection, each terminal task or unit was placed before a startable
successor. The successor was selected in all six cases. When every unit was
terminal, the dispatcher correctly reported that no open unit remained.

Whitespace and case attacks also passed. All six values remained terminal
with surrounding whitespace, and ASCII values such as `CLOSED` and
`ReLeAsEd` remained no-transition. `UnKnOwN-State` normalized to
`unknown-state` and remained actionable, showing that the patch did not turn
unknown vocabulary into a terminal state.

## Preserved Non-Terminal Behavior

The following pre-existing boundaries were exercised against both copies:

- Empty, whitespace-only, unknown, `planned`, `active`, and their registered
  startable Korean aliases still target `in_progress`.
- `계획`, `계획됨`, `활성`, `제안`, `준비`, `준비됨`, and `대기` still use
  the localized persisted value `진행 중` when a transition is required.
- Already-normalized localized in-progress aliases remain equivalent and do
  not acquire a new terminal classification.
- `hold`, `hold_pending`, `보류`, and `보류됨` retain the hold family target.
- `blocked`, `차단`, and `차단됨` retain `blocked`.
- `review`, `waiting_review`, and `ready_for_governance_review` retain their
  review target.
- A planned task dependency and a planned unit dependency were still rejected;
  only the intended terminal family satisfies dependency completion.

This confirms that expanding dispatcher-local `DONE_STATUSES` did not widen
the start guard into hold, blocked, review, planned, active, blank, or unknown
states.

## DONE_STATUSES Consumer Impact

The local set is exactly:

```text
closed, completed, done, released
```

The adversarial probe exercised every consumer of that set:

1. `_next_task` skips terminal task records.
2. `_next_task` accepts terminal task dependencies and rejects planned ones.
3. `_ready_unit_for_task` excludes terminal units and rejects an all-terminal
   unit collection as having no open unit.
4. `_require_unit_dependencies` accepts terminal unit dependencies and rejects
   planned ones.
5. `_target_status_for_work_start` returns `None` for terminal values.

All five behaviors passed for the six requested canonical/alias inputs in both
dispatcher copies.

## Failure-First Causality

The exact failure-first SHA
`61eaab67ca013df0aacdfb9e54d6101b65001ee5` was archived to a disposable
directory. Running only the two new parameterized regression functions there
produced:

```text
6 failed, 6 passed in 3.62s
```

All six failures were the no-start-transition parameters: the pre-fix helper
returned `in_progress` for every requested terminal value. The six selection
parameters passed through the existing downstream board-lane behavior. The
implementation therefore has direct failure-first causality for the restart
defect and explicitly aligns local terminal membership with the already
terminal selection outcome.

## Scope, Schema, and Parity

The full task range from parent `e92802836784b1f80d2c6ac909c13b086c9c6581`
through implementation changes exactly the four authorized product/test files:

```text
scripts/taskset_dispatcher.py
src/agent_runtime/templates/project/scripts/taskset_dispatcher.py
tests/fixtures/host/agent_runtime.lock.json
tests/test_taskset_dispatcher.py
```

The implementation-only range changes the two dispatcher copies and generated
host lock. `git diff --check` passed.

Blob comparison across failure-first and implementation confirmed no change to:

- `scripts/status_alias.py`
- `src/agent_runtime/templates/project/scripts/status_alias.py`
- `agents/project/WORK-SCHEMA.yml`

The live and template dispatcher files are byte-identical at SHA-256:

```text
0d0947d2cd88b3f53ddef384f1520bb3e1ec3ca2a2bbf66f48f4a22b60d5bfe5
```

The generated-host lock check is current.

## Independent Commands

After selecting the installed Python 3.10 runtime on `PATH`, the registered
commands were rerun at the exact W4a HEAD:

```text
python -m pytest tests/test_taskset_dispatcher.py -q
94 passed in 39.31s

python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.

python scripts/taskset_work_gate.py --check
taskset-work-gate: pass
findings=0
```

Additional independent probes passed for:

- six terminal values plus whitespace/case variants;
- blank, unknown, hold, blocked, review, planned, active, and localized values;
- task selection and dependency completion;
- unit selection and dependency completion;
- exact live/template parity.

## W4a Cross-Check

The following worker-produced evidence was inspected:

- `reviews/VERIFY-2026-07-23-task-ar-612-20260723080853.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-612-001-20260723080740.json`

The task record reports all three registered commands passing; the unit record
reports its two registered commands passing. Both identify
`codex-root-task-ar-612` as verifier. This skeptic W4b used a distinct verifier
identity and independently reran the code paths and commands above.

## Measurable Validation Summary

| Metric | Required | Measured | Result |
|---|---:|---:|---|
| Terminal no-transition | 6/6 per copy | 6/6 root, 6/6 template | Pass |
| Terminal no-selection | 6/6 per copy | 6/6 root, 6/6 template | Pass |
| Task dependency completion | 6/6 per copy | 6/6 root, 6/6 template | Pass |
| Unit selection/dependency | 6/6 per copy | 6/6 root, 6/6 template | Pass |
| Whitespace/case terminal handling | all six | all six per copy | Pass |
| Non-terminal preservation | all attacked classes | 25 direct target cases per copy | Pass |
| Failure-first causality | pre-fix failure | 6 failed, 6 passed | Pass |
| Focused suite | 94 passing | 94 passed | Pass |
| Root/template parity | exact | byte-identical | Pass |
| Shared schema changes | none | none | Pass |

No follow-up is required for TASK-AR-612.
