---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-596-001
work_uid: 5af29d84-753d-4c83-9c58-596a001f8f2b
kind: unit
parent_id: TASK-AR-596
unit_id: UNIT-TASK-AR-596-001
task_id: TASK-AR-596
task_set_id: TASKSET-AR-LLM-WIKI
initiative_id: INIT-AR-LLM-WIKI
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: qa
created_at: 2026-06-19T01:12:00+09:00
updated_at: 2026-06-19T01:12:00+09:00
origin_type: owner_request
origin_ref: chat:2026-06-19-doc-scribe-wiki-graph-cleanup
created_by: codex-planner
summary: Extend wiki corpus lint checks
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - closeout_blocked
context: TASK-AR-596 is the final LLM-Wiki QA and closeout task, but TASK-AR-594 and TASK-AR-595 still own UI-facing mini-graph/nav work. This unit covers the non-overlapping lint extension first so expanded corpus kinds have deterministic quality checks before final taskset closeout.
inputs:
  - docs/superpowers/specs/2026-06-17-llm-wiki-design.md
  - docs/superpowers/specs/2026-06-14-knowledge-lint.md
  - docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md
  - scripts/knowledge_graph.py
  - scripts/knowledge_lint.py
target_files:
  - scripts/knowledge_lint.py
  - tests/test_knowledge_lint.py
  - scripts/knowledge_lint_gate.py
  - tests/test_knowledge_lint_gate.py
  - src/agent_runtime/templates/project/scripts/knowledge_lint.py
  - docs/superpowers/specs/2026-06-14-knowledge-lint.md
  - agents/lead_engineer/tasks/TASK-AR-596.md
  - agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md
scope: Add deterministic lint checks for the expanded wiki/corpus node kinds and relationship contracts. Do not edit UI console assets, mini-graph rendering, navigation, or close TASKSET-AR-LLM-WIKI while TASK-AR-594 and TASK-AR-595 remain open.
acceptance:
  - Lint reports block findings for expanded-corpus nodes missing required metadata such as source paths.
  - Lint reports block findings when doc/module/config/schema/asset nodes lack the relationship types required by their kind.
  - Observational false positives remain bounded so existing clean graphs still pass without new block findings.
  - Root and generated-host template lint contracts stay aligned.
verification:
  - python -m pytest tests/test_knowledge_lint.py tests/test_knowledge_lint_gate.py -q
  - python scripts/knowledge_lint.py --root . --git-limit 0 check --json
  - python scripts/knowledge_graph.py check --json --git-limit 0
handoff: Report lint contract changes, regression commands, and whether TASK-AR-596 still needs later E2E/W4b/taskset closeout after TASK-AR-594 and TASK-AR-595.
stop_condition: Stop after expanded corpus lint checks are implemented, focused tests pass, template parity is updated, and follow-up closeout status is explicit.
---

# UNIT-TASK-AR-596-001 - Extend wiki corpus lint checks

## Context

TASK-AR-596 is the final LLM-Wiki QA and closeout task, but two earlier UI-facing
units are still open. This unit isolates the non-overlapping quality gate work:
the expanded corpus already emits `doc`, `module`, `file`, `config`, `schema`,
and `asset` nodes, so lint should validate their minimum metadata and
relationship contracts before the taskset can be closed.

## Inputs

- docs/superpowers/specs/2026-06-17-llm-wiki-design.md
- docs/superpowers/specs/2026-06-14-knowledge-lint.md
- docs/superpowers/plans/2026-06-17-llm-wiki-unit1-corpus-expansion.md
- scripts/knowledge_graph.py
- scripts/knowledge_lint.py

## Target Files

- scripts/knowledge_lint.py
- tests/test_knowledge_lint.py
- scripts/knowledge_lint_gate.py
- tests/test_knowledge_lint_gate.py
- src/agent_runtime/templates/project/scripts/knowledge_lint.py
- docs/superpowers/specs/2026-06-14-knowledge-lint.md
- agents/lead_engineer/tasks/TASK-AR-596.md
- agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md

## Scope

Add deterministic lint checks for the expanded wiki/corpus node kinds and
relationship contracts. Do not edit UI console assets, mini-graph rendering,
navigation, or close `TASKSET-AR-LLM-WIKI` while `TASK-AR-594` and
`TASK-AR-595` remain open.

## Steps

1. Define the minimum metadata and relationship contracts for the expanded
   corpus node kinds.
2. Extend `knowledge_lint` with bounded kind-specific checks and stable finding
   codes.
3. Add tests for missing paths, missing required relationships, and clean
   expanded-corpus nodes.
4. Mirror the lint contract into the generated host template copy.
5. Run focused graph/lint verification and record follow-up closeout status.

## Acceptance Criteria

- Lint reports block findings for expanded-corpus nodes missing required
  metadata such as source paths.
- Lint reports block findings when doc/module/config/schema/asset nodes lack the
  relationship types required by their kind.
- Observational false positives remain bounded so existing clean graphs still
  pass without new block findings.
- Root and generated-host template lint contracts stay aligned.

## Verification

- `python -m pytest tests/test_knowledge_lint.py tests/test_knowledge_lint_gate.py -q`
- `python scripts/knowledge_lint.py --root . --git-limit 0 check --json`
- `python scripts/knowledge_graph.py check --json --git-limit 0`

## Handoff

Report lint contract changes, regression commands, and whether `TASK-AR-596`
still needs later E2E/W4b/taskset closeout after `TASK-AR-594` and
`TASK-AR-595`.

## Stop Boundary

Stop after expanded corpus lint checks are implemented, focused tests pass,
template parity is updated, and follow-up closeout status is explicit.
