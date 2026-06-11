---
id: TASK-AR-307
display_id: TASK-AR-307
task_uid: 2457f407-5d44-4f83-a1e0-0d3176541638
registered_at: 2026-06-11T17:34:00+09:00
created_at: 2026-06-11T17:34:00+09:00
updated_at: 2026-06-11T17:34:00+09:00
title: 전사 구조 개선 분석 후속 계획 확정
status: planned
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-OPS-FEEDBACK-ANALYSIS
tags:
  - analysis
  - structure
  - planning
  - feedback
---

# TASK-AR-307 - 전사 구조 개선 분석 후속 계획 확정

## Goal

- 2026-06-11 전사 구조 분석에서 식별된 개선 항목을 Owner가 우선순위 결정할 수 있는 실행 계획으로 확정한다 (분석/계획 전용, 구현 없음).

## Scope

- HIGH: hook-logs 이중 구조 통합(.codex vs agents/runtime), 템플릿 backlog_board.py drift 동기화 게이트, .tmp 수명 정책.
- MEDIUM: reviews/ 평면 구조(368+ 파일) 네임스페이스화 + INDEX 자동 생성, agents/project/ config/release 분리, BACKLOG.md vs BACKLOG-BOARD.md 단일 소스 원칙, hook-log 로테이션, task identity 검증 게이트.
- LOW: tests/ 카테고리화(95 파일), docs/README, hook timeout SLA 문서화, .gitignore 정리.

## Acceptance Criteria

- 각 항목에 대해 채택/보류/기각과 근거가 기록된다.
- 채택 항목은 신규 taskset 또는 기존 taskset 산하 태스크로 등록된다.

## Evidence Targets

- `reviews/REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session.md` (분석 전문 수록)
