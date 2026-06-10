---
id: TASK-AR-209
display_id: TASK-AR-209
task_uid: 914d9b65-a634-482d-928c-1fd3cb19d2c8
registered_at: 2026-06-09
created_at: 2026-06-09
updated_at: 2026-06-11T00:00:00+09:00
completed_at: 2026-06-11T00:00:00+09:00
status: completed
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
task_set_id: TASKSET-AR-MIGRATION-PARITY
tags:
  - migration-audit
  - tag-manual
  - parity
  - release-gate
audit_log:
  - BACKLOG.md
  - STATUS.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap.md
  - reviews/RESEARCH-2026-06-11-agent-runtime-official-guidance-and-migration-evidence.md
  - reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md
  - reviews/MEETING-2026-06-13-agent-runtime-task-ar-211-overlay-implementation-checkpoint.md
  - reviews/RESEARCH-2026-06-13-agent-runtime-task-ar-211-official-multi-project-overlay.md
trigger_meeting: yes
created: 2026-06-09
started_at: 2026-06-13T10:10:00+09:00
---

## 목표
`tag_manual`에서 `agent_runtime`로 이식할 때 누락·변형·의도적 제외 항목을 분리해, 다음 릴리스에서 추적 가능하게 증빙한다.

## 작업 내용

- 비교 범위 정리: `skill / hook / script`
- 정합 기준: `tag_manual/scripts` 171개 vs `runtime/scripts` 120개 (해시 기반)
- 1차 분류 규칙: `kept`, `changed`, `deprecated`, `dropped`, `missing`
- 누락 사유를 태스크, owner, approved_by, decision_date와 함께 매핑
- `TASK-AR-213` 정규화 산출을 위해 분류 체계를 사전 고정
- release-preflight에서 핵심 항목 누락 시 block 할 수 있는 체크 제안

## 결과물

- `MIGRATION-COMPAT-MAP.example.yml`
- `reviews/` 내 감사 리포트
- 누락 항목별 승인 경로 문서

## 완료 조건

- 비교 대상 집합이 명확히 고정되고 수집 스크립트/수동 체크리스트가 일치
- 의도적 제외 항목에 승인 근거가 반드시 포함
- 스크립트/hook/skill 항목을 `kept/changed/deprecated/dropped/missing` 5-분류로 우선 분리
- `TASK-AR-204`와 연동 가능한 누락 이벤트로 통합
- skill/hook 분류는 `MIGRATION-COMPAT-MAP.yml` 동일 status 키로 정규화 후 `TASK-AR-213`로 인계

- 분류 근거:
  - scripts 차분: `tag_manual`에서만 `53`개, `agent_runtime`에서만 `2`개
  - 공통 스크립트 118개는 `kept 59`, `changed 59`
  - skills: `16`개 중 `changed 15`, `kept 1`
  - hooks: `src/hooks`는 placeholder(`.gitkeep`) 중심, runtime은 `*_hook.py` 재구성
  - `TASK-AR-213`은 해당 분류를 approval 스키마(`approved_by`/`expiry`/`justification`)로 정규화해 `TASK-AR-212` 증빙에 넘김
- 추가 확인 항목:
  - docs/스킬맵의 상태 누락 파일(1개)은 이슈를 `TASK-AR-213`에서 승인기한/오너로 해소
  - hooks: 공용/프로젝트 오버레이 중 어떤 실행 경로가 사용 중인지 runtime 경로 추적 문서화
