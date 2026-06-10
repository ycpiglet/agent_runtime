---
id: TASK-AR-214
status: in_progress
started_at: 2026-06-09T10:20:00+09:00
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 16
est_tokens: 2600
tags:
  - query-contract
  - metadata-governance
  - quality-gate
trigger_meeting: yes
created: 2026-06-09
audit_log:
  - BACKLOG.md
  - STATUS.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - agents/project/CONTEXT-SOURCES.yml
  - agents/project/SKILL-GOVERNANCE.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-214-official-query-contract.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-214-query-contract.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-214-query-contract.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-214-owner-sync.md
---

## 목표
질의 실행 전후의 `source_tier`, `owner`, `access`, `freshness`, `lineage`, `ambiguity`, `tradeoff`를 구조화해
정확도 결정을 모델 성능이 아니라 "맥락 + 검증"으로 고정한다.

## 작업 내용

- `agents/project/CONTEXT-SOURCES.yml`과 `SKILL-GOVERNANCE.md`에서 필수 메타 필드 강제화:
  - question, business_scope, time_window, tolerance, ambiguity_level, query_tolerance, tradeoff_preference
- `TASK-AR-204`의 `SKILL-DATA-MAP`에 질의 계약 변경 경로를 추가
- `TASK-AR-205` 오프라인 게이트 데이터셋에서 모호성·비용·정확도 트레이드오프 항목을 스코어링 메트릭으로 추가
- 고위험 요청에서 `clarify_required` 또는 `reviewer_review`가 발생하면 실행 종료 후 자동 기록
- 고의적 오답/누락/오해 케이스를 correction 제안으로 환류

## 완료 조건

- 필수 필드 미기재시 기본 종료를 하지 않고 `clarify_required`/`reviewer_review`로 강제 종료
- source_footer에 `source_tier`, `source`, `confidence`, `access_level`, `ambiguity_score`, `freshness_sla`, `reviewer_verdict`가 항상 존재
- `TASK-AR-204`/`TASK-AR-210` 블로커 규칙에서 `query contract violation`을 감지 가능해야 함
- `TASK-AR-216` release-state 이관을 위해 `hold_for_query_contract` 트리거를 남겨야 함
- `TASK-AR-205` 데이터셋 게이트에서 `ambiguous` 샘플(범위/오류허용/트레이드오프 누락)은 별도 라벨링되어야 함

## 증빙

- `agents/project/SKILL-GOVERNANCE.md`
- `agents/project/CONTEXT-SOURCES.yml`
- `agents/project/EVAL-POLICY.yml`
- `reviews/RESEARCH-` 또는 `reviews/MEETING-` 중 본 과제 증빙 문서
