---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-363
work_uid: 86672244-5c17-43a9-ab26-ded26488f9d2
kind: task
parent_id: TASKSET-AR-UI-LIVING-CONSOLE
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-LIVING-CONSOLE
created_by: planner
id: TASK-AR-363
display_id: TASK-AR-363
task_uid: 86672244-5c17-43a9-ab26-ded26488f9d2
registered_at: 2026-06-11T19:48:00+09:00
created_at: 2026-06-11T19:48:00+09:00
updated_at: 2026-06-11T19:48:00+09:00
title: 성장 시스템 — 프로젝트 Lv·사업 단계·XP 산식 + 게임화 가드레일
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-LIVING-CONSOLE
tags:
  - gamification
  - progression
  - metrics
---

# TASK-AR-363 - 성장 시스템 — 프로젝트 Lv·사업 단계·XP 산식 + 게임화 가드레일

## Goal

- 프로젝트의 성숙도를 진화하는 캐릭터처럼 측정·표시한다: 프로젝트 Lv.N(누적 경험), 사업 단계 칭호(garage→seed→startup→scaleup→unicorn), 에이전트별 XP — 단 실증된 역효과를 막는 가드레일과 함께.

## Scope

- XP 산식: 완료 task 수·게이트 통과·테스트 증가·리뷰 산출 가중합. **토큰 소비는 XP 직접 가산 금지**(낭비 유인) — "누적 경험"과 "효율 스탯"(task당 토큰, 재작업률) 분리 표시.
- 프로젝트 Lv = 누적 XP 곡선, 사업 단계 = 마일스톤/릴리스 달성 기반 칭호.
- 에이전트 XP/레벨: 역할별 완료 실적 기반, 팀 단위 성취 우선(관계성 g=1.776 — 메타분석 근거).
- 가드레일(연구 근거): 처벌 메커니즘 금지(Habitica 역효과), 스트릭/연속일 압박 금지(GitHub 제거 사례), 피드백 가시성 확보, 전체 토글(TASK-AR-340 폴리시와 통합).

## Acceptance Criteria

- Lv/단계/XP가 실데이터에서 계산·표시되고 가드레일 위반 메커니즘이 없음을 체크리스트로 검증.

## Evidence Targets

- 산식 정의 문서, 지표 어댑터, Home 위젯
