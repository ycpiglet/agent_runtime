---
id: TASK-AR-310
display_id: TASK-AR-310
task_uid: 9f5e2229-3d3e-44df-9466-0727be021341
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-11T22:14:43+09:00
updated_at: 2026-06-11T23:01:07+09:00
title: tag_manual 의존성 해소 및 완전 독립
status: completed
completed_at: 2026-06-11T23:01:07+09:00
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - migration
  - independence
  - gate
  - fixture
---

# TASK-AR-310 - tag_manual 의존성 해소 및 완전 독립

## Goal

- 레거시 전신 프로젝트(tag_manual)에 대한 라이브 의존을 모두 해소해 이관을 최종 마감하고, agent_runtime이 레거시 참조 없이 완전히 독립하도록 한다.

## Scope

- `scripts/co_location_gate.py`의 `DEFAULT_MIGRATION_MAP`(agents/project/MIGRATION-COMPAT-MAP.yml) 의존을 일반화하거나 제거.
- `tests/fixtures/host/agent_runtime.lock.json`의 `MIGRATION-COMPAT-MAP.example.yml` 해시 항목 갱신/제거.
- `agents/project/MIGRATION-COMPAT-MAP.yml`, `MIGRATION-HOLD-ROUTING.yml`, `MIGRATION-COMPAT-MAP.example.yml`을 라이브 트리에서 제거하고 감사 기록은 reviews/ 스냅샷으로 보존.
- `src/agent_runtime/templates/project/AGENTS.md`의 MIGRATION 참조 일반화.
- `BACKLOG.md`, `STATUS.md`, `AGENTIC_KNOWLEDGE_EVAL_PLAN.md` 활성 문서의 tag_manual 표기를 레거시 중립 표기로 일반화 (reviews/, TASK closeout 등 불변 역사 기록은 보존).
- `agents/project/README.md` 목록에서 제거된 파일 반영.

## Acceptance Criteria

- `rg -i tag_manual` 결과가 reviews/ 및 마감된 TASK closeout 기록에서만 발견된다.
- `python scripts/owner_governance_gate.py` exit 0, `pytest tests -q` 통과.
- 이관 마감 선언과 보존 스냅샷 위치가 closeout review에 기록된다.

## Evidence Targets

- `reviews/REVIEW-*-tag-manual-independence-closeout.md`
- `scripts/co_location_gate.py`
- `tests/fixtures/host/agent_runtime.lock.json`

## Completion - 2026-06-11

- Result: 라이브 전신 프로젝트 의존을 제거하고 이관 증거를 `reviews/` 스냅샷으로 고정했다.
- Gate change: `scripts/co_location_gate.py`는 기본 실행에서 live migration map을 요구하지 않고, `--migration-map`이 명시된 경우에만 archive map을 검증한다.
- Removed live overlay files:
  - `agents/project/MIGRATION-COMPAT-MAP.yml`
  - `agents/project/MIGRATION-HOLD-ROUTING.yml`
  - `agents/project/MIGRATION-COMPAT-MAP.example.yml`
  - `src/agent_runtime/templates/project/agents/project/MIGRATION-COMPAT-MAP.example.yml`
- Preserved snapshots:
  - `reviews/MIGRATION-COMPAT-MAP-2026-06-11-SNAPSHOT.yml`
  - `reviews/MIGRATION-HOLD-ROUTING-2026-06-11-SNAPSHOT.yml`
  - `reviews/MIGRATION-COMPAT-MAP-EXAMPLE-2026-06-11-SNAPSHOT.yml`
  - `reviews/TEMPLATE-MIGRATION-COMPAT-MAP-EXAMPLE-2026-06-11-SNAPSHOT.yml`
- Active docs updated: `BACKLOG.md`, `STATUS.md`, `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`, `BACKLOG-BOARD.md`, `agents/project/README.md`, `agents/project/PROJECT-CONTEXT.yml`, `agents/project/RELEASE-GATE-TEMPLATE.yml`, `src/agent_runtime/templates/project/AGENTS.md`.
- Fixture updated: `tests/fixtures/host/agent_runtime.lock.json` regenerated after template example removal.
- Closeout review: `reviews/REVIEW-2026-06-11-tag-manual-independence-closeout.md`.
- Verification:
  - `rg -n -i "tag_manual" -g "!reviews/**" -g "!agents/lead_engineer/tasks/**" -g "!agents/runtime/task_claims/**" .` -> exit 1, no live matches.
  - `python scripts/co_location_gate.py --out reviews/CO-LOCATION-GATE-2026-06-11-task-ar-310.json` -> pass, findings=0.
  - `pytest tests/test_co_location_gate.py -q` -> 2 passed.
  - `python -m py_compile scripts/co_location_gate.py scripts/backlog_board.py` -> pass.
  - `python scripts/owner_governance_gate.py` -> exit 0.
  - `pytest tests -q` -> 384 passed in 457.08s.
