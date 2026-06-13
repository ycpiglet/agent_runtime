---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-334
work_uid: 6c29d210-c19d-437a-b0bc-7fd0266d44df
kind: task
parent_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-PLATFORM-EXTENSIONS
created_by: planner
id: TASK-AR-334
display_id: TASK-AR-334
task_uid: 6c29d210-c19d-437a-b0bc-7fd0266d44df
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 전역 검색 + 빠른 열기
status: completed
started_at: 2026-06-13T21:39:28+09:00
completed_at: 2026-06-13T22:10:00+09:00
resolution: done
verification_status: passed
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - search
---

# TASK-AR-334 - 전역 검색 + 빠른 열기

## Goal

- task/taskset/메시지/이벤트/evidence/reviews 문서를 한 검색창에서 풀텍스트로 찾고 즉시 이동한다 (Notion 검색 + Slack 연산자 모델).

## Scope

- `/api/search` 인덱스(경량, 파일 기반) + 타입/날짜/담당 연산자(`type:task status:blocked`).
- Ctrl+P 빠른 열기(최근·즐겨찾기), 검색 결과에 관련 커밋/리뷰 문서 링크 표면화.

## Acceptance Criteria

- 5종 이상 엔티티가 단일 검색에서 반환되고 결과 클릭 시 해당 뷰/상세로 딥링크된다.

## Evidence Targets

- 검색 인덱스 모듈, UI 검색창, 테스트
