---
id: TASK-AR-211
display_id: TASK-AR-211
task_uid: d477effb-70e0-490d-b8fd-6daacd7f61fd
registered_at: 2026-06-11
created_at: 2026-06-11
updated_at: 2026-06-11T00:00:00+09:00
status: in_progress
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 16
est_tokens: 2200
task_set_id: TASKSET-AR-CONTEXT-KNOWLEDGE
tags:
  - project-overlay
  - multi-team
  - context
trigger_meeting: yes
created: 2026-06-11
started_at: 2026-06-13T09:40:00+09:00
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - STATUS.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap.md
  - reviews/MEETING-2026-06-10-task-ar-201-definition-policy.md
  - reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md
  - reviews/MEETING-2026-06-13-agent-runtime-task-ar-211-overlay-implementation-checkpoint.md
  - reviews/CALL-2026-06-13-agent-runtime-task-ar-211-overlay-sync-call.md
  - reviews/SEMINAR-2026-06-13-agent-runtime-task-ar-211-overlay-seminar-notes.md
  - reviews/RESEARCH-2026-06-13-agent-runtime-task-ar-211-official-multi-project-overlay.md
  - reviews/REVIEW-2026-06-13-agent-runtime-task-ar-211-overlay-bundle-review.md
---

## 목표
에이전트 런타임을 여러 프로젝트에서 공통 reuse할 때 프로젝트 고유의 vision/roadmap/조직/연결 문맥을 오버레이로 주입한다.

## 작업 내용

- `agents/project/ROADMAP.md`, `agents/project/ORG.md`, `agents/project/LINKS.md`, `agents/project/TEAMS.md` 템플릿 추가
- `PROJECT-CONTEXT`에서 프로젝트 오버레이 파일 경로를 필수 키로 요구
- role/쿼리 패킷에서 오버레이 미기입 시 경고 또는 보완 질의 유도
- team id/team owner/team access level 기반 라우팅 및 감사 출력 형식 정리

## 결과물

- 프로젝트 오버레이 템플릿 집합
- 오버레이 바인딩/검증 룰 문서 (`SKILL-GOVERNANCE` 링크)

## 완료 조건

- 공용 runtime는 유지하고, 프로젝트 고유 항목은 오버레이 파일로만 확장됨
- 오버레이 누락 시 요청이 high-risk로 처리되거나 보완 질문을 강제
- 최소 2개 프로젝트 시나리오에서 상호 충돌 없이 실행 시뮬레이션 성공
- 오버레이 누락은 즉시 `TASK-AR-204` 이관되어 게이트 차단 경로로 연결

## 현재 상태

- 상태: 다중 프로젝트 투입 시 overlay 경계 정의 1차 산출 완료
- 현재 액션:
  - `agents/project/*` 오버레이 에셋 생성 및 경로·권한·메타 정책 고정
  - 오버레이 누락을 고위험 라우팅으로 전환해 `TASK-AR-204` 차단 게이트로 이관
  - `TASK-AR-209`/`212` 공통 감사 키(MIGRATION-COMPAT-MAP)로 정렬
