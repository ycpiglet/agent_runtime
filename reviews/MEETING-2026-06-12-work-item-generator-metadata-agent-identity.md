---
type: meeting
id: MEETING-2026-06-12-work-item-generator-metadata-agent-identity
audience: owner
status: pass
signal: pass
score: 92
priority: High
tags: [work-items, metadata, agent-identity, task-ar-370, owner-claude-intake]
---

# Work Item Generator, Metadata, And Agent Identity Intake

## Bottom Line

- Summary: recorded the Owner/Claude conversation from `text_for_goal.txt` and split it into executable slices instead of attempting one broad rewrite.
- Current slice: `TASK-AR-370` implements the measurable ID-reservation part of the Work Item generator plan.
- Boundary: `WORK-SCHEMA.yml`, full `work` CLI, AI split/criteria/assign tools, agent spawn records, and analytics Explorer remain follow-up work items, not hidden scope inside `TASK-AR-370`.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| Source dialogue captured | pass | `text_for_goal.txt` read from the main checkout |
| Existing assets reused | pass | `task_identity.py`, `work_item_classifier.py`, `task_unit_readiness_gate.py`, `PARALLEL_AGENT_WORKTREE_PROTOCOL.md` |
| Measurable first slice selected | pass | `TASK-AR-370` acceptance: reservation collision, stale reservation gate, reservation fulfillment |
| C-mode boundary preserved | pass | AI split/criteria/assign remain proposal-gated future work |

## Insight

- The right umbrella term is `Work Item`; the canonical execution hierarchy stays `initiative -> taskset -> task -> unit`.
- The durable value is a shared envelope schema, not the label alone: identity, provenance, routing, verification, relationships, governance, and analytics fields should be declared once and consumed by generators, gates, viewers, and stats.
- Agent skills are class-like definitions; live agents need instance-level identity. Existing claim fields already expose `agent_instance_id`, `display_name`, `callsite_id`, and `pane_id`, but the repo still needs a stronger spawn-record and attribution contract.
- Derived values such as progress, age, and roll-up status should be computed from records, not manually stored as authoritative state.

## Decision

- Decision: implement deterministic scaffolding before AI generation. The first concrete implementation is `task_identity.py reserve-id` plus reservation-aware `create`.
- Decision: use a JSON ledger at `agents/project/work-items/TASK-ID-RESERVATIONS.json` for display-ID reservations, guarded by a local lock and checked by `task_identity.py check`.
- Decision: a task created from a reservation must fulfill that reservation with `fulfilled_by`, `fulfilled_task_id`, `fulfilled_task_uid`, and `fulfilled_at`.
- Decision: future AI tools (`work split`, `work criteria`, `work assign`) must produce proposals and pass readiness/verification gates before applying files.
- Decision: future agent attribution must require instance identity for actor fields; role-only attribution is a watch/block signal.

## Measurable Evaluation

| Requirement | Measurement |
| --- | --- |
| Duplicate live reservations are rejected | `pytest tests/test_task_identity.py -q` includes duplicate reservation test |
| Stale active reservations are visible to gates | `pytest tests/test_task_identity.py -q` includes stale reservation check |
| Reserved task creation fulfills the reservation | `pytest tests/test_task_identity.py -q` checks ledger status and task frontmatter |
| Existing task identity and classifier gates remain valid | `python scripts/task_identity.py check --check` and `python scripts/work_item_classifier.py --check` |
| Planning discussion is durable | `python scripts/evidence_index_generator.py --write` then `--check` |

## Action Board

| Slice | Status | Scope | Verification |
| --- | --- | --- | --- |
| `TASK-AR-370` reservation ledger | implemented in this branch | `reserve-id`, reservation-aware `create`, reservation gate findings | `tests/test_task_identity.py` |
| Work Item envelope schema | follow-up | `agents/project/WORK-SCHEMA.yml`, required/optional matrix, unknown-field policy | schema/gate tests |
| `work` CLI scaffold | follow-up | `new`, `close`, `now`, `tree`, `stats`, create from schema | CLI tests and generated fixtures |
| AI planner tools | follow-up | `split`, `criteria`, `assign` through B-mode proposal gate | proposal/readiness tests |
| Agent identity contract | follow-up | spawn records, role/instance/callsign split, attribution gate | claim/pane/A2A fixture tests |
| Analytics Explorer | follow-up | dimensions and measures for work/agent stats plus export | state/UI tests |

## Risks / Blockers

- Risk: until the broader registration CLI lands, humans can still bypass the reservation path by hand-editing task files.
- Risk: a single ledger file is acceptable for the current local repo workflow, but a future remote/multi-host allocator should use a stronger shared store or merge-safe append protocol.
- Blocker: none for `TASK-AR-370`; broader Work Item/agent identity work should be registered as separate tasks before implementation.

## Next

- Finish `TASK-AR-370` verification and closeout.
- Route the remaining conversation items into `TASK-AR-372` or a new Work Item schema/agent identity taskset, rather than expanding this task after it passes.
