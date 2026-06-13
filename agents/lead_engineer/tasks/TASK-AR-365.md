---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-365
work_uid: a11704bf-f62c-46c0-a3da-0cf324e703fa
kind: task
parent_id: TASKSET-AR-UI-LIVING-CONSOLE
origin_type: planning_proposal
origin_ref: TASKSET-AR-UI-LIVING-CONSOLE
created_by: planner
id: TASK-AR-365
display_id: TASK-AR-365
task_uid: a11704bf-f62c-46c0-a3da-0cf324e703fa
registered_at: 2026-06-11T19:48:00+09:00
created_at: 2026-06-11T19:48:00+09:00
updated_at: 2026-06-11T19:48:00+09:00
title: 외부 알림 라우팅 — 웹훅 퍼스트 (Discord/Telegram/email)
status: completed
started_at: 2026-06-14T00:35:14+09:00
completed_at: 2026-06-14T01:15:00+09:00
resolution: done
verification_status: passed
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-LIVING-CONSOLE
tags:
  - notifications
  - webhook
  - integrations
---

# TASK-AR-365 - 외부 알림 라우팅 — 웹훅 퍼스트 (Discord/Telegram/email)

## Goal

- 작업 이벤트(완료/차단/승인 대기)를 사용자가 쓰는 메신저로 내보낸다 — LangSmith 패턴(범용 웹훅 + 채널 레시피, 집계 윈도우 기반)을 채택.

## Scope

- 범용 웹훅 발신기 + 채널 레시피: Discord 웹훅, Telegram 봇, email(SMTP). KakaoTalk 알림톡은 Idea Vault IV-007(사업자 제약).
- 심각도 라우팅: block/승인 대기=즉시, watch=5/15분 집계 윈도우, pass/완료=데일리 다이제스트 — 알림 피로 방지.
- 인앱 알림 센터(TASK-AR-338)와 단일 이벤트 소스 공유, 채널별 구독 규칙 설정 UI.
- 시크릿(웹훅 URL/토큰)은 로컬 설정 파일로, 저장소 커밋 금지.

## Acceptance Criteria

- blocked 이벤트가 설정된 메신저로 즉시 도착하고 pass 이벤트는 다이제스트로만 발송된다.

## Evidence Targets

- 알림 라우터 모듈, 채널 레시피 문서, 테스트
