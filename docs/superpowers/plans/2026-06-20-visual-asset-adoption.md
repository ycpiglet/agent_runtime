---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
work_uid: 1d387882-b28f-4d68-b24f-1795c3833aca
kind: taskset
id: TASKSET-AR-VISUAL-ASSET-ADOPTION
parent_id: INIT-AR-VISUAL-ASSET-ADOPTION
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
status: active
owner: lead-engineer
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-20T01:04:15+09:00
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Implement the research-backed visual upgrade: DiceBear CC0 seeded agent avatars with role accents; Dagre+d3-force graph rendering for dependency/state-machine/live-agent views; Geist OFL fonts; Lucide icons; unDraw state illustrations; Radix+Carbon data-viz palette tokens and sparklines. Permissive-only, no-build, self-hosted, token-driven, landed experimental.
---

# Visual Asset Adoption

## Goal

- Implement the research-backed visual upgrade: DiceBear CC0 seeded agent avatars with role accents; Dagre+d3-force graph rendering for dependency/state-machine/live-agent views; Geist OFL fonts; Lucide icons; unDraw state illustrations; Radix+Carbon data-viz palette tokens and sparklines. Permissive-only, no-build, self-hosted, token-driven, landed experimental.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-587` | Agent avatar identity system (DiceBear CC0 + role accent) |
| `TASK-AR-588` | Dependency / state-machine / live-agent graph upgrade (Dagre + d3-force) |
| `TASK-AR-589` | Typography + icon foundation (Geist OFL fonts + Lucide icons) |
| `TASK-AR-590` | State illustrations + data-viz palette + sparklines |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-587-001` | `TASK-AR-587` | Vendor + self-host a CC0 DiceBear style and add patternAgentAvatar |
| `UNIT-TASK-AR-587-002` | `TASK-AR-587` | Deterministic role accent + console placement |
| `UNIT-TASK-AR-588-001` | `TASK-AR-588` | Vendor Dagre + layered DAG renderer for dependency/state-machine |
| `UNIT-TASK-AR-588-002` | `TASK-AR-588` | Vendor d3-force + live agent map renderer |
| `UNIT-TASK-AR-589-001` | `TASK-AR-589` | Self-host Geist + Geist Mono as font tokens |
| `UNIT-TASK-AR-589-002` | `TASK-AR-589` | Vendor Lucide icon set + componentIcon helper |
| `UNIT-TASK-AR-590-001` | `TASK-AR-590` | Recolorable unDraw state illustrations |
| `UNIT-TASK-AR-590-002` | `TASK-AR-590` | Data-viz palette tokens + componentSparkline |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
