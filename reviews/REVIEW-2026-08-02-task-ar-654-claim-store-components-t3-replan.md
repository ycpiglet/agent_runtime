---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-claim-store-components-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T13:57:25+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/AUDIT-2026-08-02-task-ar-654-claim-store-component-final.md
  - reviews/AUDIT-2026-08-02-task-ar-654-windows-reparse-parent.md
tags: [task-ar-654, t3, claim-store, reparse-point, enumeration, missing-parent, bounded-error]
---

# TASK-AR-654 claim-store component integrity T3 replan

## Why the candidate is reopened again

Candidate `9c3119dd39ad6978a74c64f09aa40d43321de995` (tree
`86630bc9f1bc9cf550c25f917d225253150140ff`) fixed the original POSIX
broken-parent symlink and passed `1152` registered tests plus the full Runtime
suite (`3995 passed, 3 skipped`). Two distinct read-only audits then found
three remaining cross-platform/data-availability defects:

1. a Windows directory junction retains directory mode under `lstat()`, so
   discarding reparse metadata can recreate the broken-parent fail-open;
2. Python 3.10 `Path.glob()` silently presents an unreadable claim store as
   empty, and a missing intermediate `agents/runtime` parent is also accepted
   as ordinary absence; and
3. resolving a claim-entry symlink loop raises an unbounded `RuntimeError`
   instead of a bounded per-entry finding.

The first two classes were independently shown capable of hiding active
repeated-failure authority before an otherwise successful close mutation. The
loop remains fail-closed but violates the bounded-error contract. The
candidate is rejected, unit verification stays failed, and the claim remains
held.

## Prior-knowledge search

Exact canonical `--no-legacy --json` searches returned `[]` for all four
stable signatures:

- `windows junction parent hides canonical active claim store` →
  `defect:windows-junction-parent-hides-canonical-active-c:731de644205f5d8d`;
- `unreadable active claim store enumerates as empty` →
  `defect:unreadable-active-claim-store-enumerates-as-empt:c7816e3946c29101`;
- `missing intermediate claim store parent hides active authority` →
  `defect:missing-intermediate-claim-store-parent-hides-ac:4560560004a1fb77`;
- `active claim symlink loop escapes bounded handling` →
  `defect:active-claim-symlink-loop-escapes-bounded-handli:49bf17a5e1901460`.

No Compound is created during replanning. Every existing TASK-AR-654 record
remains immutable. Append a new record only after the complete new prevention
matrix and fresh Verify evidence exist.

## Failure-first repair decision

1. Add regressions before implementation for Windows name-surrogate reparse
   metadata, a missing intermediate `agents/runtime` parent, unreadable direct
   store enumeration, and a claim-entry symlink loop.
2. The two availability P1 regressions must exercise actual `work close` and
   prove no unit, hidden claim, backlog, classification, or review-index
   mutation. The loop regression must prove a bounded error without traceback.
3. Add positive actual-close controls for an absent final `task_claims` store
   beneath verified direct `agents/runtime` directories and for a direct empty
   store. Only this final-component absence is compatible.
4. Retain complete `lstat()` metadata and reject Windows name-surrogate
   reparse points through Python 3.10-compatible
   `st_file_attributes`/`st_reparse_tag` checks; do not rely on the Python
   3.12-only `Path.is_junction()` API.
5. Treat a missing `agents` or `agents/runtime` component as store-integrity
   failure. Consumer templates already create the direct runtime parent; the
   final `task_claims` directory may legitimately remain absent until the
   first claim.
6. Replace silent `Path.glob()` enumeration with an operation whose `OSError`
   is observable and maps to `active-claim-store-integrity-invalid`.
7. Reject entry aliases before resolution where possible and map
   `RuntimeError`, `FileNotFoundError`, and `OSError` to the existing bounded
   per-entry integrity finding.
8. Preserve source/template byte parity, regenerate the host lock, and replay
   every earlier strict-authority regression and compatibility control.
9. Run the complete closure/Compound consumers, registered unit verification,
   full Runtime suite, asset/mirror/lock gates, Compound integrity, work schema,
   and owner governance on one exact candidate.
10. Create fresh Verify evidence and one new append-only Compound linking both
    work IDs, all four signatures, and the new prevention matrix. Then require
    fresh W4a, distinct W4b, and fresh skeptic approval.

## Scope amendment

Implementation stays bounded to:

- `scripts/closure_gate.py`;
- `src/agent_runtime/templates/project/scripts/closure_gate.py`;
- `tests/test_closure_gate.py` and `tests/test_compound_records.py`;
- `agents/project/TEMPLATE-MIRROR-CONTRACT.json` only if generated metadata
  changes; and
- `tests/fixtures/host/agent_runtime.lock.json`.

Task, unit, claim, handoff, log, review, Verify, Compound, and generated index
files remain lifecycle evidence. Scribe archive migration is a separate P1
task; this replan does not authorize that work, consumer changes, or release.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer write, version, tag, publication,
push, deployment, or external release action is authorized.
