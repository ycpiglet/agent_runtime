---
id: TASK-AR-530
display_id: TASK-AR-530
task_uid: fa0dc086-45f9-4a02-a1ad-93d48939e1b4
registered_at: 2026-06-14T02:08:50+09:00
created_at: 2026-06-14T02:08:50+09:00
started_at: 2026-06-14T13:40:00+09:00
updated_at: 2026-06-14T13:55:00+09:00
completed_at: 2026-06-14T13:55:00+09:00
status: completed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 9000
owner: lead_engineer
task_set_id: TASKSET-AR-HOST-FEEDBACK-INTAKE
tags:
  - host-feedback
  - self-eval
  - rsi
  - fitness-gate
  - candidate
---

# TASK-AR-530 - Cross-version self-eval harness + RSI fitness gate

## Goal

- Give the platform an objective, quantitative self-eval so each version can prove it is *better*, not just *changed* — the prerequisite that turns recursive self-improvement (RSI) into improvement rather than drift. Skill self-mutation must pass an eval-improvement gate to be adopted. (GH #128)

## Scope

- Fixed (held-out) metrics — meaningful across versions: first-try test pass rate, `gate_failure_count`, `rework_count`, `reopened_count`, per-task wall-clock/tokens, merge-conflict count, Owner-intervention count. Enables N vs N+1 comparison.
- Variable (per-version) metrics — tied to that version's new capability (e.g. v0.2.0 parallel wave: wave concurrency factor, footprint violations, wave-defer rate, pane utilization).
- Objective mandate: core metrics from test-verified resolution (repo tests = oracle, SWE-bench principle); subjective scoring is secondary only.
- RSI fitness gate: adopt a skill mutation only when it passes eval improvement; run multiple times to account for run-to-run model variance.
- Host data pipeline: a contract for a real-use host (autofolio) to emit per-cycle metrics as live eval data, reusing existing `WORK-SCHEMA` measurement/closure fields (rework/gate_failure/actual_*/reopened) as substrate.

## Acceptance Criteria — candidate

- Adoption (accept/defer/reject) is decided by the TASK-AR-527 deliberation; this file pre-registers the proposal so it is tracked.

## Acceptance Criteria

- A harness runs the fixed held-out benchmark + per-version variable metrics and reports N->N+1 deltas quantitatively.
- A fitness gate blocks skill mutation that does not pass eval improvement (variance-aware).
- A documented contract exists for host-supplied per-cycle eval data.

## Evidence Targets

- A self-eval harness + held-out workset under `scripts/` / `tests/` / `agents/project/`.
- `docs/AGENT_RUNTIME_EVAL_METRICS.md` (host counterpart) referenced.
- Source: GH ycpiglet/agent_runtime#128.

## Deliberation Verdict (2026-06-14)

- ACCEPT (staged), P2 — `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.
- Build the held-out fixed/variable metric HARNESS (additive, safe).
- Keep the RSI self-mutation fitness gate ADVISORY/report-only (record N->N+1 delta, never block) until a trustworthy, variance-aware baseline exists AND R3 sign-off — it gates the safety-sensitive self-modification surface; a noisy/gameable metric (Goodhart) could rubber-stamp drift or block real gains.
- Minority concern preserved: the systems-thinker rated this the single highest-leverage item (P0) as the RSI fitness function; honored by accepting the harness now.

## Completion Evidence

- `scripts/self_eval_harness.py` + `tests/test_self_eval_harness.py`: cross-version self-eval. The FIXED held-out schema (the #128 set: first_try_test_pass_rate / gate_failure_count / rework_count / reopened_count / merge_conflict_count / owner_intervention_count, plus computed completed_tasks / open_tasks / verification_coverage_pct / est totals) is the stable spine; uncaptured metrics report `null` (await WORK-SCHEMA actuals). Per-version VARIABLE metrics (w4b_records, council_deliberations).
- Real signal computed now: `verification_coverage_pct` = completed tasks with an independent W4B record / completed (a genuine RSI fitness signal). Snapshot: 194 completed, 18.6% verification coverage.
- **RSI fitness gate is ADVISORY** (council-scoped): `--gate` reports the N->N+1 delta per metric (improved/REGRESSED by direction) and exits 0 ALWAYS -- it does NOT block skill mutation yet. Hard enforcement awaits a trustworthy variance-aware baseline + R3 sign-off. Baseline persisted to `SELF-EVAL-BASELINE.json` (--write).

## Verification Results

- W4a: 4 tests pass; --report/--write/--gate work; advisory gate exit 0 on regression; governance gate exit 0.
- W4b (independent, verifier != worker): see `reviews/W4B-2026-06-14-TASK-AR-530.md`.
