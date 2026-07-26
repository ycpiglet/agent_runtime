---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-625
display_id: TASK-AR-625
task_uid: b17921ba-8c9e-41fc-bd1c-d67fa9ccf196
work_id: TASK-AR-625
work_uid: b17921ba-8c9e-41fc-bd1c-d67fa9ccf196
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
registered_at: 2026-07-26T13:16:03+09:00
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:16:03+09:00
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
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-625/UNIT-TASK-AR-625-001.md
reservation_id: RES-20260726-131603-af796687-03
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

# TASK-AR-625 - 프론트 위생 — 죽은 코드·아이콘·i18n·다크베이스·칸반

## Goal

- P1 화면 작업 전에 저위험 단건 결함들을 정리해 소음을 제거한다.

## Scope

- 논리/배선 단건 위생(팔레트 nav 파생·죽은 activateView 제거·i18n 회귀잠금). 시각/디자인 단건(Lucide 아이콘·8/9px 토큰·다크캔버스·칸반)은 P1 디자인 시스템(1-10)으로 이관 — P0 조각 구현은 P1 재설계와 충돌(W4b 합의).

## Acceptance Criteria

- 커맨드 팔레트 대상이 실제 nav(navLinks)에서 파생되어 신규 뷰로 점프 가능하고, 중복/죽은 activateView 정의가 제거된다
- /api/i18n가 문자열 테이블을 반환한다(기존에도 정상 — 회귀 테스트로 잠금)
- i18n_literal_gate와 design_system_gate가 통과한다
- deferred(P1 1-10): Lucide 아이콘 교체 / 8-9px 토큰 리매핑 / 다크 canvas 상향 / 칸반 1레인=1열

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q`
- `python scripts/i18n_literal_gate.py --check`
- `python scripts/design_system_gate.py --check`
