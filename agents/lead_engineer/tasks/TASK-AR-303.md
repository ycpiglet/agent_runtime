---
id: TASK-AR-303
display_id: TASK-AR-303
task_uid: 5cccc334-b5c9-465a-a083-2712624cb640
registered_at: 2026-06-11T12:10:00+09:00
created_at: 2026-06-11T12:10:00+09:00
updated_at: 2026-06-11T12:10:00+09:00
title: Preserve latent C-mode and bounded apply gate roadmap
status: planned
priority: P1
difficulty: M
est_hours: 2
est_tokens: 900
owner: risk-and-safety
task_set_id: TASKSET-AR-RSI-OPERATING-SYSTEM
tags:
  - rsi
  - c-mode
  - apply-gate
  - guardrails
---

# TASK-AR-303 - Preserve latent C-mode and bounded apply gate roadmap

## Goal

- Keep C-mode as a potential long-term department runtime without promoting it before B-mode quality and safety evidence exists.

## Scope

- Document C-mode as a latent option, not an active implementation path.
- Define the apply gate from proposal to canonical mutation with risk tiers, repeated-pass thresholds, kill switch, owner approval boundaries, and rollback evidence.
- Preserve the existing rule that release, version, external, destructive, prod-data, and cost-bearing actions remain Owner-gated.
- Define what evidence would justify revisiting the full agent-department runtime later.

## Acceptance Criteria

- C-mode cannot activate from a single successful run.
- Auto-apply remains limited to low-risk, reversible, local-only changes after repeated B-mode pass evidence.
- The roadmap states what must be true before option C moves from latent to planned.
- The C-mode section is visible from the Owner brief and next-session pointer.

## Evidence Targets

- `agents/project/C-MODE-LATENT-ROADMAP.md`
- `agents/project/C-MODE-PROMOTION-CHECKLIST.md`
- `agents/project/PLANNING-GUARDRAILS.yml`

