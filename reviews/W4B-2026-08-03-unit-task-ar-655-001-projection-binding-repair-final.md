---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final
title: TASK-AR-655 Projection-Binding Repair Final Independent W4b
date: 2026-08-03
created_at: 2026-08-03T05:13:17+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: codex-independent-task-ar-655-projection-repair-w4b
reviewer_role: independent-auditor
status: blocked
signal: fail
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: b78f484d6e599d3ef1e376d1d6fe3b945f98906e
candidate_tree: d13684d7f47d92f8f95b704a2b0a6f58c4ccbd22
accepted_replan_commit: 42222a24a148060e6f280cb69311111f26ac91f8
red_commit: b4e6d7829fb11cff3c2535d9c642a842477a6eef
implementation_commit: 1239d0322ea3b9ea2631d31e31ff7c868fbde1d2
implementation_tree: e926b684f781c41405aefd3a76964f0f6b1a4732
implementation_range: 42222a24a148060e6f280cb69311111f26ac91f8..1239d0322ea3b9ea2631d31e31ff7c868fbde1d2
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803045245.json
w4a_ref: reviews/W4A-2026-08-03-unit-task-ar-655-001-projection-binding-repair-final.md
source_w4b: reviews/W4B-2026-08-03-unit-task-ar-655-001-lease-authority-final.md
replan_ref: reviews/REVIEW-2026-08-03-task-ar-655-w4b-projection-binding-t3-replan.md
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed
scribe_blocker: preserved_unresolved
external_release_blockers: preserved_not_run
tags: [w4b, task-ar-655, claim-progress, projection, pointer, claim-path, identity, fail-closed, revise]
---

# TASK-AR-655 projection-binding repair final independent W4b

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

The exact clean candidate
`b78f484d6e599d3ef1e376d1d6fe3b945f98906e`, tree
`d13684d7f47d92f8f95b704a2b0a6f58c4ccbd22`, still acknowledges zero-exit
claim-progress responses whose merge `current_agents` record is not bound to
the canonical committed claim path. The same validator also accepts malformed
present optional identities and missing or contradictory projected lifecycle
status. Those are current-scope matching-projection failures, so this review
stopped immediately under the assigned stop-on-P1 rule.

The active claim must remain `claimed`. This report does not authorize claim
release, merge, close, version, tag, push, package, publish, deploy, consumer
mutation, or CI dispatch.

## Candidate and independence

The review began in only
`/home/keti-itp-01/ycpiglet/.control-clones/agent-runtime-task-ar-648/.worktrees/TASK-AR-655`.
At start:

```text
$ git status --short --branch
## codex/task-ar-655-v080-lease-bounds
$ git rev-parse HEAD
b78f484d6e599d3ef1e376d1d6fe3b945f98906e
$ git rev-parse HEAD^{tree}
d13684d7f47d92f8f95b704a2b0a6f58c4ccbd22
```

There were no staged, unstaged, or untracked paths. Both
`git diff --check 42222a24a148060e6f280cb69311111f26ac91f8..1239d0322ea3b9ea2631d31e31ff7c868fbde1d2`
and `git diff --check` returned zero with no output.

Reviewer `codex-independent-task-ar-655-projection-repair-w4b` is a distinct,
context-isolated agent instance from worker
`le-20260803-001200-kst-ar655lease001`. The reviewer read `AGENTS.md`, the
complete `skills/independent-verification/SKILL.md`, the host-template
`AGENTS.md`, the prior W4b finding, accepted T3 replan, replacement W4a, fresh
Verify JSON, all three linked Compound records, and the implementation range.
The reviewer independently inspected production and regression code and ran
the decisive temporary counterexample matrix. No worker conclusion was
adopted as independent evidence.

## P1-1 — Merge current-agent authority is still only partially bound

