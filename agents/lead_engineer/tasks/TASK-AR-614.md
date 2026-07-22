---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-614
display_id: TASK-AR-614
task_uid: e7aed944-1282-4d64-becd-0bc1796e3df6
work_id: TASK-AR-614
work_uid: e7aed944-1282-4d64-becd-0bc1796e3df6
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: W4c 이해도 퀴즈 게이트 승격 + held-out 검증
status: planned
priority: P1
difficulty: L
est_hours: 14
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260722-174534-8e86c307-06
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [A3-5·A3-6] Phase0 /quiz opt-in 실데이터로 문항·임계 캘리브레이션 후 게이트로 승격(기본 켜짐+loud escape). QLC 4유형 한국어 3~5문항, 독립 출제자, teach-back 루프, held-out 봉인, trajectory_audit. (§Decisions 4·5·6·7 종속)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-614 - W4c 이해도 퀴즈 게이트 승격 + held-out 검증

## Goal

- diff를 이해했는지 pre-PR 단계에서 독립 출제자가 퀴즈로 검증하고, 통과 못 하면 teach-back으로 반복 학습시킨다.

## Scope

- 퀴즈 게이트 승격 + 완화 패키지 + held-out + trajectory_audit. Owner 승인 티어링(1-7)과 동시 배포.

## Acceptance Criteria

- pre-PR에서 작업 세션과 컨텍스트 분리된 독립 인스턴스가 diff 구성물을 참조하는 QLC 4유형 한국어 문항을 출제한다
- 통과 임계(예: 4/5) 미달 시 오답 문항만 재설명->Owner 재진술->재출제하는 teach-back 루프가 돈다
- 기록이 reviews/QUIZ-*.json(agent-runtime-comprehension/v1)으로 evidence INDEX에 편입되고 --skip-quiz는 사유 기록을 강제한다
- held-out AC 1~2개가 검증자만 아는 케이스로 봉인되고 W4b frontmatter에 trajectory_audit 3필드가 기록된다

## Verification

- `python -m pytest tests/test_work_close.py tests/test_work_index.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
