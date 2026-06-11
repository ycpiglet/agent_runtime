---
id: TASK-AR-202
display_id: TASK-AR-202
task_uid: f4057c67-bc4c-4a63-b76b-fbd1c59daf52
registered_at: 2026-06-11
created_at: 2026-06-11
updated_at: 2026-06-11T11:50:00+09:00
completed_at: 2026-06-11T11:50:00+09:00
status: completed
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 10
est_tokens: 1700
task_set_id: TASKSET-AR-CONTEXT-KNOWLEDGE
tags:
  - runbook
  - workflow-governance
  - runbook-template
  - release-gate
trigger_meeting: yes
created: 2026-06-11
started_at: 2026-06-11T11:45:00+09:00
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - agents/project/SKILL-GOVERNANCE.md
  - src/agent_runtime/templates/project/agents/project/SKILL-GOVERNANCE.md
  - scripts/context_knowledge_gate.py
  - reviews/CONTEXT-KNOWLEDGE-GATE-2026-06-11-final.json
---

## 목표
`runbook`를 재사용 가능한 숙련 프로세스로 표준화해, 질문 명확화-자료 검색-실행-적대적 검토-검증-기록 흐름을 에이전트가 강제하도록 한다.

## 작업 내용

- veteran 스타일의 runbook 템플릿(clarify/retrieve/execute/review/verify/record) 작성
- 불충분한 질문을 받을 때 refinement 패턴 추가
- 검증된 스크립트/패턴 재사용 섹션 설계
- adversarial review 요청/반례 처리 규칙 추가

## 결과물

- `runbook` 스키마 템플릿
- `SKILL-GOVERNANCE.md`에서 runbook 필수 단계 반영
- 완료 조건에 evidence(입력, evidence, review, footer)를 묶는 검증 규칙

## 완료 조건

- runbook 항목이 “완료”로 표시되려면 6단계 증거(clarify/retrieve/execute/review/verify/record)가 모두 존재해야 한다.
- `source_footer`, `review_verdict`, `evidence`가 모두 남지 않으면 자동으로 미완료로 간주한다.
- 재사용 패턴(verified pattern) 참조가 없으면 완료 조건 미달.

## 비고

- 선행: `TASK-AR-201`
- 의존: `TASK-AR-204`의 감사 기준과 문서 매핑과 연동

## Completion Log (2026-06-11)

- `SKILL-GOVERNANCE.md`와 생성 프로젝트 템플릿에 clarify/retrieve/execute/review/verify/record 6단계 runbook 계약을 반영했다.
- 완료 evidence는 `source_footer`, `review_verdict`, `evidence`, `verified_pattern`, `correction_path`, `record_path`가 모두 있어야 한다.
- `query contract violation`은 `hold_for_query_contract`로 이관되도록 문서화하고 게이트에서 검사한다.
