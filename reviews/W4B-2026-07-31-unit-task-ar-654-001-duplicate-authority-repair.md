---
title: TASK-AR-654 Duplicate Authority Repair Independent W4b
date: 2026-07-31
created_at: 2026-07-31T05:34:47+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
review_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
repair_base: 3360a637b4c4416caa6dab0c4de9ce9139e6437f
reviewed_commit: 84404f2e5e6bef5577410eee488a6c61532e190f
reviewed_tree: 6dace9cc19b6a0660a66bf73f169550a3553fa7b
administrative_head: bca3a915acb1ea66f76b2eb7f21de76e49dca163
administrative_tree: 65d991ebf177dabd03620f3303d8c327cb5353bd
worker: le-20260731-040735-kst-ar654001
verified_by: codex-independent-task-ar-654-duplicate-authority-repair-w4b
verifier_role: independent-auditor
independence_status: independent
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731052414.json
tags: [w4b, independent-verification, compound, accepted-watch, yaml, duplicate-keys, revise]
---

# TASK-AR-654 Duplicate Authority Repair Independent W4b

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

The repair rejects byte-identical duplicate Markdown keys and duplicate JSON
object members, but it does not canonicalize YAML frontmatter keys before
duplicate detection. A quoted YAML authority key and its plain equivalent are
semantically the same mapping key while the lightweight Markdown parser treats
them as distinct raw strings. An accepted value on the plain occurrence can
therefore override an explicitly conflicting quoted occurrence without
producing `compound:prevention-watch-invalid`.

This was reproduced through both mandatory closure consumers. It is a P1
bypass of the accepted-watch prevention authority contract. Claim
`CLAIM-20260731-040735-task-ar-654-ar654001` must remain active; this report
does not authorize release, merge-queue entry, local integration, or closeout.

