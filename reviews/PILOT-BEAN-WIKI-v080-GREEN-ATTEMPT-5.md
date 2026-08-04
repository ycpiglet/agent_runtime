---
title: Bean Wiki v0.8 Green Pilot Attempt 5
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-014
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: blocked
signal: block
score: 89
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 2}
tags: [pilot, bean-wiki, green-replay, attempt-5, acceptance-contract, evidence-portability]
---

# Bean Wiki v0.8 Green Pilot Attempt 5

## Bottom Line

The disposable Bean Wiki consumer journey passed, but UNIT-014 is blocked at
the Runtime evidence-acceptance boundary.

Exact Runtime product
`34427e1fe18d6c4db8a81142616ccad24cc6e7de` safely installed
`core+web-content`, preserved Bean host and content bytes, completed exactly
three bounded offline traces, passed causal isolation, and produced no
external effect. All three Runtime/task traces received independent local
approval with no P0 or P1. The separate editorial review correctly returned
`REVISE` for the article-publication domain and made no content change.

The Runtime validator cannot accept that truthful green evidence. It embeds
one Bean contract for the historical red pilot and requires its red
`pilot_id`, blocked result, old Runtime commit, old selection count, old task
identities, old findings, and old verification failures. The accurate
attempt-5 fixture therefore fails with twelve red-contract mismatches.

A second contract conflict prevents promotion of the isolation evidence:
`pilot_isolation_gate.py` requires machine-local canonical absolute checkout
roots, while the repository sanitizer rejects those paths in committed
fixtures. The current raw isolation fixture passes the isolation gate, but it
cannot pass the public sanitizer without replacing observed provenance with
invented paths.

Verdict: `BLOCK / P1`; P0 none. Freeze attempt 5 as valid consumer-run
evidence but not an accepted Runtime release fixture. Do not start Allimbot.

## Finding Summary

| Finding | Scope | Priority | Effect |
| --- | --- | ---: | --- |
| Bean acceptance is hard-coded to one historical red execution | Runtime acceptance harness | P1 | Every truthful green replay is rejected; making it pass would require false evidence or source edits |
| Isolation evidence and public sanitization contracts are incompatible | Runtime evidence lifecycle | P1 | Exact local checkout provenance cannot be promoted as a sanitized repository fixture |
| Contract data is embedded in executable Python | Maintainability | P2 | Every new immutable pilot requires code modification instead of declarative contract registration |
| Acceptance messages encode red-pilot semantics | Diagnostics | P2 | Generic failures refer to “pinned red-pilot observation,” obscuring which contract was selected |

## Fixed Provenance

| Field | Observed value |
| --- | --- |
| Runtime product | `34427e1fe18d6c4db8a81142616ccad24cc6e7de` |
| Runtime product tree | `d94bf33a89482a6299b454e6594404afef7adfcf` |
| Runtime template tree | `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f` |
| Runtime packaged-scripts tree | `62311b7847f66206a2a33e4bd497750bf074384f` |
| Runtime template digest | `sha256:236d6f1cabf57cc87da1346df8c55a5f96615406c2ecbd5833e2dd47ccf09c01` |
| Bean baseline/current HEAD | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Bean target branch | `codex/task-ar-648-agent-runtime-green-pilot-5` |
| Runtime acceptance fixture SHA-256 | `3a212a2d77831b6f17e3a104098c55cb5bf32676879654ec531d805d108df25e` |
| Raw isolation fixture SHA-256 | `761b236f6ad9f1fd99cb88e688ffefb75422e0e177e5fc8422b1738fbcfd52b1` |
| Consumer commit count | `0` |

The detached Runtime product checkout remained clean. The disposable Bean
target retained its baseline HEAD and an empty tracked diff. Its expected
Runtime projection is untracked consumer state only.

## Adoption and Preservation

| Check | Result |
| --- | --- |
| Selected files | 246 (`core+web-content`) |
| Effective ownership | 239 managed, 5 seed-once, 2 host-owned excluded |
| Initial reconcile | 244 safe updates, 0 preserved, 2 excluded, 0 conflicts |
| Safe apply | 244 applied, 0 remaining conflicts |
| Immediate reconcile | 0 updates, 244 preserved, 2 excluded, 0 conflicts |
| Final reconcile | 0 updates, 244 preserved, 2 excluded, 0 conflicts |
| Lock | v2, exact Runtime/template provenance, 0 findings |
| Doctor | 0 blockers, 8 warnings after restoring the required empty message directory |
| Installed `work.py now` | passed |
| Delayed complete-taskset gate | passed after a distinct wall-clock second |
| State sync / continuity / RBAC / Owner governance | passed |
| Declared host assets | 16 files, manifest unchanged at `d87317141c2e662cb667f22a3c0049b154dedb55f76855defa2548c71ee06478` |
| Complete `src/content` | 125 files, manifest unchanged at `2d45cb99dbcd1e3fe86ad0ebf9d31646580a0720d3496c27c952e829e2ba07cb` |
| Target article | unchanged at `a4c431e1ad5eb77d260c37e19b2ceb3637b43f2c606a2b87b81e99857354f4d6` |
| Generated article index | unchanged at `0f635c697d019744a8a9abfbc357723261537a088308d05692ea87a0edc476b0` |
| Bean content check | passed: 98 Korean articles, 12 English articles, references valid |
| Bean editorial check | passed with 17 pre-existing non-blocking length warnings |
| External effects | publish, deploy, push, commit, credential, network, install, and content mutation all integer zero |

