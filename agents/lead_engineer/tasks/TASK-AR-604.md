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

- 논리/배선 단건 위생(팔레트·죽은 코드·i18n 회귀잠금). 시각/디자인 단건(아이콘·토큰·
  다크캔버스·칸반)은 아래 "Deferred to P1"로 이관. i18n 전수 확장도 P1(1-10).

## Acceptance Criteria

- 커맨드 팔레트 대상이 실제 nav(navLinks)에서 파생되어 신규 뷰로 점프 가능하고, 중복/죽은 activateView 정의가 제거된다
- /api/i18n가 문자열 테이블을 반환한다(검증 결과 기존에도 정상 동작 — 회귀 테스트로 잠금; 마스터플랜의 "빈 응답 결함" 주장은 부정확)
- i18n_literal_gate와 design_system_gate가 통과한다

## Deferred to P1 (1-10, 디자인 시스템 패스) — W4b 독립 검증 반영

다음 시각/디자인 항목은 실재하나(예: 사이드바 재탕 엔티티 아이콘 &#9776;×11·&#9783;×12
확인) 마스터플랜에서 P1 디자인 시스템(1-10)으로 매핑되며, P0에서 조각내면 P1의
컬러·토큰·다크테마 물리교정(D-2/D-3)·칸반(D-7) 재설계와 충돌하므로 이관한다
(독립 검증자 W4b도 "이 항목들은 P1 소관" 동의):
- 사이드바 HTML 엔티티 재탕 아이콘 → 벤더링된 Lucide 고유 아이콘 교체
- --font-size-ui-8/9 토큰 → 11px 별칭 리매핑
- 다크 canvas 그레이(#0E1013~) 상향
- 칸반 1레인=1열 가로 스크롤

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q`
- `python scripts/i18n_literal_gate.py --check`
- `python scripts/design_system_gate.py --check`
