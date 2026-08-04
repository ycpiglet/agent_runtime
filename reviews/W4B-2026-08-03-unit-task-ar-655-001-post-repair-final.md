---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-03-unit-task-ar-655-001-post-repair-final
title: TASK-AR-655 Post-Repair Final Independent W4b
date: 2026-08-03
created_at: 2026-08-03T06:25:00+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: codex-independent-task-ar-655-post-repair-final-w4b
reviewer_role: independent-auditor
status: blocked
signal: fail
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
candidate_commit: 5b6a5a9fddccd318fc6f8a813ddc1ab42f036ebb
candidate_tree: b956ec4edc5a705423704f49b191d9598b1112f5
current_agent_red_commit: 214864cefd1106edf9f95d4948942171f9028b0d
current_agent_repair_commit: 3adaff660f99c3bdb4a85adb731bc20a5883d508
ui_freshness_red_commit: deb75ee16d625a360066a071bf0061839a92da50
ui_summary_red_commit: 63e0ed9ac5523bef2f296975ee9136b2a64fea2c
ui_repair_commit: 7fecfbe5a6f9ebdbd6dd08502fb5c84396ae0650
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803054932.json
w4a_ref: reviews/W4A-2026-08-03-unit-task-ar-655-001-post-repair-final.md
source_w4b: reviews/W4B-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final.md
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
skeptic_authorized: false
release_authorized: false
claim_disposition: remain_claimed
scribe_blocker: scribe-source-debt-overdue
external_release_blockers: preserved_not_run
tags: [w4b, task-ar-655, claim-progress, current-agent, ui, preload, fail-closed, revise]
---

# TASK-AR-655 post-repair final independent W4b

## Verdict

`REVISE — P0: 0, P1: 2, P2: 0.`

The exact clean candidate
`5b6a5a9fddccd318fc6f8a813ddc1ab42f036ebb`, tree
`b956ec4edc5a705423704f49b191d9598b1112f5`, correctly rejects the specific
missing/conflicting `claim_path` and `status` cases, inactive or missing claim
status, empty present unit/task-set identities, and the earlier outer
projection conflicts. It also prevents the original null dereference in both
desktop and mobile rendering.

Two release-blocking contract gaps remain. Claim-progress still accepts an
incomplete or conflicting canonical pointer agent outside the seven fields it
checks, and the pre-load home summary renders factual-looking healthy zeros
before Runtime state exists. These are current-scope P1 findings. Therefore
`w4b_acceptance`, `skeptic_authorized`, and `release_authorized` are all
`false`; the claim must remain `claimed`.

## Candidate and independence

The review ran only in
`/home/keti-itp-01/ycpiglet/.control-clones/agent-runtime-task-ar-648/.worktrees/TASK-AR-655`.
At review start and again immediately before this report was written:

```text
$ git rev-parse HEAD
5b6a5a9fddccd318fc6f8a813ddc1ab42f036ebb
$ git rev-parse HEAD^{tree}
b956ec4edc5a705423704f49b191d9598b1112f5
$ git status --porcelain=v2
<empty>
$ git diff --check
<empty; exit 0>
```

Reviewer `codex-independent-task-ar-655-post-repair-final-w4b` is distinct
from worker `le-20260803-001200-kst-ar655lease001` and did not share the
worker's conversation context. The worker W4a was inspected as evidence, not
as approval authority. No prior W4b verdict was adopted without inspecting
the production source, tests, history, and counterexamples on this exact
candidate.

## The named RED to GREEN repairs are genuine

The committed failure-first history was replayed from isolated `git archive`
exports, so no historical checkout or repository file was changed:

| Contract | RED result | GREEN result |
| --- | --- | --- |
| Gross projection identity conflict | `b4e6d782`: `1 failed` | `1239d032`: `1 passed` |
| Missing/conflicting current-agent path/status, inactive/missing claim status, empty present identities | `214864ce`: `8 failed` | `3adaff66`: `8 passed` |
| Pre-load freshness guard | `deb75ee1`: `1 failed` | `7fecfbe5`: passed |
| Pre-load home-summary guard | `63e0ed9a`: `1 failed` | `7fecfbe5`: passed; both UI guards `2 passed` |

On the exact candidate, the registered focused selection covering the prior
projection conflict, overlay boundary, all eight current-agent recurrence
rows, and both served-asset guards returned `13 passed in 0.19s`. The existing
desktop/mobile two-screen Playwright test returned `2 passed in 7.94s`.

