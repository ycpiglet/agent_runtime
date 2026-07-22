---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
work_uid: 5a49b578-950b-4193-855d-96f444f473c1
kind: taskset
id: TASKSET-AR-CONSOLE-OVERHAUL-P1
parent_id: INIT-AR-CONSOLE-OVERHAUL-P1
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
status: active
owner: lead_engineer
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: attention 단일 정본화, 홈 Decision Screenfit 완성(verdict 배지+어텐션 큐+집계 스트립+흐름 타일), renderAll 해체, /clarify 인터뷰 게이트+EARS, 요구-검증-증거 3자 추적성, W4c 이해도 퀴즈 게이트 승격+held-out, Owner 승인 위험 티어링, FLOW-DIGEST 주간 자동+actor 스탬프+Ownership Concentration. 1–2개월. Phase 0 완료가 전제.
---

# Console Overhaul P1 — Core Structure

## Goal

- attention 단일 정본화, 홈 Decision Screenfit 완성(verdict 배지+어텐션 큐+집계 스트립+흐름 타일), renderAll 해체, /clarify 인터뷰 게이트+EARS, 요구-검증-증거 3자 추적성, W4c 이해도 퀴즈 게이트 승격+held-out, Owner 승인 위험 티어링, FLOW-DIGEST 주간 자동+actor 스탬프+Ownership Concentration. 1–2개월. Phase 0 완료가 전제.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-609` | attention 신호 단일 정본화 (보드=콕핏 로직 공유) |
| `TASK-AR-610` | 홈 Decision Screenfit 완성 |
| `TASK-AR-611` | renderAll() 해체 — 선택 렌더 + 갱신 경로 단일화 |
| `TASK-AR-612` | /clarify 엔지니어링 인터뷰 게이트 (W1.5) + EARS 수용 기준 |
| `TASK-AR-613` | 요구-검증-증거 3자 추적성 게이트 |
| `TASK-AR-614` | W4c 이해도 퀴즈 게이트 승격 + held-out 검증 |
| `TASK-AR-615` | Owner 승인 위험 티어링 (위임 확대) |
| `TASK-AR-616` | FLOW-DIGEST 주간 자동 + actor 스탬프 + Ownership Concentration |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
