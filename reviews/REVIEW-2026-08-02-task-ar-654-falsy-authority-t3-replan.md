---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-falsy-authority-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T12:51:20+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_refs:
  - reviews/W4B-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md
  - reviews/SKEPTIC-2026-08-02-task-ar-654-canonical-authority-final.md
tags: [task-ar-654, t3, claim-store, unit-spec, canonical-identity, fail-closed]
---

# TASK-AR-654 strict canonical authority T3 replan

## Why the candidate is reopened again

Candidate `c63f7e78f93e3d551b61f78a0e3a4ad7fd8d78d9` (tree
`433ba54cbcdce0e9a61af102b611a3ec10eb4003`) passed the maintained closure
and Compound suites, fresh machine verification, and worker W4a. Distinct
independent review then found four remaining authority classes that actual
closure can accept before mutation:

1. an active claim entry, or the entire active claim store, may resolve through
   a symlink to a different location;
2. a unit claim's present `unit_spec` may be a falsey non-string and fall back
   to its `unit_id`;
3. present TASK/UNIT identity fields may be blank or containers and be treated
   as omitted; and
4. a conflicting UNIT `unit_id` may become the resolver key, skip the
   canonical active claim context, and close the canonical path under the
   wrong identity.

The earlier W4a remains append-only historical evidence, but both
`reviews/W4B-2026-08-02-unit-task-ar-654-001-canonical-authority-final.md`
and `reviews/SKEPTIC-2026-08-02-task-ar-654-canonical-authority-final.md`
supersede its release verdict. The unit verification state returns to failed
and the repair claim remains held.

## Prior-knowledge search

The stable signatures were generated from the four normalized descriptions
below. Exact canonical searches with `--no-legacy --json` each returned `[]`:

- `active claim symlink escapes canonical claim store` →
  `defect:active-claim-symlink-escapes-canonical-claim-sto:3e1307eb404a2428`;
- `falsy non string unit spec falls back to canonical unit` →
  `defect:falsy-non-string-unit-spec-falls-back-to-canonic:64fe169f1ab37824`;
- `falsy non string work identity treated as missing` →
  `defect:falsy-non-string-work-identity-treated-as-missin:2349f1fed3ad7660`;
- `untrusted unit id bypasses canonical claim context` →
  `defect:untrusted-unit-id-bypasses-canonical-claim-conte:9950c5dcb729c2d4`.

No Compound is created during replanning. All three existing append-only
TASK-AR-654 Compound records remain immutable. A new record may be created
only after durable prevention tests and fresh machine verification exist.

## Failure-first repair decision

1. Add actual `work close` regressions before implementation for an active
   claim-file symlink and an active claim-store symlink. Both must fail before
   unit, claim, or generated-view mutation.
2. Parameterize present unit-claim `unit_spec` values `null`, `false`, `0`,
   `[]`, `{}`, and blank string. Unit claims must require a non-empty string
   equal to the canonical repository-relative unit path.
3. Parameterize present TASK/UNIT identity aliases with blank/container
   values. Every present identity value must be an exact non-empty string
   matching path-derived identity; omission remains compatible only where the
   schema permits it.
4. Reproduce a canonical UNIT whose frontmatter declares another valid
   `unit_id`. Close authority must validate the path-derived identity before
   resolving claims and must use that canonical identity as its resolver key.
5. Validate the lexical claim-store directory and each active claim entry as
   direct canonical non-symlink objects whose strict resolved path equals the
   canonical path. Any mismatch produces one bounded active-claim integrity
   reason.
6. Preserve valid direct claims, canonical absolute and Git-primary-relative
   worktree bindings, valid task-level claim compatibility, source/template
   byte parity, and all earlier failure-first contracts.
7. Commit tests before implementation, then run the selected new matrix,
   both complete closure/Compound files, the registered focused suite, the
   full Runtime suite, asset/mirror/host-lock gates, and owner governance.
8. Create fresh machine Verify evidence and a new append-only current-work
   Compound linking both TASK and UNIT plus all four new signatures.
9. Require a new worker W4a, a distinct new-context W4b, and a fresh skeptic
   approval on one exact candidate. No earlier approval may release the claim.

## Scope amendment

The implementation footprint remains bounded to the already-owned authority
surfaces and their mirrors:

- `scripts/closure_gate.py`;
- `src/agent_runtime/templates/project/scripts/closure_gate.py`;
- `scripts/work.py`;
- `src/agent_runtime/templates/project/scripts/work.py`;
- `tests/test_closure_gate.py`;
- `tests/test_compound_records.py`;
- `agents/project/TEMPLATE-MIRROR-CONTRACT.json` if its generated digest is
  affected; and
- `tests/fixtures/host/agent_runtime.lock.json` after template changes.

Task, unit, claim, handoff, log, review, Verify, Compound, and generated index
files are lifecycle evidence. This replan does not authorize Scribe cleanup,
consumer-repository writes, ordinary closure-policy expansion, or any external
release action.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer write, version, tag, publication,
push, deployment, or external release action is authorized. Keep the claim
held until the repaired candidate completes the entire fresh verification and
independent-review sequence.
