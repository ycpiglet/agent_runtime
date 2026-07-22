---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-618
display_id: TASK-AR-618
task_uid: fa8cf982-ecd5-49a0-915c-ea631bf63c05
work_id: TASK-AR-618
work_uid: fa8cf982-ecd5-49a0-915c-ea631bf63c05
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: IA 재프루닝 2.0 (35뷰->6허브) + 확장기 정산 + VISION.md 갱신
status: planned
priority: P2
difficulty: L
est_hours: 14
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-02
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A1-5] 2-0(파일 분리) 이후, 1-2에서 홈이 결정 중심으로 검증된 뒤 전역 확장. 관제 뷰와 디버깅 뷰를 명시 분리. (§Decisions 1·2·3 종속)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-618 - IA 재프루닝 2.0 (35뷰->6허브) + 확장기 정산 + VISION.md 갱신

## Goal

- 35개 뷰를 관제 6허브(Home/Work/Agents/Records/Ops/Search)+drawer로 재편하고, 확장기 산출물 존치/폐기를 정산하며, 정본 비전을 의사결정 콘솔로 갱신한다.

## Scope

- IA 재편 + gamification·idea vault·progression·office map 존치/폐기 문서 정산 + VISION.md 갱신 + nav 예산 게이트 목표 복원.

## Acceptance Criteria

- 사이드바가 코어 6허브(+커맨드 팔레트 drawer)로 재편되고 작업 8뷰/에이전트 5뷰가 세그먼트/단일 허브로 통합된다
- 관제 뷰와 디버깅 뷰(트레이스·그래프·evidence)가 명시적으로 분리된다
- 확장기 산출물의 존치/폐기가 reviews/ 문서로 정산된다
- agents/project/VISION.md가 의사결정 콘솔 비전으로 갱신되어 두 정체성 병존이 해소된다

## Verification

- `python -m pytest tests/test_ui_console.py -q`
- `python scripts/nav_budget_gate.py --check`
