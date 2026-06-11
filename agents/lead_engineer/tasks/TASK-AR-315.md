---
id: TASK-AR-315
display_id: TASK-AR-315
task_uid: ee3763c2-877b-499f-8bb2-5aa0bfeb5686
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
updated_at: 2026-06-11T17:58:45+09:00
title: Provider-live eval로 모델 정확도 0.90 목표 검증
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - eval
  - quality-loop
  - measurement
---

# TASK-AR-315 - Provider-live eval로 모델 정확도 0.90 목표 검증

## Goal

- 결정적 계약 베이스라인(현 1.0 대체 통과)이 가리고 있는 실제 모델 출력 정확도(offline 0.6667 vs 목표 0.90) 격차를 provider-live 평가로 측정하고 마감 기준을 확정한다.

## Scope

- golden set 기반 provider-live 평가 러너 구성 (`scripts/offline_eval_gate.py` 확장 또는 별도 러너).
- 실패 케이스를 `scripts/correction_collector.py` 루프에 연결.
- 0.90 미달 시 격차 원인 분류와 개선 제안을 evidence로 기록.

## Acceptance Criteria

- provider-live 점수가 측정되어 evidence 레코드로 저장된다.
- 통과 기준(0.90) 충족 또는 미충족 시 후속 태스크 제안이 기록된다.

## Evidence Targets

- `agents/project/evidence/evaluations/`
- eval 러너 스크립트 및 리포트