An independent 42-row response-mutation matrix exercised valid merge and
overlay receipts plus 40 malformed or conflicting path, claim status,
identity, receipt, projection, pointer, agent, revision, and overlay cases.
Both valid rows returned zero. Every adverse row returned exit `2`,
`claim_progress_receipt_indeterminate`, `commit_state: unknown`, and
`retry_safe: false`. All 42 claim and pointer sentinels remained byte-identical.
This confirms the explicitly repaired cases and the read-only failure path.

## P1-1 — `current_agents` is not bound to the full canonical pointer record

`src/agent_runtime/templates/project/scripts/agent_orchestrator.py` validates
the merge agent's claim ID, canonical claim path, active claim status,
task/unit/task-set tuple, and exact mutation revision. It does not validate the
rest of the canonical current-agent record.

That remainder is not an optional alternate representation:

- `src/agent_runtime/templates/project/scripts/task_claim_dispatcher.py`
  builds the projection agent from the committed claim and emits a complete
  record.
- `src/agent_runtime/templates/project/scripts/parallel_worktree_gate.py`
  defines `POINTER_AGENT_FIELDS` and requires every one of its 22 fields to be
  present and equal to the canonical claim.
- The earlier installed-host contract explicitly established that deterministic
  projection emits the complete pointer agent record needed by that gate.

The validator currently leaves 16 gate-required fields unbound:
`agent_role`, `team_id`, `agent_instance_id`, `display_name`, `callsite_id`,
`pane_id`, `phase`, `progress_pct`, `step_index`, `step_total`, `status_text`,
`worktree_path`, `branch`, `handoff_path`, `log_path`, and `last_heartbeat`.

An exact-candidate inline Python probe started with the real dispatcher's full
claim-derived shape. For each of those 16 fields it made one missing mutation
and one conflicting mutation, invoked `cmd_claim_progress` through a zero-exit
dispatcher seam, and retained byte sentinels at the canonical claim and
pointer paths:

```json
{"all_sentinels_unchanged": true, "rows": 32, "unexpected_successes": 32}
```

Every row returned code zero and passed the conflicting projection through.
The canonical pointer gate would reject every missing field and every value
that differs from its claim. The orchestrator's lack of direct mutation is
correct, but it does not make a success receipt safe: the serial projection
owner can be told that progress succeeded and then receive a pointer payload
that fails the registered continuity gate.

The current positive orchestrator fixtures themselves contain only the
seven-field agent subset, so they encode acceptance of a partial record rather
than exercising the producer's full projection. This is a further recurrence
of
`defect:claim-progress-accepts-non-matching-committed-pr:354921871935cffe`,
not a failure of the newly added eight regression rows.

Required repair: validate presence and exact claim equality for the complete
canonical `POINTER_AGENT_FIELDS` tuple, preferably through one shared field
contract rather than a third manually duplicated list. Seed positive and
adverse tests from the production projection shape, remove or conflict each
field individually, and require the existing bounded indeterminate/no-mutation
outcome for every mismatch.

## P1-2 — Null-safe pre-load summary fabricates a healthy zero state

`stateFreshness()` now behaves correctly when `runtimeState` is null: it
returns no timestamp, age zero only as an internal neutral value, `stale:
false`, and the visible `--:--:--` clock. However, `renderHomeSummary()` uses
the same empty object as though it were a real state snapshot. Missing tasks,
claims, and gate metrics become open `0`, WIP `0/3`, gate `pass`, and agents
`idle`; the flow tiles also render zero or unknown values.

This violates the accepted UI replan and unit acceptance that pre-load output
remain neutral and must not claim a fabricated healthy state. It is observable
because `loadState()` and `loadCockpit()` start independently, and
`renderCockpit()` calls `renderHomeSummary()`.

An independent Playwright probe blocked SSE, delayed `/api/state` by 1.5
seconds, allowed `/api/inbox` to render first, and inspected both registered
viewports before and after the real state arrived:

| Viewport | Before state | After state |
| --- | --- | --- |
| Desktop `1366x768` | null state, `--:--:--`, `WIP 0/3`, `gates pass`, agents idle, zero/unknown tiles | `WIP 1/3`, `block 3`, one active agent, real throughput/cycle values |
| Mobile `390x844` | same false healthy pre-load summary | same real blocked-state summary after load |

