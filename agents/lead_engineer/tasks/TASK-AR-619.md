---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-619
display_id: TASK-AR-619
task_uid: ec652e49-7363-4738-92fc-f794f710818b
work_id: TASK-AR-619
work_uid: ec652e49-7363-4738-92fc-f794f710818b
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: 상태 전이 이벤트 로그 실체화 (JSONL + 샤딩 + 하트비트)
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-03
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A2-5] ui_state.py:524-560이 읽도록 설계된 이벤트 로그를 상태전이·claim·verify·게이트 실패 시 1줄 append로 생산. 1-8 다이제스트가 소비처로 먼저 존재해야 낭비가 없음. 월별 샤딩+로드 캡 필수.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-619 - 상태 전이 이벤트 로그 실체화 (JSONL + 샤딩 + 하트비트)

## Goal

- 설계됐으나 없는 agents/runtime/events/*.jsonl을 훅 체인이 생산하게 해 단계별 체류시간·병목·stall을 관측한다.

## Scope

- 이벤트 append 훅 + 월별 샤딩 + 로드 캡 + 단계 체류시간 계산. 프레즌스 뷰 투자는 데이터 확인 후.

## Acceptance Criteria

- 상태 전이/claim/verify/게이트 실패가 agents/runtime/events/*.jsonl에 1줄씩 append된다
- 로그가 월별 샤딩되고 로드 시 캡이 적용되어 무상한 로드가 없다
- 등록->claim->구현->검증->머지 단계별 체류시간과 병목 추세가 계산된다
- 하트비트 필드로 장기 /goal 루프의 stall이 감지된다

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_work_efficiency.py -q`
