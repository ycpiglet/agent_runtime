---
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - STATUS.md
  - agents/project/ROADMAP.md
  - agents/project/PROJECT-CONTEXT.yml
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-version-update-and-official-guidance-refresh.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-official-release-governance-research.md
  - reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-release-governance-seminar.md
  - reviews/CALL-2026-06-10-agent-runtime-task-ar-221-cycle-sync-call.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-sync.md
id: TASK-AR-219
status: in_progress
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 10
est_tokens: 1800
task_set_id: TASKSET-AR-RELEASE-STEWARD
started_at: 2026-06-10T09:00:00+09:00
tags:
  - release-planning
  - versioning
  - official-guidance
  - evidence-gate
trigger_meeting: yes
created: 2026-06-09
---

## 목표

현재 로드맵 기준으로 `v0.1.8` 후보 공개 판단을 한 번 더 고정하고,
Claude/Codex 계열 공식 권고(컨텍스트 우선순위, trace-grading/traceability,
도구 안전성, 허가 제어, A2A 연동)을 릴리스 게이트에 운영적으로 반영한다.

## 작업 내용

- 다음 버전 업데이트 판정 일정 고정:
  - 1차 판정: 2026-07-02
  - 2차 판정(보완 허용): 2026-07-09
  - 최종 판정: 2026-07-16
- `TASK-AR-221` 요구사항 묶음(1~16 항목)을 공식 가이드 근거와 연결:
  - 질의 계약(clarify/reviewer/hold_for_query_contract)
  - 오프라인 90%/실시간 reviewer/correction/A2A
  - 스킬/스키마 동기화 및 migration map
  - 오버레이 누락 자동 hold
- `TASK-AR-216`/`TASK-AR-217`/`TASK-AR-210`의 gate 증거 체계와 `release-state`
  (`hold`, `hold_for_data`, `hold_for_query_contract`, `hold_for_overlay`, `ready`)를
  동일 문구로 동기화.
- 오프라인 90%·라이브 reviewer·교정 수집·A2A chain이 동시에 연결된 버전 판정 번들
  템플릿 확정.
- 공식 가이드 반영 항목 문서화:
  - 컨텍스트 소스 랭킹(SSoT + lineage + history + context knowledge)
  - trace/trainer 기반 평가 재현성
  - 허용 명령어 allowlist 방식과 승인 피로도 완화 균형
- 미해결 블로커를 `TASK-AR-210`에 `release-state`와 `decision_deadline`/`blocked_by`로
  누락 없이 이관.

## 완료 조건

- 다음 버전 업데이트를 위한 1차/2차/최종 판정 일정이 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에서 동일.
- `TASK-AR-210`에 `v0.1.8` 판정 이관 사유(`request_for_v0.1.8`, `release_state`,
  `release_cause`)가 남고, Owner 승인/보류 경로가 비어 있지 않음.
- `TASK-AR-221`에서 정한 1~16 항목이 공식 문서 기반 태스크로 역추적 가능.
- 판정 문구(1차/2차/최종)와 hold 분기(`hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`)가
  `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에서 완전 일치.
- 공식 가이드 반영이 문서/증거로 추적되는지 `decision_logs`에 최소 1개 review 증빙 추가.
- 버전 판정 패키지 산출물(리허설 로그, 게이트 근거, 재현 경로)이 존재.

## Cycle Log (2026-06-10)

- 1차 판정 템플릿(`07-02`, `07-09`, `07-16`)과 `hold_for_*` 라우팅 동기화 대상:
  - `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210` 문구 동기 점검
  - 공식 가이드 반영 증적 번들(Research/SEMINAR/CALL/Meeting) 연결
- 다음 단계:
  - `TASK-AR-220`의 migration 근거 분리 결과를 동일 증적 체인에 묶어, `TASK-AR-221` 완료 조건으로 전달

## 산출물(예정)

- `reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md`
- `BACKLOG.md` 버전 일정 정합 업데이트
- `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`의 공식 권고 반영 항목 업데이트
- `agents/project/ROADMAP.md` + `agents/project/PROJECT-CONTEXT.yml`의 판정 문구 정합