`src/agent_runtime/templates/project/scripts/agent_orchestrator.py` now binds
the response path, projection claim ref, task/unit/task-set tuple, primary
pointer scalars, active-claim list, current-agent claim ID, and mutation
revision. However,
`_claim_progress_projection_valid` does not validate the merge agent's
`claim_path` or `status`. It also treats an empty string as valid whenever
`_claim_progress_identity_value_valid(..., required=False)` validates a
present `unit_id` or `task_set_id`.

These are not decorative fields:

- `scripts/task_claim_dispatcher.py::_projection_payload` emits the complete
  merge agent and explicitly sets `claim_path` to the canonical claim ref and
  carries the claim `status`.
- `scripts/parallel_worktree_gate.py` lists both `claim_path` and `status` in
  `POINTER_AGENT_FIELDS`; for every active non-overlay claim it requires every
  field to exist, compares `claim_path` with the canonical repository-relative
  claim path, and compares `status` with the committed claim.
- `scripts/state_sync_gate.py` separately requires a non-overlay active worker
  claim to have non-empty `unit_id` and `task_set_id` and rejects canonical
  task/unit/task-set disagreement.

Consequently, a serial projection owner can receive a successful receipt and
project a `current_agents` entry that points at another claim, has no claim
path, contradicts the committed lifecycle status, or carries empty worker
identity. The next registered pointer gate would reject that projection, but
the orchestrator has already returned success. This violates the registered
task/unit requirement that success requires a matching claim projection.

### Independent zero-exit matrix

One inline `python - <<'PY'` probe loaded the exact candidate orchestrator by
path, replaced only its `subprocess.run` seam, and invoked
`cmd_claim_progress` once per response. Every case used its own
`TemporaryDirectory(prefix="task-ar-655-w4b-matrix-")` with byte sentinels at
the canonical claim and pointer paths. The valid merge base carried canonical
path, task, unit, task set, one current agent, exact revision, canonical
`claim_path`, and `status: claimed`; each adverse row changed only the named
surface. A valid explicit overlay used `overlay-no-primary-pointer` and no
`pointer` key.

| Probe group | Required | Actual | Mutation check |
| --- | --- | --- | --- |
| Valid merge; valid overlay | code `0` | both code `0`, exact response status `heartbeated` | both sentinels unchanged |
| Response path/ref mismatch; task/unit/task-set mismatch; task list shape | code `2`, `retry_safe: false` | all code `2`, bounded indeterminate | all sentinels unchanged |
| Missing/multiple current agents; stale revision; conflicting claim ID | code `2`, `retry_safe: false` | all code `2`, bounded indeterminate | all sentinels unchanged |
| Pointer active task/task set/claim ref mismatch | code `2`, `retry_safe: false` | all code `2`, bounded indeterminate | all sentinels unchanged |
| Merge-for-overlay; overlay-for-primary; invented overlay pointer | code `2`, `retry_safe: false` | all code `2`, bounded indeterminate | all sentinels unchanged |
| Present `unit_id: ""` with otherwise matching tuple | code `2`, `retry_safe: false` | **code `0`, `heartbeated`; `retry_safe` absent** | sentinels unchanged |
| Present `task_set_id: ""` with otherwise matching tuple | code `2`, `retry_safe: false` | **code `0`, `heartbeated`; `retry_safe` absent** | sentinels unchanged |
| Merge agent `claim_path` missing | code `2`, `retry_safe: false` | **code `0`, `heartbeated`; `retry_safe` absent** | sentinels unchanged |
| Merge agent `claim_path` names `CLAIM-OTHER.json` | code `2`, `retry_safe: false` | **code `0`, `heartbeated`; `retry_safe` absent** | sentinels unchanged |
| Merge agent `status` missing or `released` while claim is `claimed` | code `2`, `retry_safe: false` | **both code `0`, `heartbeated`; `retry_safe` absent** | all sentinels unchanged |

