---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-360
work_uid: 762e5eb1-7263-41c3-b8c8-a54a156d616b
kind: task
parent_id: TASKSET-AR-UI-LIVING-CONSOLE
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-LIVING-CONSOLE
created_by: planner
id: TASK-AR-360
display_id: TASK-AR-360
task_uid: 762e5eb1-7263-41c3-b8c8-a54a156d616b
registered_at: 2026-06-11T19:48:00+09:00
created_at: 2026-06-11T19:48:00+09:00
updated_at: 2026-06-11T19:48:00+09:00
title: Idea Vault 운영 규칙 — 재발굴 루프 + 프로세스 A/B 실험
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-LIVING-CONSOLE
tags:
  - idea-vault
  - rsi
  - ab-test
  - governance
---

# TASK-AR-360 - Idea Vault 운영 규칙 — 재발굴 루프 + 프로세스 A/B 실험

## Goal

- 기각/보류 아이디어를 폐기하지 않고 보존·재발굴하는 체계를 RSI 운영 원칙으로 정착시킨다 (Owner 통찰: 진화 시 과거를 잊지 않고 주기적으로 재평가·A/B 검증).

## Scope

- `agents/project/idea-vault/IDEA-VAULT.md` 레지스트리 운영 규칙 확정 (시드 11건 등록 완료).
- 재발굴 루프: retro/planning scan이 `revisit_after` 도래 항목을 Owner 제안으로 자동 재상정.
- 부활 시 프로세스 A/B 실험 규약: 한 변수씩, 측정 지표·기간 선정, 결과로 채택/재보류 결정 (Measured Improvement 원칙과 통합).
- 모든 신규 보류 결정이 Vault 등록을 거치도록 게이트/체크리스트 연결.
- UI: Vault 패널(보류 사유·부활 조건·기한 표시, 수동 부활 버튼).

## Acceptance Criteria

- revisit_after 도래 항목이 planning 제안으로 생성되는 흐름이 테스트로 증명된다.
- 선행 사례 정합: Icebox/ADR superseded/resurfacing 패턴 매핑 문서화.

## Evidence Targets

- `agents/project/idea-vault/IDEA-VAULT.md`, planning scan 연동 코드, 테스트

## W4a Self-Verification (inst-ui1-ar360)

- Branch `claude/task-ar-360-ui` rebased on `origin/main` (cb22565).
- Files: `scripts/idea_vault.py` (new), `tests/test_idea_vault.py` (new),
  `scripts/planning_loop.py` (`_scan_idea_vault` + `idea_vault_revival` action
  mapping), `agents/project/idea-vault/IDEA-VAULT.md` (operating rules + A/B
  protocol + precedent map), `agents/project/WORK-SCHEMA.yml` and template copy
  (`origin_type` enum += `idea_vault_revival`).
- Focused: `python -m pytest tests/test_idea_vault.py -q` -> 12 passed.
- Full: `python -m pytest tests -q` -> 741 passed (0:10:04).
- Gate: `python scripts/owner_governance_gate.py` -> exit 0, all sub-gates
  findings=0.
- Demo: `python scripts/idea_vault.py due --now 2027-01-01` -> 12 due seeds,
  exit 0, ASCII-safe stdout.
- Revive verified proposal-only: emits `origin_type: idea_vault_revival`,
  `proposal_output: owner_decision`, `canonical_mutation_allowed: false`, no
  task created.

### W4b follow-up (REQUEST-CHANGES addressed)

- Finding 1 (important): `cmd_defer` lacked a terminal-status guard, so deferring
  an `adopted`/`retired` entry would corrupt permanent decision-history. Fixed by
  adding the same `TERMINAL_STATUS` guard `cmd_revive` uses (extracted to a shared
  `TERMINAL_STATUS = {"adopted", "retired"}` constant).
- Note A: parametrized `test_revive_rejects_terminal_status` over `adopted`+`retired`
  and added `test_defer_rejects_terminal_status` (same coverage).
- Note B: documented `revive` idempotency on already-`revived` entries in
  IDEA-VAULT.md command rules.
- Note C: tightened `test_real_registry_validates` seed-count assertion to `>= 12`.
- Re-verify: focused 15 passed; full `pytest tests -q` -> 744 passed (0:05:49);
  `owner_governance_gate.py` -> exit 0; defer-on-adopted CLI demo -> exit 1, entry
  unchanged.
