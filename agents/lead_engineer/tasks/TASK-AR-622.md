---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-622
display_id: TASK-AR-622
task_uid: 37639c5d-1ccf-4ec2-b25c-d0f2f567b52d
work_id: TASK-AR-622
work_uid: 37639c5d-1ccf-4ec2-b25c-d0f2f567b52d
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: orchestrator 권한 3분할 (planner·integrator 실체화)
status: planned
priority: P3
difficulty: L
est_hours: 12
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-06
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-7c·d] 1-9의 점유 실측이 분해 우선순위를 지정. 명목 33역할 중 planner·integrator 우선 실체화, 소규모 변경은 review+W4 evidence 2종만. (§Decision 10 종속)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-622 - orchestrator 권한 3분할 (planner·integrator 실체화)

## Goal

- lead-engineer에 집중된 독박을 분해해 planner(W1)와 integrator(W5)를 우선 실체화하고 산출물 크기를 비례화한다.

## Scope

- planner/integrator 역할 실체화 + 사이클 산출물 크기 비례화. 전면 33역할 실체화는 범위 밖.

## Acceptance Criteria

- 1-9의 점유 실측을 근거로 분해 우선순위가 문서화된다
- planner(W1 인터뷰·수용 기준)와 integrator(W5 merge queue) 역할이 명목에서 실체 lane으로 승격된다
- 소규모 변경의 필수 사이클 산출물이 review+W4 evidence 2종으로 축소된다(크기 비례화)

## Verification

- `python -m pytest tests/test_work_lane_playbooks.py tests/test_taskset_work_gate.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
