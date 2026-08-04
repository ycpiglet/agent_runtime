---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-02-unit-task-ar-654-001-claim-transaction-final
title: TASK-AR-654 Claim Transaction Final Independent W4b
date: 2026-08-02
created_at: 2026-08-02T20:33:30+09:00
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: w4b
reviewer: codex-independent-task-ar-654-claim-transaction-final-w4b-20260802
reviewer_role: independent-auditor
status: blocked
signal: fail
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 2}
candidate_commit: d1300a921a5d22e496060a3a2867b3214c8afa83
candidate_tree: 41ef322db924a6e432571900aa0b0be424f3ad32
implementation_commit: 19362133d2dffc91647b23beab8f01956a403f7f
implementation_range: d300810b..19362133
review_range: d300810b..d1300a921a5d22e496060a3a2867b3214c8afa83
w4a_ref: reviews/W4A-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
verification_evidence: reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802195023.json
compound_record: agents/project/knowledge/compounds/records/COMPOUND-20260802-195951-bind-claim-authority-to-one-durable-no-clobber-t-3b8cec108077.json
independence_status: independent
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_repair_and_fresh_independent_w4b
tags: [w4b, claim-store, atomic-publication, canonical-authority, no-clobber, fail-closed, compound, revise]
---

# TASK-AR-654 claim-transaction final independent W4b

## Independent verdict

`REVISE — P0: 0, P1: 2, P2: 2.`

Candidate `d1300a921a5d22e496060a3a2867b3214c8afa83`, tree
`41ef322db924a6e432571900aa0b0be424f3ad32`, is not acceptable at W4b. Two
independently reproduced current-scope P1 defects violate the transaction's
fail-closed authority boundary:

1. POSIX atomic publication follows a symlinked ancestor when the lexical
   direct parent already exists, and all four public writers can publish
   outside the intended lexical authority tree.
2. A malformed active-claim witness with container-valued core identities is
   activated and consumed; W0 normalizes it and the real dispatcher creates a
   second authority for the represented task.

The P1 stop rule was applied when these defects were confirmed. Passing broad
tests and formal Compound coverage do not neutralize either behavioral
counterexample. W4b acceptance is false, release is not authorized, and the
active claim must remain held pending repair and a fresh independent W4b.

The exact candidate was clean before this report was created. The implementation
range is `d300810b..19362133`; commits `fca90d65` and `d1300a92` add lifecycle
evidence only. No code or test changed after the implementation commit.

## P1-1 — Atomic publication follows an aliased ancestor

### Evidence

On secure POSIX, `scripts/atomic_io.py:84-105` stops ancestry discovery at an
existing leaf anchor. The validation/open sequence at `scripts/atomic_io.py:112-164`
then validates that anchor but deliberately permits aliases above it. Publication
therefore binds to the resolved location of an existing direct parent rather
than proving every lexical component below the trusted root is a non-alias
directory.

An isolated `/tmp` probe created this layout:

```text
probe-root/
├── alias -> outside
└── outside/
    └── direct-parent/
```

It called `atomic_io.publish_text_owned_atomic()` for lexical target
`probe-root/alias/direct-parent/escaped.txt`, required refusal and absence of
the outside target, and observed:

```text
secure_posix_parent=True
outcome=published
outside_target_exists=True
outside_target_content='escaped authority\n'
```

The assertion probe exited `42`. A second matrix exercised the four public
writers and observed `published-outside` for each:

- `publish_bytes_owned_atomic`
- `publish_text_owned_atomic`
- `publish_json_owned_atomic`
- `publish_yaml_frontmatter_owned_atomic`

The source and template copies are byte-identical, so the same defect is
shipped in the template. This directly reproduces registered defect signature
`defect:atomic-publication-accepts-aliased-parent-compon:e89f4bf8d6bd13c4`,
which the new Compound record claims to mitigate.

### Impact

The no-clobber inode check protects the destination object that the operating
system resolves; it does not prove that object remains inside the caller's
lexical authority tree. An existing parent below a symlinked ancestor can
therefore redirect a first-store marker, witness, claim, or other authority
artifact outside the intended root. This violates the accepted ancestor-alias
and durable no-clobber transaction contract.

