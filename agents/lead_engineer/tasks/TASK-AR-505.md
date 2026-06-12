---
id: TASK-AR-505
display_id: TASK-AR-505
task_uid: 69f8bed3-e0df-47d8-a847-4d16529b6a33
registered_at: 2026-06-12T21:15:09+09:00
created_at: 2026-06-12T21:15:09+09:00
updated_at: 2026-06-12T21:15:09+09:00
title: Worktree/branch lifecycle gate — zombie detection and retention policy
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - parallel
  - worktree-hygiene
  - lifecycle
  - gate
---

# TASK-AR-505 - Worktree/branch lifecycle gate

## Goal

- 작업 수명주기의 W5(통합 후 정리) 단계를 실행 가능하게 만든다: merge
  완료 + claim released 상태의 좀비 워크트리/브랜치를 검출하고, retention
  정책에 따라 정리해 "더러운 워크트리"와 ahead/behind 적체를 구조적으로
  소멸시킨다.

## Context

- 실측(2026-06-12): 워크트리 11개 중 3개가 좀비 — TASK-AR-316(behind=14),
  TASK-AR-320(behind=3), TASK-AR-369(behind=6), 전부 ahead=0 (merge 완료).
  정리 단계가 수명주기에 없어 누적.
- 단순 일괄 삭제는 금지 — git 이력에 "Preserve TASK-AR-369 worktree
  branch" 등 의도적 보존 결정이 존재한다. 보존 태그 예외가 필요하다.
- 규칙 기록: `reviews/MEETING-2026-06-12-parallel-work-lifecycle-rules.md` (W0~W6).

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰 선행 필수.

## Scope

- `scripts/worktree_lifecycle_gate.py`: `.worktrees/*` 전수 스캔 —
  (a) 좀비 판정: 브랜치 ahead=0 + 대응 claim released/completed + dirty 0
  (b) retention 정책: closeout 리뷰 merge 후 보존 기간(기본 7일) 또는
  명시 보존 태그(`preserve` claim tag / PRESERVE 마커 파일) 시 면제
  (c) `--check` watch finding 보고 / `--clean` 정리 실행(worktree remove +
  merge된 브랜치 삭제, 보존 예외 제외).
- stale claim(만료 lease + 미해제)도 같은 스캔에서 watch로 보고.
- owner governance 체인 편입은 watch 전용(비차단) — 정리는 orchestrator
  수동/주기 실행.
- 기존 좀비 3개를 정책 결정 후 일괄 처리하고 결과를 closeout에 기록.
- 템플릿 미러 동기화.

## Out Of Scope

- merge 자체의 자동화(AR-502 머지 큐).
- 미머지(ahead>0) 브랜치 정리 — 활성 작업 보호.

## Acceptance Criteria

- 좀비 조건 충족 워크트리가 finding으로 보고되고, `--clean`이 보존 예외를
  제외하고 제거한다.
- ahead>0 또는 dirty 워크트리는 절대 정리 대상이 되지 않는다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- `scripts/worktree_lifecycle_gate.py` + 테스트
- 기존 좀비 3개 처리 기록
- closeout review record
