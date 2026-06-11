# Project Management Operating System Plan

> **For agentic workers:** implement this plan task-by-task. Do not skip the
> hierarchy contract or unit readiness gate; they are the core value.

**Goal:** Register and implement `TASKSET-AR-PM-OPERATING-SYSTEM`, a durable
project management layer that lets high-tier planner agents decompose work into
small, explicit units that lower-cost worker models can execute safely.

**Architecture:** Backlog remains metadata. Detailed intent lives in linked
project, taskset, task, and unit specs. Dispatcher, gates, board rendering, and
templates enforce readiness before low-tier execution.

**Task Set:** `TASKSET-AR-PM-OPERATING-SYSTEM`

## File Structure

- Existing: `agents/project/PROJECT-MANAGEMENT-CONTRACT.md`
- Existing: `reviews/RESEARCH-2026-06-11-agent-runtime-project-management-methods.md`
- Create/modify during implementation:
  - `agents/lead_engineer/tasks/units/README.md`
  - `schemas/task-unit.schema.json`
  - `scripts/task_unit_readiness_gate.py`
  - `scripts/model_routing.py` or existing routing surface
  - `scripts/taskset_dispatcher.py`
  - `scripts/backlog_board.py`
  - `tests/test_task_unit_readiness_gate.py`
  - `tests/test_model_routing.py`
  - template mirrors under `src/agent_runtime/templates/project/`

## Registered Tasks

| Task | Title | Intent |
| --- | --- | --- |
| `TASK-AR-342` | Project hierarchy SSoT and horizon metadata | Make project/taskset/task/unit plus short/mid/long horizon explicit |
| `TASK-AR-343` | Unit spec template and worker-ready definition | Create the detailed unit document shape lower-cost models can execute |
| `TASK-AR-344` | Unit readiness gate | Block worker dispatch when context, files, scope, acceptance, verification, or handoff are missing |
| `TASK-AR-345` | Model-tier routing metadata | Add planner/worker/reviewer tiers and escalation triggers to task/unit records |
| `TASK-AR-346` | Dispatcher unit claims and scope stop | Claim a unit, record model tier, and stop after taskset/unit completion |
| `TASK-AR-347` | WIP and flow policy | Add Kanban-style WIP controls, flow metrics, and stale-unit signals |
| `TASK-AR-348` | Board and project views | Render project/taskset/task/unit hierarchy without stuffing details into backlog |
| `TASK-AR-349` | Template propagation | Mirror PM contract, templates, schemas, and gates into generated host projects |
| `TASK-AR-350` | Verification and closeout | Add wrapper checks and Owner-facing closeout evidence |

## Phase 1: Contract And Schema

- [ ] Add `project_id`, `horizon`, `planner_model_tier`, `worker_model_tier`,
  `reviewer_model_tier`, `unit_spec`, and `escalation_triggers` conventions.
- [ ] Define `task-unit.schema.json` with required context, target files, scope,
  acceptance, verification, and handoff fields.
- [ ] Add `agents/lead_engineer/tasks/units/README.md` with examples.

## Phase 2: Readiness Enforcement

- [ ] Implement `scripts/task_unit_readiness_gate.py`.
- [ ] The gate must fail when a planned or in-progress worker task lacks a
  ready unit spec or equivalent detailed task section.
- [ ] Wire the gate into Owner governance after initial focused tests pass.

## Phase 3: Model Routing

- [ ] Add model-tier fields to task/unit parsing and dispatcher claim output.
- [ ] Default routine precise units to lower-cost workers.
- [ ] Escalate to higher-tier planner/reviewer when the task is ambiguous,
  high-risk, cross-cutting, security-sensitive, external, or repeatedly failing.

## Phase 4: Dispatch, WIP, And Scope Stop

- [ ] Extend dispatcher claims with `project_id`, `unit_id`, model tier, WIP
  slot, and completion stop condition.
- [ ] Prevent a worker from continuing into adjacent tasksets after completing
  the assigned unit or taskset.
- [ ] Add WIP count and work-item-age reporting to board output.

## Phase 5: Views, Templates, Verification

- [ ] Render hierarchy summaries in `BACKLOG-BOARD.md`.
- [ ] Mirror templates into `src/agent_runtime/templates/project/`.
- [ ] Add `scripts/verify_pm_operating_system_taskset.py`.
- [ ] Run focused tests, owner doc format gate, task identity gate, and named
  taskset gate before closeout.

## Done Criteria

- A low-tier worker can open a unit spec and complete the assignment without
  reconstructing planner intent from chat.
- The dispatcher and gates reject worker execution when details are missing.
- The board shows the hierarchy and progress without becoming the full spec.
- Completion evidence proves the taskset stopped at its own boundary.