### Required repair

Validate every lexical directory component from the trusted root to the direct
parent with directory-relative, no-follow handles. Reject symlink/reparse aliases
before staging or publication, including when the final direct parent already
exists. Retain isolated regressions for all four public writers that prove:

- the operation refuses the alias;
- no outside target is created or changed;
- no staging residue survives; and
- source/template behavior remains identical.

## P1-2 — Malformed core claim identities become active authority

### Evidence

The shared claim reader at `scripts/agent_runtime/claim_store.py:301-325`
validates the schema, claim ID, filename, and status, but does not validate the
JSON types and bounds of core `task_id`, `task_set_id`, or agent identity
fields. All three runtime copies are byte-identical.

W0's canonical snapshot path calls the closure authority-shape helper, but the
helper at `scripts/closure_gate.py:257-266` checks only optional list-valued
authority fields. W0 then stringifies malformed identities at
`scripts/work.py:3832-3856`. The dispatcher duplicate-authority check at
`scripts/task_claim_dispatcher.py:493-503` likewise stringifies `task_id`.

The isolated fixture installed a marker-activated witness with this body:

```json
{
  "schema": "agent-runtime-claim/v1",
  "claim_id": "CLAIM-malformed-active-shape",
  "status": "claimed",
  "task_id": ["TASK-AR-target"],
  "task_set_id": {"bad": "shape"},
  "agent_instance_id": ["bad"]
}
```

The probe invoked the actual dispatcher entry point with:

```text
--root <probe-root> create
--task-id TASK-AR-target
--agent-role orchestrator
--mode orchestrator
--now 2026-08-02T11:00:00+09:00
--suffix second-authority
--json
```

Observed result:

```text
rc=0
response_status=created
new_claim_task=TASK-AR-target
claim_json_count=2
```

The only stderr diagnostics were the expected footprint-less work-item warning
and lookup count `0`; the malformed active authority did not block creation.
A separate W0 probe used `task_id: []` and a mapping-valued agent identity.
Store initialization succeeded and `status_work` returned `status: ok`, with an
empty normalized task ID and a stringified mapping as the active agent.

### Impact

A marker-activated, filename-valid JSON object can enter the canonical store
without canonical scalar identities. Different consumers then normalize the
same malformed value differently, so W0 fails to reject it and the dispatcher
fails to recognize its represented task. The real `create` seam consequently
creates a second active claim authority for that task. This breaks canonical
witness truth, complete-snapshot projection, and the one-active-claim invariant.

### Required repair

Before marker activation, snapshot admission, W0 projection, or dispatcher
duplicate checks, require every core identity to have its canonical bounded
non-empty scalar-string shape. Presence with a list, mapping, boolean, number,
null, or blank value must fail closed; it must never be stringified or treated
as omission. Add regressions through both actual W0/status and actual dispatcher
`create`, with pre/post snapshots proving no second authority and no mutation.
Mirror the repair across all runtime/template copies.

## P2-1 — Released role overlays can omit terminal provenance

The role overlay accepts an existing record as idempotent after generic stable
metadata validation. Mutable fields at `scripts/role_routing.py:345-349`
include release provenance, while the lifecycle validation at
`scripts/role_routing.py:354-383` does not impose status-specific terminal
requirements.

An isolated probe created a valid overlay, mutated it to `status: released`
and terminal phase/progress/timestamps, removed `released_at`, `verified_by`,
`verifier_role`, and `verification_evidence`, then routed the same overlay
again. It observed:

```text
first_created=1
mutated_status=released
release_fields_present=[]
second={"created": [], "enabled": true}
```

The terminal record was accepted as an idempotent match despite lacking all
release provenance. Require status-specific immutable terminal provenance
before an existing released overlay can be accepted. The template has the same
bytes and needs the same regression.

## P2-2 — Supplemental W4a counts lack reproducible provenance

