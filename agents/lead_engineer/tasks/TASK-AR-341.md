---
id: TASK-AR-341
display_id: TASK-AR-341
task_uid: b1d9446c-cfd5-4fbb-b6bf-5a0e975aef29
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 워크스페이스 스위처 + 위젯 확장 포인트 + i18n
status: planned
priority: P3
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - workspace
  - extensibility
  - i18n
---

# TASK-AR-341 - 워크스페이스 스위처 + 위젯 확장 포인트 + i18n

## Goal

- 멀티 호스트 프로젝트(agent_runtime, autofolio 등)를 Notion 워크스페이스처럼 전환하고, 대시보드 위젯 확장 포인트와 KR/EN 국제화를 제공한다.

## Scope

- 워크스페이스 스위처: `--root` 전환 UI(등록된 호스트 프로젝트 목록), 프로젝트별 최근 상태 미리보기 — sync/템플릿 체계가 전제하는 멀티 호스트 활용.
- 위젯 확장 포인트: Home 대시보드 카드를 선언적 정의(JSON/YAML)로 추가하는 경량 플러그인 규약 + 단축키 커스텀.
- i18n: UI 문자열 KR/EN 리소스화, 설정에서 전환.

## Acceptance Criteria

- 두 개 이상 호스트 프로젝트 간 전환이 동작하고, 샘플 커스텀 위젯이 선언만으로 렌더된다.

## Evidence Targets

- 워크스페이스 스위처, 위젯 규약 문서, i18n 리소스
