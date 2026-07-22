---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-623
display_id: TASK-AR-623
task_uid: 61bffa37-a5a3-40ed-acfe-14963a067b3c
work_id: TASK-AR-623
work_uid: 61bffa37-a5a3-40ed-acfe-14963a067b3c
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: 에이전트 상호검증 debate 확장 (설명자·심문자·심판)
status: planned
priority: P3
difficulty: L
est_hours: 12
est_tokens: 1000
owner: lead_engineer
team: evaluation-office
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-07
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-5 팀/에이전트 확장판] agent-runtime-comprehension/v2. 동질 에이전트 합의의 상관 오류(Consensus Trap)를 피해 다른 모델 계열로 역할 분리. 1-6 안착 후. Owner의 '에이전트끼리 상호 검증' 아이디어의 실현.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-623 - 에이전트 상호검증 debate 확장 (설명자·심문자·심판)

## Goal

- 사람 퀴즈 장치를 에이전트 간 상호검증으로 확장해 설명자-심문자-심판 3역 debate 구조를 도입한다.

## Scope

- 3역 debate 오케스트레이션 + v2 스키마. 단독 개인 타겟 강화(Phase 0/1)가 전제된 확장 단계.

## Acceptance Criteria

- 설명자·심문자·심판 3역이 서로 다른 모델 계열로 분리되어 상관 오류를 완화한다
- debate 결과가 agent-runtime-comprehension/v2 스키마로 기록되고 evidence INDEX에 편입된다
- 심판의 판정 근거가 감사 가능하게 기록된다

## Verification

- `python -m pytest tests/test_work_index.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