`build:content` was intentionally not run because it writes the generated
article index; the read-only pilot instead verified that the existing index
and complete content manifest were unchanged.

## Three Bounded Traces

| Task | Route | Result |
| --- | --- | --- |
| `TASK-AR-201` adoption | requested/selected `worker_low`; provider tier `haiku`; deterministic local; observed provider model and usage unavailable | W4a and independent W4b approve; P0 0, P1 0, P2 2 |
| `TASK-AR-202` editorial | requested/selected `worker_standard`; provider tier `sonnet`; one selective specialist; provider model and usage unavailable | Runtime trace W4a/W4b approve; article publication remains `REVISE` |
| `TASK-AR-203` restart/Compound/Scribe | requested/selected `worker_low`; provider tier `haiku`; deterministic local processes; observed provider model and usage unavailable | W4a and independent W4b approve; P0 0, P1 0, P2 2 |

The editorial specialist wrote only
`agents/host/pilot/reviews/coffee-flavor-wheel-green-5.md`, whose SHA-256 is
`dd7243074023deb6797b89edf9642b1dd131f8e5be8b9ae302c7ce1946570a97`.
It read the declared Bean editorial SSOT and returned article-domain
`REVISE` with P0 2, P1 3, and P2 2. The leading article blockers are missing
traceable references and an incomplete beginner-learning structure. This is a
useful content diagnosis, not a failure of the requested read-only Runtime
trace, and no article remediation was authorized.

TASK-AR-203 deliberately reproduced a missing pre-compact checkpoint,
recorded the task-linked Compound
`COMPOUND-20260730-050750-restart-continuity-requires-a-persisted-pre-comp-e09b269d7ed8`,
and retrieved it first with score 180 and no unrelated match. Writer PID
`1067788` and reader PID `1068190` resumed the same claim in distinct local
processes. The checkpoint and `latest.json` shared SHA-256
`28dce2749e6279ab750583782d53e4b0bd06f3e9c81383e4ce129cb271a8d427`.
Scribe refreshed only its configured projection; source `BACKLOG.md` remained
unchanged at
`c8c323352fcaf1b477094afb86f789728b2f85cc7f23429a9462af1c1dfad591`.

## Causal Isolation

The raw attempt-5 isolation evidence records one disposable target, one new
same-commit frozen control, the live Bean primary as a non-causal observation,
and Allimbot as an untouched observation. The isolation gate returns:

```text
status=pass
block_count=0
watch_count=0
```

The disposable target changed only through its authorized Runtime projection.
The frozen control retained identical HEAD, status digest, and tracked-diff
digest. Bean primary and Allimbot retained their captured baseline states; no
command or write trace targeted either repository.

The same fixture necessarily contains canonical machine-local checkout roots.
The public sanitizer returns one `absolute-local-path` finding for that file.
Replacing those roots with convenient fictitious locations would make the
fixture sanitized but no longer exact evidence, so UNIT-014 does not do so.

## Runtime Acceptance Failure

The accurate, path-sanitized green evidence fixture was evaluated with:

```text
python scripts/pilot_acceptance.py \
  --host bean-wiki \
  --fixture tests/fixtures/pilots/bean-wiki/evidence-green-attempt-5.json \
  --check
```

Result:

```text
pilot-acceptance: fail
findings=12
pilot-contract-mismatch
result-contract-mismatch
fixture-semantic-digest-mismatch
baseline-contract-mismatch
selection-contract-mismatch
post-registration-reconcile-mismatch
unexpected-task-trace (three instances)
finding-contract-mismatch
verification-contract-mismatch (two instances)
```

These are exactly the fields that differ between the historical red run and
the new green run. They do not identify an internal inconsistency in attempt
5. The validator currently has no `(host, pilot_id)` contract lookup and no
explicit contract file; `HOST_CONTRACTS["bean-wiki"]` is the single red
record.

## Required Runtime Repair

Open a separate Runtime-only unit. It must:

1. move immutable pilot expectations into declarative, schema-checked contract
   records keyed by both `host` and `pilot_id`;
2. preserve and revalidate the original red fixture without changing its
   semantic digest;
3. register the truthful attempt-5 contract without weakening shared safety,
   preservation, routing-truth, or zero-effect checks;
4. fail closed on unknown, duplicate, malformed, cross-host, path-traversal,
   or semantically drifted contracts and evidence;
5. introduce an explicit raw-to-sanitized isolation-evidence contract, so the
   public fixture retains verifiable checkout identity without local path
   leakage;
6. test both historical red and green contracts plus adversarial mutations;
7. pass canonical W4a and fresh independent W4b on one exact Runtime product.

After that repair, use a sixth fresh disposable Bean checkout and a sixth
fresh frozen control. Do not reinterpret attempt 5 as release acceptance after
the product under test changes.

## Decision

Freeze attempt 5. Preserve it as evidence that the consumer journey and
selective routing now work, while recording that the Runtime acceptance and
evidence-portability harnesses are not yet release-ready.

Allimbot, versioning, tagging, packaging, pushing, publishing, deployment, and
release remain blocked.
