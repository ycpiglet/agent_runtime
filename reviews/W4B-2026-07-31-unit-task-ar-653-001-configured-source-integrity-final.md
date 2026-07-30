---
title: TASK-AR-653 Configured Source Integrity Final Independent W4b
date: 2026-07-31
created_at: 2026-07-31T03:27:08+09:00
task_id: TASK-AR-653
unit_id: UNIT-TASK-AR-653-001
claim_id: CLAIM-20260730-234934-task-ar-653-ar653004
status: blocked
signal: block
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
reviewed_base: ae998f7b3b96def7347be7317e3cadda6078150f
blocking_evidence_commit: de2726a6fe688e8ba81bb58a3067a7d2826664e4
repair_parent: de2726a6fe688e8ba81bb58a3067a7d2826664e4
reviewed_commit: 3887286387e8f8799edbd1ad66687c44e6fbdc32
reviewed_tree: 56f18328c09685833144bb1924b56ebc039f70e7
w4a_admin_head: 3d83a6864458e57fb99758af1e662d7c55b1c886
w4a_admin_tree: a293e9a939cba9594c1ce913fe9921958d64dc7d
complete_review_range: ae998f7b3b96def7347be7317e3cadda6078150f..3887286387e8f8799edbd1ad66687c44e6fbdc32
repair_range: de2726a6fe688e8ba81bb58a3067a7d2826664e4..3887286387e8f8799edbd1ad66687c44e6fbdc32
verifier_agent_instance_id: qa-20260731-ar653-configured-source-integrity-final-w4b
verified_by: qa-20260731-ar653-configured-source-integrity-final-w4b
verifier_role: qa-reviewer
verifier_task: /root/task_ar_653_semantic_delta_exact_identity_final_w4b
worker_identity: le-20260730-234934-kst-ar653004
independence_status: independent
w4b_acceptance: false
claim_disposition: remain_claimed_pending_repair_and_fresh_w4b
tags: [w4b, scribe, config, source-integrity, fail-closed, closure-gate, independent-verification, revise]
---

# TASK-AR-653 Configured Source Integrity Final Independent W4b

## Independent Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

The candidate correctly blocks configured sources that reach evaluation as
`source-missing`, `source-unsafe`, `source-too-large`, or
`source-parse-error`. Projection refresh does not clear those reasons, and
substantial closure receives the intended source-integrity obligation.

One normal configuration path still fails open: an unsafe configured adapter
is rejected while loading `agent_runtime.yml` and becomes a top-level
`config-invalid` finding before any `StateSource` exists. The new integrity
logic scans only evaluated sources, so it sees no unavailable path and leaves
substantial closure approved. This contradicts the repair's declared unsafe
configured-source invariant and blocks release.

## Exact State, Evidence, and Independence

| Identity | Exact value |
| --- | --- |
| Complete implementation base | `ae998f7b3b96def7347be7317e3cadda6078150f` |
| Blocking evidence / repair parent | `de2726a6fe688e8ba81bb58a3067a7d2826664e4` |
| Reviewed implementation | `3887286387e8f8799edbd1ad66687c44e6fbdc32` |
| Reviewed implementation tree | `56f18328c09685833144bb1924b56ebc039f70e7` |
| W4a/admin HEAD | `3d83a6864458e57fb99758af1e662d7c55b1c886` |
| W4a/admin tree | `a293e9a939cba9594c1ce913fe9921958d64dc7d` |
| Verifier | `qa-20260731-ar653-configured-source-integrity-final-w4b` |
| Worker | `le-20260730-234934-kst-ar653004` |

The verifier is a distinct instance from the worker. It reread the repository
contract and complete independent-verification skill, inspected the prior
blocking report, fresh W4a and machine evidence, reviewed both exact ranges,
and designed a separate file-config-to-closure reproduction rather than
relying only on worker tests.

Reviewed ranges:

- `ae998f7b3b96def7347be7317e3cadda6078150f..3887286387e8f8799edbd1ad66687c44e6fbdc32`
- `de2726a6fe688e8ba81bb58a3067a7d2826664e4..3887286387e8f8799edbd1ad66687c44e6fbdc32`

Candidate-to-admin changes are only unit metadata, `reviews/INDEX.md`, the
fresh W4a, and machine verification evidence. No implementation drift occurs
after the candidate.

Supplied evidence hashes matched:

| Evidence | SHA-256 |
| --- | --- |
| Prior blocking W4b | `a5130faf647708520aba02ab6ad13cdd43a8c22e4ec47c251fa20cf7f4b08a23` |
| Fresh W4a | `3a4751b0dfa8bc91d69d22856e350929239c44d45671948b4a3afa0af16b092e` |
| Machine verification | `713c764bd51849bfa1a6e63c280b9f96b0d8f4acc32e8bc04e1c4196b48b923b` |

## P1 — File-Config Unsafe Adapter Bypasses Source-Integrity Closure

