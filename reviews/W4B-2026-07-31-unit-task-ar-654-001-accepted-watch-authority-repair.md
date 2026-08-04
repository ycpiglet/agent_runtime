---
title: TASK-AR-654 Accepted-Watch Authority Repair Independent W4b
date: 2026-07-31
created_at: 2026-07-31T05:12:15+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260731-040735-task-ar-654-ar654001
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
review_base: e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9
revise_evidence_commit: a90a51c8d605fbc95a2d87984d8deabecbbe32dc
reviewed_commit: ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4
reviewed_tree: 85f60fd7415323211513dafd44ad63569c86802c
administrative_head: 002cc2cf595fbadaa1aa29aa5884a9dd32b559df
administrative_tree: 38b45ff33fabbda38f2b78d7522b8a845efa4ec2
worker: le-20260731-040735-kst-ar654001
verified_by: codex-independent-task-ar-654-authority-repair-w4b
verifier_role: independent-auditor
independence_status: independent
verification_evidence: reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731050030.json
tags: [w4b, independent-verification, compound, accepted-watch, authority, duplicate-keys, revise]
---

# TASK-AR-654 Accepted-Watch Authority Repair Independent W4b

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

The repair closes the first W4b's empty/null/false/placeholder reviewer and
alias-only decision bypasses. It does not fail closed on duplicate,
conflicting accepted-watch authority keys. Both the Markdown frontmatter
reader and JSON reader retain only the last occurrence of a key. A watch that
first records a rejected decision, rejected status, missing reviewer, or
different work identity and then repeats the same key with an acceptable value
closes repeated-failure work through both mandatory consumers.

This is a P1 authority bypass. The claim must remain active. This report does
not authorize claim release, merge-queue entry, integration, or closeout.

## Exact review target

| Identity | Value |
| --- | --- |
| Original review base | `e6c8fb4bffff141095ec1d2e8c6dbaadcf3401d9` |
| Original-base tree | `87c593a547675afdc901fa8f6f247d6b994bc2d4` |
| Committed first-W4b `REVISE` / repair base | `a90a51c8d605fbc95a2d87984d8deabecbbe32dc` |
| Repair-base tree | `6e567d52481521f684af6b02781b5e0607be9b38` |
| Repaired implementation | `ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4` |
| Repaired tree | `85f60fd7415323211513dafd44ad63569c86802c` |
| Repaired implementation parent | `a90a51c8d605fbc95a2d87984d8deabecbbe32dc` |
| Fresh W4a / administrative HEAD | `002cc2cf595fbadaa1aa29aa5884a9dd32b559df` |
| Administrative tree | `38b45ff33fabbda38f2b78d7522b8a845efa4ec2` |
| Administrative parent | `ea01f2d578c6fe84b321b1d649a0e667a1c0c6b4` |
| Worker | `le-20260731-040735-kst-ar654001` |
| Independent verifier | `codex-independent-task-ar-654-authority-repair-w4b` |
| Claim | `CLAIM-20260731-040735-task-ar-654-ar654001` |

`git show -s --format='%H %T %P %s'` independently confirmed every commit,
tree, and parent above. The repair range changes exactly six declared paths:
the authoritative and packaged Compound helper, mirror contract, generated
host lock, and two registered test files. The administrative commit changes
only the unit's W4a metadata and review/evidence/index documentation. There is
no code or test diff from the repaired implementation to administrative HEAD.

## P1 — Duplicate authority keys are accepted with last-value-wins semantics

The Markdown reader assigns every parsed key directly into one dictionary
without tracking prior occurrences
(`src/agent_runtime/knowledge_records.py:188-229`). The JSON reader uses
default `json.loads`, which also discards earlier duplicate object members
(`src/agent_runtime/knowledge_records.py:232-238`). Authority validation then
examines only the surviving values
(`src/agent_runtime/knowledge_records.py:262-301`).

For example, each format accepts an explicitly conflicting decision:

```yaml
---
status: accepted
decision: rejected
decision: accepted_watch
reviewed_by: qa-independent
work_id: UNIT-TASK-AR-645-001
---
```

