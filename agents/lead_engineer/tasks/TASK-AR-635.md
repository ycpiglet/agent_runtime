---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-635
display_id: TASK-AR-635
task_uid: 5f1c3acb-800a-49e8-af00-5af1364caa06
work_id: TASK-AR-635
work_uid: 5f1c3acb-800a-49e8-af00-5af1364caa06
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
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
reservation_id: RES-20260726-204104-63e72cf5-06
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: "\u001eagent-runtime-work-scalar-v1:[A3-5\u00b7A3-6] Owner \uacb0\uc815 \ud655\uc815 \ubc18\uc601: #4 \uae30\ubcf8 \ucf1c\uc9d0+--skip-quiz(\uc0ac\uc720 \uae30\ub85d) loud escape, \ud504\ub808\uc774\ubc0d\uc740 '\uc18d\ub3c4 \uc870\uc808\uae30'(Litt). #5 explainer \ubb38\uc11c(\ubc30\uacbd\u2192\uc9c1\uad00\u2192\uc11c\uc220\ud615 diff\u2192\ud034\uc988) \ub0b4\uc7a5 5\ubb38\ud56d medium, gotcha \uae08\uc9c0, \uc989\uc2dc \ud53c\ub4dc\ubc31, \uc120\ud0dd\uc9c0 \ub79c\ub364\ud654, PR \ub2e8\uc704 \ubc1c\ub3d9(diff<100\uc904\u00b7\ube44\ud575\uc2ec \uc2a4\ud0b5, scripts/\u00b7.githooks/\u00b7AGENTS.md \ubb34\uc870\uac74), \ud1b5\uacfc 4/5+\uc624\ub2f5 teach-back \uc7ac\ucd9c\uc81c. #6 \ucd9c\uc81c\uc790\ub294 \uc791\uc5c5 \uc138\uc158\uacfc \ubd84\ub9ac\ub41c \ud0c0 \ubaa8\ub378 \uacc4\uc5f4. #7 held-out \uc704\uce58\ub294 \uad6c\ud604 \ucc29\uc218 \uc2dc Owner \ud655\uc815(OWNER-DECIDES). \uadfc\uac70: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md"
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-635 - W4c 이해도 퀴즈 게이트 승격 + held-out 검증

## Goal

- diff를 이해했는지 pre-PR 단계에서 독립 출제자가 퀴즈로 검증하고, 통과 못 하면 teach-back으로 반복 학습시킨다.

## Scope

- 퀴즈 게이트 승격 + 완화 패키지 + held-out + trajectory_audit. Owner 승인 티어링(1-7)과 동시 배포.

## Acceptance Criteria

- pre-PR에서 explainer 문서(배경→직관→서술형 diff→퀴즈)가 생성되고, 작업 세션과 분리된 타 모델 계열 인스턴스가 diff 실질을 묻는 5문항(medium, gotcha 금지)을 출제한다
- 객관식 선택지 순서가 랜덤화되고 즉시 정오 피드백이 제공되며, 통과선 4/5 미달 시 오답 문항만 teach-back(재설명→재진술) 후 재출제된다
- 발동 규칙: PR 단위, diff 100줄 미만·비핵심 경로는 스킵, scripts/·.githooks/·AGENTS.md 변경은 무조건 발동
- 기본 켜짐이며 --skip-quiz는 사유 기록을 강제하고 그 기록이 reviews/QUIZ-*.json으로 evidence INDEX에 편입된다
- held-out AC 봉인(#7 위치는 OWNER-DECIDES)과 trajectory_audit 필드가 W4b 리포트에 기록된다

## Verification

- `python -m pytest tests/test_work_close.py tests/test_work_index.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
