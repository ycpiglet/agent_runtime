---
id: TASK-AR-339
display_id: TASK-AR-339
task_uid: 9d3f5b16-fe29-4751-8184-966972e8beb1
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 운영 대시보드 — 토큰/비용·eval·게이트·번다운
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - dashboard
  - metrics
---

# TASK-AR-339 - 운영 대시보드 — 토큰/비용·eval·게이트·번다운

## Goal

- 운영 지표를 Grafana/Sentry형 대시보드로 상시 노출한다: 토큰/비용 추이, eval 점수, 게이트 pass/watch/block 보드, taskset 번다운/속도.

## Scope

- task/세션별 토큰·비용 집계(est_tokens 대비 실적), taskset당 예산 표시.
- offline/live eval 점수 추이 차트(evidence/evaluations 데이터), 게이트 상태 보드.
- taskset 번다운 차트와 완료 속도(주간 done 수).

## Acceptance Criteria

- 4종 지표 위젯이 Home/전용 뷰에서 렌더되고 출처 파일이 링크된다.

## Evidence Targets

- 지표 어댑터(`ui_state.py`), 대시보드 뷰
