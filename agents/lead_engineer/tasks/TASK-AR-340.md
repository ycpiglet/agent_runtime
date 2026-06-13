---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-340
work_uid: 0b3562e5-8bf0-4656-9834-1fd74f743b43
kind: task
parent_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-PLATFORM-EXTENSIONS
created_by: planner
id: TASK-AR-340
display_id: TASK-AR-340
task_uid: 0b3562e5-8bf0-4656-9834-1fd74f743b43
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 마이크로인터랙션/게임화 폴리시 (토글형)
status: completed
started_at: 2026-06-13T23:59:13+09:00
completed_at: 2026-06-14T01:30:00+09:00
resolution: done
verification_status: passed
priority: P3
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - animation
  - gamification
---

# TASK-AR-340 - 마이크로인터랙션/게임화 폴리시 (토글형)

## Goal

- 콘솔에 생동감을 더하는 애니메이션/이펙트와 RPG형 게임화 요소를 토글 가능한 폴리시 레이어로 추가한다 (기본은 차분한 진지 모드).

## Scope

- 마이크로인터랙션: 상태 전이 애니메이션, 드래그 물리감, 스켈레톤 로딩, 낙관적 업데이트, 토스트.
- 게임화(설정에서 on): taskset 완료 셀레브레이션(컨페티), 에이전트 XP/레벨/스트릭(완료 task·게이트 통과 기반), 퀘스트 보드 용어 모드, 완료 사운드(기본 off).
- 온보딩 투어, 빈 상태(empty state) 일러스트, 컨텍스트 도움말.
- 접근성: `prefers-reduced-motion` 존중, 애니메이션 전체 끄기.

## Acceptance Criteria

- 게임화 off 시 잔여 효과가 없고, reduced-motion 환경에서 애니메이션이 비활성화된다.

## Evidence Targets

- 설정 패널, 폴리시 레이어 코드, Playwright 검증
