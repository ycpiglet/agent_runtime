---
id: TASK-AR-320
display_id: TASK-AR-320
task_uid: 02490505-11c7-47cc-b1a7-6b8c5493bab9
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: 테마 시스템 — Notion형 라이트 기본 + Dark Mode 토글
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - theme
  - design-system
---

# TASK-AR-320 - 테마 시스템 — Notion형 라이트 기본 + Dark Mode 토글

## Goal

- 기본 테마를 Notion형 라이트로 전환하고 기존 Linear 다크 토큰을 Dark Mode 옵션으로 보존한다.

## Scope

- 모든 색상을 시맨틱 토큰으로 이원화(`docs/superpowers/plans/2026-06-11-ui-ux-v2-console.md` §2.1 라이트 토큰 초안).
- 헤더 토글 + `prefers-color-scheme` 자동 감지 + localStorage 저장.
- 상태색(green/amber/red/blue/purple) 의미 체계는 양 테마에서 유지.

## Acceptance Criteria

- 전 뷰가 토큰만으로 라이트/다크 전환되고 라벨 없는 색상 의존이 없다(접근성 대비 기준 유지).

## Evidence Targets

- `src/agent_runtime/ui_console.py`, `docs/design/agent-runtime/DESIGN.md` Amendment
