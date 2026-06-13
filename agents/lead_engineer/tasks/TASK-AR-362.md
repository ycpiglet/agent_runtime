---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-362
work_uid: c8740b62-ba07-4e05-b9d8-02790400186a
kind: task
parent_id: TASKSET-AR-UI-LIVING-CONSOLE
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-LIVING-CONSOLE
created_by: planner
id: TASK-AR-362
display_id: TASK-AR-362
task_uid: c8740b62-ba07-4e05-b9d8-02790400186a
registered_at: 2026-06-11T19:48:00+09:00
created_at: 2026-06-11T19:48:00+09:00
updated_at: 2026-06-11T19:48:00+09:00
title: 전역 직접 조작 레이어 — hover peek + DnD 1급 동사 + 키보드 등가
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-LIVING-CONSOLE
tags:
  - interaction
  - hover
  - drag-drop
  - accessibility
---

# TASK-AR-362 - 전역 직접 조작 레이어 — hover peek + DnD 1급 동사 + 키보드 등가

## Goal

- hover 미리보기와 드래그앤드롭을 콘솔 전역의 1급 상호작용 동사로 표준화한다 (Notion peek + Discord 접근성 DnD 패턴).

## Scope

- hover peek: task/에이전트/taskset/evidence 링크에 호버 시 요약 카드(지연 300ms, Esc 닫기).
- DnD 표준화: 칸반 상태 변경, taskset 간 이동, 회의실 투입, 첨부 업로드를 단일 DnD 프레임워크로 — 드롭 가능 영역 하이라이트, 유효성 피드백.
- 키보드 등가: 들기(Ctrl+D)/이동(화살표)/드롭(Space)/취소(Esc) 전 DnD 동작에 제공.
- Agent Follow: 에이전트 아바타 클릭 → 해당 에이전트 활동 따라가기 모드 (Figma 멀티플레이어 패턴).

## Acceptance Criteria

- 모든 DnD 동작에 키보드 경로가 존재하고 hover peek가 3개 이상 엔티티에서 동작한다.

## Evidence Targets

- DnD/peek 공통 모듈, Playwright 검증
