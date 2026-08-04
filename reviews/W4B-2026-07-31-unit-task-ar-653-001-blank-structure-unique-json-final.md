---
title: TASK-AR-653 Blank Structure and Unique JSON Final Independent W4b
date: 2026-07-31
created_at: 2026-07-31T03:05:43+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: f285aa0a11a1b0456be90001706de158b2fde8db
repair_parent: f285aa0a11a1b0456be90001706de158b2fde8db
reviewed_commit: 26e50b9781ba8ca4efc785c5c899dcc834e471da
reviewed_tree: d7097cc34ff02b7f07f07a2ed663872be7b9ee75
w4a_admin_head: 9d7999379cdecd67bb7f85a5dda7a80a8e97a69c
w4a_admin_tree: 2a37cb58c7c8fa315c75e0f4e35c1dd45c690f8e
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..26e50b9781ba8ca4efc785c5c899dcc834e471da
repair_range: f285aa0a11a1b0456be90001706de158b2fde8db..26e50b9781ba8ca4efc785c5c899dcc834e471da
verifier_agent_instance_id: qa-20260731-ar653-blank-structure-unique-json-final-w4b
verified_by: qa-20260731-ar653-blank-structure-unique-json-final-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_semantic_delta_exact_identity_final_w4b
worker_identity: le-20260730-234934-kst-ar653004
independence_status: independent
w4b_acceptance: false
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
tags: [w4b, scribe, json, parse-error, fail-closed, closure-gate, independent-verification, revise]
---

# TASK-AR-653 Blank Structure and Unique JSON Final Independent W4b

## Independent Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

The candidate closes both prior raw-delta reproductions at cleanup record and
receipt replay: Markdown blank rows are position-bound, and duplicate JSON
members are rejected recursively. The registered suite, focused repair
matrix, mirrors, host lock, and valid unique-key compatibility paths are
green.

One integration-level fail-open remains. A configured, present JSON state
source with duplicate members is now rejected by `parse_json()`, but
`evaluate_state()` converts that rejection into advisory `unavailable` state
with `closure_blocking=false`. A substantial closure therefore remains
approved even though the canonical source cannot be interpreted. This exact
candidate is not releasable.

## Exact State, Evidence, and Independence

| Identity | Exact value |
| --- | --- |
| Complete implementation base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Blocking evidence / repair parent | `f285aa0a11a1b0456be90001706de158b2fde8db` |
| Reviewed implementation | `26e50b9781ba8ca4efc785c5c899dcc834e471da` |
| Reviewed implementation tree | `d7097cc34ff02b7f07f07a2ed663872be7b9ee75` |
| W4a/admin HEAD | `9d7999379cdecd67bb7f85a5dda7a80a8e97a69c` |
| W4a/admin tree | `2a37cb58c7c8fa315c75e0f4e35c1dd45c690f8e` |
| Verifier | `qa-20260731-ar653-blank-structure-unique-json-final-w4b` |
| Worker | `le-20260730-234934-kst-ar653004` |

The verifier is distinct from the worker, reread `AGENTS.md` and the complete
`independent-verification` skill, reviewed the prior blocking report, fresh
W4a, machine evidence, implementation code, and both exact ranges, and
designed a separate public closure-flow probe rather than relying only on
worker regressions.

Reviewed ranges:

- `ae998f7b3b96def7347be7317e3cadda6078150f..26e50b9781ba8ca4efc785c5c899dcc834e471da`
- `f285aa0a11a1b0456be90001706de158b2fde8db..26e50b9781ba8ca4efc785c5c899dcc834e471da`

Candidate-to-admin changes are administrative only: unit metadata,
`reviews/INDEX.md`, fresh machine evidence, and W4a. There is no
post-candidate implementation drift.

Supplied evidence hashes matched:

| Evidence | SHA-256 |
| --- | --- |
| Blocking W4b | `3274154e63152816467c1d81a3afa990be07e964235ac0e49baa07e9d61ab7e1` |
| Fresh W4a | `4ee500e3071338a040665754676c9a1e649d8a2624263add2d819aa3b3abf9d0` |
| Machine verification | `2a3a73e094344c4a5ad7c9bcf9207ad7b18b69bb94f487deb5bd837b67775d5d` |

## P1 — Duplicate-JSON Parse Rejection Is Downgraded to Nonblocking Advisory

The new recursive `object_pairs_hook` correctly raises
`StateProjectionError` for a repeated JSON member. `_evaluate_source()` catches
that error and returns a present but unavailable source with a
`source-parse-error` finding. The overall closure calculation does not add a
reason for a configured/present source parse failure:

- there is no `overdue_source` because no hot count was recovered;
- `projection-not-fresh` is considered only when an overdue source exists;
- empty current/projected active identities make coverage complete; and
- `state=unavailable` maps to `readiness=advisory`, not a blocking reason.

