---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-630-001
work_uid: 7c1c630a-0001-4630-8630-630630630001
kind: unit
parent_id: TASK-AR-630
unit_id: UNIT-TASK-AR-630-001
task_id: TASK-AR-630
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
status: worker_ready
verification_status: passed
owner: lead_engineer
created_at: 2026-07-27T10:00:00+09:00
updated_at: 2026-07-27T10:30:21+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-worker-630
summary: attention 신호 단일 정본화 (보드=콕핏 공유 모듈 + gate watch 승격)
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 보드 Rollups의 Needs attention은 triage+Ask 휴리스틱, 콘솔 콕핏은 scripts/attention_inbox.py로 서로 다른 정의를 써서 두 표면이 다른 현황을 말할 수 있었다. 또한 watch 상태 게이트 신호는 reviews/*GATE*.json에만 있고 콕핏에 도달하지 않았다(Owner 결정 1번, 웹=1차 표면).
inputs:
  - scripts/attention_inbox.py
  - scripts/backlog_board.py
  - scripts/taskset_work_gate.py
  - src/agent_runtime/ui_console.py
  - reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
target_files:
  - scripts/attention_inbox.py
  - scripts/backlog_board.py
  - scripts/taskset_work_gate.py
  - src/agent_runtime/ui_console.py
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_state.py
  - tests/test_attention_inbox.py
  - tests/test_backlog_board_tasksets.py
  - tests/test_taskset_work_gate.py
  - tests/test_ui_console.py
scope: attention 계산의 단일 정본화(attention_inbox)와 보드/콘솔 동시 소비 + gate_watch 그룹 승격. 홈 레이아웃 재구성(631)이나 renderAll 해체(632)로 확장 금지.
acceptance:
  - backlog_board Rollups의 "Needs attention"이 root 제공 시 scripts/attention_inbox.inbox()의 total/counts를 그대로 렌더한다(공유 import; rootless는 기존 lane 휴리스틱 폴백)
  - attention_inbox에 gate_watch 그룹이 추가되어 최신 레코드가 watch인 게이트만 severity 0(저강조)로 gate 티어에 승격된다
  - 콕핏 JS 어휘(INBOX_GROUPS/INBOX_GROUP_TIER/action map)와 i18n(ko/en), ui_console 폴백 그룹 목록이 gate_watch를 포함한다
  - 동일 상태에서 보드 headline 수와 콘솔 inbox total이 일치함을 회귀 테스트가 잠근다
  - taskset_work_gate가 시간 가변(stale 포함) attention 라인을 wall-clock 마스킹해 시간 경과만으로 보드 신선도가 red가 되지 않는다
verification:
  - python -m pytest tests/test_attention_inbox.py tests/test_backlog_board_tasksets.py tests/test_taskset_work_gate.py tests/test_ui_console.py tests/test_ui_state.py -q
  - python scripts/taskset_work_gate.py --check
handoff: 보드/콕핏 동일 집계 스냅샷과 테스트 로그를 evidence로 남긴다. gate watch 실데이터 검증은 watch 상태 GATE json이 생길 때 콕핏에서 확인.
stop_condition: 홈 Decision Screenfit(631) 또는 renderAll 해체(632) 범위로 확장하지 말 것.
verified_at: 2026-07-27T10:30:21+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-27-unit-task-ar-630-001-20260727103021.json
---

# UNIT-TASK-AR-630-001 - attention 신호 단일 정본화

## Context

보드 Rollups의 "Needs attention"은 triage+Ask 휴리스틱, 콘솔 콕핏은 scripts/attention_inbox.py로 서로 다른 정의를 써서 두 표면이 다른 현황을 말할 수 있었다. watch 상태 게이트 신호는 reviews/*GATE*.json에만 있고 콕핏에 도달하지 않았다.

## Inputs

- scripts/attention_inbox.py
- scripts/backlog_board.py
- scripts/taskset_work_gate.py
- src/agent_runtime/ui_console.py
- reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md

## Target Files

- scripts/attention_inbox.py
- scripts/backlog_board.py
- scripts/taskset_work_gate.py
- src/agent_runtime/ui_console.py
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_state.py
- tests/test_attention_inbox.py
- tests/test_backlog_board_tasksets.py
- tests/test_taskset_work_gate.py
- tests/test_ui_console.py

## Scope

attention 계산의 단일 정본화(attention_inbox)와 보드/콘솔 동시 소비 + gate_watch 그룹 승격. 홈 레이아웃 재구성(631)이나 renderAll 해체(632)로 확장 금지.

## Steps

1. attention_inbox에 gate_watch(root) 빌더 추가 — reviews/*GATE*.json에서 kind별 최신 레코드가 watch인 것만 severity 0으로 승격, GROUP_ORDER/GROUP_TIER 등록
2. backlog_board가 attention_inbox를 공유 import(폴백 포함)하고 root 제공 시 Rollups headline을 canonical total/counts로 렌더
3. taskset_work_gate의 wall-clock 마스크에 attention 라인 추가(stale 시간 가변성으로 인한 CI red 방지)
4. ui_console 폴백 그룹 목록 동기화(gate_watch + 누락 unowned), 콕핏 JS 어휘와 i18n(ko/en) 추가
5. 회귀 테스트: 보드=콘솔 집계 일치, gate_watch 최신-watch-만 승격, 마스크, JS 어휘

## Acceptance Criteria

- backlog_board Rollups의 "Needs attention"이 root 제공 시 scripts/attention_inbox.inbox()의 total/counts를 그대로 렌더한다(공유 import; rootless는 기존 lane 휴리스틱 폴백)
- attention_inbox에 gate_watch 그룹이 추가되어 최신 레코드가 watch인 게이트만 severity 0(저강조)로 gate 티어에 승격된다
- 콕핏 JS 어휘(INBOX_GROUPS/INBOX_GROUP_TIER/action map)와 i18n(ko/en), ui_console 폴백 그룹 목록이 gate_watch를 포함한다
- 동일 상태에서 보드 headline 수와 콘솔 inbox total이 일치함을 회귀 테스트가 잠근다
- taskset_work_gate가 시간 가변(stale 포함) attention 라인을 wall-clock 마스킹해 시간 경과만으로 보드 신선도가 red가 되지 않는다

## Verification

- `python -m pytest tests/test_attention_inbox.py tests/test_backlog_board_tasksets.py tests/test_taskset_work_gate.py tests/test_ui_console.py tests/test_ui_state.py -q`
- `python scripts/taskset_work_gate.py --check`

## Handoff

보드/콕핏 동일 집계 스냅샷과 테스트 로그를 evidence로 남긴다. gate watch 실데이터 검증은 watch 상태 GATE json이 생길 때 콕핏에서 확인.

## Stop Boundary

홈 Decision Screenfit(631) 또는 renderAll 해체(632) 범위로 확장하지 말 것.