---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-631
display_id: TASK-AR-631
task_uid: d66cb389-909a-4baa-b8d7-3785ce60faee
work_id: TASK-AR-631
work_uid: d66cb389-909a-4baa-b8d7-3785ce60faee
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
title: 홈 Decision Screenfit 완성
status: planned
priority: P1
difficulty: L
est_hours: 12
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260726-204104-63e72cf5-02
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: [A1-2+A2-4] Bottom Line 한 줄 + health verdict 배지(이미 계산됨) + 어텐션 큐(최대 5) + 정상 집계 스트립 + 흐름 타일 3종(WIP·throughput·중위 cycle time). Phase 0(신선도·위생)과 1-1(정본화) 이후.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-631 - 홈 Decision Screenfit 완성

## Goal

- 스크롤 없이 5초 내 '개입 필요 여부'에 예/아니오로 답하는 단일 화면을 완성한다.

## Scope

- 홈 뷰 전면 재구성 + 흐름 타일 3종. 전역 IA 재프루닝(35뷰->6허브)은 Phase 2(2-1).

## Acceptance Criteria

- above-the-fold(스크롤 0)에 health verdict 배지와 어텐션 큐가 렌더된다
- 정상 상태에서 어텐션 큐가 비고 한 줄 정상 집계 스트립('open N · WIP M · gates pass · agents idle')이 보인다
- 흐름 타일 3종(WIP·주간 throughput·중위 cycle time)이 큰 숫자+스파크라인+임계 색으로 표시된다
- Playwright above-the-fold 검증에서 홈 <=2화면, DOM 노드 예산 내

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_console_microinteractions.py -q`
- `python scripts/nav_budget_gate.py --check`
