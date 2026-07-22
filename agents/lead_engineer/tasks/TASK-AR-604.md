---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-604
display_id: TASK-AR-604
task_uid: 44c63587-7d2b-41c2-8855-dd96ea942ed5
work_id: TASK-AR-604
work_uid: 44c63587-7d2b-41c2-8855-dd96ea942ed5
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-22T17:45:27+09:00
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
title: 프론트 위생 — 죽은 코드·아이콘·i18n·다크베이스·칸반
status: planned
priority: P2
difficulty: M
est_hours: 5
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-604/UNIT-TASK-AR-604-001.md
reservation_id: RES-20260722-174527-39947af3-03
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A1-6·D-1·D-3·D-5·D-7] 커맨드 팔레트 뷰목록 동기화+죽은 activateView 삭제, Lucide 아이콘 교체, /api/i18n 빈응답 수정, 8/9px 리매핑, 다크 베이스 상향, 칸반 1레인=1열.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-604 - 프론트 위생 — 죽은 코드·아이콘·i18n·다크베이스·칸반

## Goal

- P1 화면 작업 전에 저위험 단건 결함들을 정리해 소음을 제거한다.

## Scope

- 열거된 단건 위생 수정. i18n 전수 확장(KR 정적 카피 전면)은 P1(1-10).

## Acceptance Criteria

- 커맨드 팔레트 뷰 목록이 실제 35개 뷰와 동기화되고 중복/죽은 activateView 정의가 제거된다
- 사이드바 HTML 엔티티 재탕 아이콘(9곳)이 벤더링된 Lucide 고유 아이콘으로 교체된다
- /api/i18n가 실제 문자열 테이블을 반환한다(빈 응답 결함 수정)
- --font-size-ui-8/9 토큰이 11px 별칭으로 리매핑되고, 다크 canvas가 그레이(#0E1013~)로 상향되며, 칸반이 1레인=1열 가로 스크롤이 된다

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q`
- `python scripts/i18n_literal_gate.py --check`
- `python scripts/design_system_gate.py --check`
