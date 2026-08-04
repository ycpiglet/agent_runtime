---
title: Bean Wiki v0.8 Green Pilot Attempt 6
date: 2026-07-30
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-016
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
status: passed
signal: pass
score: 97
priority: P2
finding_counts: {P0: 0, P1: 0, P2: 3}
tags: [pilot, bean-wiki, green-replay, attempt-6, acceptance-contract, evidence-portability]
---

# Bean Wiki v0.8 Green Pilot Attempt 6

## Bottom Line

Bean Wiki attempt 6 is a truthful green consumer replay on exact Runtime
product `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2`.

The new disposable Bean checkout installed `core+web-content`, preserved all
declared host and content bytes, completed exactly three bounded offline
traces, passed delayed taskset completion, and produced zero consumer commits
or external effects. Raw physical-root isolation passed with zero blocks and
zero watches, then the exact product generated a deterministic path-free v2
projection bound to the raw byte digest. The new strict attempt-6 contract
accepts the evidence, while the historical red and attempt-5 contracts still
accept only their own immutable fixtures.

All three local Runtime traces received W4a and independent W4b approval with
no P0 or P1. The separate Bean article review remains `REVISE`; this is an
editorial publication decision, not a Runtime harness failure or publication
authorization.

Verdict: `PASS / P2`. Bean is eligible for final UNIT-016 W4a and fresh W4b.
Do not start Allimbot or any release action before that independent review.

## Signal

| Signal | Result |
| --- | --- |
| Exact Runtime product | `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` |
| Bean target/control baseline | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Adoption | 246 selected; 244 safe-applied; zero conflicts |
| Host/content preservation | pass; 16 host assets and 125 content files unchanged |
| Three bounded traces | completed and independently approved |
| Raw isolation | pass; 0 block / 0 watch |
| Sanitized isolation | pass; no local path |
| Exact attempt-6 acceptance | pass; 0 findings |
| Historical red and attempt-5 acceptance | pass; 0 findings each |
| External effects | all required counters integer zero |

## Fixed Provenance

| Field | Observed value |
| --- | --- |
| Runtime product | `4929415d059ec8a8dc3b409b2c2e64ca7f9d98f2` |
| Runtime product tree | `b50ec188fc8ed078b34b2e86954dd7ef5bd58d2f` |
| Runtime template tree | `e45e7aaeeb0639c24f5e9e80c18d5e203b98ba8f` |
| Runtime packaged-scripts tree | `62311b7847f66206a2a33e4bd497750bf074384f` |
| Runtime lifecycle baseline | `57c7ba45ad5d7c56fed2d7bf5cebb4aee60e58ae` |
| Runtime registration boundary | `2025bc75a1c044e69e23bf975ee1243298db7b2c` |
| Runtime claim boundary | `1134b3ac2ae337ff3f054270b3d9d4881f74ab41` |
| Bean baseline/current HEAD | `357eee4fd8c29c33a949adbe3a0ffa80c874bf42` |
| Runtime template digest | `sha256:236d6f1cabf57cc87da1346df8c55a5f96615406c2ecbd5833e2dd47ccf09c01` |
| Consumer commit count | `0` |

The detached Runtime product checkout remained clean. The Bean target retained
its baseline HEAD and an empty tracked diff; all projected Runtime state is
untracked consumer evidence. The frozen control retained its baseline HEAD,
empty porcelain status, and empty tracked diff.

## Adoption and Preservation

