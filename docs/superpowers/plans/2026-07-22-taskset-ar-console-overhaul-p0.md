---
schema_version: agent-runtime-work-item/v1
work_id: TASKSET-AR-CONSOLE-OVERHAUL-P0
work_uid: b39556b1-7778-492d-aff5-4bdff61ebc5d
kind: taskset
id: TASKSET-AR-CONSOLE-OVERHAUL-P0
parent_id: INIT-AR-CONSOLE-OVERHAUL-P0
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P0
status: active
owner: lead_engineer
created_at: 2026-07-22T17:45:27+09:00
updated_at: 2026-07-22T17:45:27+09:00
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: 결정 비종속 quick-win 묶음. 신선도 배지·캐시 사각지대 해소, 홈 요약 위계 정리, 프론트 위생(죽은 코드·아이콘·i18n·다크베이스·칸반), 데이터 위생(타임스탬프 게이트·actuals/rework 자동화), 세션 delta·throughput 전달 씨앗, REPORTING-FORMAT/OPS 계약 봉합, requirements-lint·NEEDS CLARIFICATION 마커 씨앗. 1–2주.
---

# Console Overhaul P0 — Trust & Hygiene

## Goal

- 결정 비종속 quick-win 묶음. 신선도 배지·캐시 사각지대 해소, 홈 요약 위계 정리, 프론트 위생(죽은 코드·아이콘·i18n·다크베이스·칸반), 데이터 위생(타임스탬프 게이트·actuals/rework 자동화), 세션 delta·throughput 전달 씨앗, REPORTING-FORMAT/OPS 계약 봉합, requirements-lint·NEEDS CLARIFICATION 마커 씨앗. 1–2주.

## Tasks

| Task | Title |
| --- | --- |
| `TASK-AR-602` | 신뢰 복구 — 신선도 배지 + 캐시 사각지대 해소 |
| `TASK-AR-603` | 홈 위계 1차 — 요약 소음 제거 |
| `TASK-AR-604` | 프론트 위생 — 죽은 코드·아이콘·i18n·다크베이스·칸반 |
| `TASK-AR-605` | 데이터 위생 — 타임스탬프 게이트 + actuals/rework 자동 파생 |
| `TASK-AR-606` | 전달 씨앗 — 세션 delta + 보드 throughput |
| `TASK-AR-607` | Owner-facing 계약 봉합 — REPORTING-FORMAT + 참조 드리프트 |
| `TASK-AR-608` | 축3 씨앗 — requirements-lint + NEEDS CLARIFICATION 마커 + checkpoints 필드 |

## Unit Specs

| Unit | Task | Title |
| --- | --- | --- |
| `UNIT-TASK-AR-602-001` | `TASK-AR-602` | 상태 시그니처 감시 디렉터리 확장 + 홈 신선도 배지 배선 |
| `UNIT-TASK-AR-603-001` | `TASK-AR-603` | 전역 폼 스코프 축소 + 0건 그룹 렌더 생략 + 히어로 강등 |
| `UNIT-TASK-AR-604-001` | `TASK-AR-604` | 커맨드 팔레트 동기화 + 죽은 activateView 제거 + 아이콘/토큰/칸반 위생 |
| `UNIT-TASK-AR-605-001` | `TASK-AR-605` | 타임스탬프 단조성 게이트 + actuals/rework 자동 파생 |
| `UNIT-TASK-AR-606-001` | `TASK-AR-606` | session_dashboard flow delta 1줄 + 보드 throughput 숫자 |
| `UNIT-TASK-AR-607-001` | `TASK-AR-607` | REPORTING-FORMAT 복원 + response_contract_gate 강화 + OPS 참조 정정 |
| `UNIT-TASK-AR-608-001` | `TASK-AR-608` | requirements-lint 게이트 + NEEDS CLARIFICATION 마커 거부 |

## Verification

- `python scripts/task_identity.py check --check`
- `python scripts/work_item_classifier.py --check`
- `python scripts/taskset_work_gate.py --check`
