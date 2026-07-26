---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-624-001
work_uid: 6cfb0da7-e3d9-41b0-ae9c-422414e70985
kind: unit
parent_id: TASK-AR-624
unit_id: UNIT-TASK-AR-624-001
task_id: TASK-AR-624
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:19:13+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 전역 폼 스코프 축소 + 0건 그룹 렌더 생략 + 히어로 강등
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 태스크 생성 폼과 런타임 커맨드 폼이 .work-surface 최상단에 있어 모든 뷰 위에 항상 노출된다(ui_console_assets.py:305-334). 홈에는 콕핏+Work state 히어로+메트릭 4타일+위젯의 요약 장치 4종이 세로 병렬로 위계가 붕괴돼 있다.
inputs:
  - src/agent_runtime/ui_console_assets.py:305-334 (전역 폼)
  - src/agent_runtime/ui_console_assets.py:263-303 (홈 콕핏/히어로/타일)
target_files:
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_console.py
scope: 폼 노출 조건화, 0건 어텐션 그룹 조건부 렌더, 히어로/위젯 접이식 강등. 신규 컴포넌트 도입 없음.
acceptance:
  - 홈/Work 외 뷰의 렌더 출력에 태스크 생성 폼 마크업이 없다
  - 개체 0건 어텐션 그룹이 렌더 출력에 없다
verification:
  - python -m pytest tests/test_ui_console.py tests/test_ui_console_microinteractions.py -q
handoff: before/after 스크린샷 또는 렌더 스냅샷 차이를 evidence로 남긴다.
stop_condition: verdict 배지·집계 스트립·흐름 타일 신설로 넘어가지 말 것 — P1(1-2).
verified_at: 2026-07-26T13:19:13+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-26-unit-task-ar-624-001-20260726131913.json
---

# UNIT-TASK-AR-624-001 - 전역 폼 스코프 축소 + 0건 그룹 렌더 생략 + 히어로 강등

## Context

태스크 생성 폼과 런타임 커맨드 폼이 .work-surface 최상단에 있어 모든 뷰 위에 항상 노출된다(ui_console_assets.py:305-334). 홈에는 콕핏+Work state 히어로+메트릭 4타일+위젯의 요약 장치 4종이 세로 병렬로 위계가 붕괴돼 있다.

## Inputs

- src/agent_runtime/ui_console_assets.py:305-334 (전역 폼)
- src/agent_runtime/ui_console_assets.py:263-303 (홈 콕핏/히어로/타일)

## Target Files

- src/agent_runtime/ui_console_assets.py
- tests/test_ui_console.py

## Scope

폼 노출 조건화, 0건 어텐션 그룹 조건부 렌더, 히어로/위젯 접이식 강등. 신규 컴포넌트 도입 없음.

## Steps

1. 전역 태스크/커맨드 폼을 홈·Work 뷰에서만 렌더하도록 조건을 건다(또는 Ctrl+K 액션으로 이동)
2. 콕핏 어텐션 그룹 렌더에서 count==0 그룹을 건너뛴다
3. Work state 히어로와 위젯을 접이식(details)이나 하위 순서로 강등해 콕핏을 상단에 둔다
4. tests/test_ui_console.py에 폼 스코프와 0건 그룹 생략을 검증하는 케이스를 추가한다

## Acceptance Criteria

- 홈/Work 외 뷰의 렌더 출력에 태스크 생성 폼 마크업이 없다
- 개체 0건 어텐션 그룹이 렌더 출력에 없다

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_microinteractions.py -q`

## Handoff

before/after 스크린샷 또는 렌더 스냅샷 차이를 evidence로 남긴다.

## Stop Boundary

verdict 배지·집계 스트립·흐름 타일 신설로 넘어가지 말 것 — P1(1-2).