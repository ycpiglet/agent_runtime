---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-02-task-ar-654-canonical-authority-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-08-02T11:14:53+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/AUDIT-2026-08-02-task-ar-654-canonical-authority-probe.md
tags: [task-ar-654, t3, canonical-authority, symlink, identity, json, fail-closed]
---

# TASK-AR-654 canonical authority T3 replan

## Why the candidate is reopened

Candidate `1b0db7d8555e12e781d7ddfa0850037a875f05fd` passed W4a,
`1105` registered tests, and `3948` full-suite tests. Independent review still
found six P1 boundary gaps. Five were reproduced in a temporary exact-candidate
archive by the claim-context auditor. The W4b reviewer independently found a
deep-JSON exception that the actual Stop wrapper silently converts into no
decision before its review session was interrupted.

The W4a remains append-only evidence of what passed, but its zero-finding
verdict is superseded for release purposes. The active repair claim must not be
released.

## Prior-knowledge search

Exact canonical Compound search returned no match for the six new signatures:

- `defect:released-claim-scalar-authority-shape-accepted:12a9795c8b117218`;
- `defect:claim-ref-symlink-escapes-canonical-claim-store:09782265a699dc29`;
- `defect:unit-spec-symlink-alias-accepted-as-canonical-id:8f8644f6caac78e7`;
- `defect:relative-worktree-falls-back-to-linked-root-shad:a9421e5faf4c59df`;
- `defect:work-frontmatter-identity-contradicts-canonical:bb011854a4cc3ca2`;
- `defect:deep-accepted-watch-json-recursion-fail-open:5d494f605a860dac`.

No new Compound will be created until durable prevention tests and fresh
machine verification exist. Existing append-only records remain unchanged.

## Repair decision

1. Add RED tests for all six findings before implementation, including actual
   `work close` and Stop consumers plus byte/state non-mutation checks.
2. Share the exact non-empty-string-list authority shape contract between
   active and explicitly linked released claims; do not coerce scalar
   authority into trusted lists.
3. Require a claim ref to resolve to its exact canonical regular file under
   `agents/runtime/task_claims`; reject symlink aliases and resolved targets
   outside that store even when they remain inside the repository.
4. Require claim `unit_spec` to equal the canonical repository-relative unit
   path and reject symlink aliases or noncanonical path components.
5. Resolve relative worktree paths against the Git primary checkout only.
   Never fall back to a linked-root shadow when the primary target is absent.
6. Derive and validate task/unit identity from the canonical filesystem path,
   then require frontmatter and claim identity to agree with it. Contradictory
   metadata must fail closed without leaking its authority.
7. Bound accepted-watch JSON structural recursion in addition to raw bytes.
   Convert `RecursionError` into a deterministic finding in source and package
   helpers.
8. Make the actual Stop wrapper emit an explicit block decision on an
   unexpected closure-gate exception; empty output must never mean approval.
9. Preserve source/template byte parity, regenerate the host lock, replay all
   prior accepted-watch and claim tests, and run both registered and full
   suites on one exact candidate.
10. After fresh Verify, create a new append-only current-work Compound carrying
    both work IDs and all six new signatures. Then require new W4a, complete
    independent W4b, and fresh skeptic approval.

## Scope amendment

The existing unit already owns `closure_gate.py`, `work.py`, Compound helpers,
their templates, regressions, mirror contract, and host lock. Add only the
actual Stop wrapper pair to the implementation footprint:

- `scripts/stop_hook_closure_gate.py`;
- `src/agent_runtime/templates/project/scripts/stop_hook_closure_gate.py`.

Review, claim, index, and generated projection files remain lifecycle evidence.
This does not authorize consumer-repository changes, Scribe cleanup, external
release, or changes to ordinary non-repeated closure policy.

## Safety boundary

No credential, provider, live network, package installation, broker, order,
database migration, notification, consumer write, version, tag, publication,
push, deploy, or release action is authorized. Keep the claim held until the
entire repaired candidate passes fresh machine and human gates.
