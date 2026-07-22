---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-613
display_id: TASK-AR-613
task_uid: d0afc4ad-5737-4501-8333-3e1710797e34
work_id: TASK-AR-613
work_uid: d0afc4ad-5737-4501-8333-3e1710797e34
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: 요구-검증-증거 3자 추적성 게이트
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260722-174534-8e86c307-05
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-3] 의미적 일치를 리뷰어 재량에서 기계 검사로 이관. 1-4의 AC ID 체계를 소비하므로 후행.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-613 - 요구-검증-증거 3자 추적성 게이트

## Goal

- acceptance criterion에 ID를 부여하고 검증 명령과 매핑해 dangling(검증 없는 요구/요구 없는 검증)을 기계 적발한다.

## Scope

- AC ID + verification proves 매핑 + evidence_index 확장 + W4b AC 커버리지 필수화.

## Acceptance Criteria

- acceptance criterion에 AC-N ID가 부여되고 unit verification에 proves:[AC-N] 매핑이 추가된다
- evidence_index_generator가 dangling AC와 dangling 검증 명령을 적발해 리포트한다
- W4b 리포트에 'AC 커버리지 n/m'이 필수 필드로 포함된다

## Verification

- `python -m pytest tests/test_work_index.py tests/test_work_criteria.py -q`
- `python scripts/evidence_index_generator.py --check`
