---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-626-001
work_uid: fc6cc71a-40a2-44e1-aa30-2398554679d6
kind: unit
parent_id: TASK-AR-626
unit_id: UNIT-TASK-AR-626-001
task_id: TASK-AR-626
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:19:19+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 타임스탬프 단조성 게이트 + actuals/rework 자동 파생
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 지표 정의·계산 코드는 존재하나 actual_hours 기입 18/259, rework_count 0/259로 사실상 수동 미기입이고, 타임스탬프 백필 모순(completed_at<started_at)이 존재한다(ARCHIVE-INDEX.md:30,32). 소급 정정이 아니라 격리를 권고한다.
inputs:
  - scripts/work_schema_gate.py
  - scripts/work.py:116-145,2401-2662 (지표 계산)
  - scripts/task_claim_dispatcher.py (release/W4b 경로)
  - ARCHIVE-INDEX.md:30,32 (모순 레코드)
target_files:
  - scripts/work_schema_gate.py
  - agents/project/WORK-SCHEMA.yml
  - tests/test_work_schema_gate.py
scope: 단조성 검사 + backfilled 마커 격리 + 스키마 등록. 자동 파생은 후속 태스크.
acceptance:
  - 단조성 위반 레코드가 게이트 findings에 나타나고 backfilled 마커로 면제된다
  - timestamp_quality가 WORK-SCHEMA 카탈로그에 등록된다
verification:
  - python -m pytest tests/test_work_schema_gate.py -q
  - python scripts/work_schema_gate.py --items --check
handoff: 게이트 findings 샘플과 마킹된 레코드 diff를 evidence로 남긴다. actuals/rework 자동 파생은 closeout-automation 후속 태스크로 명시 이관.
stop_condition: FLOW-DIGEST 자동 생성이나 Ownership Concentration 위젯으로 넓히지 말 것 — P1(1-8).
verified_at: 2026-07-26T13:19:19+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-26-unit-task-ar-626-001-20260726131919.json
---

# UNIT-TASK-AR-626-001 - 타임스탬프 단조성 게이트 + actuals/rework 자동 파생

## Context

지표 정의·계산 코드는 존재하나 actual_hours 기입 18/259, rework_count 0/259로 사실상 수동 미기입이고, 타임스탬프 백필 모순(completed_at<started_at)이 존재한다(ARCHIVE-INDEX.md:30,32). 소급 정정이 아니라 격리를 권고한다.

## Inputs

- scripts/work_schema_gate.py
- scripts/work.py:116-145,2401-2662 (지표 계산)
- scripts/task_claim_dispatcher.py (release/W4b 경로)
- ARCHIVE-INDEX.md:30,32 (모순 레코드)

## Target Files

- scripts/work_schema_gate.py
- agents/project/WORK-SCHEMA.yml
- tests/test_work_schema_gate.py

## Scope

단조성 검사 + backfilled 마커 격리 + 스키마 등록. 자동 파생은 후속 태스크.

## Steps

1. work_schema_gate에 registered_at<=started_at<=completed_at 단조성 검사를 추가한다(backfilled 마커 면제)
2. 위반하는 기존 레코드에 timestamp_quality: backfilled를 부여한다
3. timestamp_quality를 WORK-SCHEMA 카탈로그에 등록한다(root+template 변이 스타일)
4. tests/test_work_schema_gate.py에 위반 감지/면제 케이스를 추가한다

## Acceptance Criteria

- 단조성 위반 레코드가 게이트 findings에 나타나고 backfilled 마커로 면제된다
- timestamp_quality가 WORK-SCHEMA 카탈로그에 등록된다

## Verification

- `python -m pytest tests/test_work_schema_gate.py -q`
- `python scripts/work_schema_gate.py --items --check`

## Handoff

게이트 findings 샘플과 마킹된 레코드 diff를 evidence로 남긴다. actuals/rework 자동 파생은 closeout-automation 후속 태스크로 명시 이관.

## Stop Boundary

FLOW-DIGEST 자동 생성이나 Ownership Concentration 위젯으로 넓히지 말 것 — P1(1-8).