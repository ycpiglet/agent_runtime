---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-654-001
work_uid: 4b57e68f-5a15-4afe-adf2-492f583d3932
kind: unit
parent_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
task_id: TASK-AR-654
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-07-30T11:25:00+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Enforce repeated-failure Compound closure and ship its skill
horizon: unit
model_tier: worker_standard
escalation_triggers:
context: The claim dispatcher already searches canonical Compound records, but closure_gate accepts any one of compound, review, or retro. The failure-to-regression skill exists only in the Runtime repository and is absent from consumer templates.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - skills/failure-to-regression/SKILL.md
target_files:
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - tests/test_closure_gate.py
  - tests/test_compound_record.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_runtime_asset_usage.py
scope: Tighten only the repeated-failure lane and preserve ordinary review/retro closure compatibility.
acceptance:
  - Repeated failures cannot bypass Compound.
  - Compound dedupe and lookup remain deterministic.
  - The skill is discoverable in a freshly adopted host.
  - No legacy Compound log is rewritten.
verification:
  - python -m pytest tests/test_compound_record.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py -q
handoff: Attach failure-first closure evidence, skill packaging proof, backward compatibility, template parity, and independent W4b.
stop_condition: Stop before rewriting legacy Compound history or turning all reviews into mandatory Compound records.
---

# UNIT-TASK-AR-654-001 - Enforce repeated-failure Compound closure and ship its skill

## Context

The claim dispatcher already searches canonical Compound records, but closure_gate accepts any one of compound, review, or retro. The failure-to-regression skill exists only in the Runtime repository and is absent from consumer templates.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- src/agent_runtime/templates/project/scripts/compound_record.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- skills/failure-to-regression/SKILL.md

## Target Files

- src/agent_runtime/templates/project/scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/compound_record.py
- src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- tests/test_closure_gate.py
- tests/test_compound_record.py
- tests/test_task_claim_dispatcher.py
- tests/test_runtime_asset_usage.py

## Scope

Tighten only the repeated-failure lane and preserve ordinary review/retro closure compatibility.

## Steps

1. Add a negative where repeated_failure closes with review only.
2. Require a canonical linked Compound record and prevention destination.
3. Copy and register the failure-to-regression skill in the consumer template.
4. Verify ordinary non-repeated work remains compatible.

## Acceptance Criteria

- Repeated failures cannot bypass Compound.
- Compound dedupe and lookup remain deterministic.
- The skill is discoverable in a freshly adopted host.
- No legacy Compound log is rewritten.

## Verification

- `python -m pytest tests/test_compound_record.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py -q`

## Handoff

Attach failure-first closure evidence, skill packaging proof, backward compatibility, template parity, and independent W4b.

## Stop Boundary

Stop before rewriting legacy Compound history or turning all reviews into mandatory Compound records.
