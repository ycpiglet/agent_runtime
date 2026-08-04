---
title: TASK-AR-648 Skeptic Audit — Closeout Overlay Claim Contract
date: 2026-07-29
status: request_changes
signal: block
score: 62
verdict: REQUEST_CHANGES
task_id: TASK-AR-648
review_claim_id: CLAIM-REVIEW-TASK-AR-648-skeptic-closeout
verified_product_head: 5ae787d556908d923be46ebc9498bee628a3065b
verified_by: p0-example-classifier-task-ar-648-overlay-audit
verifier_role: independent-auditor
tags: [skeptic, overlay-claim, persistence, gate-contract, request-changes]
---

# TASK-AR-648 Skeptic Audit — Closeout Overlay Claim Contract

## Bottom Line

**REQUEST_CHANGES — parent consumer work must not proceed on this gate result.**

The product change at `5ae787d` correctly closes the staged-only authorized
claim gap, but the automatic high-risk closeout overlay it generated does not
meet the gate's active-claim or persistence contract. Releasing this synthetic
overlay claim is lifecycle cleanup only; it is **not** approval of parent
TASK-AR-648, its P0 fixes, consumer replay, release, or any external effect.

## Independent Results

- `python -m pytest tests/test_parallel_worktree_gate.py tests/test_task_claim_dispatcher.py -q`
  passed: **101 passed**.
- `git diff --check 5ae787d^ 5ae787d` passed.
- Source and template `parallel_worktree_gate.py` files are byte-identical.
- `python scripts/parallel_worktree_gate.py --check` returned non-zero with
  7 blocks and 4 watches. Six blocks are active-overlay omissions:
  `callsite_id`, `pane_id`, `phase`, `progress_pct`, `worktree_path`, and
  `branch`.
- The same overlay also blocks as
  `task-claim:claim-not-committed`: its JSON is untracked, absent from HEAD,
  and has no `persistence.mode` / `scm_commit_authorized` declaration.

## Contract Analysis

The new `HEAD` comparison is valid for the stated product defect: a staged
claim after a failed authorized commit is still reset+clean vulnerable. The
focused regression reproduces that condition, and the implementation checks
both `HEAD:<claim>` existence and worktree equality.

However, the auto-generated overlay is a real active claim according to the
same gate. It supplies a distinct synthetic task id and parent references,
and a repository scan found exactly one copy of its claim id; no duplicate
claim-id finding was observed. Its producer nevertheless omits the mandatory
active fields and chooses no persistence mode. This creates a self-blocking
release closeout path.

Adding `scm_commit` authorization without committing would remain a block.
Adding explicit `working_tree` plus `scm_commit_authorized: false` would lower
the persistence finding to a watch, but cannot repair the six required active
fields. The producer and gate therefore need one coherent overlay contract:
either emit the complete active-claim envelope with intentional working-tree
persistence, or explicitly exempt a narrowly defined overlay record in both
validation and persistence logic. The latter must retain duplicate and parent
linkage checks.

## Required Before Consumer Progress

1. Define and test the overlay producer's full active-claim envelope.
2. Define its intentional persistence behavior without weakening the
   staged-only authorized-claim protection.
3. Add a gate regression using an automatically produced high-risk overlay,
   then verify no block remains before treating parent work as releasable.

## Scope / External Effects

This audit changed no product or test code and performed no commit, push,
publish, deploy, credential access, network delivery, or product-content
mutation. The requested overlay release is recorded separately as claim
lifecycle cleanup and does not alter this verdict.