## Exact review target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Duplicate-repair base / second REVISE evidence | `3360a637b4c4416caa6dab0c4de9ce9139e6437f` |
| Reviewed implementation candidate | `84404f2e5e6bef5577410eee488a6c61532e190f` |
| Candidate tree | `6dace9cc19b6a0660a66bf73f169550a3553fa7b` |
| Candidate parent | `3360a637b4c4416caa6dab0c4de9ce9139e6437f` |
| Administrative W4a HEAD | `bca3a915acb1ea66f76b2eb7f21de76e49dca163` |
| Administrative tree | `65d991ebf177dabd03620f3303d8c327cb5353bd` |
| Administrative parent | `84404f2e5e6bef5577410eee488a6c61532e190f` |
| Repair range | `3360a637b4c4416caa6dab0c4de9ce9139e6437f..84404f2e5e6bef5577410eee488a6c61532e190f` |
| Complete implementation range | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9..84404f2e5e6bef5577410eee488a6c61532e190f` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Independent verifier | `codex-independent-task-ar-654-duplicate-authority-repair-w4b` |

`git show -s --format='%H %T %P %s'` confirmed the commit, tree, and parent
identities above. The repair range changes exactly six declared paths: the
authoritative and packaged Compound helpers, mirror contract, generated host
lock, and two registered test files. The administrative commit changes only
the unit's W4a metadata and review/evidence/index documentation; it does not
change candidate production or test content.

## P1 — YAML authority keys are deduplicated as raw text, not semantic keys

`_simple_frontmatter_payload()` strips surrounding whitespace from a key and
checks that raw string against `seen`. It does not decode a quoted YAML scalar
key before the check. Consequently the following two entries are distinct to
the Runtime parser but the same `decision` key to a YAML parser:

```yaml
"decision": rejected
decision: accepted_watch
```

An independent YAML composition check confirmed that both entries resolve to
the scalar key `decision`. The Runtime parser instead retains the quoted
spelling as an unrelated field, reads only the plain `decision`, and accepts
the document when the other watch metadata is valid. The closure result is
therefore selected by the parser's raw key spelling/order rather than by an
unambiguous authority record.

A fresh disposable-repository reproduction produced these endpoint outcomes:

| Consumer | Observed outcome |
| --- | --- |
| Actual `python scripts/work.py --root <temp> close ... --json` | exit `0`; unit status became `closed` |
| Work-linked `closure_gate.assess(...)` Stop path | `decision=approve`, `reason=repeated-failure-compound-present`, `repeat_failure.satisfied=true`, zero findings |

Both paths consumed the same canonical current-unit Compound and the same
quoted-versus-plain duplicate watch. Neither emitted
`compound:prevention-watch-invalid`. The demonstrated record contains both an
explicit rejection and acceptance for one semantic authority key, so accepting
it violates the repair's stated rule that duplicates fail closed regardless of
order or value.

### Required repair and regression matrix

1. Parse frontmatter keys into one bounded semantic representation before
   duplicate detection, or explicitly reject any key syntax outside the
   supported plain-key grammar before accepted-watch validation.
2. Reject a second semantic occurrence of every accepted-watch authority key
   regardless of value equality, conflict direction, quoting, or order.
3. Add end-to-end Markdown regressions for `decision`, `status`, every member
   of `ACCEPTED_WATCH_REVIEWER_FIELDS`, and `work_id` / `task_id` / `unit_id` /
   `work_ids`.
4. For each authority field, cover plain versus single-quoted, double-quoted,
   and escaped quoted spellings in both relative orders, plus equal-value
   duplicates. Every duplicate must block through actual `work.py close` and
   the work-linked Stop gate with
   `compound:prevention-watch-invalid`; canonical single-key Markdown and JSON
   controls must continue to close.
5. Keep the existing JSON object-pair and exact-raw-key Markdown matrix. It is
   useful coverage, but it is not sufficient for semantic frontmatter
   duplicates.

## Completed independent evidence

| Command or check | Result |
| --- | --- |
| Registered focused suite: `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q` | pass; `318 passed in 13.51s` |
| `git diff --check 3360a637b4c4416caa6dab0c4de9ce9139e6437f 84404f2e5e6bef5577410eee488a6c61532e190f` | pass |
| `git diff --check e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9 84404f2e5e6bef5577410eee488a6c61532e190f` | pass |
| Authoritative/package Compound helper `sha256sum` and `cmp -s` | byte-identical; both `5ec29ae67b7ae1855d50ffbe6167b35360ecf11cb889a73b06aa874301a74c0c` |
| Source/template `work.py` parity | byte-identical; both `e89ac68031ac8747403f2002ee937d87ca5b427b96406ca3682b6f001d1a1cac` |
| Source/template `closure_gate.py` parity | byte-identical; both `87c4c10f5eb0c06cffaf95fc1f0304152c99103223d022372b5c14e9fd3402b1` |
| Source/template `failure-to-regression` skill parity | byte-identical; both `af125ac7007089f70eaa8ed760611807f9515e185459be38bcadca301e782d59` |
| Fresh W4a evidence SHA-256 | `c85dcecaaecdf02bb0b075ddc795c8b4798c3dcef0081df53842b1b64ef72d54` |
| Disposable quoted/plain YAML reproduction | unsafe approval through both mandatory consumers |
| YAML semantic-key composition check | quoted and plain occurrences both resolve to `decision` |

The registered suite includes the existing exact-key duplicate matrix and
coverage for parent repeated-failure aggregation, ordinary review/retro
compatibility, supported prevention types, repository containment and symlink
escape, current-work ownership, claim lookup before persistence, deterministic
Compound search/index behavior, and append-only compatibility. Those
registered checks passed, but they do not cover the semantic-key discrepancy
reported above.

I did not rerun the complete Runtime suite after the P1 was established. I
explicitly rely on the exact-candidate W4a report for `3161 passed, 3 skipped`
with four known UI warnings. I independently confirmed the candidate
commit/tree and the W4a evidence file identity and SHA. The machine evidence
also records passing Runtime asset usage, template mirror, and host-lock
checks; those command outputs were inspected, not adopted as an independent
approval.

## Independence and boundary statement

This review was performed by
`codex-independent-task-ar-654-duplicate-authority-repair-w4b`, a fresh agent
instance distinct from worker `le-20260731-040735-kst-ar654001` and from both
prior W4b verifier instances. I read the prior REVISE reports to preserve their
required replay boundary, then independently inspected the exact repair and
complete ranges, verified identities and packaging parity, ran the registered
focus suite, and exercised the mandatory consumers in a disposable repository.
I did not treat the worker's W4a conclusion as approval.

Only this W4b report was written. No production file, test, Compound record,
claim, task/unit state, index, registry, lock, branch, commit, consumer
repository, release, version, tag, push, publication, deployment, credential,
provider, or external system was modified. Because P1 is nonzero, the verdict
is `REVISE` and the claim must remain active. A future independent `APPROVE`
may authorize claim release and local W5 integration only; it never authorizes
an external release.
