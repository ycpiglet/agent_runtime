---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-654
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: scope-amendment
status: accepted
signal: correction
priority: P1
created_at: 2026-08-02T23:04:00+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/W4B-2026-08-02-unit-task-ar-654-001-claim-transaction-final.md
replan_ref: reviews/REVIEW-2026-08-02-task-ar-654-ancestor-identity-provenance-t3-replan.md
historical_candidate_commit: d1300a921a5d22e496060a3a2867b3214c8afa83
historical_candidate_tree: 41ef322db924a6e432571900aa0b0be424f3ad32
release_authorized: false
tags: [task-ar-654, w4b, evidence-correction, atomic-publication, claim-identity, compatibility]
---

# TASK-AR-654 W4b evidence and contract correction

## Bottom line

The adverse W4b verdict remains valid, but two embedded examples in the final
report are not exact descriptions of the Runtime source surface. This record
preserves the committed W4b and T3 replan as immutable history while binding
the repair to the actual APIs, schema, and supported identity compatibility.
It does not convert the historical W4b into acceptance and does not authorize
release.

## Atomic publication surface

The W4b final report names `publish_bytes_owned_atomic` and
`publish_yaml_frontmatter_owned_atomic`; neither function exists in
`scripts/atomic_io.py`. The actual public surface affected through the shared
parent-opening primitive contains six functions:

- `write_text_atomic`
- `write_json_atomic`
- `publish_text_atomic`
- `publish_json_atomic`
- `publish_text_owned_atomic`
- `publish_json_owned_atomic`

The independent runtime-semantics slice directly reproduced the defect through
the four regular write/publish wrappers. The RED-first repair slice reproduced
it through the four publish and owned-publication wrappers. The durable
regression therefore covers the union: all six real public functions, with an
existing direct parent beneath a symlinked ancestor, and requires refusal,
unchanged outside state, and no staging residue.

The bounded repair deliberately adopts a POSIX root-to-leaf fail-closed
contract. Every lexical ancestor must be alias-free and openable as a directory
handle. Runtime claim, lease, role, dispatcher, reaper, stop-event, and task
identity paths are built below a previously canonicalized Runtime root, and
pytest canonicalizes its temporary base path, so those supported paths do not
retain the macOS `/var` alias. Direct generic calls with `/var`, `/var/run`, a
symlinked home prefix, or a non-openable ancestor must canonicalize the path
before calling the primitive. A wider `authority_root` API is not introduced
inside this bounded repair; generic arbitrary-path support would require a
separate compatibility contract and cross-platform design.

## Claim fixture and identity compatibility

The W4b report's illustrative JSON block uses
`agent-runtime-claim/v1`. The actual claim-store schema is
`agent-runtime-task-claim/v1`, and the durable RED/GREEN marker, canonical
snapshot, W0/status, and real dispatcher-create regressions use that exact
schema. Their pre-repair RED result independently preserves the P1 finding:
container-valued core identity entered active authority and allowed mutation
toward a second claim.

The repaired shared reader applies this exact compatibility boundary:

- an active claim requires a nonblank, trimmed string `task_id` of at most 160
  characters;
- any present `task_id`, `task_set_id`, or `agent_instance_id` must otherwise
  be a nonblank, trimmed string of at most 160 characters;
- exact `task_set_id: ""` remains the dispatcher's legacy absent sentinel;
- omission of `task_set_id` or `agent_instance_id` remains supported; and
- an inactive legacy claim may omit `task_id`.

No consumer may stringify a list, mapping, boolean, number, or null core
identity after the canonical reader has accepted it.

## W4a evidence rule

The superseded W4a's supplemental `1591`, `968`, and `363` pass counts are not
promoted into durable evidence because that review does not bind them to named
commands, reviewer identity, and a committed evidence artifact. The repaired
candidate's fresh W4a must cite only its registered Verify artifact and named,
reproducible committed review evidence. The earlier W4a is not rewritten.

## Disposition

- Historical W4b: `REVISE`, acceptance false.
- Historical W4a: superseded for approval purposes.
- Current unit and claim: remain open and claimed pending implementation
  commit, fresh Verify, append-only Compound, exact-candidate W4a, distinct
  W4b, and—only if W4b has no P1 finding—a separate skeptic review.
- Native Windows Python 3.10/3.11/3.12 execution and adjacent TASK-AR-655,
  TASK-AR-657, TASK-AR-651, and Scribe blockers remain outside this repair.

No claim release, closeout, consumer mutation, CI dispatch, push, tag,
versioning, package publication, deployment, or external release is
authorized.
