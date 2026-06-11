---
id: TASK-AR-316
display_id: TASK-AR-316
task_uid: e60e5407-f2bc-441a-97f8-0770cc927d8b
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-12T00:55:55+09:00
updated_at: 2026-06-12T02:02:59+09:00
completed_at: 2026-06-12T02:02:59+09:00
title: 스킬 레이어 패키징 (메타데이터/버전/레지스트리)
status: completed
priority: P2
difficulty: S
est_hours: 4
est_tokens: 3000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - skills
  - packaging
  - reuse
---

# TASK-AR-316 - 스킬 레이어 패키징 (메타데이터/버전/레지스트리)

## Goal

- skills/(session-closeout, taskset-dispatch)를 버전·트리거 조건·메타데이터를 갖춘 재사용 가능한 패키지로 만들어 다른 프로젝트에서 발견/조합 가능하게 한다.

## Scope

- 각 SKILL.md에 버전, 트리거 조건, 의존 스크립트 메타데이터 정형화.
- 스킬 레지스트리(`agents/project/SKILL-DATA-MAP.yml` 확장 또는 `.codex/skills.yml`) 등록.
- taskset-dispatch 스킬과 dispatcher 직접 호출의 사용 경계 문서화.

## Acceptance Criteria

- 스킬 목록/버전이 레지스트리에서 조회 가능하고 템플릿 배포 경로가 정의된다.

## Evidence Targets

- `skills/*/SKILL.md`, 스킬 레지스트리 파일

## Completion Evidence

- `skills/session-closeout/SKILL.md`
- `skills/taskset-dispatch/SKILL.md`
- `agents/project/SKILL-DATA-MAP.yml`
- `src/agent_runtime/templates/project/skills/session-closeout/SKILL.md`
- `src/agent_runtime/templates/project/skills/taskset-dispatch/SKILL.md`
