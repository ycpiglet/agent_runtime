---
id: TASK-AR-500
display_id: TASK-AR-500
task_uid: 15e90de2-ca81-4611-8b6d-078de0a04e18
registered_at: 2026-06-12T18:35:45+09:00
created_at: 2026-06-12T18:35:45+09:00
updated_at: 2026-06-12T18:35:45+09:00
title: Claim-time footprint conflict gate (target_files intersection)
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
  - race_condition
  - cross_cutting
tags:
  - parallel
  - concurrency
  - gate
---

# TASK-AR-500 - Claim-time footprint conflict gate

## Goal

- 충돌 발견 시점을 merge-time(사후)에서 claim-time(사전)으로 옮긴다.
  새 클레임 생성 시 활성 클레임들의 선언 footprint(`target_files`)와
  교집합이 있으면 생성을 차단한다.

## Context

- unit spec frontmatter에 `target_files` 선언 필드가 이미 존재한다
  (`agents/lead_engineer/tasks/units/README.md`).
- 현재는 `parallel_worktree_gate`가 task 단위 단일 점유만 검사하고, 서로
  다른 task가 같은 파일을 만지는 경우는 merge에서야 발각된다.
- 설계 기록: `reviews/REVIEW-2026-06-12-agent-runtime-parallel-wave-scheduling-design.md`.

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰(차분 재계획 + anchor 갱신) 선행 필수. 근거: `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md`.

## Scope

- claim 레코드에 `target_files`(또는 unit 참조 시 unit에서 파생) 필드 채움.
- `scripts/task_claim_dispatcher.py create` 경로에 활성 클레임 footprint
  교집합 검사 추가 — 교집합 발생 시 차단 + 충돌 클레임 ID 보고.
- glob/디렉터리 prefix 매칭 지원 (`scripts/**` 류 선언).
- 검사 로직을 별도 게이트(`scripts/footprint_conflict_gate.py`)로 분리해
  `owner_governance_gate` 체인에 `--check` 모드로 편입.
- 템플릿 미러 동기화 (`src/agent_runtime/templates/project/scripts/`).

## Out Of Scope

- wave 묶음 발급(TASK-AR-501), 머지 큐(TASK-AR-502).
- 기존 완료 클레임의 소급 footprint 채움.

## Acceptance Criteria

- 교집합 있는 두 클레임 생성 시 두 번째가 명확한 사유와 함께 거부된다.
- 서로소 footprint 클레임 N개는 동시 활성 가능하다.
- `pytest tests -q` 통과, 게이트 체인 exit 0.

## Evidence Targets

- `scripts/footprint_conflict_gate.py` + 테스트
- `scripts/task_claim_dispatcher.py` 변경분
- closeout review record
