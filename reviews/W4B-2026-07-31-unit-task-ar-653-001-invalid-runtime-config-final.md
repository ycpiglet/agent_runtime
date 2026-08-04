---
title: TASK-AR-653 Invalid Runtime Config Final Independent W4b
date: 2026-07-31
created_at: 2026-07-31T03:44:33+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: approved
signal: approve
verdict: APPROVE
priority: P1
finding_counts: {P0: 0, P1: 0, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: a904ae8960420f125cb2c5bc8c46d12b717bbcd0
repair_parent: a904ae8960420f125cb2c5bc8c46d12b717bbcd0
reviewed_commit: ee7d0a8569f835b16b6ca8e1938db34f25628fa0
reviewed_tree: 408a3a18e3da964e671db6f7bf49fae904d53213
w4a_admin_head: 61af007de8e08a91181adfb2bda4c540410ce745
w4a_admin_tree: e8531e20d48bd6622fad2d496d36ed11a324257b
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..ee7d0a8569f835b16b6ca8e1938db34f25628fa0
repair_range: a904ae8960420f125cb2c5bc8c46d12b717bbcd0..ee7d0a8569f835b16b6ca8e1938db34f25628fa0
verifier_agent_instance_id: qa-20260731-ar653-invalid-runtime-config-final-w4b
verified_by: qa-20260731-ar653-invalid-runtime-config-final-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_semantic_delta_exact_identity_final_w4b
worker_identity: le-20260730-234934-kst-ar653004
independence_status: independent
w4b_acceptance: true
claim_disposition: remain_claimed_pending_orchestrator_release
tags: [w4b, scribe, config-invalid, source-integrity, fail-closed, closure-gate, independent-verification, approve]
---

# TASK-AR-653 Invalid Runtime Config Final Independent W4b

## Independent Verdict

`APPROVE — P0: 0, P1: 0, P2: 0.`

Exact implementation candidate
`ee7d0a8569f835b16b6ca8e1938db34f25628fa0` closes the remaining
top-level invalid-configuration bypass without reopening the prior Scribe
cleanup, replay, semantic-delta, exact-identity, source-integrity, or Git-view
families. A present but invalid `agent_runtime.yml` now becomes bounded
configured-source debt, blocks readiness, refuses projection writes, and
blocks substantial closure. A genuinely unconfigured host remains advisory.

No P0, P1, or P2 finding was found. This W4b approves the exact candidate and
tree only. It does not itself release the claim, merge, enter W5, publish,
deploy, or mutate a consumer.

## Exact State, Evidence, and Independence

| Identity | Exact value |
| --- | --- |
| Complete implementation base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Blocking evidence / repair parent | `a904ae8960420f125cb2c5bc8c46d12b717bbcd0` |
| Reviewed implementation | `ee7d0a8569f835b16b6ca8e1938db34f25628fa0` |
| Reviewed implementation tree | `408a3a18e3da964e671db6f7bf49fae904d53213` |
| W4a/admin HEAD | `61af007de8e08a91181adfb2bda4c540410ce745` |
| W4a/admin tree | `e8531e20d48bd6622fad2d496d36ed11a324257b` |
| Verifier | `qa-20260731-ar653-invalid-runtime-config-final-w4b` |
| Worker | `le-20260730-234934-kst-ar653004` |

The verifier is a distinct instance from the worker. It reread the repository
contract and the complete independent-verification skill, inspected the prior
blocking W4b, fresh W4a, and machine evidence, reviewed both exact ranges, and
designed a separate public configuration-to-closure matrix rather than
accepting worker tests as sufficient proof.

Reviewed ranges:

- `ae998f7b3b96def7347be7317e3cadda6078150f..ee7d0a8569f835b16b6ca8e1938db34f25628fa0`
- `a904ae8960420f125cb2c5bc8c46d12b717bbcd0..ee7d0a8569f835b16b6ca8e1938db34f25628fa0`

Candidate-to-admin changes are only the unit record, `reviews/INDEX.md`, fresh
machine verification evidence, and W4a. There is no implementation drift
after the candidate.

Supplied evidence hashes matched:

| Evidence | SHA-256 |
| --- | --- |
| Prior blocking W4b | `59e7a0bc777701eb402a7799a9430887453c1daea36dc71a2a0021db5d487bc7` |
| Fresh W4a | `97c12edbf245157eda773886255962bb5b6c3e6ff1001c01ed73351262c44739` |
| Machine verification | `32bf9bd766f62269f367ae69cf0fc0467ee2966b299599f60b3acae58d3fa76b` |

The machine evidence records the worker's exact-candidate full suite as
`3102 passed, 3 skipped, 4 warnings`. This W4b separately reran the registered
unit surface and targeted adversarial families below.

## Repair Review

`resolve_settings()` preserves configuration-loading failures as
`config-invalid`. The repair consumes that existing finding in
`evaluate_state()` and adds the canonical bounded path `agent_runtime.yml` to
the same sorted, deduplicated unavailable-source set used for evaluated
configured sources.

Independent code inspection confirmed:

- the original `config-invalid` finding and diagnostic remain available;
- `source_debt.unavailable_sources` names `agent_runtime.yml`;
- `configured-source-integrity` is emitted for the bounded repair path;
- closure reasons include `configured-source-integrity`;
- `write_projection()` refuses the invalid configuration;
- substantial closure maps the state to the existing
  `scribe-source-integrity` obligation;
- valid, due, overdue, and optional-unconfigured behavior is not broadened.

The change is narrow and uses the existing configuration authority rather
than reparsing config or guessing paths.

## Independent Invalid-Configuration Matrix

A separate offline probe built real temporary host trees and exercised public
`evaluate_state()` and `write_projection()` entry points. Each case was also
composed through `closure_gate.assess()` with otherwise valid review evidence
and substantial work (`200` changed lines).

| Invalid `agent_runtime.yml` case | Evaluation | Projection write | Substantial closure |
| --- | --- | --- | --- |
| unsafe ownership path `../outside.json` | blocked | refused | block |
| unsafe adapter path `../outside.json` | blocked | refused | block |
| unsafe projection path `../projection.json` | blocked | refused | block |
| unsafe host-context path `../HOST-CONTEXT.yml` | blocked | refused | block |
| unsafe role-overlay path `../overlay.yml` | blocked | refused | block |
| malformed top-level indentation | blocked | refused | block |
| unsupported schema `v9` | blocked | refused | block |
| missing `sync.allow_silent_overwrite` | blocked | refused | block |
| unknown root key | blocked | refused | block |
| ownership conflict across host-owned and generated sets | blocked | refused | block |

For all ten invalid configurations, the independent result was:

```json
{
  "state": "unavailable",
  "readiness": "blocked",
  "closure_blocking": true,
  "closure_reasons": ["configured-source-integrity"],
  "source_debt": {
    "unavailable_sources": ["agent_runtime.yml"]
  },
  "config_invalid_present": true,
  "write_projection": "StateProjectionError",
  "substantial_closure_decision": "block",
  "substantial_closure_reason": "scribe-source-integrity"
}
```

The excerpt above shows the relevant assertions; the full result also
retained the bounded hot/debt fields defined by the state schema.

Compatibility controls passed:

| Control | State/readiness | Closure |
| --- | --- | --- |
| healthy configured source, hot count 11 | `ok` / `ready` | nonblocking |
| due configured source, hot count 13 | `due` / `advisory` | nonblocking |
| overdue configured source, hot count 16 | `overdue` / `blocked` | blocking |
| no config and no conventional source | `unavailable` / `advisory` | nonblocking |

Healthy, due, and overdue retained the pre-repair `source_debt` shape. The
optional no-source control did not acquire configured-source debt.

## Prior Families Closed

The independent focused rerun covered the current repair and prior attack
families:

- configured missing, unsafe, oversized, invalid UTF-8, malformed, and
  duplicate-member sources remain fail-closed;
- optional-unconfigured no-source remains advisory;
- Markdown blank-record cleanup and replay remain bound to semantic content;
- recursive JSON duplicate members remain rejected, while valid unique-key
  reorder and whitespace-only changes remain accepted;
- exact padded and legacy identity matching does not collapse distinct
  records;
- owner `no_touch` exclusions remain enforced;
- repository-local Git replacement and graft views cannot substitute the
  canonical audit view;
- bounded Markdown and JSON summary identities retain their positive and
  negative controls.

The targeted pytest selection returned:

```text
53 passed, 108 deselected in 5.24s
```

Resource bounds are unchanged by this repair: source reads retain the 2 MiB
cap, cleanup alternatives retain the 10-candidate cap, and matching remains
source-linear with plan-bounded alternative states.

## Mirrors, Host Lock, Package, and Footprint

The three portable state-projection copies are byte-identical with SHA-256:

`ad9a1072600e31b7c7612a19d3088c1586cba5a5626b5dcda6d71c23eedfbc9`

The root/template closure-gate pair is byte-identical with SHA-256:

`9b1ccb00a9014ff20a9af9dba8cdeeacabe1b2db7e43cead261d46101cb83ee2`

Host lock freshness passed; fixture SHA-256:

`30070d95b21384634ea7b4f020cff0e4d5e50621b118fa26ed50355c8231cefe`

The static wheel/package-data guard passed `2/2`. An independent, no-network
wheel build from an exact candidate `git archive` also succeeded using cached
build tooling. Inspection of
`agent_runtime-0.7.0-py3-none-any.whl` found all required artifacts:

- `agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `agent_runtime/templates/project/scripts/closure_gate.py`
- `agent_runtime/templates/project/agents/scribe/SKILL.md`
- `agent_runtime/templates/project/skills/independent-verification/SKILL.md`

The latest repair range changes exactly six declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `tests/test_scribe_due.py`
- `tests/test_closure_gate.py`
- `tests/fixtures/host/agent_runtime.lock.json`

Both requested `git diff --check` ranges passed. No undeclared repair path was
found.

## Independent Command Ledger

| Check | Result |
| --- | --- |
| Registered unit pytest command | `214 passed in 48.06s` |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Focused repair/prior-family pytest matrix | `53 passed, 108 deselected in 5.24s` |
| Independent ten-case config/evaluation/write/closure matrix | pass |
| Independent healthy/due/overdue/optional compatibility matrix | pass |
| Three-way state module parity | byte-identical |
| Two-way closure-gate parity | byte-identical |
| Host lock freshness | pass |
| Static wheel/package-data guard | `2 passed in 0.11s` |
| Exact-candidate offline wheel build and archive inspection | pass, required 4/4 |
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

Claim `CLAIM-20260730-234934-task-ar-653-ar653004` remains `claimed` in this
report. Once this W4b evidence is committed without candidate drift, the
orchestrator may release the claim and continue the separately governed
lifecycle. This report does not perform that action.

This report is the verifier's only repository change.
