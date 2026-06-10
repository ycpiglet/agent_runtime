---
id: TASK-AR-203
status: planned
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 8
est_tokens: 1500
task_set_id: TASKSET-AR-CONTEXT-KNOWLEDGE
tags:
  - warehouse
  - knowledge-doc
  - data-governance
trigger_meeting: yes
created: 2026-06-11
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
---

## 목표
지식창고 문서를 `빠른 참조, 차원 설명, 핵심 테이블, 주의사항/패턴, 상위 문맥 링크` 형식으로 표준화해 사람이 즉시 구조를 읽고 판단할 수 있게 한다.

## 작업 내용

- 창고 문서 템플릿 고도화(헤더, dimension, source table, caveat, links)
- `source tier`, `lineage`, `history`, `context knowledge` 체인 필수화
- stale 정책과 SSoT 레벨을 명시하고 freshness 미달 시 경고

## 결과물

- `AGENT-KNOWLEDGE-WAREHOUSE` 템플릿 초안
- stale 체크 규칙 제안(문서 패턴 기반)
- `check_agent_docs.py` 연동 포인트 제안

## 완료 조건

- 최소 1개 role가 표준 문서 템플릿으로 문서 작성 및 경로 일치
- stale/메타 누락 시 pre-check 경고가 남아야 한다.
- 문서는 아래 5개 항목을 필수 포함: `빠른 참조`, `차원설명`, `핵심 테이블`, `주의사항/패턴`, `연결고리`.

## 비고

- 선행: `TASK-AR-202`