```json
{
  "status": "accepted",
  "decision": "rejected",
  "decision": "accepted_watch",
  "reviewed_by": "qa-independent",
  "work_id": "UNIT-TASK-AR-645-001"
}
```

A fresh disposable-repository matrix repeated the same invalid-then-valid
attack separately for `decision`, `status`, `reviewed_by`, and `work_id` in
both Markdown and JSON. All eight records produced:

- actual `python scripts/work.py --root <temp> close ... --json`: exit `0`
  and closed status;
- work-linked `closure_gate.assess(...)`: `decision=approve`,
  `reason=repeated-failure-compound-present`, and no repeat-failure finding.

That is 16 unsafe endpoint approvals. Reversing the order of every conflicting
pair blocked all eight records through both consumers, proving that authority
depends solely on field order. A record carrying both rejection and acceptance
cannot be treated as unambiguous approval merely because the acceptable value
appears last.

Required repair:

1. Detect duplicate recognized accepted-watch authority keys before value
   normalization in both Markdown and JSON.
2. Reject duplicates for `decision`, `status`, reviewer fields, and work-link
   fields regardless of whether values are equal or conflicting.
3. For JSON, use duplicate-aware object-pair parsing; for Markdown, retain a
   seen-key set while reading frontmatter.
4. Add invalid-then-valid and valid-then-invalid end-to-end negatives for all
   four authority categories, both formats, and both closure consumers.

## Independent accepted-watch attack matrix

All cases below used fresh temporary repositories. Each case ran through the
actual `work.py close` CLI and the work-linked closure gate.

| Matrix | Cases | Endpoint checks | Result |
| --- | ---: | ---: | --- |
| Original reviewer replay: `[]`, `null`, `false`, `TBD` | 4 | 8 | all block; repaired |
| Alias-only `disposition` / `prevention_status` without `decision` | 2 | 4 | all block; repaired |
| JSON type matrix on `decision`, `status`, `reviewed_by`, and `work_id`: null/bool/list/object/number | 20 | 40 | all block |
| YAML inline list/object, inline comment, control tab, quoted whitespace, overlength identity | 6 | 12 | all block |
| YAML placeholder reviewer spellings | 17 | 34 | all block |
| Invalid-leading reviewer identities, including digit/punctuation/non-ASCII starts | 9 | 18 | all block |
| Valid exact Markdown and JSON watches | 2 | 4 | all pass |
| Duplicate invalid-then-valid decision/status/reviewer/work keys in Markdown and JSON | 8 | 16 | **all pass; P1** |
| Duplicate valid-then-invalid order controls | 8 | 16 | all block |
| **Total** | **76** | **152** | **one grouped P1** |

The valid controls explicitly used `decision: accepted_watch`, accepted
status, bounded reviewer `qa.independent@runtime-01`, and the current unit
identity. Both controls closed successfully, so strict scalar validation has
not removed the valid accepted-watch path.

## Repeated-failure and compatibility rechecks

Independent disposable-repository checks and a named 16-test regression slice
confirmed the remaining contract:

| Behavior | Actual `work.py close` | Work-linked closure gate |
| --- | --- | --- |
| Ordinary linked review | pass | approve |
| Ordinary linked retro | pass | approve |
| Parent `repeated_failure` with no Compound | block | block |
| Parent-linked current-task Compound with supported gate | pass | approve |
| Signature-matching Compound owned only by another task | block with work mismatch | block with current-work mismatch |
| Absolute-path defect signature | block with signature finding | block with signature finding |
| Secret-like defect signature | block with signature finding | block with signature finding |
| Oversized defect signature | block with signature finding | block with signature finding |
| Symlinked prevention gate escaping repository root | block with outside-root finding | block with outside-root finding |

Direct ref normalization also rejected `../outside.py`,
`scripts/../outside.py`, `/tmp/outside.py`, and a Windows absolute path.
Registered coverage for missing refs, unsupported-only destinations, and
symlink escape passed. Current-work aggregation continues to accept either
the unit or its parent task only when the Compound itself owns one of those
identities.

## Claim lookup, parity, packaging, and append-only review