| Check | Result |
| --- | --- |
| Selected files | 246 (`core+web-content`) |
| Effective ownership | 239 managed, 5 seed-once, 2 host-owned excluded |
| Initial reconcile | 244 safe updates, 0 preserved, 2 excluded, 0 conflicts |
| Safe apply | 244 applied, 0 remaining conflicts |
| Immediate reconcile | 0 updates, 244 preserved, 2 excluded, 0 conflicts |
| Post-registration reconcile | 0 updates, 244 preserved, 2 excluded, 0 conflicts |
| Final reconcile | 0 updates, 244 preserved, 2 excluded, 0 conflicts |
| Lock | v2, exact Runtime/template provenance, 0 findings |
| Doctor | 0 blockers, 8 warnings |
| Installed `work.py now` | passed |
| Delayed completed-taskset gate | passed after a distinct wall-clock second |
| State sync / continuity / RBAC / Owner governance | passed; no block finding |
| Host assets | 16 files, unchanged aggregate `d09b7a36a2e329a1ca47110f53dbcb8ae6303de6b72bdfe8e278cd09aea94107` |
| Complete `src/content` | 125 files, unchanged aggregate `650644e5398b955d87b36d3f78bde97921f297b8df707b0d19d84074d8f98c71` |
| Target article | unchanged at `a4c431e1ad5eb77d260c37e19b2ceb3637b43f2c606a2b87b81e99857354f4d6` |
| Generated article index | unchanged at `0f635c697d019744a8a9abfbc357723261537a088308d05692ea87a0edc476b0` |
| Bean content check | pass: 98 Korean articles, 12 English articles, references valid |
| Bean editorial check | pass with 17 pre-existing non-blocking length warnings |

The host/content aggregate is calculated from sorted relative paths and
per-file SHA-256 output. This removes the machine-path dependence present in
earlier narrative aggregates. `build:content` was intentionally not run
because it writes the generated article index; the read-only pilot verified
the existing index directly instead.

## Three Bounded Traces

| Task | Route | Result |
| --- | --- | --- |
| `TASK-AR-201` adoption | requested/selected `worker_low`; policy alias `haiku`; deterministic local; actual model and usage unverified | W4a and independent W4b approve; P0 0, P1 0, P2 2 |
| `TASK-AR-202` editorial | requested/selected `worker_standard`; policy alias `sonnet`; exactly one existing specialist invocation; actual model and usage unverified | Runtime W4a/W4b approve; article remains `REVISE` |
| `TASK-AR-203` restart/Compound/Scribe | requested/selected `worker_low`; policy alias `haiku`; deterministic local processes; actual model and usage unverified | W4a and independent W4b approve; P0 0, P1 0, P2 2 |

The one editorial specialist read every declared Bean editorial input and
wrote only `agents/host/pilot/reviews/coffee-flavor-wheel-green-6.md`. The
final artifact SHA-256 is
`91edb49228a7fe4e369e944c5ed8d51ad220c002a243f5a0dd15450b134bd7c7`.
Its article-domain verdict is `REVISE` with P0 2, P1 2, and P2 1. Missing
traceable references and an incomplete beginner-learning structure remain
publication blockers. No article remediation or publication was authorized.

W4a caught that the specialist initially reused the prior attempt's
path-sensitive content aggregate. It recomputed the declared relative-path
aggregate and corrected only that digest before independent review. The
specialist's prose, priorities, and verdict did not change.

TASK-AR-203 deliberately reproduced the missing pre-compact checkpoint,
recorded task-linked Compound
`COMPOUND-20260730-065600-restart-continuity-requires-a-persisted-pre-comp-c32dc434e47c`,
and retrieved it exactly first and alone at score 180. Writer PID `1356811`
and reader PID `1357293` resumed the same task and claim in distinct local
processes. The checkpoint and `latest.json` share SHA-256
`98e9d286e8d8ac4069d8dfc34d9cf7b0f58a8f5055941f37b362c649481283d2`.

Scribe refreshed only its configured projection. Source `BACKLOG.md` remained
unchanged at
`c8c323352fcaf1b477094afb86f789728b2f85cc7f23429a9462af1c1dfad591`;
the fresh projection is
`45e58ac59b7dde48e639f97a06d7d59845d0bff0742f37aea78dfbfda4a8a6e9`.

## Causal Isolation and Portable Evidence

