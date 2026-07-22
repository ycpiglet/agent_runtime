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
verification_status: passed
owner: lead_engineer
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T18:14:59+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 커맨드 팔레트 동기화 + 죽은 activateView 제거 + 아이콘/토큰/칸반 위생
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 커맨드 팔레트 뷰 목록이 구버전에 고정돼 신규 뷰로 점프 불가하고(ui_console_assets.py:8480-8484), activateView가 8497·13782행에 중복 정의되며 8497행은 존재하지 않는 .tab 셀렉터를 조회한다. 사이드바 아이콘은 HTML 엔티티 재탕(&
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
verified_at: 2026-07-22T18:14:59+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-22-unit-task-ar-604-001-20260722181459.json
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

논리/배선 단건 위생(팔레트 파생화·죽은 코드 제거·i18n 회귀잠금). 시각/디자인 단건
(아이콘·토큰·다크캔버스·칸반)은 P1 디자인 시스템(1-10)으로 이관 — 아래 Steps 참고.

## Steps

1. 커맨드 팔레트 대상을 navLinks에서 파생하도록 바꾸고, 죽은 .tab 기반 activateView 중복 정의를 제거한다 (완료)
2. /api/i18n 응답이 문자열 테이블을 반환함을 회귀 테스트로 잠근다 (완료 — 기존에도 정상)
3. 관련 테스트를 갱신/추가한다 (완료)

### Deferred to P1 (1-10) — W4b 검증 반영
- (P1) _ENTITY_ICON_MAP을 사이드바 전 항목에 적용해 재탕 엔티티 아이콘을 Lucide로 교체
- (P1) --font-size-ui-8/9 → 11px 별칭 리매핑
- (P1) 다크 --canvas 그레이 상향, 칸반 1레인=1열
근거: 이 항목들은 마스터플랜 D-2/D-3/D-7로 P1 디자인 시스템 소관이며 P0 조각 구현은
P1 재설계와 충돌한다. 독립 검증자(W4b)도 동의.

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