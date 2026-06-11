---
id: TASK-AR-308
display_id: TASK-AR-308
task_uid: 0985351f-c25e-4f9e-84ba-05246ce4f7ca
registered_at: 2026-06-11T17:34:00+09:00
created_at: 2026-06-11T17:34:00+09:00
started_at: 2026-06-11T22:28:32+09:00
updated_at: 2026-06-11T22:28:32+09:00
completed_at: 2026-06-11T22:28:32+09:00
title: 기능·비전 전략 분석 후속 우선순위 결정
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-OPS-FEEDBACK-ANALYSIS
tags:
  - analysis
  - vision
  - rsi
  - a2a
  - planning
---

# TASK-AR-308 - 기능·비전 전략 분석 후속 우선순위 결정

## Goal

- Ralph/Loop Engineering, Multi-agent/A2A, 측정 가능한 평가·검증, backlog UI/task management, 추적 가능한 문서 관리 관점의 2026-06-11 종합 분석을 바탕으로 다음 전략 무브를 Owner가 결정한다 (분석/계획 전용).

## Scope

- 제안된 5대 전략 무브 검토: (1) Evidence-to-Proposal OS 완성(TASK-AR-297~301), (2) ToolRunner 강화 + race-safe claim(IMPLEMENTATION_PLAN Phase 3-4), (3) A2A 라이프사이클 end-to-end 검증(TASK-AR-302) + RBAC, (4) 스킬 레이어 패키징, (5) UI 실시간화(SSE) + Planner 승인 워크플로.
- 리스크 검토: C-mode 조기 승격, offline eval 0.6667 vs 0.90 격차, 멀티에이전트 동시 실행 미검증, 스킬 재사용성 미패키징.

## Acceptance Criteria

- 5대 무브 각각에 대한 채택 여부와 착수 순서가 기록된다.
- C-mode 승격 보류 조건(회귀 픽스처/제안 품질 지표)이 재확인된다.

## Evidence Targets

- `reviews/REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session.md` (분석 전문 수록)

## Strategy Decision

| Move | Decision | Start Order | Registered Work |
| --- | --- | ---: | --- |
| Evidence-to-Proposal OS 완성 | 채택 | 1 | `TASKSET-AR-RSI-OPERATING-SYSTEM` (`TASK-AR-297`~`TASK-AR-305`) |
| ToolRunner 강화 + race-safe claim | 채택 | 2 | `TASK-AR-313`, `TASK-AR-314` |
| A2A 라이프사이클 end-to-end 검증 + RBAC | 채택 | 3 | `TASK-AR-302`, `TASK-AR-311`, `TASK-AR-312` |
| 스킬 레이어 패키징 | 채택 | 4 | `TASK-AR-304`, `TASK-AR-316` |
| UI 실시간화 + Planner 승인 워크플로 | 채택 | 5 | `TASK-AR-317`, `TASK-AR-326` |

## C-mode Hold Conditions

- C-mode 자동 적용은 보류한다.
- 승격 전 최소 조건은 proposal quality metric(`TASK-AR-300`), failure/compound casebook(`TASK-AR-299`), council review(`TASK-AR-301`), A2A lifecycle 검증(`TASK-AR-302`), provider-live eval 0.90 검증(`TASK-AR-315`)이다.
- offline eval 0.6667 vs 0.90 격차는 "대체 통과"가 아니라 C-mode 보류 신호로 유지한다.

## Priority Rationale

- 1순위는 evidence-to-proposal 품질 기반이다. 이 레이어가 약하면 ToolRunner, A2A, UI 승인이 모두 잘못된 제안을 빠르게 실행하는 경로가 된다.
- 2~3순위는 실행 안전성이다. command policy, claim race safety, A2A/RBAC가 안정돼야 멀티에이전트 운영을 확대할 수 있다.
- 4~5순위는 재사용성과 조작 표면이다. 스킬 패키징과 UI 실시간화는 앞선 evidence/claim 기반이 검증된 뒤 효과가 커진다.
