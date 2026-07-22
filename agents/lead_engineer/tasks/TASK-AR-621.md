---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-621
display_id: TASK-AR-621
task_uid: c3c5cfce-ed0b-4948-9bf7-e4afc321fbf1
work_id: TASK-AR-621
work_uid: c3c5cfce-ed0b-4948-9bf7-e4afc321fbf1
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: 축3 패턴군 UI 통합 (InterviewPanel·AlignmentScorecard·QuizGate)
status: planned
priority: P3
difficulty: L
est_hours: 12
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-05
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [D-6] InterviewPanel(질문 카드 스택+번호키 즉답), AlignmentScorecard(AC 충족 n/m·스코프 이탈·검증 통과율), QuizGate(차단 모달 아닌 인박스 카드+통과 전 PR disabled), OwnershipConcentration. CLI/훅 선행, 콘솔 후행. 2-0 파일 분리 이후.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-621 - 축3 패턴군 UI 통합 (InterviewPanel·AlignmentScorecard·QuizGate)

## Goal

- 1-4~1-6에서 확정된 데이터 계약(INTERVIEW/QUIZ 스키마)을 콘솔에 1급 컴포넌트로 통합한다.

## Scope

- 축3 4종 패턴 컴포넌트 UI. 데이터 계약 자체는 Phase 1에서 확정됨.

## Acceptance Criteria

- InterviewPanel이 reviews/INTERVIEW-* 데이터를 질문 카드 스택으로 렌더하고 번호키 즉답을 지원한다
- AlignmentScorecard가 AC 커버리지·스코프 이탈·검증 통과율을 pass/watch/block+score로 표시한다
- QuizGate가 차단 모달이 아닌 인박스 카드로 착륙하고 통과 전 PR 액션이 disabled+이유 표시된다
- 모든 결정 카드에 accept/edit/respond/ignore 액션이 선언 내장된다

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_microinteractions.py -q`
