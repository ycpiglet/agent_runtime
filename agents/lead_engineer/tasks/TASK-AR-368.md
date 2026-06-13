---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-368
work_uid: 587a4f9e-5261-4a63-b7a8-300af15910d8
kind: task
parent_id: TASKSET-AR-DOC-TO-PLAN
origin_type: planning_proposal
origin_ref: TASKSET-AR-DOC-TO-PLAN
created_by: planner
id: TASK-AR-368
display_id: TASK-AR-368
task_uid: 587a4f9e-5261-4a63-b7a8-300af15910d8
registered_at: 2026-06-12T00:09:43+09:00
created_at: 2026-06-12T00:09:43+09:00
updated_at: 2026-06-12T00:09:43+09:00
title: 실측 지표 캡처 + 다요소 평가/정렬 기준 확장
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-DOC-TO-PLAN
tags:
  - metrics
  - actuals
  - sorting
  - evaluation
---

# TASK-AR-368 - 실측 지표 캡처 + 다요소 평가/정렬 기준 확장

## Goal

- 예상치(est_*)만 있는 현 체계에 실측치를 더해, task/taskset을 우선순위·난이도·예상/실제 토큰·예상/실제 시간·부서 등 다요소로 정렬·필터·평가할 수 있게 한다 (Owner 요구: "토큰 사용량은 적은데 사업 성숙도는 높다" 같은 평가가 가능해야 함).

## Scope

- task frontmatter 표준 확장: `actual_tokens`, `actual_hours`, `team` — 세션/클레임 로그에서 자동 집계해 closeout 시 기록.
- 효율 지표 단일 정의: 성과(완료·게이트 통과) / 비용(토큰·시간) — AR-363 성장 시스템 "효율 스탯"·AR-339 대시보드와 공유.
- 정렬/필터 기준 추가: AR-322 공통 리스트 패턴에 est/actual 편차, 효율, 부서 축 연동.
- Paperclip식 예산 경고 임계값의 데이터 기반 마련 (강제는 AR-367 결정 후).

## Acceptance Criteria

- 완료 task에 actual_*가 기록되고, est 대비 편차·효율로 보드 정렬이 동작한다.

## Evidence Targets

- frontmatter 스키마 확장, 집계 스크립트, 보드/필터 연동 테스트
