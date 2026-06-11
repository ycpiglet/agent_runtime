---
name: failure-to-regression
version: 1.0.0
description: Use when a repeated failure, compound case, review finding, or Owner correction should become a regression fixture, gate, task proposal, or accepted watch state.
triggers:
  - repeated failure
  - compound
  - regression
  - failure casebook
dependencies:
  - agents/project/casebooks/README.md
  - agents/project/casebooks/failure-and-compound-casebook.md
  - agents/project/evidence/inbox/README.md
  - agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md
registry_id: failure-to-regression
---

# Failure To Regression

## Required Sequence

1. Add or update a casebook entry in `agents/project/casebooks/failure-and-compound-casebook.md`.
2. Record `dedupe_key`, `symptom`, `trigger`, `owner_boundary`, `affected_gate`, `recurrence_count`, and source refs.
3. Add a reproduction command, or write an explicit non-repro reason when deterministic reproduction is unavailable.
4. Route the case to one of: regression fixture, executable gate, task proposal, skill proposal, or explicit accepted watch state.
5. If the case touches Owner-only, external, destructive, release/version, production-data, secret, or cost-bearing boundaries, stop at a proposal.

## Completion Criteria

- The case can be searched by symptom, trigger, owner boundary, or affected gate.
- `needs enforcement` is not left as a loose note; it becomes a gate, fixture, task proposal, or accepted watch.
- The proposal path cites `agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md`.