All 24 matrix rows left both sentinels byte-identical. This confirms the
orchestrator remains read-only at the mutation seam, but non-mutation does not
make an acknowledged conflicting projection safe. `claim_path` is direct
claim-selection authority. `status` is also projection-relevant because the
registered primary-pointer gate requires it to exist and match the active
claim; it is supporting evidence within this one P1 rather than a separate
finding count.

## Implementation and durable-evidence inspection before the stop

The bounded implementation range changes the orchestrator validator, its
atomic-write regression file, managed host lock, and registered lifecycle
surfaces. Source/test implementation ends at
`1239d0322ea3b9ea2631d31e31ff7c868fbde1d2`, tree
`e926b684f781c41405aefd3a76964f0f6b1a4732`. Diff inspection confirmed the
repair covers the prior gross task/ref/pointer conflict and invented overlay
pointer, but its production validator and committed tests do not cover the
counterexamples above.

The fresh Verify artifact was inspected and is attributed to the active worker
`le-20260803-001200-kst-ar655lease001`, not this W4b reviewer. It records
exactly the five commands registered by the task and unit, all with return code
zero:

| Durable command evidence | Recorded result |
| --- | --- |
| Primary claim/liveness/consumer suite | `789 passed, 2 skipped` |
| Secondary mirror/managed-host suite | `68 passed` |
| Template mirror gate | `expected=86 common=86 identical=83 intentional=3 findings=0` |
| Managed host lock check | current |
| Complete repository suite | `4506 passed, 11 skipped, 4 known warnings` |

The W4a declares Verify SHA-256
`345edbe5f053ff8a3352d46ba519efa8d7f4b09fb66c7afa90a556de884fb624`.
The three linked Compound records were read completely and contain distinct
sets of 2, 9, and 1 signatures, respectively: a 12-signature union, each
linked to `TASK-AR-655` and `UNIT-TASK-AR-655-001`. Their record contents and
the existing Compound index entries were present. The W4a also records
`compound_record.py check` pass, 12-of-12 task/unit/active-claim coverage,
evidence-index findings `0`, and work-schema findings `0` with 19 unrelated
legacy warnings.

Per the explicit stop-on-current-scope-P1 rule, this reviewer did **not** rerun
the registered suites, template gate, lock gate, Compound gate, evidence index,
work schema, or full suite after the decisive reproduction. Their durable
green evidence cannot override the uncaught zero-exit counterexample.

## Required repair and re-verification

1. For a merge projection, require `current_agents[0].claim_path` to equal the
   same canonical `agents/runtime/task_claims/<claim_id>.json` ref already
   required from response `path`, projection `task_claim_ref`, and
   `pointer.active_claims`.
2. Require the merge agent's projected lifecycle status to be present and
   consistent with the committed active claim. Preserve intentional overlay
   absence by keeping overlays pointer-free.
3. Treat present empty or otherwise malformed optional unit/task-set values as
   invalid; intentional absence/`null` may retain the documented optional
   semantics.
4. Add zero-exit, no-mutation regressions for missing/conflicting claim path,
   missing/conflicting status, and empty present identities, then rerun fresh
   Verify, replacement W4a, context-isolated W4b, and the separately required
   skeptic review.

## Preserved blockers and safety boundary

The Scribe blocker remains unresolved and unwaived:
`scribe-source-debt-overdue`, including missing `scribe_source_debt` and
`scribe_active_coverage`. Native Windows Python CI and the Bean Wiki, Allimbot,
and Autofolio consumer pilots remain external release gates and were not run;
Basketball Platform remains outside the bounded pilot scope. The active claim,
fresh skeptic, external release authority, and all later W5/W6 actions remain
blocked.

All probe state lived outside the repository in temporary directories. This
new W4b report is the reviewer's only repository write. No production, test,
lifecycle, claim, Compound, index, Git-history, credential, network, consumer,
CI, release, push, tag, package, publication, or deployment state was changed.
`release_authorized` is `false`.
