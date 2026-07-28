---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
work_uid: 7ed39415-692e-4039-99e8-d46d811566c6
kind: taskset
id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
parent_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
status: active
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-28T16:36:01+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Deliver brownfield profiles, lifecycle truth, consumer-complete assets, continuity hooks, knowledge and model-economy enforcement, then validate two pilots and one upgrade rehearsal.
---

# v0.8 Adoption and Enforcement

## Goal

- Deliver brownfield profiles, lifecycle truth, consumer-complete assets, continuity hooks, knowledge and model-economy enforcement, then validate two pilots and one upgrade rehearsal.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-639` | Restore lifecycle truth and Work CLI producer-consumer parity |
| `TASK-AR-640` | Introduce profile and ownership-aware host configuration |
| `TASK-AR-641` | Build brownfield adopt planning and generated-tree filtering |
| `TASK-AR-642` | Make sync ownership-aware and explicitly reconcilable |
| `TASK-AR-643` | Enforce consumer template and skill dependency closure |
| `TASK-AR-644` | Provide cross-platform start, compact, and resume continuity hooks |
| `TASK-AR-645` | Make compound and scribe task-linked and host-configurable |
| `TASK-AR-646` | Make model routing economically effective and auditable |
| `TASK-AR-647` | Adopt native Allimbot events and security-service guardrails |
| `TASK-AR-648` | Run the Bean Wiki web-content pilot |
| `TASK-AR-649` | Run the Allimbot security-service pilot |
| `TASK-AR-650` | Rehearse Autofolio v0.6 to v0.8 migration |
| `TASK-AR-651` | Prepare v0.8.0 release candidate from pilot evidence |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-639-001` | `TASK-AR-639` | Align work registration output with verify and close consumers |
| `UNIT-TASK-AR-639-002` | `TASK-AR-639` | Block task-claim-projection split-brain and support explicit recovery |
| `UNIT-TASK-AR-640-001` | `TASK-AR-640` | Add backward-compatible profile and ownership config schema |
| `UNIT-TASK-AR-641-001` | `TASK-AR-641` | Implement read-only brownfield adoption planner |
| `UNIT-TASK-AR-642-001` | `TASK-AR-642` | Implement ownership manifest and sync reconcile |
| `UNIT-TASK-AR-643-001` | `TASK-AR-643` | Add profile-aware asset dependency closure and clean-host lifecycle smoke |
| `UNIT-TASK-AR-644-001` | `TASK-AR-644` | Replace platform-specific hook shims with verified Python entrypoints |
| `UNIT-TASK-AR-645-001` | `TASK-AR-645` | Introduce per-entry task-linked compound records and retrieval |
| `UNIT-TASK-AR-645-002` | `TASK-AR-645` | Add configurable scribe state adapters and generated projections |
| `UNIT-TASK-AR-646-001` | `TASK-AR-646` | Add effective-tier detection and dispatch cost ledger |
| `UNIT-TASK-AR-647-001` | `TASK-AR-647` | Replace legacy notifier with optional native ProjectEmitter adapter |
| `UNIT-TASK-AR-648-001` | `TASK-AR-648` | Adopt and exercise core plus web-content in Bean Wiki |
| `UNIT-TASK-AR-649-001` | `TASK-AR-649` | Adopt and exercise core plus security-service in Allimbot |
| `UNIT-TASK-AR-650-001` | `TASK-AR-650` | Execute and document the Autofolio migration rehearsal |
| `UNIT-TASK-AR-651-001` | `TASK-AR-651` | Assemble and verify the v0.8.0-rc.1 release candidate |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
