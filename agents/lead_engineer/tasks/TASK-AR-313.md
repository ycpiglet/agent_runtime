---
id: TASK-AR-313
display_id: TASK-AR-313
task_uid: 753d8012-6dd1-46ef-a8b1-7a1da9d0f1f1
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-11T23:16:07+09:00
updated_at: 2026-06-11T23:26:35+09:00
title: ToolRunner 명령 정책 강화 (IMPLEMENTATION_PLAN Phase 3)
status: completed
completed_at: 2026-06-11T23:26:35+09:00
priority: P1
difficulty: M
est_hours: 6
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - security
  - tool-runner
  - loop-engineering
---

# TASK-AR-313 - ToolRunner 명령 정책 강화 (IMPLEMENTATION_PLAN Phase 3)

## Goal

- 광범위한 python 허용 목록을 정확한 명령 프로파일(ci/owner/research)로 좁혀 임의 코드 실행 경로를 제거한다.

## Scope

- IMPLEMENTATION_PLAN.md Phase 3 수용 기준 이행.
- 프로파일별 허용 명령 정의와 위반 시 차단 동작.
- 부정 보안 테스트(우회 시도 차단) 추가.

## Acceptance Criteria

- Phase 3 수용 기준 전 항목 통과, 부정 테스트 포함 pytest 통과.

## Evidence Targets

- `IMPLEMENTATION_PLAN.md` Phase 3 섹션
- ToolRunner 정책 코드 및 테스트

## Completion - 2026-06-11

- Result: `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`의 기존 profile-scoped ToolRunner 정책이 Phase 3 기준을 충족하는지 재검증하고, profile별 부정 테스트를 보강했다.
- Existing policy confirmed:
  - default `ci` profile is strict and deterministic.
  - read-only git is allowed by default; mutable git is blocked outside explicit owner allowlist.
  - Python execution is restricted to `python -m pytest`, `scripts/check_agent_docs.py`, `scripts/check_messages.py`, and `scripts/agent_orchestrator.py status --json`.
  - `python -c`, `python -`, pip/module installs, shell control tokens, and repo path escapes are denied.
- Added test coverage:
  - research profile blocks mutable git, pip, and non-help agent worker execution.
  - owner profile blocks mutable git path escapes.
  - pytest unknown flags are blocked.
- Closeout review: `reviews/REVIEW-2026-06-11-toolrunner-policy-closeout.md`.
- Verification:
  - `pytest tests/test_template_agent_tools.py -q` -> 19 passed.
  - `python -m py_compile src/agent_runtime/templates/project/scripts/providers/agent_tools.py` -> pass.
  - `pytest tests -q` -> 390 passed in 372.82s.
  - `python -m py_compile scripts/backlog_board.py` -> pass.
  - `pytest tests/test_backlog_board_tasksets.py tests/test_template_agent_tools.py -q` -> 22 passed.
  - `python scripts/owner_governance_gate.py` -> exit 0.
