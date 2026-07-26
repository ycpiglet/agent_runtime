---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-637
display_id: TASK-AR-637
task_uid: 378a8ffc-fb00-4640-acdc-96fbeecfde54
work_id: TASK-AR-637
work_uid: 378a8ffc-fb00-4640-acdc-96fbeecfde54
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
title: FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration
status: planned
priority: P2
difficulty: L
est_hours: 10
est_tokens: 1000
owner: lead_engineer
team: agent-runtime-core
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260726-204104-63e72cf5-08
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: "\u001eagent-runtime-work-scalar-v1:[A2-3\u00b7A2-6] Owner \uacb0\uc815 #13 \ud655\uc815: \uace0\uc815 \uc8fc\uae30 \ub300\uc2e0 \uc784\uacc4 \uae30\ubc18 \ubc1c\ud589 \u2014 \uc644\ub8cc \ub204\uc801 N\uac74(\ucd08\uae30 10) \ub610\ub294 \uacb0\uc815 \ud544\uc694 \uc2e0\ud638(\uac8c\uc774\ud2b8 watch \uc2b9\uaca9\u00b7\uc810\uc720 \uc9d1\uc911 \uc784\uacc4\u00b7\ubc18\ub824) \ubc1c\uc0dd \uc2dc \ubc1c\ud589, 3\uc8fc \uce68\ubb35 \uac00\ub4dc(1\uc904 \ud558\ud2b8\ube44\ud2b8). actor \uc2a4\ud0ec\ud504+Ownership Concentration\uc740 #10(\uc2e4\uc81c \ubd84\uc5c5 \ud655\uc815)\uc758 \uce21\uc815 \uc120\ud589 \ub2e8\uacc4. #11(actual_hours=\uc2e4\uc791\uc5c5)\uc758 \uce21\uc815 \ubc29\uc2dd \uc124\uacc4\ub294 closeout-automation \ud6c4\uc18d\uacfc \uc5f0\uacc4."
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-637 - FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration

## Goal

- 흐름 인사이트를 주간 다이제스트로 자동 전달하고, 주체별 점유를 측정 가능하게 만들어 독박을 지표로 확인한다.

## Scope

- 다이제스트 자동 생성 + actor 차원 스탬프 + Ownership Concentration 위젯. 이벤트 로그 실체화는 Phase 2(2-2).

## Acceptance Criteria

- FLOW-DIGEST가 임계 기반으로 발행된다: 완료 누적 10건 또는 결정 필요 신호 발생 시 (고정 주기 아님)
- 트리거가 3주간 없으면 1줄 하트비트 다이제스트가 발행된다(침묵과 고장을 구분)
- 발행물은 Bottom Line->Signal->Insight->Decision 포맷이며 결정할 것이 없으면 1줄로 끝난다
- claim/verify/closeout 시 실제 수행 instance/role이 frontmatter에 자동 스탬프되고, 담당/리뷰/실패의 주체별 파레토가 시각화되어 임계 초과 시 콕핏에 concentration risk로 승격된다

## Verification

- `python -m pytest tests/test_work_efficiency.py tests/test_ui_state.py -q`
- `python scripts/owner_governance_gate.py --allow-empty-owner-docs`