Static inspection confirms claim-time knowledge lookup remains before any
claim persistence. `_knowledge_lookup()` runs at
`scripts/task_claim_dispatcher.py:1610`; the claim directory is not created
until line 1661, handoff/log writes start at line 1668, and claim/event
persistence starts at line 1722. Targeted tests passed both a matching prior
Compound and a malformed-store refusal with no claim JSON written.

Source/template parity is current:

| Pair | SHA-256 / result |
| --- | --- |
| `scripts/work.py` and consumer template | both `e89ac68031ac8747403f2002ee937d87ca5b427b96406ca3682b6f001d1a1cac` |
| `scripts/closure_gate.py` and consumer template | both `87c4c10f5eb0c06cffaf95fc1f0304152c99103223d022372b5c14e9fd3402b1` |
| source and consumer `failure-to-regression` skill | both `af125ac7007089f70eaa8ed760611807f9515e185459be38bcadca301e782d59` |
| authoritative knowledge module and packaged `compound_record.py` | both `1e240dfc5c58c88aa8b412c7652a0bb862f0a282b1bff4a192a60211f24feefa` |
| source wrapper `scripts/compound_record.py` | intentional divergence hash `050b123b6608763a3e7ba1abf8bb733e43df21764decd55a4c4415907ff8b10e` matches the mirror contract |

The failure-to-regression skill is byte-identical on source and consumer
surfaces, registered in both asset registries, selected by the core profile,
free of the prohibited Runtime-only dependencies, and present as a managed
host-lock entry. The Compound store check passes. Validation remains
consumption-time only; no historical Compound record or legacy Compound log
is rewritten.

## Command evidence

Commands ran from administrative HEAD `002cc2cf`, whose production and test
content is byte-identical to repaired implementation `ea01f2d5`.

| Command | Result |
| --- | --- |
| Registered `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q` | pass; `286 passed in 11.75s` |
| Named parent/ordinary/containment/lookup/core/lock regression slice | pass; `16 passed in 1.33s` |
| Fresh 76-case / 152-endpoint accepted-watch harness | original and scalar attacks closed; 16 duplicate-key unsafe approvals |
| Fresh ordinary/other-task/signature/containment harness | all expected pass/block outcomes confirmed |
| `python scripts/runtime_asset_usage.py --check` | pass; 39 assets, 713 uses, 0 block, 0 watch; core selects 247 files |
| `python scripts/template_mirror_gate.py --check` | pass; expected/common 84, identical 81, intentional 3, findings 0 |
| `python scripts/regen_host_lock_if_needed.py --check` | pass; lock current |
| `python scripts/compound_record.py --root . check` | pass |
| `python scripts/owner_governance_gate.py` | exit 0; aggregate pass with pre-existing non-blocking watch output |
| `git diff --check e6c8fb4b..ea01f2d5` | pass |
| `git diff --check a90a51c8..ea01f2d5` | pass |
| Source/template SHA-256 checks | pass |

The W4a machine evidence file independently hashes to
`60765e91455b4f5af6c6f8f5bc6cd5a0da00fb3f97911d25d7517e869141c818`.
I did not rerun the full Runtime suite. I explicitly rely on the fresh W4a
exact-repair-tree result of `3129 passed, 3 skipped` with four known UI
warnings. The registered focused suite, relevant gates, packaging checks, and
adversarial matrices were rerun independently.

## Independence and boundary statement

This review was performed by
`codex-independent-task-ar-654-authority-repair-w4b`, a fresh agent instance
distinct from worker `le-20260731-040735-kst-ar654001`. I read the prior
`REVISE` only to identify the required replay, then independently inspected
the exact repair range, constructed expanded disposable attack matrices, and
evaluated the fresh W4a evidence rather than adopting its conclusion.

Only this report was written. No production file, test, Compound record,
claim, task/unit state, registry, index, lifecycle record, consumer
repository, branch, commit, release, merge, push, tag, package, deployment,
credential, provider, or external system was modified. Because P1 is nonzero,
the verdict is `REVISE` and
`CLAIM-20260731-040735-task-ar-654-ar654001` stays active.
