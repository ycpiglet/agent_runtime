---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-607-001
work_uid: 7c7e5696-c3b6-4549-ab2b-cee5d9a8c809
kind: unit
parent_id: TASK-AR-607
unit_id: UNIT-TASK-AR-607-001
task_id: TASK-AR-607
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T23:06:05+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: REPORTING-FORMAT 복원 + response_contract_gate 강화 + OPS 참조 정정
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: response_contract_gate가 등재 경로가 없을 때 조용히 통과한다(scripts/response_contract_gate.py:22-46). OPS-COMMAND-REFERENCE.md 스킬 표에 6종이 누락되고 예시가 powershell로 되어 있어 리눅스 Owner와 불일치한다. REPORTING-FORMAT 정본이 부재하다.
inputs:
  - scripts/response_contract_gate.py:22-46
  - OPS-COMMAND-REFERENCE.md:92-100
  - AGENTS.md (Owner-Facing Language/Reporting 계약)
target_files:
  - new:agents/lead_engineer/REPORTING-FORMAT.md
  - scripts/response_contract_gate.py
  - OPS-COMMAND-REFERENCE.md
scope: 정본 문서 신설 + 게이트 강화 + 참조 표 정정. 신규 스킬 파일 생성은 범위 밖.
acceptance:
  - REPORTING-FORMAT.md 정본이 존재한다
  - response_contract_gate가 등재 경로 부재를 fail로 잡는다
  - OPS 표에 6종이 있고 powershell 예시가 없다
verification:
  - python scripts/response_contract_gate.py
  - python scripts/owner_governance_gate.py --allow-empty-owner-docs
handoff: 게이트 강화 전후 동작 차이를 evidence로 남긴다.
stop_condition: /clarify·/quiz 스킬 파일 작성으로 넓히지 말 것 — 별도 태스크.
verified_at: 2026-07-22T23:06:05+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-607-001-20260722230605.json
---

# UNIT-TASK-AR-607-001 - REPORTING-FORMAT 복원 + response_contract_gate 강화 + OPS 참조 정정

## Context

response_contract_gate가 등재 경로가 없을 때 조용히 통과한다(scripts/response_contract_gate.py:22-46). OPS-COMMAND-REFERENCE.md 스킬 표에 6종이 누락되고 예시가 powershell로 되어 있어 리눅스 Owner와 불일치한다. REPORTING-FORMAT 정본이 부재하다.

## Inputs

- scripts/response_contract_gate.py:22-46
- OPS-COMMAND-REFERENCE.md:92-100
- AGENTS.md (Owner-Facing Language/Reporting 계약)

## Target Files

- new:agents/lead_engineer/REPORTING-FORMAT.md
- scripts/response_contract_gate.py
- OPS-COMMAND-REFERENCE.md

## Scope

정본 문서 신설 + 게이트 강화 + 참조 표 정정. 신규 스킬 파일 생성은 범위 밖.

## Steps

1. agents/lead_engineer/REPORTING-FORMAT.md를 Bottom Line->Signal->Insight->Decision 계약으로 신설한다
2. response_contract_gate가 등재 경로 부재 시 fail하도록 강화하고 REPORTING-FORMAT를 참조하게 한다
3. OPS-COMMAND-REFERENCE.md 스킬 표에 누락 6종을 추가하고 예시 명령을 bash로 정정한다
4. 관련 테스트를 갱신한다

## Acceptance Criteria

- REPORTING-FORMAT.md 정본이 존재한다
- response_contract_gate가 등재 경로 부재를 fail로 잡는다
- OPS 표에 6종이 있고 powershell 예시가 없다

## Verification

- `python scripts/response_contract_gate.py`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`

## Handoff

게이트 강화 전후 동작 차이를 evidence로 남긴다.

## Stop Boundary

/clarify·/quiz 스킬 파일 작성으로 넓히지 말 것 — 별도 태스크.