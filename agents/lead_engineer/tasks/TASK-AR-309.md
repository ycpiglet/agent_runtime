---
id: TASK-AR-309
display_id: TASK-AR-309
task_uid: d5458ef2-2dd5-47a3-9695-8c57a9eb6a31
registered_at: 2026-06-11T17:34:00+09:00
created_at: 2026-06-11T17:34:00+09:00
started_at: 2026-06-11T22:24:37+09:00
updated_at: 2026-06-11T22:28:32+09:00
completed_at: 2026-06-11T22:28:32+09:00
title: UI 배포 경로 가드 계획 (stale install/process 재발 방지)
status: completed
priority: P2
difficulty: S
est_hours: 2
est_tokens: 1500
owner: lead_engineer
task_set_id: TASKSET-AR-OPS-FEEDBACK-ANALYSIS
tags:
  - ui
  - doctor
  - guard
  - planning
---

# TASK-AR-309 - UI 배포 경로 가드 계획 (stale install/process 재발 방지)

## Goal

- 2026-06-11 "UI 미반영" 사건의 두 원인(비-editable stale 설치, 장수 구버전 서버 프로세스)이 재발하지 않도록 가드 방안을 계획한다 (계획 전용, 구현은 별도 승인).

## Scope

- `agent-runtime doctor`에 설치 경로 검사 추가 검토: `agent_runtime.__file__`이 저장소 src 밖이면 경고.
- ui-console 기동 시 빌드/커밋 식별자(예: git SHA)를 `/api/state` 또는 푸터에 노출해 사용자 화면에서 stale 여부 즉시 식별.
- 세션 closeout 스킬에 장수 ui-console 프로세스 감지/재시작 항목 추가 검토.

## Acceptance Criteria

- 가드 방식별 비용/효과와 채택 여부가 기록된다.

## Evidence Targets

- `reviews/REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session.md`

## Guard Decision

| Guard | Decision | Cost | Effect | Follow-up |
| --- | --- | --- | --- | --- |
| `agent_runtime doctor` install-path check | 채택 | Low | High - editable checkout이 아닌 site-packages 설치본을 즉시 경고한다. | `TASK-AR-20260611-2230-UI-STALE-GUARD` |
| UI commit/build identifier in `/api/state` and footer | 채택 | Low | High - 사용자가 보고 있는 서버가 현재 checkout인지 화면에서 바로 검증한다. | `TASK-AR-20260611-2230-UI-STALE-GUARD`, `TASK-AR-317` |
| long-running `ui-console` process detection in closeout/start flow | 채택 | Medium | Medium - 오래 떠 있던 8765 서버가 최신 코드를 가리는 사고를 줄인다. | `TASK-AR-20260611-2230-UI-STALE-GUARD` |
| automatic process kill/restart without Owner visibility | 기각 | Medium | Risky - 다른 pane의 관찰/시연 세션을 끊을 수 있다. | no task |
| full UI packaging/deployment redesign | 보류 | High | Medium - stale guard보다 범위가 크며 `TASK-AR-317` 이후 판단하는 편이 낫다. | `TASK-AR-317` 이후 재평가 |

## Closeout

- This task remains planning-only; no guard implementation was added here.
- Adopted guards are registered as `TASK-AR-20260611-2230-UI-STALE-GUARD` to avoid mixing incident prevention with the current taskset closeout.
