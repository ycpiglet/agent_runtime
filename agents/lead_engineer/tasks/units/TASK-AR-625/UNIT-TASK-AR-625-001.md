---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-625-001
work_uid: fd8197a8-36e7-4758-8950-9af6d856e3cf
kind: unit
parent_id: TASK-AR-625
unit_id: UNIT-TASK-AR-625-001
task_id: TASK-AR-625
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:19:16+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 커맨드 팔레트 동기화 + 죽은 activateView 제거 + 아이콘/토큰/칸반 위생
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: "\u001eagent-runtime-work-scalar-v1:\ucee4\ub9e8\ub4dc \ud314\ub808\ud2b8 \ubdf0 \ubaa9\ub85d\uc774 \uad6c\ubc84\uc804\uc5d0 \uace0\uc815\ub3fc \uc2e0\uaddc \ubdf0\ub85c \uc810\ud504 \ubd88\uac00\ud558\uace0(ui_console_assets.py:8480-8484), activateView\uac00 8497\u00b713782\ud589\uc5d0 \uc911\ubcf5 \uc815\uc758\ub418\uba70 8497\ud589\uc740 \uc874\uc7ac\ud558\uc9c0 \uc54a\ub294 .tab \uc140\ub809\ud130\ub97c \uc870\ud68c\ud55c\ub2e4. \uc0ac\uc774\ub4dc\ubc14 \uc544\uc774\ucf58\uc740 HTML \uc5d4\ud2f0\ud2f0 \uc7ac\ud0d5(&#9776; 4\uacf3, &#9783; 5\uacf3)\uc774\uace0, \ud0c0\uc774\ud3ec\ub294 8/9px \ud1a0\ud070\uc774 \uc874\uc7ac\ud558\uba70, \ub2e4\ud06c canvas\ub294 \uc21c\ud751(#010102), \uce78\ubc18\uc740 6\ub808\uc778\uc744 3\uc5f4 2\ud589\uc73c\ub85c \uac10\ub294\ub2e4."
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
scope: 논리/배선 단건 위생만. 시각/디자인 단건은 P1(1-10) 이관.
acceptance:
  - 팔레트에서 신규 뷰로 점프 가능하고 activateView 중복 정의가 없다
  - /api/i18n 응답이 비어있지 않다
  - i18n_literal_gate와 design_system_gate가 통과한다
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q
  - python scripts/i18n_literal_gate.py --check
handoff: 각 수정 항목별 diff 근거와 게이트 통과 로그를 W4a 리포트에 남긴다.
stop_condition: KR i18n 정적 카피 전수 번역이나 컬러 상태 문법 전면 도입으로 넓히지 말 것 — P1(1-10).
verified_at: 2026-07-26T13:19:16+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-26-unit-task-ar-625-001-20260726131916.json
---

# UNIT-TASK-AR-625-001 - 커맨드 팔레트 동기화 + 죽은 activateView 제거 + 아이콘/토큰/칸반 위생

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

논리/배선 단건 위생만. 시각/디자인 단건은 P1(1-10) 이관.

## Steps

1. 커맨드 팔레트 뷰 목록을 navLinks에서 파생하도록 바꾸고 죽은 .tab 기반 activateView 중복 정의를 제거한다
2. /api/i18n 문자열 테이블 반환을 회귀 테스트로 잠근다
3. 관련 테스트를 갱신/추가한다

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