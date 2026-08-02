---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-03-unit-task-ar-655-001-full-pointer-neutral-final
title: TASK-AR-655 Full-Pointer and Neutral Pre-load Final Independent W4b
date: 2026-08-03
created_at: 2026-08-03T07:35:09+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
claim_id: CLAIM-20260803-002651-task-ar-655-5f27
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: w4b
reviewer: codex-independent-task-ar-655-full-pointer-neutral-final-w4b
reviewer_role: independent-auditor
status: blocked
signal: block
score: 68
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: c877b0b6bc50c3ba925c9562a82897df7a3bb833
candidate_tree: ead19cfacd1b3b2dbe3dbcccac02ca7c41873cd0
accepted_replan_commit: a40974a48f97cbcfae376aa3ec67e614032ab347
pointer_red_commit: 601f0ff28c9c597df9c51f9779f3cc675f6da31a
ui_red_commit: 9ced8d6187e1c86ee1c0f3bb52e5740125cf53da
production_repair_commit: 93b28a9ee7b2aa78c606e64b6c9bd4d74ae36968
verification_evidence: reviews/VERIFY-2026-08-03-unit-task-ar-655-001-20260803065900.json
w4a_ref: reviews/W4A-2026-08-03-unit-task-ar-655-001-full-pointer-neutral-final.md
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
skeptic_authorized: false
release_authorized: false
claim_disposition: remain_claimed
scribe_blocker: scribe-source-debt-overdue
external_release_blockers: preserved_not_run
tags: [w4b, task-ar-655, claim-progress, pointer-agent, type-safety, ui, preload, truthfulness, revise]
---

# TASK-AR-655 full-pointer and neutral pre-load final independent W4b

## Bottom Line

`REVISE — P0: 0, P1: 1, P2: 0.`

The exact clean candidate
`c877b0b6bc50c3ba925c9562a82897df7a3bb833`, tree
`ead19cfacd1b3b2dbe3dbcccac02ca7c41873cd0`, still acknowledges malformed or
incompletely bound canonical pointer-agent tuples. Python's non-type-strict
equality lets an integer claim field match a projected float or boolean, and
`claim.get(field)` lets a missing response-claim field match a projected
`null`. Those zero-exit responses return `heartbeated` instead of the required
bounded indeterminate result even though the canonical pointer consumer would
reject the projected values.

The UI half passes independent desktop/mobile delayed-success, HTTP-503, and
network-abort review, including neutral pre-load facts, the error signal, real
post-arrival metrics, and `built_at` before `generated_at` precedence. The
fresh Verify receipt, seven Compound records, and 14-signature coverage also
validate. They do not override the current-scope P1.

## Signal

| Surface | Signal | Independent evidence |
| --- | --- | --- |
| Candidate identity | pass | clean HEAD `c877b0b6...`, tree `ead19cfa...` |
| RED/GREEN lineage | pass | test-only pointer RED `601f0ff2...`, test-only UI RED `9ced8d61...`, production GREEN `93b28a9e...` |
| Valid merge, routing metadata, revision, overlay | pass | 22 canonical fields present/exact; six supplementary routing fields preserved; stale/float revision rejected; pointer-free overlay accepted; invented overlay pointer rejected |
| Complete canonical binding | **fail / P1** | float/int, bool/int, and missing-claim/`null` counterexamples return code `0` |
| UI pre-Runtime truthfulness | pass | browser `6 passed`; asset/source guards `3 passed` |
| Fresh official Verify | pass | primary `844 passed, 2 skipped`; secondary `68 passed`; mirror findings `0`; lock current; full `4567 passed, 11 skipped, 4 known warnings` |
| Compound parity | pass | task/unit/claim have the same 14 unique signatures and seven unique refs; union coverage 14/14; projection recurrence counts 1/2/3; UI truthfulness count 1 |
| Closure | block, preserved | `scribe_source_debt` and `scribe_active_coverage` remain missing |

The review started with these exact read-only identity checks:

```text
$ git status --short
[no output]
$ git rev-parse HEAD
c877b0b6bc50c3ba925c9562a82897df7a3bb833
$ git rev-parse HEAD^{tree}
ead19cfacd1b3b2dbe3dbcccac02ca7c41873cd0
$ git diff --check
[no output; exit 0]
```

The accepted lineage is linear. `git show -s --format='%H %T %P %s'` returned:

