---
id: TASK-AR-212
status: in_progress
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 14
est_tokens: 2400
tags:
  - migration-audit
  - tag-manual
  - migration-evidence
trigger_meeting: yes
created: 2026-06-11
started_at: 2026-06-13T10:25:00+09:00
audit_log:
  - reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md
  - reviews/MEETING-2026-06-13-agent-runtime-task-ar-211-overlay-implementation-checkpoint.md
  - reviews/SEMINAR-2026-06-13-agent-runtime-task-ar-211-overlay-seminar-notes.md
  - reviews/CALL-2026-06-13-agent-runtime-task-ar-211-overlay-sync-call.md
  - reviews/REVIEW-2026-06-13-agent-runtime-task-ar-211-overlay-bundle-review.md
---

## 목표
`TASK-AR-209`의 마이그레이션 감사 결과를 재현 가능한 증거로 완결하고, 향후 release-block 규칙에 연결한다.

## 작업 내용

- `tag_manual` 대비 비교 항목을 `scripts`, `hook`, `skill` 카테고리로 공식 분류
- 각 항목 상태를 `kept/changed/deprecated/dropped/missing`으로 정렬
- `TASK-AR-213`에서 수집한 분류 집합을 `approved_by`/`expiry`/`justification` 포함으로 보정
- `MIGRATION-COMPAT-MAP.example.yml`을 수치/근거 중심으로 갱신
- 미해결 누락 항목은 `TASK-AR-204`와 연결되도록 의무 경로 설정

## 결과물

- migration 감사 보고서(`reviews/` 내)
- `MIGRATION-COMPAT-MAP.example.yml` 보완본
- 오차/누락 항목의 owner/rationale/approval 체계

## 완료 조건

- scripts/hook/skill 항목이 동일 스키마 키로 정렬됨
- 누락 항목이 누적 오해를 줄이기 위해 승인/반려 근거를 모두 갖춤
- release-preflight에서 `TASK-AR-204` 연동 이벤트가 동작
- 미이식 항목은 의도적 제외/누락/회귀로 분류 후 에스컬레이션
- `MIGRATION-COMPAT-MAP` `summary.total_source_items`와 실제 분류 카운트 정합
- `kept/changed/deprecated/dropped/missing` 누적이 `TASK-AR-204`의 차단 룰에 직접 반영됨을 증빙
- `TASK-AR-213` 산출이 `TASK-AR-210` block matrix에 참조되어야 함
- 오버레이 연결고리 미비(`TASK-AR-215`)는 `high-risk` 미결 블로커로 전환해 `TASK-AR-204` 경로와 일치시킴
