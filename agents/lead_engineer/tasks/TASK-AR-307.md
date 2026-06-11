---
id: TASK-AR-307
display_id: TASK-AR-307
task_uid: 2457f407-5d44-4f83-a1e0-0d3176541638
registered_at: 2026-06-11T17:34:00+09:00
created_at: 2026-06-11T17:34:00+09:00
started_at: 2026-06-11T22:28:32+09:00
updated_at: 2026-06-11T22:28:32+09:00
completed_at: 2026-06-11T22:28:32+09:00
title: 전사 구조 개선 분석 후속 계획 확정
status: completed
priority: P1
difficulty: M
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-OPS-FEEDBACK-ANALYSIS
tags:
  - analysis
  - structure
  - planning
  - feedback
---

# TASK-AR-307 - 전사 구조 개선 분석 후속 계획 확정

## Goal

- 2026-06-11 전사 구조 분석에서 식별된 개선 항목을 Owner가 우선순위 결정할 수 있는 실행 계획으로 확정한다 (분석/계획 전용, 구현 없음).

## Scope

- HIGH: hook-logs 이중 구조 통합(.codex vs agents/runtime), 템플릿 backlog_board.py drift 동기화 게이트, .tmp 수명 정책.
- MEDIUM: reviews/ 평면 구조(368+ 파일) 네임스페이스화 + INDEX 자동 생성, agents/project/ config/release 분리, BACKLOG.md vs BACKLOG-BOARD.md 단일 소스 원칙, hook-log 로테이션, task identity 검증 게이트.
- LOW: tests/ 카테고리화(95 파일), docs/README, hook timeout SLA 문서화, .gitignore 정리.

## Acceptance Criteria

- 각 항목에 대해 채택/보류/기각과 근거가 기록된다.
- 채택 항목은 신규 taskset 또는 기존 taskset 산하 태스크로 등록된다.

## Evidence Targets

- `reviews/REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session.md` (분석 전문 수록)

## Decision Record

| Area | Decision | Rationale | Follow-up |
| --- | --- | --- | --- |
| hook-logs 이중 구조(`.codex/hook-logs` vs `agents/runtime/hook-logs`) | 채택 | 같은 런타임 사실이 두 위치로 갈라지면 stop hook/closeout 판단이 흔들린다. | `TASK-AR-20260611-2230-STRUCT-HOOK-LOGS` |
| hook-log 로테이션 | 채택 | 로그가 gitignored라도 장기 세션에서는 디스크/탐색 비용이 커지고 dirty intake 판단을 어렵게 한다. | `TASK-AR-20260611-2230-STRUCT-HOOK-LOGS` |
| 템플릿 `backlog_board.py` drift 게이트 | 채택 | host template과 live script가 갈라지면 새 프로젝트의 taskset UI/board가 즉시 낡는다. | `TASK-AR-20260611-2230-STRUCT-BOARD-TMP` |
| `.tmp` 수명 정책 | 채택 | 보존 아카이브와 임시 산출물이 같은 공간에 쌓여 수동 삭제 판단이 반복된다. | `TASK-AR-20260611-2230-STRUCT-BOARD-TMP` |
| `BACKLOG.md` vs `BACKLOG-BOARD.md` 단일 소스 원칙 | 채택 | 생성본과 서사본의 역할이 섞이면 UI/dispatcher/Owner 보고가 서로 다른 truth를 보게 된다. | `TASK-AR-20260611-2230-STRUCT-BOARD-TMP` |
| `reviews/` 평면 구조 네임스페이스화 + INDEX | 채택 | 368개 이상 증거 파일은 현재 규모에서 수동 탐색 한계가 분명하다. | `TASK-AR-319`, `TASK-AR-20260611-2230-STRUCT-DOC-NAMESPACE` |
| `agents/project/` config/release 분리 | 채택 | 설정, release evidence, policy가 한 디렉터리에 섞여 generated host project 경계가 흐려진다. | `TASK-AR-20260611-2230-STRUCT-DOC-NAMESPACE` |
| task identity 검증 게이트 | 완료 유지 | `TASKSET-AR-TASK-IDENTITY`가 이미 collision-proof `task_uid`와 board visibility를 구현했다. | 기존 완료 taskset 유지 |
| tests/ 카테고리화 | 보류 | 현재 우선 병목은 task routing/문서 추적/로그 SSoT이며, 테스트 재배치는 이득 대비 충돌면이 크다. | 후속 증상 발생 시 repo hygiene로 재평가 |
| docs/README 구분 | 보류 | 문서 탐색 문제는 `reviews/INDEX`와 evidence 자동화가 선행되어야 효과가 난다. | `TASK-AR-319` 결과 후 재평가 |
| hook timeout SLA 문서화 | 보류 | 먼저 hook log SSoT와 로테이션을 정해야 SLA 측정 기준이 안정된다. | `TASK-AR-20260611-2230-STRUCT-HOOK-LOGS` 후 재평가 |
| `.gitignore` 정리 | 보류 | closeout dirty-intake가 현재 안전망이며, 별도 정리는 실제 누락 패턴이 쌓인 뒤 처리한다. | 후속 dirty-intake findings로 재평가 |

## Registered Follow-ups

- `TASK-AR-20260611-2230-STRUCT-HOOK-LOGS` - hook/runtime log SSoT and rotation policy.
- `TASK-AR-20260611-2230-STRUCT-BOARD-TMP` - board/template drift gate and `.tmp` lifecycle policy.
- `TASK-AR-20260611-2230-STRUCT-DOC-NAMESPACE` - evidence namespace, config/release split, and index migration plan.