`resolve_settings()` catches configuration-loading exceptions and returns:

```text
configured=true
sources=[]
finding=config-invalid
```

The repair derives `unavailable_sources` exclusively from evaluated
`sources[]` whose per-source finding codes intersect
`_CONFIGURED_SOURCE_INTEGRITY_CODES`. With no source object, the
`config-invalid` condition never becomes `configured-source-integrity`.

### Independent public-flow reproduction

An offline temporary host used a real `agent_runtime.yml` with an unsafe
adapter and matching unsafe ownership entry:

```yaml
ownership:
  host_owned:
    - ../outside.md
host:
  state_adapters:
    escaped: ../outside.md
```

Observed result:

```json
{
  "finding_codes": [
    "config-invalid",
    "projection-missing",
    "active-coverage-complete"
  ],
  "source_count": 0,
  "state": "unavailable",
  "readiness": "advisory",
  "closure_blocking": false,
  "closure_reasons": [],
  "write_projection": "StateProjectionError",
  "substantial_closure_decision": "approve"
}
```

`write_projection()` correctly rejected the invalid configuration. That does
not close the gate: applying the Scribe obligation to otherwise approved,
enabled substantial work (`substantial_lines=100`, `threshold=1`) returned
`approve` because evaluation did not mark the condition blocking.

This is not an intentionally optional no-source host. A configuration file is
present and explicitly declares canonical state, but its unsafe declaration
disappears from the closure-debt model before source evaluation.

### Required repair

- When a Runtime config is present, map `config-invalid` to a
  closure-blocking configuration/source-integrity reason even if source
  materialization fails.
- Preserve the exact configuration error in findings while exposing a bounded
  remediation path such as `agent_runtime.yml` in closure evidence.
- Ensure substantial `closure_gate.assess()` blocks with a distinct missing
  obligation; projection refusal alone is insufficient.
- Add public regressions for unsafe adapter/ownership paths and malformed or
  schema-invalid Runtime configuration through `evaluate_state()`,
  `write_projection()`, and substantial closure.
- Keep an actually unconfigured, no-conventional-source host advisory.

## Closed Families and Compatibility

Independent reruns confirmed:

- configured missing, oversized, invalid UTF-8, malformed JSON, and recursive
  duplicate-member sources block evaluation and remain blocked after
  projection write;
- substantial closure blocks for configured per-source integrity debt;
- optional unconfigured no-source remains advisory;
- healthy and overdue configured-source behavior remains compatible;
- prior Markdown blank-structure, JSON uniqueness, semantic-delta,
  exact-identity, owner `no_touch`, Git replacement, and graft regressions
  remain green;
- valid unique-key JSON reorder/whitespace, deletion, and bounded summary
  paths remain valid.

Resource bounds remain unchanged: sources are capped at 2 MiB, cleanup plans
at 10 candidates, and the matcher uses source-linear traversal with
plan-bounded alternative states.

## Mirrors, Host Lock, Package, and Footprint

The three portable state-projection copies are byte-identical with SHA-256:

`c3e24cd20a0ae12030eb76337a3ee801db45093fc8807492c95b354760f52b2a`

The root/template closure-gate pair is byte-identical with SHA-256:

`9b1ccb00a9014ff20a9af9dba8cdeeacabe1b2db7e43cead261d46101cb83ee2`

Host lock freshness passed; fixture SHA-256:

`24f4b98754dd4db3018962fed3f2a380d20c89b9d66f25cf9ce069f793c19c6c`

The static wheel/package-data guard passed `2/2`; the actual wheel build was
not independently rerun. Package/template coverage is also exercised by the
registered template-smoke suite and mirror gate.

The repair range changes exactly eight declared unit targets:

- `src/agent_runtime/state_projection.py`
- `scripts/agent_runtime/state_projection.py`
- `src/agent_runtime/templates/project/scripts/agent_runtime/state_projection.py`
- `scripts/closure_gate.py`
- `src/agent_runtime/templates/project/scripts/closure_gate.py`
- `tests/test_scribe_due.py`
- `tests/test_closure_gate.py`
- `tests/fixtures/host/agent_runtime.lock.json`

Both requested `git diff --check` ranges passed. No undeclared implementation
path was found.

## Independent Command Ledger

| Check | Result |
| --- | --- |
| Registered unit pytest command | `206 passed in 47.94s` |
| Template mirror gate | expected 84, common 84, identical 81, intentional 3, findings 0 |
| Focused integrity/compatibility/prior-attack matrix | `45 passed, 108 deselected in 5.05s` |
| Independent unsafe file-config evaluation/write/closure probe | **fail-open reproduced** |
| Three-way state module parity | byte-identical |
| Two-way closure-gate parity | byte-identical |
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
It must remain `claimed` and must not enter the merge queue or W5. A repair
needs fresh exact-commit W4a evidence and another distinct W4b with P0=0 and
P1=0.

This report is the verifier's only repository change.