```text
a40974a48f97cbcfae376aa3ec67e614032ab347 ba8d0c9d99fed117389ff069b256b172a1b8b376 5b6a5a9fddccd318fc6f8a813ddc1ab42f036ebb docs(runtime): accept full pointer and neutral preload repair
601f0ff28c9c597df9c51f9779f3cc675f6da31a d97e5bb1ee78eecde83ed2d2f79c8538ca79c8d8 a40974a48f97cbcfae376aa3ec67e614032ab347 test(runtime): expose incomplete pointer agent binding
9ced8d6187e1c86ee1c0f3bb52e5740125cf53da fa5b381911579c78fbb335e90bf56c0ac832b290 601f0ff28c9c597df9c51f9779f3cc675f6da31a test(ui): expose fabricated preload summary
93b28a9ee7b2aa78c606e64b6c9bd4d74ae36968 6de724e9050ba8bb51c403526468d069ecb95c5c 1a266cde03788b9ab2706f03331de874aa825427 fix(runtime): bind full pointer and neutral preload
6e0fb779e89c916a24c715c89707aea7b79ec917 7b1dda68fd115254fe3403fdd073c14fb7e8ddcc d55849960f33e562f7d001cfd3d78470a3fd417d docs(runtime): record full pointer verification and recurrence
c877b0b6bc50c3ba925c9562a82897df7a3bb833 ead19cfacd1b3b2dbe3dbcccac02ca7c41873cd0 6e0fb779e89c916a24c715c89707aea7b79ec917 docs(runtime): self-review full pointer repair
```

### P1-1 — canonical equality is not exact and missing claim fields can be laundered through `null`

`src/agent_runtime/templates/project/scripts/agent_orchestrator.py:1014` loops
over the shared `claim_store.POINTER_AGENT_FIELDS`, but line 1023 derives the
expected value with `claim.get(field)` and line 1024 compares with ordinary
Python `!=`.

Two independent production-shaped zero-exit probe groups exposed the gap:

| Counterexample | Required result | Actual result | Mutation |
| --- | --- | --- | --- |
| claim `progress_pct: 60` / agent `60.0`; `step_index: 6` / `6.0`; `step_total: 10` / `10.0` | code `2`, indeterminate, unknown, non-retryable | all code `0`, `heartbeated` | sentinels byte-identical |
| claim `progress_pct: 0` / agent `false`; claim `step_index: 1` or `step_total: 1` / agent `true` | code `2`, indeterminate, unknown, non-retryable | all code `0`, `heartbeated` | sentinels byte-identical |
| response claim omits `agent_role`, `phase`, `progress_pct`, `handoff_path`, or `last_heartbeat`; agent retains the field as `null` | code `2`, indeterminate, unknown, non-retryable | all code `0`, `heartbeated` | sentinels byte-identical |

The probes loaded the exact candidate orchestrator and live dispatcher
projection helper, replaced only the `subprocess.run` seam, used a separate
`TemporaryDirectory(prefix="ar655-w4b-...")` per case, invoked
`agent_orchestrator.main(...)`, and compared claim and pointer sentinels before
and after. The response claim retained an integer while only the projected
agent used the float or boolean in the type-alias cases. Thus the values were
not exact within the same receipt; this is not a discrepancy inferred from an
external file.

The downstream mismatch is concrete. The canonical pointer gate normalizes
the same values to strings before comparison:

```text
$ PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
... print(_normalized_pointer_value(60), _normalized_pointer_value(60.0), equality) ...
PY
60 60.0 False
6 6.0 False
10 10.0 False
```

Therefore claim-progress can report success for a projection that
`parallel_worktree_gate.py:845` rejects. The no-mutation half remains true,
but success instead of `claim_progress_receipt_indeterminate`,
`commit_state: unknown`, and `retry_safe: false` violates the registered task,
unit, and accepted T3 contract.

The committed matrix does not catch either mechanism. Its missing case removes
only the projected-agent key; its conflicting helper increments integer fields
instead of crossing JSON types. The focused committed suite consequently stays
green:

```text
$ PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_orchestrator_atomic_writes.py -q
.....................................................................    [100%]
69 passed in 0.42s
```

Positive contract probes on the same source returned:

```json
{"canonical_all_exact": true, "canonical_all_present": true, "canonical_field_count": 22, "float_revision_valid": false, "full_merge_valid": true, "overlay_with_pointer_valid": false, "pointer_free_overlay_valid": true, "stale_revision_valid": false, "supplementary_preserved": true}
```

This confirms the finding is bounded to canonical field presence/type equality;
exact revision, valid full merge, supplementary routing data, and pointer-free
overlay behavior remain intact.

### UI, Verify, Compound, and lifecycle evidence

The exact UI checks were:

```text
$ PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_ui_console_e2e.py -k 'initial_state_preload or initial_state_failure' -q
......                                                                   [100%]
6 passed, 19 deselected in 13.45s
$ PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/test_ui_design_assets.py -k 'cockpit_freshness or cockpit_summary or home_wip' -q
...                                                                      [100%]
3 passed, 50 deselected in 0.12s
```

