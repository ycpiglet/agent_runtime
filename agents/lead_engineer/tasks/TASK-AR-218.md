---
id: TASK-AR-218
status: in_progress
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2400
tags:
  - migration-hardening
  - release-gate
  - query-overlay-governance
  - stale-control
  - source-of-truth
trigger_meeting: yes
created: 2026-06-09
started_at: 2026-06-09T16:00:00+09:00
audit_log:
  - BACKLOG.md
  - STATUS.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - agents/project/PROJECT-CONTEXT.yml
  - agents/project/ROADMAP.md
  - agents/project/MIGRATION-COMPAT-MAP.yml
  - agents/project/SKILL-GOVERNANCE.md
  - agents/project/EVAL-POLICY.yml
  - reviews/RESEARCH-2026-06-09-agent-runtime-official-runtime-ops-update.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-218-handoff-call.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-log.md
---

## 목표

`TASK-AR-216`/`TASK-AR-217` 판정 전제 조건을 위해
`tag_manual` 이식 누락·변경 근거가 미정으로 남는 상태를 제거하고,
오버레이 stale/누락과 질의-쿼리 계약의 런타임 반영을 강제한다.

## 작업 내용

- `MIGRATION-COMPAT-MAP.yml` 미완 항목 정리:
  - `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper` 각각에 대해
    `approved_by`/`justification`/`expiry`를 반드시 채움.
  - 승인이 유효하지 않으면 `TASK-AR-210` block/hold로 남김.
- `TASK-AR-204`와 `TASK-AR-213` 연동 강화를 위한 차단 규칙 정리:
  - 승인 근거 없는 스킬/스크립트/훅 변경은 `warn`이 아닌 `block`.
  - 미승인 의도적 제외는 `expiry`가 있는 타스크 산출물로만 허용.
- 오버레이/문서 신선도 규칙 정리:
  - `ROADMAP`/`CONTEXT-SOURCES`/`LINKS`의 stale(30일+) 감지 시 `hold_for_overlay`.
  - mission-critical 문맥(`vision`/`roadmap`/`org`/`links`) 누락 시 `clarify_required`.
- 질의 계약/출처 정합을 release gate에 묶기:
  - `source_footer`, `tradeoff`, `ambiguity`, `owner` 메타 미완 시 `TASK-AR-214`로 전이.
- 오프라인/라이브 증거 연결:
  - `TASK-AR-217` rehearsal에서 migration hardening 결과(로그, blocker list, decision mapping)를 1건 이상 재현 가능 형태로 저장.

## 완료 조건

- `MIGRATION-COMPAT-MAP.yml`의 미완 항목이 0건.
- `TASK-AR-204`의 block 규칙이 `approved_by/expiry/justification` 미정 상태를 실제로 reject.
- `TASK-AR-210` matrix에서 migration hardening 미완이 `hold_for_data` 또는 `hold_for_overlay`로 반영.
- stale 문서/누락 오버레이가 `release-preflight`에서 경고가 아닌 block/hold로 처리됨.
- `TASK-AR-216`의 release-state 이관 사유가 migration/오버레이 근거를 참조해 보완됨.

## 산출물

- `reviews/MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-plan.md`
- `agents/project/MIGRATION-COMPAT-MAP.yml` (승인 근거 채움/수정 이력 반영)
- `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference.md`
- `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar.md`
- `reviews/CALL-2026-06-09-agent-runtime-task-ar-218-handoff-call.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-log.md`
