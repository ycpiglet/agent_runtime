---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-623-001
work_uid: f890c258-8720-4d9b-85ed-8674ee28dec1
kind: unit
parent_id: TASK-AR-623
unit_id: UNIT-TASK-AR-623-001
task_id: TASK-AR-623
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-26T13:16:03+09:00
updated_at: 2026-07-26T13:19:11+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 상태 시그니처 감시 디렉터리 확장 + 홈 신선도 배지 배선
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 콘솔 상태 캐시는 _STATE_SIG_DIRS의 4개 디렉터리(agents/lead_engineer/tasks, agents/runtime, agents/project, reviews)만 mtime 감시한다. agents/messages·.ui_outbox·STATUS.md 변경은 캐시를 무효화하지 못해 최대 300초 stale로 표시되고, '빈 인박스'가 '처리할 것 없음'인지 '캐시 낡음'인지 구분 불가하다. freshness 스탬프는 이미 전 레코드에 있으므로(ui_state.py:2924-2961) 대부분 배선이다.
inputs:
  - src/agent_runtime/ui_state.py:8118-8123 (_STATE_SIG_DIRS)
  - src/agent_runtime/ui_console_assets.py:264-303 (홈 콕핏/헤더 영역)
  - reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
target_files:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_state.py
scope: _STATE_SIG_DIRS 확장 + 서버 상태 페이로드에 계산 기준시각(generated_at) 노출 + 홈 헤더 신선도 배지 렌더. 보드 generated_at 초 단위화는 동일 태스크의 후속 유닛/스텝.
acceptance:
  - agents/messages, .ui_outbox, STATUS.md 중 하나를 편집하면 _state_signature 반환값이 변한다
  - 상태 페이로드에 generated_at과 age_seconds가 포함된다
  - 홈 헤더 신선도 배지가 age_seconds를 표시하고 임계 초과 시 watch 색이 된다
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q
handoff: 변경 요약 + 신규 테스트 통과 로그를 W4a 리포트로 남기고, 보드 generated_at 초 단위화(A1-1 잔여)를 후속 스텝으로 명시한다.
stop_condition: 홈 레이아웃 전면 재구성(A1-2)이나 attention 로직 통합(A1-3)으로 범위를 넓히지 말 것 — 그것은 P1이다.
verified_at: 2026-07-26T13:19:11+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-26-unit-task-ar-623-001-20260726131911.json
---

# UNIT-TASK-AR-623-001 - 상태 시그니처 감시 디렉터리 확장 + 홈 신선도 배지 배선

## Context

콘솔 상태 캐시는 _STATE_SIG_DIRS의 4개 디렉터리(agents/lead_engineer/tasks, agents/runtime, agents/project, reviews)만 mtime 감시한다. agents/messages·.ui_outbox·STATUS.md 변경은 캐시를 무효화하지 못해 최대 300초 stale로 표시되고, '빈 인박스'가 '처리할 것 없음'인지 '캐시 낡음'인지 구분 불가하다. freshness 스탬프는 이미 전 레코드에 있으므로(ui_state.py:2924-2961) 대부분 배선이다.

## Inputs

- src/agent_runtime/ui_state.py:8118-8123 (_STATE_SIG_DIRS)
- src/agent_runtime/ui_console_assets.py:264-303 (홈 콕핏/헤더 영역)
- reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md

## Target Files

- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_state.py

## Scope

_STATE_SIG_DIRS 확장 + 서버 상태 페이로드에 계산 기준시각(generated_at) 노출 + 홈 헤더 신선도 배지 렌더. 보드 generated_at 초 단위화는 동일 태스크의 후속 유닛/스텝.

## Steps

1. _STATE_SIG_DIRS에 'agents/messages'를 추가하고, .ui_outbox와 STATUS.md는 _state_signature가 파일도 감시하도록 확장한다
2. 상태 페이로드 상단에 generated_at(계산 기준 ISO 초)과 age_seconds를 추가한다
3. ui_console_assets 홈 헤더에 age_seconds를 소비하는 신선도 배지를 렌더하고 임계(예: 60s) 초과 시 watch 색 클래스를 적용한다
4. 콕핏 빈 상태 카피를 기준 시각 포함 문구로 바꾼다
5. tests/test_ui_state.py에 messages/outbox/STATUS 편집이 시그니처를 바꾸는 케이스와 generated_at 노출 케이스를 추가한다

## Acceptance Criteria

- agents/messages, .ui_outbox, STATUS.md 중 하나를 편집하면 _state_signature 반환값이 변한다
- 상태 페이로드에 generated_at과 age_seconds가 포함된다
- 홈 헤더 신선도 배지가 age_seconds를 표시하고 임계 초과 시 watch 색이 된다

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py -q`

## Handoff

변경 요약 + 신규 테스트 통과 로그를 W4a 리포트로 남기고, 보드 generated_at 초 단위화(A1-1 잔여)를 후속 스텝으로 명시한다.

## Stop Boundary

홈 레이아웃 전면 재구성(A1-2)이나 attention 로직 통합(A1-3)으로 범위를 넓히지 말 것 — 그것은 P1이다.