### Independent public-flow reproduction

An offline temporary host configured `state/current.json` as its canonical
adapter. The source contained two `items` members, each carrying 16 open rows:

```json
{
  "items": [{"id": "item-0", "status": "open"}],
  "items": [{"id": "item-0", "status": "open"}]
}
```

Each abbreviated collection above contained the complete `item-0` through
`item-15` sequence. The exact observed result was:

```json
{
  "state": "unavailable",
  "finding_codes": ["source-parse-error"],
  "projection_after_normal_write": "fresh",
  "active_coverage": "complete",
  "readiness": "advisory",
  "closure_blocking": false,
  "closure_reasons": [],
  "substantial_closure_gate_decision": "approve"
}
```

`write_projection()` accepted and persisted this unavailable view. Passing the
result to `apply_scribe_obligation()` with `substantial_lines=100`,
`threshold=1`, `disabled=false`, and an otherwise approved closure left the
decision `approve`.

This is candidate-relevant behavior: before duplicate-member rejection,
last-value decoding of the same second 16-row collection classified it
`overdue`; the new rejection instead erases the count from closure policy.
The parser is stricter, but the composed system is less fail-closed.

### Required repair

- Treat a configured/present source read, decode, size, or parse failure as a
  closure-blocking source-integrity reason.
- Do not allow `write_projection()` to turn such a failure into a fresh,
  nonblocking projection.
- Carry the reason through `closure_gate.apply_scribe_obligation()` with an
  explicit remediation message.
- Add direct evaluation, projection-write, and substantial closure-gate
  regressions for duplicate outer, entry, and summary members, plus malformed
  ordinary JSON.
- Preserve advisory `unavailable` behavior only for the intentionally optional
  no-source configuration, if that compatibility is required.

## Closed Repair Families and Positive Compatibility

Independent reruns confirmed:

- blank insertion/deletion at Setext, raw HTML, list continuation, fenced
  block, comment, and heading boundaries fails closed at record and replay;
- duplicate outer collection, entry, and cleanup-summary members fail closed
  at record and replay;
- unique-member JSON key reordering and whitespace remain valid;
- normal Markdown/JSON deletion and exact bounded summary paths remain valid;
- prior semantic hiding, exact ASCII/Unicode/control identity, legacy replay,
  exact owner `no_touch`, Git replacement, and graft regressions remain green;
- the repair does not change the prior Git audit environment or bounded
  receipt authority model.

The rewrite matcher remains source- and plan-bounded: source reads are capped
at 2 MiB, cleanup candidates at 10, and alternate matcher states arise only
from those bounded candidates. The repair adds recursive JSON object
validation and full Markdown row retention without introducing an unbounded
diff.

## Mirrors, Host Lock, Package, and Footprint

All three portable state-projection copies are byte-identical with SHA-256:

`a870b54ffdc52bfc3dd8228dfeb041d11a629a35fc8f68d09d7e4b4e8d7974c7`

Host lock freshness passed; fixture SHA-256:

`62c9135869129a86b4097c6a081be4e413a22e03ecd96b584658792bd6c507dc`

The static wheel/package-data guard passed `2/2`; the actual wheel build was
not independently rerun. Template-smoke/package inclusion coverage is present
in the registered 196-test command, and the template mirror gate reports zero
findings.

The latest repair range changes exactly five declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `tests/test_scribe_due.py`
- `tests/fixtures/host/agent_runtime.lock.json`

Both requested `git diff --check` ranges passed. No undeclared implementation
path was found.

## Independent Command Ledger

| Check | Result |
| --- | --- |
| Registered unit pytest command | `196 passed in 47.54s` |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Focused blank/duplicate/compatibility/identity/no-touch/Git matrix | `35 passed, 87 deselected in 5.14s` |
| Independent duplicate-source evaluation/write/closure probe | **fail-open reproduced** |
| Three-way portable module comparison | byte-identical |
| Host lock freshness | pass |
| Static wheel/package-data guard | `2 passed in 0.10s` |
| Complete and repair range `git diff --check` | pass |
| Worktree before report | clean |

Registered command:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  tests/test_scribe_due.py tests/test_closure_gate.py \
  tests/test_session_continuity_hooks.py tests/test_doctor.py \
  tests/test_template_smoke.py -q -p no:cacheprovider
```

No network, credentials, providers, brokers, orders, database migrations,
notifications, consumer writes, versioning, tags, package publication, push,
deployment, merge, release, or claim mutation occurred.

## Claim Disposition

Claim `CLAIM-20260730-234934-task-ar-653-ar653004` may **not** be released.
It must remain `claimed` and must not enter W5 or the merge queue. A repair
needs a fresh W4a bound to its exact implementation commit/tree and another
distinct W4b with P0=0 and P1=0.

This report is the verifier's only repository change.
