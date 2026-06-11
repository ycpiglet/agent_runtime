---
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
