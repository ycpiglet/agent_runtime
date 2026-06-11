---
id: TASK-AR-321
display_id: TASK-AR-321
task_uid: 94aac41d-b95b-4ba6-9666-6f6d6d6852ff
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: 사이드바 정보 구조 개편 + 해시 라우팅
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - ia
  - navigation
---

# TASK-AR-321 - 사이드바 정보 구조 개편 + 해시 라우팅

## Goal

- 9개 수평 탭을 접이식 좌측 사이드바(Home / WORK / AGENTS / COMMS / RECORDS / OPS 그룹)로 전환해 V2 뷰 확장을 수용한다.

## Scope

- 플랜 §2.2 사이드바 구조 구현, 아이콘 레일 접힘, 활성 taskset 진행률 고정 노출.
- URL 해시 라우팅으로 딥링크/뒤로가기 지원.
- 기존 9개 뷰를 신규 그룹에 재배치(기능 손실 없이).

## Acceptance Criteria

- 모든 기존 뷰 접근 가능 + 딥링크 동작 + 모바일에서 오버레이 사이드바로 동작.

## Evidence Targets

- `src/agent_runtime/ui_console.py`, Playwright 검증 기록
