---
id: TASK-AR-508
display_id: TASK-AR-508
task_uid: 41f58968-7dc2-4649-935c-7d327b075c9b
registered_at: 2026-06-12T21:53:22+09:00
created_at: 2026-06-12T21:53:22+09:00
started_at: 2026-06-12T21:55:08+09:00
updated_at: 2026-06-12T22:05:00+09:00
title: Agent-agnostic branch namespace in residue preservation (codex/* + claude/*)
status: in_progress
priority: P1
difficulty: S
est_hours: 3
est_tokens: 3000
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
  - branch-namespace
  - dirty-intake
  - preservation
---

# TASK-AR-508 - Agent-agnostic branch namespace preservation

## Goal

- dirty intake와 session baseline의 residue 보존 규칙이 `codex/*` 브랜치에
  하드코딩되어 있어 `claude/*` 브랜치 작업이 모든 보존 레이더(분류·스냅샷·
  원격 보존 판단)에서 빠진다. 에이전트 중립 접두사 집합으로 일반화한다.

## Context

- 실측(2026-06-12): codex 세션이 `claude/task-ar-500-footprint-conflict-gate`
  를 "codex-residue 보존 규칙에서 빠져 있다"고 보고. 같은 뿌리에서 발생한
  미추적 클레임 소실 사건은 AR-503에 기록.
- 하드코딩 위치: `scripts/dirty_intake.py` 88(목록)·161/216(분류)·170
  (`refs/heads/codex` 원격 보존), `scripts/session_baseline.py` 62(목록).
  디스패처 기본 브랜치 생성(`codex/` 접두사)은 codex 미머지 브랜치가
  수정 중이므로 본 task 범위 외.
- 두 파일과 테스트 모두 codex 미머지 브랜치 무접촉 확인 — 즉시 수정 안전.

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰 선행 필수.

## Scope

- `session_baseline.py`에 `AGENT_BRANCH_PREFIXES = ("codex/", "claude/")`
  단일 정의, 브랜치 열거를 접두사 집합 기반으로 일반화.
- `dirty_intake.py`의 목록·분류(startswith)·원격 보존(for-each-ref) 경로를
  같은 접두사 집합으로 일반화. 기존 JSON 키(`active_codex_branches`)와
  함수명은 호환성 위해 유지.
- 테스트에 claude/* residue 분류·보존 케이스 추가.

## Out Of Scope

- 디스패처 기본 브랜치 접두사 변경 (codex 미머지 브랜치와 충돌).
- 클레임 기반 보존(브랜치가 클레임에 등록되면 접두사 무관 보존) — AR-503/505
  이후 후속.

## Acceptance Criteria

- claude/* 브랜치·워크트리가 codex/*와 동일하게 residue로 분류·보존된다.
- 기존 codex/* 동작 회귀 없음 (`pytest tests/test_dirty_intake.py
  tests/test_session_baseline.py -q` 통과).
- 게이트 체인 exit 0.

## Evidence Targets

- `scripts/dirty_intake.py`, `scripts/session_baseline.py` 변경분 + 테스트
- closeout 시 독립 검증(W4b) 기록