The W4a cites supplemental results of `1591 passed`, `968 passed`, and a
“round-two independent read-only review” with `363 passed`. Repository-wide
exact searches locate those counts only in the W4a; no named command, verifier
identity, raw result, or separately committed review artifact makes them
reproducible. The registered Verify evidence does substantiate its own full and
focused commands, and the W4a correctly declares itself worker-only, so this is
an evidence-traceability defect rather than a falsification finding. Future W4a
supplemental claims should name the exact command, environment, reviewer, and
durable evidence artifact.

## Positive evidence retained

The adverse findings were not inferred from a generally failing candidate.
Fresh independent checks exercised disjoint runtime, governance, and host
surfaces before the P1 stop rule was reached.

| Check | Independent result |
| --- | --- |
| Claim/atomic/dispatcher/role/reaper/closure/projection/lifecycle focused matrix | `927 passed, 6 skipped` |
| Compound/runtime asset/docs/lock/mirror/worktree governance matrix | `656 passed, 2 skipped` |
| Host dispatcher/wave/reaper/watchdog/guard/adoption/doctor matrix | `167 passed` |
| Independent total | `1750 passed, 8 expected platform skips` |
| Strict JSON/snapshot/no-clobber/rollback positive adversarial probe | `adversarial_probe: pass` |
| Runtime asset usage | pass; 39 assets, 0 block, 0 watch |
| Template mirror | pass; 86 common, 83 identical, 3 intentional, 0 findings |
| Host lock | current |
| Evidence index | pass; 0 findings |
| Work schema | pass; 0 findings, 19 unrelated legacy warnings |
| State sync | pass; 0 block, one known `STATUS.md` watch |
| Parallel worktree | pass; 0 block, 0 watch |
| Attribution | pass; 0 block, 836 legacy watches |
| Owner governance | pass |
| Compound record check | pass |
| Range `git diff --check` | pass |

The three pytest commands used fresh `/tmp` base directories,
`PYTHONDONTWRITEBYTECODE=1`, and `-p no:cacheprovider`:

```text
python -m pytest tests/test_claim_store.py tests/test_atomic_io.py
  tests/test_task_claim_dispatcher.py tests/test_role_routing.py
  tests/test_claim_reaper.py tests/test_claim_reaper_concurrency.py
  tests/test_closure_gate.py tests/test_inventory_sync_sanitize.py
  tests/test_inflight_overlay.py tests/test_work_close.py
  tests/test_lifecycle_defaults.py -q

python -m pytest tests/test_compound_records.py
  tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py
  tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py
  tests/test_template_mirror_gate.py tests/test_parallel_worktree_gate.py -q

python -m pytest tests/host_contracts/test_autofolio_task_claim_dispatcher.py
  tests/host_contracts/test_autofolio_wave_dispatcher.py
  tests/test_claim_reaper_hook.py tests/test_deadlock_watchdog.py
  tests/test_claim_guard.py tests/test_adoption.py tests/test_doctor.py -q
```

