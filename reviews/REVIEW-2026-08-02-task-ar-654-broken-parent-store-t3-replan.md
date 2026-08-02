---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-broken-parent-store-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T13:35:55+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-strict-authority-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-strict-authority-final.md
tags: [task-ar-654, t3, claim-store, broken-parent, symlink, fail-closed]
---

# TASK-AR-654 broken-parent claim-store T3 replan

## Why the candidate is reopened again

Candidate `de01e01d1b8f966bb4414dd18c44bd45966f12d0` (tree
`0d5581db71be18bde997f5aa5f11c8b622a4619f`) passed `3994` full-suite tests,
fresh machine verification, an append-only prevention record, and worker W4a.
The fresh independent W4b and skeptic reviews both reproduced one remaining
P1: when
`agents/runtime` is replaced by a broken directory symlink, the descendant
`agents/runtime/task_claims` path appears absent and `_active_claims` treats
the canonical store as an ordinary empty store. Actual `work close` returned
success and changed the unit and generated views even though the hidden active
claim carried the only repeated-failure authority.

The prior W4a is append-only historical evidence but cannot authorize this
candidate. Both reports reject the candidate and neither can release the
claim. Unit verification returns to failed and the repair claim remains held.

## Prior-knowledge search

The stable signature generated from `broken ancestor symlink hides canonical
active claim store` is:

`defect:broken-ancestor-symlink-hides-canonical-active-c:23158c0595f498bb`

Exact canonical search with `--no-legacy --json` returned `[]`. No Compound is
created during replanning. All four existing TASK-AR-654 Compound records stay
immutable; a new record may be appended only after a durable regression and
fresh machine verification exist.

## Failure-first repair decision

1. Add an actual `work close` regression before implementation. Populate a
   direct canonical active-claim store, move the `agents/runtime` directory
   aside, replace that parent with a broken directory symlink, and assert a
   bounded failure before unit, hidden claim, backlog, classification, or
   review-index mutation.
2. Validate every lexical component from repository root through
   `agents/runtime/task_claims` before interpreting an absent final store as
   empty. A symlink, non-directory component, broken component alias, resolve
   error, or resolved-path mismatch must emit
   `active-claim-store-integrity-invalid`.
3. Preserve compatibility for a genuinely absent store beneath direct,
   non-aliased parent directories and for a valid direct canonical store.
4. Mirror the implementation byte-for-byte in the consumer template and
   regenerate the host lock if its managed digest changes.
5. Commit the RED regression before implementation. Then replay the new
   regression, all prior strict-authority cases, both complete
   closure/Compound files, the registered focused suite, the full Runtime
   suite, asset/mirror/host-lock gates, and owner governance.
6. Create fresh Verify evidence and one new append-only Compound linking TASK,
   UNIT, the new signature, the regression, and the repaired gate.
7. Require a new W4a, distinct new-context W4b, and fresh skeptic approval on
   one exact post-repair candidate. Earlier approvals remain non-authorizing.

## Scope amendment

The implementation remains bounded to:

- `scripts/closure_gate.py`;
- `src/agent_runtime/templates/project/scripts/closure_gate.py`;
- `tests/test_compound_records.py`;
- `agents/project/TEMPLATE-MIRROR-CONTRACT.json` only if generated metadata
  changes; and
- `tests/fixtures/host/agent_runtime.lock.json` after the template change.

Task, unit, claim, handoff, log, review, Verify, Compound, and generated index
files are lifecycle evidence. This replan does not authorize Scribe cleanup,
consumer-repository writes, broader path-policy changes, or an external
release action.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer write, version, tag, publication,
push, deployment, or external release action is authorized. Keep the claim
held until the complete fresh verification and independent-review sequence
passes.
