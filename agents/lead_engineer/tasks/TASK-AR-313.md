---
id: TASK-AR-313
display_id: TASK-AR-313
task_uid: 753d8012-6dd1-46ef-a8b1-7a1da9d0f1f1
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-11T23:16:07+09:00
updated_at: 2026-06-11T23:16:07+09:00
title: ToolRunner 명령 정책 강화 (IMPLEMENTATION_PLAN Phase 3)
status: in_progress
priority: P1
difficulty: M
est_hours: 6
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - security
  - tool-runner
  - loop-engineering
---

# TASK-AR-313 - ToolRunner 명령 정책 강화 (IMPLEMENTATION_PLAN Phase 3)

## Goal

- 광범위한 python 허용 목록을 정확한 명령 프로파일(ci/owner/research)로 좁혀 임의 코드 실행 경로를 제거한다.

## Scope

- IMPLEMENTATION_PLAN.md Phase 3 수용 기준 이행.
- 프로파일별 허용 명령 정의와 위반 시 차단 동작.
- 부정 보안 테스트(우회 시도 차단) 추가.

## Acceptance Criteria

- Phase 3 수용 기준 전 항목 통과, 부정 테스트 포함 pytest 통과.

## Evidence Targets

- `IMPLEMENTATION_PLAN.md` Phase 3 섹션
- ToolRunner 정책 코드 및 테스트
