---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
work_uid: b0e721ca-32c6-479e-b3c8-952baf1ff5a8
kind: taskset
id: TASKSET-AR-CONSOLE-OVERHAUL-P2
parent_id: INIT-AR-CONSOLE-OVERHAUL-P2
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
status: active
owner: lead_engineer
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 프론트 물리 파일 분리(빌드리스), IA 재프루닝 2.0(관제 6허브+drawer)+확장기 산출물 정산+VISION.md 갱신, 상태 전이 이벤트 로그 실체화(JSONL+샤딩+하트비트), 실패 패턴 압축 파이프라인, 축3 패턴군 UI 통합(InterviewPanel·QuizGate 카드), orchestrator 권한 3분할, 에이전트 상호검증 debate 확장. 2개월+. Phase 0/1 안착이 전제.
---

# Console Overhaul P2 — Structure Complete

## Goal

- 프론트 물리 파일 분리(빌드리스), IA 재프루닝 2.0(관제 6허브+drawer)+확장기 산출물 정산+VISION.md 갱신, 상태 전이 이벤트 로그 실체화(JSONL+샤딩+하트비트), 실패 패턴 압축 파이프라인, 축3 패턴군 UI 통합(InterviewPanel·QuizGate 카드), orchestrator 권한 3분할, 에이전트 상호검증 debate 확장. 2개월+. Phase 0/1 안착이 전제.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-617` | 프론트 물리 파일 분리 (빌드리스) — Phase 2의 관문 |
| `TASK-AR-618` | IA 재프루닝 2.0 (35뷰->6허브) + 확장기 정산 + VISION.md 갱신 |
| `TASK-AR-619` | 상태 전이 이벤트 로그 실체화 (JSONL + 샤딩 + 하트비트) |
| `TASK-AR-620` | 실패 패턴 압축 파이프라인 |
| `TASK-AR-621` | 축3 패턴군 UI 통합 (InterviewPanel·AlignmentScorecard·QuizGate) |
| `TASK-AR-622` | orchestrator 권한 3분할 (planner·integrator 실체화) |
| `TASK-AR-623` | 에이전트 상호검증 debate 확장 (설명자·심문자·심판) |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
