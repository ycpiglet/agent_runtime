---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-631-001
work_uid: 7c1c631a-0001-4631-8631-631631631001
kind: unit
parent_id: TASK-AR-631
unit_id: UNIT-TASK-AR-631-001
task_id: TASK-AR-631
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
status: completed
verification_status: passed
owner: lead_engineer
created_at: 2026-07-27T11:12:27+09:00
updated_at: 2026-07-28T19:18:04+09:00
timestamp_quality: backfilled
recovered_without_claim: "\u001eagent-runtime-work-scalar-v1:true"
recovery_reason: Historical implementation and W4 evidence predate a durable W2 claim; recovery preserves the absence instead of synthesizing a claim.
recovered_at: 2026-07-28T16:31:01+09:00
recovered_by: codex-root-v080-recovery-20260728
recovery_independent_evidence_refs:
  - reviews/ROLE-REVIEW-2026-07-28-TASK-AR-631-W4B.md
  - reviews/VERIFY-2026-07-27-unit-task-ar-631-001-20260727111227.json
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-worker-631
summary: 홈 Decision Screenfit (verdict 배지 + 큐 캡 + 집계 스트립 + 흐름 타일)
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: 홈에 요약 장치 4종(콕핏, 히어로, 구 dashboard 4타일, 위젯)이 세로 병렬돼 위계가 붕괴됐고, 이미 계산되는 health verdict와 velocity 시리즈가 홈에 노출되지 않았다. 목표는 스크롤 0으로 개입 필요 여부에 답하는 단일 화면.
inputs:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
  - src/agent_runtime/ui_design_assets.py
  - tests/test_ui_console_e2e.py
  - reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
target_files:
  - src/agent_runtime/ui_state.py
  - src/agent_runtime/ui_console_assets.py
  - tests/test_ui_state.py
  - tests/test_ui_console.py
  - tests/test_ui_console_e2e.py
scope: 홈 첫 화면 재구성(verdict 스트립, 콕핏 5카드 캡+오버플로 노트, 집계 스트립, 흐름 타일 3종, 히어로 기본 접힘, 구 dashboard 제거)과 서버 cycle_time 주간 중위 시리즈. renderAll 해체(632)나 IA 재프루닝(P2)으로 확장 금지.
acceptance:
  - ops_metrics에 cycle_time(주간 중위 시리즈, velocity.weeks와 x축 정렬, backfilled 제외)이 추가된다
  - 홈 상단에 health verdict 배지(healthy/watch/at_risk 시맨틱 색)와 인박스 total 기반 Bottom Line 한 줄이 렌더된다
  - 콕핏 결정 큐가 비어있지 않은 그룹 카드 최대 5개로 캡되고 초과분은 저강조 오버플로 노트 1장으로 접힌다
  - 한 줄 집계 스트립(open, WIP/한도, gates, agents)과 흐름 타일 3종(WIP, 주간 처리량+스파크라인, 중위 사이클 타임+스파크라인)이 콕핏 아래 렌더된다
  - 구 dashboard 4타일 섹션이 제거되고 work-state 히어로가 기본 접힘(명시 펼침은 localStorage로 지속)이 되어, 데스크톱/모바일 브라우저 검증에서 홈이 2화면 이내(scrollHeight <= innerHeight*2)로 복귀한다
  - real-series honesty rule 준수 — 스파크라인은 실시계열(velocity.weeks, cycle_time.weeks)에만 붙고 WIP는 점시값 숫자만
verification:
  - python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_console_microinteractions.py -q
  - python scripts/i18n_literal_gate.py --check
handoff: fold 예산 회복 수치(모바일 1737->2화면 이내)와 verdict/타일 렌더 스냅샷을 evidence로 남긴다. 다음 유닛은 renderAll 해체(TASK-AR-632).
stop_condition: renderAll 해체(632), IA 재프루닝(P2), 디자인 토큰 재설계(638)로 확장하지 말 것.
verified_at: 2026-07-27T11:12:27+09:00
verified_by: work.py verify
evidence_refs:
  - reviews/VERIFY-2026-07-27-unit-task-ar-631-001-20260727111227.json
review_refs:
  - reviews/ROLE-REVIEW-2026-07-28-TASK-AR-631-W4B.md
