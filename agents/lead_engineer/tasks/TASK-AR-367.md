---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-367
work_uid: eeebc386-16ba-457c-acc7-719937c053a9
kind: task
parent_id: TASKSET-AR-DOC-TO-PLAN
origin_type: planning_proposal
origin_ref: TASKSET-AR-DOC-TO-PLAN
created_by: planner
id: TASK-AR-367
display_id: TASK-AR-367
task_uid: eeebc386-16ba-457c-acc7-719937c053a9
registered_at: 2026-06-12T00:09:43+09:00
created_at: 2026-06-12T00:09:43+09:00
updated_at: 2026-06-15T12:01:39+09:00
title: Paperclip 기능 갭 분석 및 채택 결정 (예산 하드 스톱·heartbeat·멀티테넌시·플러그인)
status: completed
resolution: done
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-DOC-TO-PLAN
tags:
  - paperclip
  - benchmark
  - analysis
  - cost-control
started_at: 2026-06-15T12:01:39+09:00
completed_at: 2026-06-15T12:01:39+09:00
verification_status: passed
review_refs:
  - reviews/REVIEW-2026-06-15-paperclip-gap-adoption-decision.md
  - reviews/REVIEW-2026-06-15-doc-to-plan-closeout.md
---

# TASK-AR-367 - Paperclip 기능 갭 분석 및 채택 결정

## Goal

- 비전이 동일한 오픈소스 Paperclip(github.com/paperclipai/paperclip, MIT)의 기능 중 agent_runtime에 없는 4개 축의 채택 여부와 구현 방식을 결정한다 (분석/결정 태스크).

## Scope

- 에이전트별 예산 하드 스톱: 월/taskset 예산 도달 시 정지 — AR-368 실측 캡처 위에 강제 레이어 설계.
- Heartbeat 실행 수명주기: 예약 wakeup→예산 체크→워크스페이스 해석→스킬 로딩→구조화 로그 — 기존 세션/cron(AR-335) 모델과 비교, 채택 범위 결정.
- 멀티 컴퍼니/테넌시: 완전 데이터 격리 모델 vs 현 멀티 호스트(AR-341) — 격리 수준 결정.
- 플러그인(out-of-process worker) vs 선언적 위젯(AR-341): 보안 경계 비교.
- 소스 코드 직접 검토(MIT) 포함, 채택/보류 각각 근거 기록. 보류분은 Idea Vault 등록.

## Acceptance Criteria

- 4개 축 각각 채택/보류/수정 판정과 후속 구현 태스크 목록이 기록된다.

## Evidence Targets

- 분석 review 문서, Idea Vault 갱신, 후속 태스크 등록 기록
