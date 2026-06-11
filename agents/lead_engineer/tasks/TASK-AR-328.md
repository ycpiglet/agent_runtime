---
id: TASK-AR-328
display_id: TASK-AR-328
task_uid: 35bf745d-faa6-4c9f-a7c9-7eaf457b9ae7
registered_at: 2026-06-11T18:39:01+09:00
created_at: 2026-06-11T18:39:01+09:00
updated_at: 2026-06-11T18:39:01+09:00
title: Taskset 경계 실행 가드 — 완료 시 정지
status: planned
priority: P1
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-UX-V2
tags:
  - ui-ux-v2
  - guard
  - taskset-scope
  - governance
---

# TASK-AR-328 - Taskset 경계 실행 가드 — 완료 시 정지

## Goal

- 특정 taskset 실행을 지시했을 때 해당 taskset 완료 후 scope 밖 작업으로 이탈하지 않고 정지·보고하도록 런타임 정책으로 강제한다 (Owner 관찰: 현재 완료 후 미등록 후속 작업으로 이탈하는 사례 존재).

## Scope

- `taskset_dispatcher`가 active taskset scope를 클레임에 기록.
- stop hook / owner governance gate가 "active scope 외 신규 작업 착수"를 block 판정.
- 완료 시 `taskset.completed` 이벤트 발행 후 정지, UI(Home/Tasksets)에 완료 배너 + "다음 taskset 제안(승인 대기)" 표시.

## Acceptance Criteria

- taskset 완료 후 scope 외 작업 착수가 게이트 테스트에서 차단되고, 정지·보고 경로가 검증된다.

## Evidence Targets

- `scripts/taskset_dispatcher.py`, stop hook 스크립트, 게이트 테스트
