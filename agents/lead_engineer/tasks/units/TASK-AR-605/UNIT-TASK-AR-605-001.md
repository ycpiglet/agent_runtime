---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-605-001
work_uid: dcf89f7e-304d-483d-aa8e-2c38dcd46ac0
kind: unit
parent_id: TASK-AR-605
unit_id: UNIT-TASK-AR-605-001
task_id: TASK-AR-605
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: pending
owner: lead_engineer
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
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
  - scripts/work.py
  - scripts/task_claim_dispatcher.py
scope: 단조성 검사 + backfilled 마커 격리 + actual_hours/rework 자동 파생. WIP 소급 재구성은 별도 스텝.
acceptance:
  - 단조성 위반 레코드가 게이트 findings에 나타나고 backfilled 마커로 지표에서 제외된다
  - 신규 closeout에서 actual_hours가 자동 기입된다
  - W4b 반려가 rework_count를 증가시킨다
verification:
  - python -m pytest tests/test_work_efficiency.py tests/test_work_close.py -q
  - python scripts/work_schema_gate.py --check
handoff: 게이트 findings 샘플과 자동 파생 전후 frontmatter diff를 evidence로 남긴다.
stop_condition: FLOW-DIGEST 자동 생성이나 Ownership Concentration 위젯으로 넓히지 말 것 — P1(1-8).
---

# UNIT-TASK-AR-605-001 - 타임스탬프 단조성 게이트 + actuals/rework 자동 파생

## Context

지표 정의·계산 코드는 존재하나 actual_hours 기입 18/259, rework_count 0/259로 사실상 수동 미기입이고, 타임스탬프 백필 모순(completed_at<started_at)이 존재한다(ARCHIVE-INDEX.md:30,32). 소급 정정이 아니라 격리를 권고한다.

## Inputs

- scripts/work_schema_gate.py
- scripts/work.py:116-145,2401-2662 (지표 계산)
- scripts/task_claim_dispatcher.py (release/W4b 경로)
- ARCHIVE-INDEX.md:30,32 (모순 레코드)

## Target Files

- scripts/work_schema_gate.py
- scripts/work.py
- scripts/task_claim_dispatcher.py

## Scope

단조성 검사 + backfilled 마커 격리 + actual_hours/rework 자동 파생. WIP 소급 재구성은 별도 스텝.

## Steps

1. work_schema_gate에 registered_at<=started_at<=completed_at 단조성 검사를 추가한다
2. 위반하는 기존 레코드에 timestamp_quality: backfilled를 부여하고, work.py 지표 계산이 이를 제외하도록 한다
3. work close 경로에서 claim의 claimed_at→release 차이를 actual_hours(wall-clock)로 자동 기입한다
4. task_claim_dispatcher의 W4b 반려 처리에서 rework_count를 +1 한다
5. work.py의 lead_time 명칭을 cycle_time으로 정리한다(보류 주석 해소)
6. tests/test_work_efficiency.py, tests/test_work_close.py에 케이스를 추가한다

## Acceptance Criteria

- 단조성 위반 레코드가 게이트 findings에 나타나고 backfilled 마커로 지표에서 제외된다
- 신규 closeout에서 actual_hours가 자동 기입된다
- W4b 반려가 rework_count를 증가시킨다

## Verification

- `python -m pytest tests/test_work_efficiency.py tests/test_work_close.py -q`
- `python scripts/work_schema_gate.py --check`

## Handoff

게이트 findings 샘플과 자동 파생 전후 frontmatter diff를 evidence로 남긴다.

## Stop Boundary

FLOW-DIGEST 자동 생성이나 Ownership Concentration 위젯으로 넓히지 말 것 — P1(1-8).
