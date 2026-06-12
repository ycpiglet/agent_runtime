---
id: TASK-AR-509
display_id: TASK-AR-509
task_uid: 734a1b79-485c-4889-bf4a-faf4a45b8a55
registered_at: 2026-06-12T22:42:24+09:00
created_at: 2026-06-12T22:42:24+09:00
updated_at: 2026-06-12T22:42:24+09:00
title: Host update notification — upstream release check at session start
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-RELEASE-STEWARD
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - release
  - host-sync
  - update-notification
---

# TASK-AR-509 - Host update notification

## Goal

- 호스트 프로젝트(autofolio 등)가 agent_runtime 새 릴리스를 자동으로 인지하게
  한다: 세션 시작 시 업스트림 최신 태그와 호스트 고정 ref를 비교해 "새 버전
  사용 가능" 알림을 비차단으로 출력한다. Owner 요청(2026-06-12): "자동으로
  업데이트 소식을 줘서 최신 버전을 사용하게는 못하나?"

## Context

- 수동 메커니즘은 이미 완비: `agent_runtime.yml`(upstream ref 고정) +
  `update-plan --check` + `update`(install→sync check-diff-apply).
  빠진 것은 "알림" 한 조각 — 호스트가 확인을 직접 돌려야만 안다.
- autofolio 실측(2026-06-12): ref=v0.1.8 고정, main은 v0.1.8 대비 81커밋
  전진(미릴리스). 알림은 "태그된 릴리스" 기준이어야 하며 main 추적이 아니다.
- 호스트 분기 보호 확인: autofolio는 AGENTS.md/roles.yml/task.schema.json을
  unmanaged로 분리 — 알림→적용 경로가 이 분기를 존중해야 한다.

## Preconditions

- 신규 릴리스 태그 비교 로직은 codex 미머지 브랜치와 무접촉 확인됨
  (.codex/hooks.json diff 0). 단, cli.py가 merge로 변경되면 착수 전 rebase.

## Scope

- `agent_runtime update-plan --notify`(또는 신규 `update-notify`) 서브커맨드:
  `git ls-remote --tags <remote_url>` 최신 semver 태그 vs `agent_runtime.yml`
  ref 비교 → 차이 시 한 줄 알림 + 권장 절차 출력. 오프라인/타임아웃 시 조용히
  통과(비차단), 결과 캐시(예: .tmp, 24h)로 세션 시작 비용 최소화.
- 호스트 템플릿 session-start 훅(.codex/hooks.json + CLAUDE.md 안내)에 알림
  호출 배선 — 템플릿 미러 동기화.
- 호스트 런북 문서화: 알림 수신 → ref bump → update-plan → update 절차.
- autofolio에 적용 검증 (v0.1.9 릴리스 이후 실연).

## Out Of Scope

- 자동 적용(auto-apply) — sync는 Owner 승인 check-diff-apply 유지.
- 릴리스 자동화 자체(기존 release gates 소관).

## Acceptance Criteria

- 업스트림에 새 태그가 있으면 호스트 세션 시작 시 알림이 1회 출력된다.
- 오프라인/원격 실패 시 세션 시작이 차단되지 않는다.
- 호스트 unmanaged 분기 파일이 알림→적용 경로에서 덮어써지지 않는다.
- `pytest tests -q` 통과, 게이트 체인 exit 0, W4b 독립 검증 기록.

## Evidence Targets

- CLI 변경분 + 테스트, 템플릿 훅 배선
- autofolio 적용 데모 기록
- closeout review record