resolution: done
completed_at: 2026-07-28T19:18:04+09:00
closed_by: le-20260728-170130-kst-codexroot-v080-639-001
measurement_unavailable_reason: Historical implementation predates durable W2 claim and per-unit metering; recovery relies on preserved W4a and independent W4b evidence, so time and token measurements are unavailable.
---

# UNIT-TASK-AR-631-001 - 홈 Decision Screenfit

## Context

홈에 요약 장치 4종(콕핏, 히어로, 구 dashboard 4타일, 위젯)이 세로 병렬돼 위계가 붕괴됐고, 이미 계산되는 health verdict와 velocity 시리즈가 홈에 노출되지 않았다. 목표는 스크롤 0으로 개입 필요 여부에 답하는 단일 화면.

## Inputs

- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py
- src/agent_runtime/ui_design_assets.py
- tests/test_ui_console_e2e.py
- reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md

## Target Files

- src/agent_runtime/ui_state.py
- src/agent_runtime/ui_console_assets.py
- tests/test_ui_state.py
- tests/test_ui_console.py
- tests/test_ui_console_e2e.py

## Scope

홈 첫 화면 재구성(verdict 스트립, 콕핏 5카드 캡+오버플로 노트, 집계 스트립, 흐름 타일 3종, 히어로 기본 접힘, 구 dashboard 제거)과 서버 cycle_time 주간 중위 시리즈. renderAll 해체(632)나 IA 재프루닝(P2)으로 확장 금지.

## Steps

1. build_ops_metrics에 cycle_time(주간 중위, velocity.weeks 정렬, backfilled 제외) 파생 추가
2. 홈 마크업: verdict 스트립(콕핏 위) + 집계 스트립/흐름 타일(콕핏 아래) 신설, 구 dashboard 4타일 제거
3. renderHomeSummary(): verdict 배지+Bottom Line, 스트립(open/WIP/gates/agents), 타일 3종(componentSparkline 재사용, ASCII-only)
4. 콕핏 결정 큐 5카드 캡 + 저강조 오버플로 노트, 히어로 기본 접힘 전환
5. i18n ko/en 키 추가, e2e 순서/예산 테스트 갱신(2-screen 검증 유지)

## Acceptance Criteria

- ops_metrics에 cycle_time(주간 중위 시리즈, velocity.weeks와 x축 정렬, backfilled 제외)이 추가된다
- 홈 상단에 health verdict 배지(healthy/watch/at_risk 시맨틱 색)와 인박스 total 기반 Bottom Line 한 줄이 렌더된다
- 콕핏 결정 큐가 비어있지 않은 그룹 카드 최대 5개로 캡되고 초과분은 저강조 오버플로 노트 1장으로 접힌다
- 한 줄 집계 스트립(open, WIP/한도, gates, agents)과 흐름 타일 3종(WIP, 주간 처리량+스파크라인, 중위 사이클 타임+스파크라인)이 콕핏 아래 렌더된다
- 구 dashboard 4타일 섹션이 제거되고 work-state 히어로가 기본 접힘(명시 펼침은 localStorage로 지속)이 되어, 데스크톱/모바일 브라우저 검증에서 홈이 2화면 이내(scrollHeight <= innerHeight*2)로 복귀한다
- real-series honesty rule 준수 — 스파크라인은 실시계열(velocity.weeks, cycle_time.weeks)에만 붙고 WIP는 점시값 숫자만

## Verification

- `python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_console_microinteractions.py -q`
- `python scripts/i18n_literal_gate.py --check`

## Handoff

fold 예산 회복 수치(모바일 1737->2화면 이내)와 verdict/타일 렌더 스냅샷을 evidence로 남긴다. 다음 유닛은 renderAll 해체(TASK-AR-632).

## Stop Boundary

renderAll 해체(632), IA 재프루닝(P2), 디자인 토큰 재설계(638)로 확장하지 말 것.

<!-- work-close:start -->
## Closeout

- Completed at: `2026-07-28T19:18:04+09:00`
- Resolution: `done`
- Actual hours: `unavailable`
- Actual tokens: `unavailable`
- Measurement unavailable reason: Historical implementation predates durable W2 claim and per-unit metering; recovery relies on preserved W4a and independent W4b evidence, so time and token measurements are unavailable.
- Closed by: `le-20260728-170130-kst-codexroot-v080-639-001`
- Evidence:
  - `reviews/VERIFY-2026-07-27-unit-task-ar-631-001-20260727111227.json`
<!-- work-close:end -->
