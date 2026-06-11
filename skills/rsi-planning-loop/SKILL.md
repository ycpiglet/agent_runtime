---
name: rsi-planning-loop
version: 1.0.0
description: Use when converting evidence, evals, failures, A2A lifecycle records, or Owner corrections into bounded RSI planning proposals.
triggers:
  - RSI
  - evidence-to-proposal
  - planning proposal
  - proposal engine
dependencies:
  - agents/project/evidence/inbox/README.md
  - agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md
  - agents/project/DIVERSITY-COUNCIL-PROTOCOL.md
  - agents/project/C-MODE-LATENT-ROADMAP.md
  - scripts/planning_loop.py
  - scripts/a2a_lifecycle_gate.py
registry_id: rsi-planning-loop
---

# RSI Planning Loop

## Required Sequence

1. Read `agents/project/evidence/inbox/README.md` and normalize source evidence before proposing work.
2. Read `agents/project/EVIDENCE-TO-PROPOSAL-CONTRACT.md` before generating any task, plan, doc, eval, release, skill, or no-action proposal.
3. For high-impact or ambiguous work, route through `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md`.
4. For A2A evidence, run `python scripts/a2a_lifecycle_gate.py --check` and cite the lifecycle record instead of relying on prose.
5. Keep default mode as B-mode proposal-only. `agents/project/C-MODE-LATENT-ROADMAP.md` is a boundary, not approval.
6. Before closeout, run `python scripts/planning_loop.py gate --trigger manual --action scan --json` and the taskset verification wrapper when applicable.

## Boundaries

- Do not mutate canonical backlog, status, task, owner-doc, release, or version files from proposal generation alone.
- Owner-only, external, destructive, release/version, dependency, secret, production-data, cost-bearing, and gate-weakening actions remain Owner-gated.
- Rejected and no-action proposals are retained as precision evidence.

