---
type: planning
title: TASK-AR-648 Second Bean P0 Remediation Replan
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-003
signal: pass
score: 98
priority: P0
tags: [planning-record, task-ar-648, t3-replan, bean-wiki, scm-boundary, portable-runtime]
---

# TASK-AR-648 Second Bean P0 Remediation Replan

## Bottom Line

The first green replay is blocked evidence, not a partial success. Preserve
its worktree and unexpected commit, append a separately claimed remediation
unit, and repeat from the original Bean baseline only after both new P0s pass
installed-host regressions.

Allimbot and release work remain stopped.

## New Repair Matrix

| P0 | Root cause | Narrow repair | Required negative guard |
| --- | --- | --- | --- |
| implicit-consumer-claim-commit | claim crash-safety is environment opt-out and defaults on | make SCM commit an explicit CLI/environment opt-in; default to file persistence only | default installed-host create leaves exact HEAD unchanged; explicit authorized opt-in still commits only claim artifacts |
| installed-state-runtime-import-missing | managed scripts import a source package that adoption does not install | ship a minimal portable `scripts/agent_runtime` package containing exact config/state-projection modules | clear `PYTHONPATH`, isolate from source checkout, run installed state-sync and Scribe; canonical/portable/template modules stay byte-identical |

## Lifecycle and Evidence Rules

1. Write failing tests before product changes.
2. Keep the existing `claim_guard` commit primitive; change only who may
   invoke it implicitly.
3. Add a visible `--commit-claim-artifacts` opt-in and retain the explicit
   `AGENT_RUNTIME_CLAIM_AUTOCOMMIT=1` compatibility path. Absence of both must
   never mutate SCM.
4. Package only the two dependency modules needed by the installed state
   surfaces plus a namespace-safe initializer. Do not copy the full
   application package into consumer projects.
5. Treat canonical `src/agent_runtime/{config,state_projection}.py` as the
   source of truth. Root portable and packaged-template copies must be
   byte-identical and parity-tested.
6. Regenerate the host lock fixture and record the new selected-file count and
   template digest; do not preserve the obsolete 243 count as a false
   constant.
7. Run focused/full tests and independent integrated W4b.
8. Start Bean attempt 2 in a brand-new worktree at
   `357eee4fd8c29c33a949adbe3a0ffa80c874bf42`.
9. Run every consumer command with an empty or explicitly sanitized
   `PYTHONPATH`. Record exact template root/ref/digest for reconcile.
10. After the final task/claim projection, regenerate classifier output and
    require `--check` to pass before capturing evidence.

## Evidence Separation

- Original red report and fixture remain byte-identical at SHA-256
  `a8ad2dfb7f8b1e81c6606d4a51157270ca7fcfe24e0bd3750281d08a163a7a48`
  and
  `e035fa71b0a826d4a4e6d9c6f55ea5bdfe08da540017d24cf28016c73ba459cb`.
- Attempt 1 remains
  `reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-1.md`; its local false-zero
  evidence is not promoted.
- `tests/fixtures/pilots/bean-wiki/evidence-green.json` and
  `reviews/PILOT-BEAN-WIKI-v080-GREEN.md` remain reserved for a genuinely
  passing attempt 2.

## Stop Boundary

Stop on any default SCM mutation, import dependence on the Runtime source
checkout, red/attempt-1 evidence rewrite, newly observed P0, host/content
mutation, credential read, network delivery, publish, deploy, origin push,
unsupported cost claim, or independent verification failure.
