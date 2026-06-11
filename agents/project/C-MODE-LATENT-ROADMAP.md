# C-mode Latent Roadmap

## Purpose

C-mode is a latent option, not an active implementation path. The current RSI
operating system stays in B-mode: scan, propose, review, verify, and apply only
through an approved apply gate.

## Current Status

| Area | State | Evidence Needed |
| --- | --- | --- |
| Activation | blocked | repeated B-mode pass evidence and Owner policy approval |
| Auto-apply | blocked | low-risk reversible class, rollback evidence, and verifier pass history |
| Department runtime | latent option | A2A lifecycle proof, RBAC, council metrics, and live eval stability |
| Owner boundaries | Owner-gated | release, version, external, destructive, prod-data, cost-bearing, PR, and publish actions |

## Promotion Conditions

C-mode cannot activate from a single successful run. Revisit only when all are
true:

- at least three consecutive B-mode cycles pass with stable proposal_precision
  and no proposal churn increase;
- repeated B-mode pass evidence closes known failure casebook entries;
- every supported action class has rollback evidence and deterministic
  verification;
- council review has no unresolved block verdict;
- release/version steward and owner-doc/taskset gates pass;
- Owner policy explicitly allows the exact low-risk local action class.

## Allowed First Candidates

- generated view refresh;
- stale local link repair;
- proposal dedupe and supersession;
- watch-only reminder;
- low-risk plan hygiene with rollback evidence.

## Always Owner-Gated

Release, version, external, destructive, prod-data, cost-bearing, PR, publish,
dependency, secret, gate-weakening, and owner-only decisions stay Owner-gated.

## Rollback Evidence

Each candidate must record the changed files, exact verifier list, rollback
path, and post-rollback verification before it can be considered for C-mode.
