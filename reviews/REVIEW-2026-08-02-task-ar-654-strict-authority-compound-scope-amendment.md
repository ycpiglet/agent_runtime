---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-strict-authority-compound-scope-amendment
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
created_at: 2026-08-02T13:25:26+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/REVIEW-2026-08-02-task-ar-654-falsy-authority-t3-replan.md
tags: [task-ar-654, compound, append-only, canonical-authority, verification]
---

# TASK-AR-654 strict-authority Compound scope amendment

## Decision

Register the following newly generated append-only record as current-work
prevention evidence for both TASK-AR-654 and UNIT-TASK-AR-654-001:

`agents/project/knowledge/compounds/records/COMPOUND-20260802-132433-bind-close-authority-to-direct-canonical-stores-5232981b9e7c.json`

The record was created only after the failure-first matrix and fresh machine
Verify passed. Its SHA-256 is
`ea8a74e8f1312749a549afb6c63c1becdba752dd713be37b1c61c1c76a61572a`.
The generated Compound index remains a derived lifecycle target.

## Exact authority carried

The record directly links both work IDs and exactly these four new stable
signatures:

- `defect:active-claim-symlink-escapes-canonical-claim-sto:3e1307eb404a2428`;
- `defect:falsy-non-string-unit-spec-falls-back-to-canonic:64fe169f1ab37824`;
- `defect:falsy-non-string-work-identity-treated-as-missin:2349f1fed3ad7660`;
- `defect:untrusted-unit-id-bypasses-canonical-claim-conte:9950c5dcb729c2d4`.

It cites the adverse final W4b and skeptic reports, the strict-authority T3
replan, and the immediately preceding canonical-authority Compound as source
history. Prevention is anchored to the actual closeout regressions and both
runtime authority scripts.

## Verification authority

Fresh machine evidence is
`reviews/VERIFY-2026-08-02-unit-task-ar-654-001-20260802132243.json`, SHA-256
`c8f9725f6363c136d14c668ea8024e52435ecc46e52a4f9afd2e7664f3dcc1a5`.
It records `1151 passed` in the registered suite plus passing Runtime asset,
template mirror, and host-lock gates. On implementation commit
`68943821`, the three closeout consumer files plus lock tests reported
`957 passed`, and the full Runtime suite reported `3994 passed, 3 skipped`
with the same four known UI deprecation warnings.

## Immutability and release boundary

The three earlier TASK-AR-654 Compound records are retained byte-for-byte and
are not renamed, edited, or deleted. This amendment authorizes only the new
record, its deterministic index projection, and lifecycle references. It does
not authorize claim release, integration, Scribe disposition, versioning,
publication, deployment, push, or external release. Fresh W4a, independent
W4b, and skeptic approval are still required.