Both viewports had zero page errors, confirming that the exception was fixed;
the remaining defect is truthfulness, not layout. A second probe that aborted
`/api/state` showed the same summary persisted alongside the explicit state
load error. The current served-source tests check only for the local fallback,
and the existing browser test checks two-screen layout without forcing state
ordering or asserting neutral summary content.

Required repair: while `runtimeState` is null, keep freshness neutral and hide
the state-derived summary/tiles or render an explicit unavailable/loading
state. Do not render `pass`, `0`, or `idle` as observed facts. Add desktop and
mobile browser regressions that delay and fail `/api/state` while inbox data
succeeds, assert neutral output with no page error, then allow state arrival
and assert the real metrics replace it.

## Fresh Verify and bounded command evidence

Fresh durable evidence
`reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803054932.json` has
SHA-256
`297242a9bc7fd5edbbd40295384f0349091d7a3089ac0c640b510535ae620d2d`.
It is attributed to the worker, records five commands, and has pass status,
pass signal, and return code zero for every command:

| Durable worker evidence | Recorded result |
| --- | --- |
| Registered claim/liveness/UI suite | `799 passed, 2 skipped` |
| Mirror/managed-host suite | `68 passed` |
| Template mirror gate | `expected=86 common=86 identical=83 intentional=3 findings=0` |
| Managed host lock gate | current |
| Full repository suite | `4516 passed, 11 skipped, 4 known warnings` |

The four warnings are the recorded UI route-sweep invalid-escape deprecation
warnings. This W4b did not repeat the full suite: the artifact is fresh and
committed after the production repairs, while the two bounded counterexamples
are decisive and are not covered by that suite.

Fresh read-only checks on the candidate also produced:

| Command | Result |
| --- | --- |
| `python scripts/compound_record.py --root . check` | pass |
| `python scripts/evidence_index_generator.py --check` | pass, findings `0` |
| `python scripts/work_schema_gate.py --items --check` | findings `0`; 19 unrelated legacy warnings |
| `python scripts/template_mirror_gate.py --check` | findings `0` |
| `python scripts/regen_host_lock_if_needed.py --check` | current |
| Exact no-legacy Compound searches | projection signature `2` records; UI signature `1` record |

## Five Compound records and task/unit/claim parity

All five linked append-only Compound records were read completely and pass
schema/index validation. Each is linked to both `TASK-AR-655` and
`UNIT-TASK-AR-655-001`, all source/prevention/verification refs exist, and the
generated index has the same exact five-record sequence for the task and unit.

Task, unit, and active claim have identical ordered lists of 13 defect
signatures and identical ordered lists of the five Compound refs. The ordered
unique signature union across the records equals the task/unit/claim list
exactly: 13 of 13, with no uncovered registered signature. Task and unit remain
`in_progress`; claim
`CLAIM-20260803-002651-task-ar-655-5f27` remains `claimed`, at phase
`worker-w4a-post-repair-complete`, step `11/12`, progress `99`.

The new P1-1 is a live recurrence of an already registered signature, so the
existing 13/13 coverage result cannot convert this implementation review into
a pass. After repair, lifecycle evidence must add a new append-only recurrence
record rather than rewrite either earlier projection record.

## Closure result and preserved Scribe blocker

The direct closure command was:

```text
python scripts/closure_gate.py --root . \
  --work-id UNIT-TASK-AR-655-001 --check --json
```

It exited `1` with `decision: block` and
`reason: scribe-source-debt-overdue`. Its repeated-failure section separately
reported:

```text
required: true
satisfied: true
covered_defect_signatures: 13
uncovered_defect_signatures: 0
findings: 0
```

The closure block is therefore not a Compound coverage failure. It remains the
unwaived Scribe block with both missing requirements:

```text
missing: scribe_source_debt, scribe_active_coverage
source debt: STATUS.md overdue
active coverage: incomplete
```

That blocker is independently sufficient to prevent closure and is outside
this repair's authority.

## Disposition and safety boundary

Repair both P1 findings, commit new failure-first regressions, rerun fresh
Verify, add the required append-only recurrence evidence, produce replacement
W4a, and require another context-isolated W4b. A skeptic review is **not**
authorized on this candidate.

The claim remains `claimed`. This report does not authorize claim release,
merge, close, version, tag, push, package, publish, deploy, CI dispatch,
consumer-repository mutation, credential use, network-provider action,
database change, notification, broker, or order action. Native Windows CI and
the external consumer pilots remain unrun release blockers. This report is the
reviewer's only repository write; no production, test, lifecycle, claim,
Compound, index, Git-history, or external state was changed.
