---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-ancestor-identity-provenance-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
signal: revise
priority: P1
created_at: 2026-08-02T20:38:24+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/W4B-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
supersedes_ref: reviews/W4A-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
candidate_commit: d1300a921a5d22e496060a3a2867b3214c8afa83
candidate_tree: 41ef322db924a6e432571900aa0b0be424f3ad32
decision: reopen_current_unit
release_authorized: false
tags: [task-ar-654, t3-replan, atomic-publication, claim-identity, release-provenance, fail-closed]
---

# TASK-AR-654 ancestor, identity, and provenance T3 replan

## Decision

Accept the adverse independent W4b and reopen UNIT-TASK-AR-654-001. Candidate
`d1300a921a5d22e496060a3a2867b3214c8afa83`, tree
`41ef322db924a6e432571900aa0b0be424f3ad32`, is rejected with `P1: 2` and
`P2: 2`. The W4a pass is superseded for approval purposes. The active claim
remains held; skeptic review is stopped until a repaired exact candidate has a
new W4a and independent W4b.

## Reproduced defects and prior knowledge

### P1 — existing direct parent hides a symlinked ancestor

All four public POSIX atomic writers followed a symlink above an already
existing lexical direct parent and published outside the intended authority
tree. This is a recurrence of the already registered signature
`defect:atomic-publication-accepts-aliased-parent-compon:e89f4bf8d6bd13c4`.
Exact canonical search returned the current TASK-AR-654 Compound; that match
is prior knowledge, not proof that the candidate is mitigated. The record is
append-only and must not be edited.

### P1 — container-valued claim identity permits duplicate authority

A marker-activated witness with list/mapping core identities entered the
canonical snapshot. W0 stringified the malformed values and the actual
dispatcher created a second claim for the represented task. Normalize and
register this new stable signature:

`defect:container-valued-core-claim-identity-permits-dup:53594ebe603a7c1f`

Exact `--no-legacy` search returned no canonical Compound match.

### P2 — released overlay lacks terminal provenance

Role routing treated a `released` overlay without `released_at`,
`verified_by`, `verifier_role`, or `verification_evidence` as an idempotent
match. This is a recurrence of the registered signature
`defect:incomplete-role-overlay-is-accepted-as-idempoten:88dc7419f9159bb4`.
Exact canonical search returned the current TASK-AR-654 Compound as prior
knowledge.

### P2 — supplemental W4a counts are not durable evidence

The superseded W4a cited three supplemental counts without a named command,
reviewer identity, or committed evidence artifact. Do not rewrite that review.
The repaired W4a must cite only the fresh `work verify`, committed review
artifacts, and exact independently reproducible commands. Supplemental counts
without durable provenance must be omitted.

## Bounded RED-first repair

1. Add four actual publication regressions under `tests/test_atomic_io.py` for
   an existing direct parent beneath a symlinked ancestor. RED must prove
   publication currently reaches the outside target. Each repaired writer
   must refuse before staging, leave the outside target unchanged or absent,
   and leave no staging residue.
2. Make the POSIX publisher validate every lexical directory component from
   the trusted root to the direct parent with directory-relative no-follow
   handles. Do not weaken no-clobber identity capture or Windows reparse
   rejection. Mirror `atomic_io.py` byte-for-byte in the consumer template.
3. Add claim-store, actual W0/status, and actual dispatcher-create RED cases
   for present list, mapping, boolean, numeric, null, and blank core identity
   values. Canonical snapshot admission must reject malformed required
   identities before any consumer stringification, duplicate check, marker
   activation, projection, or second claim publication. Preserve explicitly
   supported legacy omissions only where the existing contract allows them.
4. Mirror the shared claim reader across all three copies and retain source/
   template parity for every affected dispatcher, work, and closure consumer.
5. Add a role-routing RED case for a terminal released overlay missing any one
   of its four provenance fields. Existing incomplete terminal authority must
   be rejected, never treated as idempotent or silently repaired. Preserve
   valid complete released overlays and mirror the runtime template.
6. Run focused matrices, integrated claim-authority tests, full Runtime suite,
   template mirror, host lock, Compound/evidence indexes, work schema,
   parallel/state/attribution gates, and a fresh registered `work verify`.
7. After all prevention is green, create one new append-only Compound linked
   to both work IDs. It must carry the two recurrent signatures and the new
   container-identity signature, cite this W4b/replan, and link the actual RED
   regressions plus fresh Verify. Earlier Compound files remain immutable.
8. Produce a new exact-commit W4a that supersedes the prior W4a, then request a
   distinct no-shared-context W4b. Only after W4b finds no current-scope P1 may
   a separate skeptic review run.

## Scope and release boundary

This repair remains inside TASK-AR-654 because it corrects claims made by the
current no-clobber transaction candidate and its linked Compound. It does not
absorb TASK-AR-655 negative lease/grace bounds, TASK-AR-657 verifier approval
authenticity, TASK-AR-651 portable release cascade/package gates, or the
archive-aware Scribe cleanup. Native Windows Python 3.10/3.11/3.12 execution
also remains pending.

No claim release, closeout, integration, consumer pilot mutation, CI dispatch,
versioning, publication, deployment, push, or external release is authorized.
