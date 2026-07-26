---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
work_uid: f946bfab-63df-4bae-b0f8-028ed508a07a
kind: taskset
id: TASKSET-AR-CONSOLE-OVERHAUL-P1
parent_id: INIT-AR-CONSOLE-OVERHAUL-P1
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
status: active
owner: lead_engineer
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: "\u001eagent-runtime-work-scalar-v1:Owner \uacb0\uc815 \ud655\uc815(2026-07-26) \ubc18\uc601 P1 \ubcf8\ub300. attention \ub2e8\uc77c \uc815\ubcf8\ud654(#1 \uc6f9=1\ucc28), \ud648 Screenfit, renderAll \ud574\uccb4, /clarify+EARS(#8 \ubcc4\ub3c4 \uc2a4\ud0ac), 3\uc790 \ucd94\uc801\uc131, W4c \ud034\uc988(explainer 5\ubb38\ud56d medium+\uc120\ud0dd\uc9c0 \ub79c\ub364\ud654+loud escape, #4/#5/#6), \uc2b9\uc778 \ud2f0\uc5b4\ub9c1(#9), \uc784\uacc4 \uae30\ubc18 FLOW-DIGEST+actor \uc2a4\ud0ec\ud504(#13, #10 \ubd84\uc5c5\uc758 \uce21\uc815 \uc120\ud589), \ub514\uc790\uc778 \ud328\uc2a4(#15). 1-2\uac1c\uc6d4."
---

# Console Overhaul P1 — Core Structure

## Goal

- Owner 결정 확정(2026-07-26) 반영 P1 본대. attention 단일 정본화(#1 웹=1차), 홈 Screenfit, renderAll 해체, /clarify+EARS(#8 별도 스킬), 3자 추적성, W4c 퀴즈(explainer 5문항 medium+선택지 랜덤화+loud escape, #4/#5/#6), 승인 티어링(#9), 임계 기반 FLOW-DIGEST+actor 스탬프(#13, #10 분업의 측정 선행), 디자인 패스(#15). 1-2개월.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-630` | attention 신호 단일 정본화 (보드=콕핏 로직 공유) |
| `TASK-AR-631` | 홈 Decision Screenfit 완성 |
| `TASK-AR-632` | renderAll() 해체 — 선택 렌더 + 갱신 경로 단일화 |
| `TASK-AR-633` | /clarify 엔지니어링 인터뷰 게이트 (W1.5) + EARS 수용 기준 |
| `TASK-AR-634` | 요구-검증-증거 3자 추적성 게이트 |
| `TASK-AR-635` | W4c 이해도 퀴즈 게이트 승격 + held-out 검증 |
| `TASK-AR-636` | Owner 승인 위험 티어링 (위임 확대) |
| `TASK-AR-637` | FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration |
| `TASK-AR-638` | 디자인 패스 1 — KR i18n 전수 + 컬러 상태 문법 + P0 이관 코스메틱 |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