The registered Verify artifact is
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802195023.json`, SHA-256
`078b8e4d6779f233c68647ae693e6541df045fa2525d518f3143650c7a2bfe7a`.
Its five commands are coherent with the candidate history and report a full
`4249 passed, 11 skipped, 4 warnings`, focused `1251 passed, 2 skipped`, plus
passing runtime-asset, template-mirror, and host-lock checks.

The independent environment was Linux `6.8.0-134-generic` x86_64 with Python
`3.10.12`. All adversarial fixtures and pytest base directories were outside
the repository under `/tmp`.

## Source/template parity

The audited source/template copies are byte-identical within each group:

| Group | SHA-256 |
| --- | --- |
| Three `claim_store.py` copies | `300b6cc3918dfbaca4c5414ad9e4b86d2ff511207e85c08c17378ee1239bcda6` |
| `atomic_io.py` pair | `116a26d97c6b2a2d1b5a01cbc6c1084cca8c1717a2cbdc095d2a611765f69c33` |
| `claim_guard.py` pair | `b00fabfed89072fa1f447a90f2cc7a85b400723ece6a9dedf1347d021460dcc7` |
| `claim_reaper.py` pair | `91d4cbd6905ddc5e2a11854db05edab6cded6b5768cdbc0de26fe987cba2a64c` |
| `closure_gate.py` pair | `c765949a0ad332cc3d385b16715ba6bbc0ef9db51e62684b300cd2c656351584` |
| `inflight_overlay.py` pair | `95ba8c356b0ab65a9b38614135a636bbc5521faf5e25280af7f0523d1cd1336d` |
| `parallel_worktree_gate.py` pair | `8b98b6f72a38a63843399686719346b5d9bedce05e3eaef94074e3f19a3153c8` |
| `role_routing.py` pair | `f4029b49bbb470871cca40a49474783162251a8633713874dddd3cc830ee1f8e` |
| `task_claim_dispatcher.py` pair | `de7961dcb650df46613ed77af3703e81c4d0a179fa7d057fd7ba302813ccb6a6` |
| `work.py` pair | `1aa01cf2305af059e6999134c968350b4209f3562d842394d57743c30261fa9a` |

Parity is positive packaging evidence, but here it also proves the P1/P2
runtime defects are mirrored rather than isolated to one source copy.

## Compound and signature audit

Task, unit, and active claim contain the same ordered 40 defect signatures and
the same four Compound references. Their newline-terminated sorted signature
hash is
`924f5d57931d391b49e9a5fd85efe2f70b66326070a13ea331a02963ac99b09a`.
The four record counts are `4 + 6 + 4 + 26 = 40`; concatenation in reference
order exactly equals the registered ordered set, with 40 unique signatures,
zero uncovered, zero extraneous, and zero overlap. Every record binds exactly
`TASK-AR-654` and `UNIT-TASK-AR-654-001`.

The new record has SHA-256
`acbf130685bde2327d531c6ec203233248e3c91dc87b4e7820217100becb23bd`.
The three prior records remain byte-unchanged across the review range, with
hashes:

- `1da4db66377f6e330521f35017526439a5d92eb34b9894b8bc08fa36817f5f81`
- `269b7dc7367b0078c7f86b054ae331e5a704ae2db6011eded33a8de592db02cb`
- `ea8a74e8f1312749a549afb6c63c1becdba752dd713be37b1c61c1c76a61572a`

This establishes syntactic completeness and append-only record integrity. It
cannot establish behavioral mitigation: P1-1 is a direct counterexample to a
signature the new record marks mitigated.

## Explicit blockers and limits

The P1 findings are independently sufficient to reject this candidate. The
following pre-existing release blockers also remain and are not waived:

- Native Windows Python 3.10, 3.11, and 3.12 execution was unavailable. The
  workflow definition is not a substitute for execution evidence.
- Explicit `closure_gate.py --work-id UNIT-TASK-AR-654-001 --check --json`
  exited `1` with decision `block` and reason `scribe-source-debt-overdue`.
  Missing coverage is `scribe_source_debt` and `scribe_active_coverage`;
  repeated-failure Compound authority reports `required=true`,
  `satisfied=true`, and no uncovered signatures.
- TASK-AR-655 still owns negative lease/grace bounds.
- TASK-AR-657 still owns verifier-approval authenticity.
- TASK-AR-651 still owns the portable version/package cascade.

Task/unit historical prose also still describes W4a as pending while
authoritative metadata marks it complete. That stale narrative is informational
and does not alter the adverse W4b outcome.

## Required disposition and safety boundary

Repair both P1 boundaries, add actual-seam non-mutation regressions, and produce
a new exact candidate. A fresh verifier distinct from the worker must then
repeat the alias-parent matrix, malformed-witness W0 and dispatcher cases,
focused suites, mirror/hash checks, Compound audit, and closure assessment.
This report is not reusable as approval for a repaired tree.

No claim release, close, lifecycle transition, integration, CI dispatch,
version change, commit, push, merge, tag, package publication, deployment,
consumer mutation, network action, or external release is authorized. Apart
from this W4b file, the review used read-only repository inspection and
isolated `/tmp` behavior probes.
