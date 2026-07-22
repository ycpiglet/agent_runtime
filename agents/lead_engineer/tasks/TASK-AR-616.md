---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-616
display_id: TASK-AR-616
task_uid: f2659e4c-2fd3-47e6-af31-5ef113951f6c
work_id: TASK-AR-616
work_uid: f2659e4c-2fd3-47e6-af31-5ef113951f6c
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration
status: planned
priority: P2
difficulty: L
est_hours: 10
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260722-174534-8e86c307-08
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A2-3·A2-6] reviews/FLOW-DIGEST-YYYY-Www.md 자동 생성(Bottom Line->Signal->Insight->Decision), claim/verify/closeout 시 actor 자동 스탬프, 담당/리뷰/실패 파레토 위젯. Phase2 권한 분해의 근거 데이터 생산. (§Decision 13 관련)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-616 - FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration

## Goal

- 흐름 인사이트를 주간 다이제스트로 자동 전달하고, 주체별 점유를 측정 가능하게 만들어 독박을 지표로 확인한다.

## Scope

- 다이제스트 자동 생성 + actor 차원 스탬프 + Ownership Concentration 위젯. 이벤트 로그 실체화는 Phase 2(2-2).

## Acceptance Criteria

- reviews/FLOW-DIGEST-*.md가 주 1회 자동 생성되고 결정할 게 없으면 1줄로 끝난다
- claim/verify/closeout 시 실제 수행 instance/role이 frontmatter에 자동 스탬프된다
- 담당/리뷰/실패의 주체별 파레토(상위 1주체 점유율 %)가 시각화되고 임계 초과 시 콕핏에 concentration risk 신호로 승격된다

## Verification

- `python -m pytest tests/test_work_efficiency.py tests/test_ui_state.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
