---
title: Bean Wiki v0.8 Green Replay Attempt 1
date: 2026-07-29
status: blocked
signal: fail
verdict: BLOCKED
priority: P0
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-002
runtime_baseline: cd79b655af86c20dad1b8717d0eb5e6c692dac5a
host_baseline: 357eee4fd8c29c33a949adbe3a0ffa80c874bf42
observed_host_head: c93d12baa0020c30e71b50211ecd0c760a65e5e2
tags: [pilot, bean-wiki, green-replay-attempt, blocked, scm-boundary, portable-runtime]
---

# Bean Wiki v0.8 Green Replay Attempt 1

## Bottom Line

**BLOCKED. This attempt is not green and must not be used as release
evidence.**

The exact five-P0 repair at Agent Runtime
`cd79b655af86c20dad1b8717d0eb5e6c692dac5a` passed its integrated tests and
replayed the original registration, dispatch, linked-worktree, example
classification, state adapter, and reconcile paths. Independent W4b then
found two new P0s:

1. claim creation silently committed three claim artifacts in the consumer
   branch, violating the declared `host_commit: 0` boundary; and
2. an installed host running `python scripts/state_sync_gate.py` without an
   Agent Runtime source checkout failed with `ModuleNotFoundError`.

The attempt stopped before the editorial and restart tasks and before
Allimbot. The failed Bean worktree is preserved in place; no reset, revert,
reuse, push, publish, or deployment was performed.

## Exact Baselines and Observations

| Surface | Exact observation |
| --- | --- |
| Agent Runtime pin | `cd79b655af86c20dad1b8717d0eb5e6c692dac5a` |
| Bean baseline | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean observed HEAD | `c93d12baa0020c30e71b50211ecd0c760a65e5e2` |
| Automatic commit subject | `chore(claim): persist CLAIM-20260729-181800-task-ar-101-green101 (crash-safety guard)` |
| Automatic commit footprint | claim JSON, handoff Markdown, log Markdown; 3 files / 99 inserted lines |
| Host/content tracked diff from baseline | only the three claim artifacts |
| `src/content/**` file count | 125 |
| `src/content/**` aggregate digest | `2d45cb99dbcd1e3fe86ad0ebf9d31646580a0720d3496c27c952e829e2ba07cb` |
| Host `BACKLOG.md` digest | `c8c323352fcaf1b477094afb86f789728b2f85cc7f23429a9462af1c1dfad591` |
| Origin push / publish / deploy | 0 / 0 / 0 |
| Credential read / network delivery / content mutation | 0 / 0 / 0 |
| Host commit | **1** |

The local attempt evidence file claimed `host_commit: 0`; W4b disproved that
claim by inspecting Git HEAD. That local file is retained only as failed
worktree evidence and is not promoted into the Runtime's sanitized fixture.

## Original Five Repairs Replayed

Before the stop:

- the canonical JSON taskset registry dispatched `TASK-AR-101`;
- the clean linked Bean worktree accepted its self-claim;
- installed examples produced zero canonical example records;
- the configured `BACKLOG.md` adapter produced a fresh Scribe projection;
- immediate and post-registration reconcile, when run against the exact
  pinned template root, reported zero safe updates and zero conflicts after
  apply; and
- `owner-docs.yml` remained `seed_once`.

These observations keep the original five repairs valid. They do not offset
the two new P0s.

## P0-6 — Default Claim Creation Mutates Consumer Git

`task_claim_dispatcher.py create` calls `claim_guard.commit_claim_artifacts`
whenever `AGENT_RUNTIME_CLAIM_AUTOCOMMIT` is not explicitly disabled. The
default is on. The pilot declared and enforced a no-consumer-commit boundary,
but the dispatcher created commit
`c93d12baa0020c30e71b50211ecd0c760a65e5e2` without a CLI opt-in.

Required repair:

- default claim creation must persist files without changing Git HEAD;
- SCM mutation must require a visible, explicit opt-in;
- the crash-safety commit path must remain available and tested for
  authorized control repositories; and
- an installed-host regression must assert exact before/after HEAD equality.

## P0-7 — Installed State Runtime Is Not Portable

The managed host script imports:

```text
from agent_runtime import state_projection
```

An adopted host does not contain or install that Python package merely because
the template scripts were synced. With no ambient `PYTHONPATH`,
`python scripts/state_sync_gate.py --root . --check` fails before evaluating
state:

```text
ModuleNotFoundError: No module named 'agent_runtime'
```

The same dependency is shared by Scribe, closure, and session-start surfaces,
so a one-script exception would leave the harness inconsistent.

Required repair:

- package the bounded configuration/state-projection dependency with the
  installed scripts;
- prove ordinary consumer execution with a cleared `PYTHONPATH` and no source
  checkout/editable install;
- retain byte/parity checks against the canonical package implementation; and
- exercise state-sync plus Scribe from the installed template.

## Non-P0 Replay Finding

`work_item_classifier.py --check` correctly reported its projection stale
after the task/unit status changed from planned/worker-ready to in-progress.
The final replay must regenerate classification after the last serial
task/claim projection and then run `--check`. This is an evidence sequencing
failure, not a third new product P0.

An independent reconcile report also appeared to use a different Runtime
source and reported four safe updates plus one conflict. Re-running reconcile
against the exact pinned template root reproduced zero safe updates and zero
conflicts. Attempt 2 must record the resolved template root and digest in
every reconcile command so source ambiguity cannot enter W4b.

## Decision

Keep `TASK-AR-648` open. Mark `UNIT-TASK-AR-648-002` and its claim blocked,
register `UNIT-TASK-AR-648-003`, repair P0-6/P0-7 with red-first regressions,
and start attempt 2 from a new Bean worktree at the original host baseline.
Do not continue this worktree and do not begin Allimbot.