The private raw v1 proof records only the disposable attempt-6 checkout as an
observed write root. The exact product, frozen control, Bean primary,
attempt-5 checkout, Autofolio, and Allimbot remain unchanged observations.
The raw gate returns:

```text
status=pass
block_count=0
watch_count=0
```

Raw byte SHA-256:
`1365fd1b1bf6f96e1f273b773fdf8ab7ef30a79a98e4bbd1396490a1c757fa2b`.

The raw artifact remains private. Exact-product sanitization emitted
`tests/fixtures/pilots/bean-wiki/isolation-green-attempt-6.json`, containing
checkout identities and snapshots but no absolute path. Its semantic SHA-256
is `37086702e4efb96fd283ded40229d6746549f6c0a36f0a6263045186fe63e367`
and its embedded raw-proof digest matches the private byte digest exactly.
The portable isolation gate passes with zero findings.

## Exact Acceptance Contract

The strict contract
`tests/fixtures/pilots/contracts/bean-wiki-v080-green-attempt-6.json` binds:

- evidence semantic SHA-256
  `99c0bd4d14b09fdd29eec596e89648d67d7006744c0af587fa086b0d9c054dfb`;
- the exact Runtime and Bean baselines;
- exact task, unit, claim, and terminal status identities;
- the zero-finding verification map and required integer-zero effects;
- portable-isolation semantic SHA-256
  `37086702e4efb96fd283ded40229d6746549f6c0a36f0a6263045186fe63e367`;
- raw isolation byte SHA-256
  `1365fd1b1bf6f96e1f273b773fdf8ab7ef30a79a98e4bbd1396490a1c757fa2b`.

Acceptance results:

| Contract | Result |
| --- | --- |
| `bean-wiki:bean-wiki-v080-green-attempt-6` | pass, 0 findings |
| `bean-wiki:bean-wiki-v080-green-attempt-5` | pass, 0 findings |
| `bean-wiki:bean-wiki-v080-red-pilot` | pass, 0 findings |

This proves that contract registration is additive and keyed by the exact
`(host, pilot_id)` pair. Attempt 6 does not reinterpret either historical
fixture.

## Verification

| Verification | Result |
| --- | --- |
| Pilot isolation and acceptance tests | `41 passed` |
| Adoption/taskset/claim/continuity/ownership focused tests | `480 passed` |
| Template mirror | 84 expected/common; 81 identical; 3 intentional; 0 findings |
| Runtime asset usage | pass; 0 block / 0 watch |
| Runtime Owner governance | pass |
| Public sanitizer | 0 findings |
| Bean content/editorial checks | pass |
| Product checkout cleanliness | pass |

## Insight

Attempt 6 closes the two attempt-5 P1s without weakening the safety model:
raw evidence proves physical containment before paths are removed, while the
public projection remains portable and cryptographically bound to that raw
decision. Versioned declarative contracts allow multiple immutable pilot
histories to coexist without executable Python edits.

The replay also exposed why calculated evidence should be generated, not
copied into prose. The stale aggregate was caught and repaired locally, but a
future evidence writer should emit this digest directly from the canonical
command.

## P2 Follow-ups

1. Scribe correctly reports Bean's 74-item backlog as overdue. Projection
   freshness and closure readiness still pass; backlog curation is a host
   operational task, not a Runtime release blocker.
2. Policy tiers are not provider observations. Actual model, token, cost, and
   savings claims remain unavailable until verified telemetry exists.
3. Promote the relative-path aggregate calculation into a generated evidence
   helper so a specialist cannot carry a path-sensitive digest across pilots.

## Decision

Accept the attempt-6 consumer evidence and proceed to canonical UNIT-016 W4a
plus a fresh independent W4b on this exact Runtime lifecycle state.

If both reviews contain no P0 or P1, Bean Wiki is independently green and
Allimbot may be registered as the next separate pilot. Version bump, tag,
package, push, publish, deploy, and release still require explicit Owner
approval and are not performed here.
