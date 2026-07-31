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
status: in_progress
verification_status: failed
owner: lead-engineer
created_at: 2026-07-30T11:25:00+09:00
updated_at: 2026-08-01T00:45:10+09:00
started_at: 2026-07-31T04:07:35+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
created_by: codex-root-task-ar-650-planner
summary: Enforce repeated-failure Compound closure and ship its skill
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - data_integrity
  - cross_cutting
  - repeated_failure
defect_signatures:
  - defect:accepted-watch-splitlines-boundary-normalization:40cd1dd2748ea694
  - defect:accepted-watch-malformed-utf8-fail-open:eac1aefa14add5d1
  - defect:claim-repeated-failure-signals-lost-at-closure:1da2d2d41b194afb
  - defect:accepted-watch-unbounded-raw-file-read:ceb1edfdb452964a
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260731-040735-task-ar-654-ar654001.json
  - agents/runtime/task_claims/CLAIM-20260801-000156-task-ar-654-ar654repair001.json
context: The claim dispatcher already searches canonical Compound records, but closure_gate accepts any one of compound, review, or retro. The failure-to-regression skill exists only in the Runtime repository and is absent from consumer templates.
inputs:
  - reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
  - reviews/REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan.md
  - reviews/REVIEW-2026-07-31-task-ar-654-rsi-skill-contract-scope-amendment.md
  - reviews/REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan.md
  - reviews/REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment.md
  - reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
  - reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
  - src/agent_runtime/knowledge_records.py
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - skills/failure-to-regression/SKILL.md
target_files:
  - src/agent_runtime/knowledge_records.py
  - scripts/work.py
  - src/agent_runtime/templates/project/scripts/work.py
  - scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/compound_record.py
  - skills/failure-to-regression/SKILL.md
  - new:src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - agents/project/TEMPLATE-MIRROR-CONTRACT.json
  - tests/fixtures/host/agent_runtime.lock.json
  - tests/test_closure_gate.py
  - tests/test_compound_records.py
  - tests/test_task_claim_dispatcher.py
  - tests/test_runtime_asset_usage.py
  - tests/test_rsi_operating_system_docs.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_lock_merge_driver.py
  - tests/test_regen_host_lock_if_needed.py
  - agents/project/knowledge/compounds/records/COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b.json
  - agents/project/knowledge/compounds/INDEX.json
scope: Tighten only the repeated-failure lane and preserve ordinary review/retro closure compatibility.
acceptance:
  - Repeated failures cannot bypass Compound.
  - Compound dedupe and lookup remain deterministic.
  - The skill is discoverable in a freshly adopted host.
  - No legacy Compound log is rewritten.
verification:
  - python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/template_mirror_gate.py --check
  - python scripts/regen_host_lock_if_needed.py --check
handoff: Attach failure-first closure evidence, skill packaging proof, backward compatibility, template parity, and independent W4b.
stop_condition: Stop before rewriting legacy Compound history or turning all reviews into mandatory Compound records.
verified_at: 2026-08-01T00:41:04+09:00
verified_by: codex-skeptic-task-ar-654-physical-line-closeout
evidence_refs:
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731043905.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731050030.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731052414.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731054736.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731061244.json
  - reviews/VERIFY-2026-07-31-unit-task-ar-654-001-20260731233354.json
  - reviews/VERIFY-2026-08-01-unit-task-ar-654-001-20260801002151.json
review_refs:
  - reviews/SKEPTIC-2026-07-31-task-ar-654-yaml-conformance-closeout.md
  - reviews/W4A-2026-08-01-unit-task-ar-654-001-physical-line-boundary-repair.md
  - reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
  - reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
---

# UNIT-TASK-AR-654-001 - Enforce repeated-failure Compound closure and ship its skill

## Context

The claim dispatcher already searches canonical Compound records, but closure_gate accepts any one of compound, review, or retro. The failure-to-regression skill exists only in the Runtime repository and is absent from consumer templates.

## Inputs

- reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
- reviews/REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan.md
- reviews/REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment.md
- reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md
- reviews/W4B-2026-08-01-unit-task-ar-654-001-physical-line-boundary-final.md
- reviews/SKEPTIC-2026-08-01-task-ar-654-physical-line-boundary-closeout.md
- src/agent_runtime/knowledge_records.py
- src/agent_runtime/templates/project/scripts/compound_record.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- skills/failure-to-regression/SKILL.md

## Target Files

- src/agent_runtime/knowledge_records.py
- scripts/work.py
- src/agent_runtime/templates/project/scripts/work.py
- scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/compound_record.py
- skills/failure-to-regression/SKILL.md
- new:src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md
- agents/project/RUNTIME-ASSET-REGISTRY.json
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- agents/project/TEMPLATE-MIRROR-CONTRACT.json
- tests/fixtures/host/agent_runtime.lock.json
- tests/test_closure_gate.py
- tests/test_compound_records.py
- tests/test_task_claim_dispatcher.py
- tests/test_runtime_asset_usage.py
- tests/test_rsi_operating_system_docs.py
- tests/test_inventory_sync_sanitize.py
- tests/test_lock_merge_driver.py
- tests/test_regen_host_lock_if_needed.py
- agents/project/knowledge/compounds/records/COMPOUND-20260801-002336-preserve-physical-accepted-watch-line-boundaries-a18a5a430b8b.json
- agents/project/knowledge/compounds/INDEX.json

## Scope

Tighten only the repeated-failure lane and preserve ordinary review/retro closure compatibility.

## Steps

1. Add a negative where repeated_failure closes with review only.
2. Aggregate task/unit repeated-failure signals and require a current-work
   canonical Compound with a repository-contained supported prevention
   destination.
3. Rewrite, copy, validate, and register the failure-to-regression skill in the
   consumer core template without root-only casebook dependencies.
4. Verify ordinary non-repeated work remains compatible.

## Acceptance Criteria

- Repeated failures cannot bypass Compound.
- Compound dedupe and lookup remain deterministic.
- The skill is discoverable in a freshly adopted host.
- No legacy Compound log is rewritten.

## Verification

- `python -m pytest tests/test_compound_records.py tests/test_closure_gate.py tests/test_task_claim_dispatcher.py tests/test_runtime_asset_usage.py tests/test_rsi_operating_system_docs.py tests/test_inventory_sync_sanitize.py tests/test_lock_merge_driver.py tests/test_regen_host_lock_if_needed.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/template_mirror_gate.py --check`
- `python scripts/regen_host_lock_if_needed.py --check`

## Handoff

Attach failure-first closure evidence, skill packaging proof, backward compatibility, template parity, and independent W4b.

## Stop Boundary

Stop before rewriting legacy Compound history or turning all reviews into mandatory Compound records.

## Reopened after skeptic closeout

The 2026-07-31 skeptic closeout found a P1 physical-line boundary bypass after
the prior W4a/W4b sequence. The unit is therefore failed and reopened under
`reviews/REVIEW-2026-08-01-task-ar-654-splitlines-boundary-t3-replan.md` until
the exact repaired candidate passes fresh machine evidence, W4a, independent
W4b, and skeptic review.

## Compound record scope amendment

The repeated-failure repair owns its current-work canonical Compound record and
generated Compound index under
`reviews/REVIEW-2026-08-01-task-ar-654-compound-record-scope-amendment.md`.
This does not widen the ordinary-work closure contract or permit legacy record
rewrites.

## Reopened after fail-closed authority reviews

The physical-line matrix passed, but fresh W4b and skeptic reviews found
malformed-UTF-8 fail-open behavior, lost active-claim repeated-failure
authority, an unbounded raw accepted-watch read, and two closeout metadata
inconsistencies. The unit remains failed under
`reviews/REVIEW-2026-08-01-task-ar-654-failclosed-authority-t3-replan.md` until
one new candidate passes fresh machine, W4a, W4b, skeptic, and actual closeout
validation.
