---
schema_version: agent-runtime-review/v1
id: SKEPTIC-2026-08-02-task-ar-654-strict-authority-final
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
review_kind: skeptic
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 0}
created_at: 2026-08-02
reviewer: codex-task-ar-654-strict-authority-final-skeptic
candidate_commit: de01e01d1b8f966bb4414dd18c44bd45966f12d0
candidate_tree: 0d5581db71be18bde997f5aa5f11c8b622a4619f
release_authorized: false
tags: [task-ar-654, skeptic, strict-authority, claim-store, fail-closed]
---

# TASK-AR-654 strict-authority final skeptic review

## Verdict

`REVISE — P0: 0, P1: 1, P2: 0.`

Candidate `de01e01d1b8f966bb4414dd18c44bd45966f12d0`, tree
`0d5581db71be18bde997f5aa5f11c8b622a4619f`, is not ready for release. A
broken symlink in a parent component of the canonical active-claim store makes
the store disappear without an integrity finding. Actual `work close` then
loses claim-only repeated-failure authority, succeeds, and mutates closeout
state.

This was a bounded software-quality consistency review, not a security
assessment. All behavioral fixture state was created in a temporary directory.
The candidate worktree was not used as closeout fixture state. The worker W4a
and the full repair range `0ba8d85e..de01e01d` were reviewed as context only;
their recorded passes were not treated as approval evidence.

## P1 finding

### P1-1 — A broken claim-store parent alias fails open

`scripts/closure_gate.py::_active_claims` handles a missing
`agents/runtime/task_claims` path as an empty store. It reports an integrity
finding only when that final `task_claims` path itself is a symlink. If an
ancestor such as `agents/runtime` is a broken directory symlink, the descendant
claim-store path both fails `exists()` and is not itself a symlink, so the
function returns no claims and no finding.

The temporary actual-close fixture contained a canonical closeable unit and an
active claim whose only repeated-failure authority had no Compound. The
fixture then moved the populated `agents/runtime` directory aside and replaced
the canonical parent with a broken directory symlink. Exact result:

```text
returncode=0
stdout first line=work-close: closed
stderr=<empty>
unit_mutated=true
shadow_claim_mutated=false
```

The command also created or changed `BACKLOG-BOARD.md`, both work-item
classification projections, and `reviews/INDEX.md`. It should instead have
returned a bounded active-claim-store integrity error before any mutation.
The hidden active claim's repeated-failure signal and defect signature must not
be silently converted into an empty authority context merely because a parent
component is a broken alias.

The source/template copies of `closure_gate.py`, `work.py`, and
`stop_hook_closure_gate.py` were byte-identical when checked, so the same
fail-open behavior is present in the shipped template rather than being a
root-only divergence.

## Checks and results

| Check | Result |
| --- | --- |
| `git rev-parse HEAD` | `de01e01d1b8f966bb4414dd18c44bd45966f12d0` |
| `git rev-parse HEAD^{tree}` | `0d5581db71be18bde997f5aa5f11c8b622a4619f` |
| Full repair-range inspection, `0ba8d85e..de01e01d` | Reviewed; W4a treated only as worker context |
| `git diff --check 0ba8d85e..de01e01d` | Pass |
| Exact source/template parity for the three closeout scripts | Pass; all three pairs byte-identical |
| Temporary broken-parent active-claim-store actual close | **Fail**; close returned 0 and mutated unit/generated views |
| P0/P1/P2 | `0 / 1 / 0` |

Per the explicit stop-on-P1 instruction, no later adversarial combinations,
host-lock command, Verify/Compound/current-closure audit, or append-only-history
check was run after this failure. No repair was attempted.

## Release decision

**Do not release, merge, or close TASK-AR-654 on this candidate.** Keep the
claim held. Repair must detect broken symlinks in every canonical claim-store
parent component and reject before all actual-close mutations. A new exact
candidate then requires fresh machine verification, W4a, independent W4b, and
skeptic review; this report does not authorize integration, claim release,
versioning, publication, deployment, or external release.
