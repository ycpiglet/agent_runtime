---
name: rsi-planning-loop
description: Use when turning runtime evidence into bounded RSI planning proposals, or when continuing TASKSET-AR-RSI-OPERATING-SYSTEM work.
---

# RSI Planning Loop

Canonical skill path: `skills/rsi-planning-loop/SKILL.md`.

## First Reads

1. `agents/project/evidence/README.md`
2. `agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md`
3. `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md`
4. `agents/project/PLANNING-GUARDRAILS.yml`
5. `agents/project/C-MODE-LATENT-ROADMAP.md`

## Workflow

1. Normalize input into the evidence inbox.
2. Check the casebook and evaluation registry for existing dedupe keys.
3. Run the proposal engine with `python scripts/planning_loop.py scan --trigger manual --json`.
4. Create proposal records with `python scripts/planning_loop.py propose --trigger manual --json`.
5. Route medium/high/owner proposals through council review.
6. Use the apply gate only for approved, low-risk, reversible local proposals.

## Boundaries

- B-mode proposal-only behavior is the default.
- C-mode is a latent option, not active.
- Release, version, external, destructive, prod-data, cost-bearing, PR, publish,
  dependency, secret, gate-weakening, and Owner-only actions remain Owner-gated.
