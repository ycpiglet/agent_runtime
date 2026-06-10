---
id: TASK-AR-201
status: in_progress
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 8
est_tokens: 1200
task_set_id: TASKSET-AR-CONTEXT-KNOWLEDGE
tags:
  - knowledge-router
  - context-source
  - project-overlay
  - release-gate
trigger_meeting: yes
created: 2026-06-09
started_at: 2026-06-09T09:20:00+09:00
audit_log:
  - BACKLOG.md
  - STATUS.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap.md
  - reviews/MEETING-2026-06-10-task-ar-201-definition-policy.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-official-guidance.md
  - reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md
---

## 목표
`agent_runtime`가 프로젝트별 요청을 처리할 때 source-tier, owner, 접근권한, freshness를 기준으로 지식 소스를 라우팅하고,
정의 책임 및 쿼리 품질 규칙을 라우터 단계에서 반영한다.

## 작업 내용

- `agents/project/CONTEXT-SOURCES.yml`의 스키마를 강제 규격화한다.
- context packet 출력 포맷에서 다음을 항상 노출한다.
  - `source_tier`
  - `owner`
  - `access_level`
  - `freshness_sla`
  - `lineage`
  - `definition_policy`
  - `query_policy`
- 필수 필드 누락 시 경고를 기록하고, 다음 작업(204/209)에 태스크 이관한다.
- ambiguous한 쿼리는 query refinement 단계에서 분해 규칙을 제시한다.
- 쿼리는 `question / business_scope / source_tier / time_window / tolerance / ambiguity_level`을 필수로 받는다.
- 질의 모호성 점수(ambiguity_score)와 SSoT 정렬(official semantic layer > lineage > history > context knowledge) 점수를 packet에 노출한다.
- `warn`가 반복 발생하면 `TASK-AR-204`에서 `block`으로 승격되도록 정책 문서화.

## 결과물

- `CONTEXT-SOURCES` 메타데이터 파서/출력 규격 문서(템플릿 반영)
- `agent_context_packet.py` 라우팅 블록 출력 템플릿(필수 필드 노출)
- 스크립트/리뷰 근거를 묶는 `audit_log` 항목 갱신
- `AGENTIC` 프로젝트 overlay를 주입받을 때 필수 오버레이 경로(`agents/project/ROADMAP.md` 등)가 없으면 경고로 치환

## 비고

- 선행: v0.1.6 context overlay 반영
- 후행: `TASK-AR-204`

## 현재 사이클 진행 메모

- `agent_context_packet.py`에서 컨텍스트 요약/경고 출력이 가능해진 상태로 보고됨.
- 다음 단계는 경고를 `TASK-AR-204`의 실차단 규칙(오퍼레이션 경고→block)으로 승격할지 최종 합의.
- 2026-06-10 연구/회의 의사결정을 반영해 `access_level`, `lineage` 가시화를 우선 반영함.
