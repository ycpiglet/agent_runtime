---
id: TASK-AR-331
display_id: TASK-AR-331
task_uid: 4e31081e-e142-4e24-9d75-3c0548438d32
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 커스텀 속성·라벨 + 자동화 규칙 편집기 + 트리아지 큐
status: planned
priority: P2
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - properties
  - automation
  - triage
---

# TASK-AR-331 - 커스텀 속성·라벨 + 자동화 규칙 편집기 + 트리아지 큐

## Goal

- Notion형 커스텀 속성과 Monday/ClickUp형 "when X then Y" 자동화 규칙, Linear형 트리아지 큐를 제공한다.

## Scope

- 커스텀 속성(텍스트/선택/숫자/날짜)을 task frontmatter 확장으로 정의·표시·필터 연동.
- 라벨 관리 UI(색·이름·사용처 카운트).
- 자동화 규칙 편집기: 트리거(상태 변경/기한 경과/blocked 지속)→액션(보드 재생성, 에스컬레이션 메시지, 라벨 부여). 실행은 기존 훅/게이트 체계 경유 — UI는 규칙 CRUD만.
- 트리아지 큐: 미분류(taskset 없음)·지연·blocked 장기화 task 자동 수집 인박스.

## Acceptance Criteria

- 규칙이 선언적 파일로 저장되고 게이트 체인에서 실행되며 UI에서 활성/비활성 토글된다.

## Evidence Targets

- 자동화 규칙 스키마/스크립트, `ui_commands.py`, 테스트