Desktop `1366x768` and mobile `390x844` snapshots stayed neutral before state:
clock `--:--:--`, empty summary and flow content, hidden blank verdict, and no
page errors. Delayed success rendered real `WIP 1/3`, `block 2`, one active
agent, flow values `1/3`, `7/wk`, `12h`, and the at-risk verdict. HTTP 503 and
network abort retained neutral state-derived surfaces while exposing
`poll-state: error` and the existing load-failure text. Source inspection at
`ui_console_assets.py:9035` confirms `state.built_at || state.generated_at`;
the injected timestamp probe selected `2026-07-30T01:02:03.000Z` over a later
`generated_at` and used `generated_at` when `built_at` was absent.

The Verify JSON has SHA-256
`13d559acff8bed6b14039297a8454fedc47875cbe1449ddc71886c1626f9fac0`, is
attributed to worker `le-20260803-001200-kst-ar655lease001`, and its five
commands exactly equal both task and unit verification lists. All commands
have recorded return code zero: primary `844/2`, secondary `68`, mirror
findings `0`, managed lock current, and complete suite `4567/11/4` with the
known UI invalid-escape deprecation warnings.

Fresh direct parity checks returned:

```text
$ python scripts/template_mirror_gate.py --check
template-mirror: expected=86 common=86 identical=83 intentional=3 findings=0
$ python scripts/regen_host_lock_if_needed.py --check
OK: .../tests/fixtures/host/agent_runtime.lock.json is up to date.
$ python scripts/compound_record.py check
compound-record: pass
```

Exact no-legacy Compound searches returned projection recurrence records at
counts `3`, `2`, and `1`, and exactly one UI truthfulness record at count `1`.
All seven records are schema-valid, mitigated, indexed, linked to both
`TASK-AR-655` and `UNIT-TASK-AR-655-001`, and their signature union exactly
covers the 14 unique task signatures. Task, unit, and active claim carry
identical ordered signature and Compound-ref lists. The task and unit remain
`in_progress`, unit verification remains `passed`, and the claim remains
`claimed`; this W4b did not alter lifecycle state.

## Action

Repair `_claim_progress_pointer_agent_matches` so every non-`claim_path`
canonical member must exist in the response claim and the projected value must
match with JSON-type-strict equality. In particular, booleans must never alias
integers and floats must never alias integers. Keep `claim_path` bound to the
canonical ref and keep the separately strict mutation-revision check.

Add regressions that, for every applicable canonical member, cover both a
missing response-claim member paired with projected `null` and same-numeric
value cross-type aliases. Each zero-exit case must produce code `2`,
`claim_progress_receipt_indeterminate`, `commit_state: unknown`, and
`retry_safe: false`, with byte-identical claim and pointer sentinels. Preserve
valid full merge, supplementary metadata, pointer-free overlays, and the UI
truthfulness behavior already passing.

## Risks/Blockers

The independent closure command remains deliberately blocked:

```text
$ python scripts/closure_gate.py --root . --work-id UNIT-TASK-AR-655-001 --json
decision: block
reason: scribe-source-debt-overdue
missing: scribe_source_debt, scribe_active_coverage
repeat_failure.required: true
repeat_failure.satisfied: true
covered: 14
uncovered: 0
findings: 0
```

The Scribe debt and active-coverage obligations remain outside this bounded
repair and unwaived. Native Windows CI and Bean Wiki, Allimbot, and Autofolio
pilots were not run; Basketball Platform remains out of scope. No consumer,
credential, live provider, network package, broker, order, database,
notification, CI, release, push, tag, version, package, publication, or
deployment state was changed.

The fresh full-suite receipt was inspected rather than rerun because the
bounded adversarial probe already establishes the P1 and there was no separate
reason to repeat a six-minute complete suite. All probe state was confined to
temporary directories. This report is the only repository write.

## Decision

Reject the candidate for W4b acceptance with one current-scope P1. Keep
`w4b_acceptance`, `skeptic_authorized`, and `release_authorized` false; keep the
task in progress and the claim held. This report authorizes neither skeptic
execution nor claim release, merge, closeout, pilot, CI, or any external or
release action.

## Next Steps

Record an accepted repair amendment, preserve failure-first order, add the
type-strict and missing-response-claim REDs, implement the bounded validator
repair, and run a fresh official Verify. Re-evaluate the existing projection
defect signature through exact no-legacy lookup before appending any new
immutable recurrence evidence. Then produce a replacement W4a and a new
context-isolated W4b. Only a future W4b `PASS` may authorize a distinct
skeptic; neither review can waive Scribe or external-release boundaries.
