---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-604-001
work_uid: a1935f61-4a7b-4707-9dcc-ae3f294f2a0b
kind: unit
parent_id: TASK-AR-604
unit_id: UNIT-TASK-AR-604-001
task_id: TASK-AR-604
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
summary: 커맨드 팔레트 동기화 + 죽은 activateView 제거 + 아이콘/토큰/칸반 위생
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 커맨드 팔레트 뷰 목록이 구버전에 고정돼 신규 뷰로 점프 불가하고(ui_console_assets.py:8480-8484), activateView가 8497·13782행에 중복 정의되며 8497행은 존재하지 않는 .tab 셀렉터를 조회한다. 사이드바 아이콘은 HTML 엔티티 재탕(&#9776; 4곳, &#9783; 5곳)이고, 타이포는 8/9px 토큰이 존재하며, 다크 canvas는 순흑(#010102), 칸반은 6레인을 3열 2행으로 감는다.
inputs:
  - src/agent_runtime/ui_console_assets.py:8480-8505 (팔레트/activateView)
  - src/agent_runtime/ui_console_assets.py:134-251 (사이드바 아이콘)
  - src/agent_runtime/ui_console_assets.py:1101-1106,1348 (아이콘맵/다크 canvas)
  - src/agent_runtime/ui_console_assets.py:2168-2171 (칸반 grid)
  - src/agent_runtime/ui_design_assets.py:149-169 (타이포 토큰)
  - src/agent_runtime/ui_state.py:2286-2612 (I18N_STRINGS / /api/i18n)
target_files:
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - src/agent_runtime/ui_state.py
scope: 열거된 6개 단건 수정. 각 수정은 독립적이며 회귀 위험이 낮다.
acceptance:
  - 팔레트에서 신규 뷰로 점프 가능하고 activateView 중복 정의가 없다
  - /api/i18n 응답이 비어있지 않다
  - i18n_literal_gate와 design_system_gate가 통과한다
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q
  - python scripts/i18n_literal_gate.py --check
handoff: 각 수정 항목별 diff 근거와 게이트 통과 로그를 W4a 리포트에 남긴다.
stop_condition: KR i18n 정적 카피 전수 번역이나 컬러 상태 문법 전면 도입으로 넓히지 말 것 — P1(1-10).
---

# UNIT-TASK-AR-604-001 - 커맨드 팔레트 동기화 + 죽은 activateView 제거 + 아이콘/토큰/칸반 위생

## Context

커맨드 팔레트 뷰 목록이 구버전에 고정돼 신규 뷰로 점프 불가하고(ui_console_assets.py:8480-8484), activateView가 8497·13782행에 중복 정의되며 8497행은 존재하지 않는 .tab 셀렉터를 조회한다. 사이드바 아이콘은 HTML 엔티티 재탕(&#9776; 4곳, &#9783; 5곳)이고, 타이포는 8/9px 토큰이 존재하며, 다크 canvas는 순흑(#010102), 칸반은 6레인을 3열 2행으로 감는다.

## Inputs

- src/agent_runtime/ui_console_assets.py:8480-8505 (팔레트/activateView)
- src/agent_runtime/ui_console_assets.py:134-251 (사이드바 아이콘)
- src/agent_runtime/ui_console_assets.py:1101-1106,1348 (아이콘맵/다크 canvas)
- src/agent_runtime/ui_console_assets.py:2168-2171 (칸반 grid)
- src/agent_runtime/ui_design_assets.py:149-169 (타이포 토큰)
- src/agent_runtime/ui_state.py:2286-2612 (I18N_STRINGS / /api/i18n)

## Target Files

- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- src/agent_runtime/ui_state.py

## Scope

열거된 6개 단건 수정. 각 수정은 독립적이며 회귀 위험이 낮다.

## Steps

1. 커맨드 팔레트 뷰 목록을 실제 뷰 레지스트리에서 파생하도록 바꾸고 죽은 activateView(8497-8505)를 제거한다
2. _ENTITY_ICON_MAP 치환을 사이드바 전 항목에 적용해 재탕 엔티티 아이콘을 Lucide 고유 아이콘으로 바꾼다
3. /api/i18n 빌더가 I18N_STRINGS를 실제로 직렬화해 반환하도록 수정한다
4. --font-size-ui-8/9를 11px 별칭으로 리매핑하고, 다크 --canvas를 #0E1013~#111318로 상향한다
5. 칸반 grid를 1레인=1열 가로 스크롤로 바꾼다
6. 관련 테스트를 갱신/추가한다

## Acceptance Criteria

- 팔레트에서 신규 뷰로 점프 가능하고 activateView 중복 정의가 없다
- /api/i18n 응답이 비어있지 않다
- i18n_literal_gate와 design_system_gate가 통과한다

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q`
- `python scripts/i18n_literal_gate.py --check`

## Handoff

각 수정 항목별 diff 근거와 게이트 통과 로그를 W4a 리포트에 남긴다.

## Stop Boundary

KR i18n 정적 카피 전수 번역이나 컬러 상태 문법 전면 도입으로 넓히지 말 것 — P1(1-10).
