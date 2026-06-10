---
id: TASK-AR-204
status: completed
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 12
est_tokens: 1800
tags:
  - skill-governance
  - ci-gate
  - co-location
audit_log:
  - BACKLOG.md
  - STATUS.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap.md
  - reviews/MEETING-2026-06-10-task-ar-201-definition-policy.md
  - reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md
trigger_meeting: yes
created: 2026-06-09
---

## 목표
런타임의 스킬/런북 문서가 코드/데이터/스키마 변경과 동기화되지 않을 경우 릴리스가 차단되도록 한다.

## 작업 내용

- `SKILL-DATA-MAP.yml` 스키마를 확정하고 템플릿화
- `release-preflight` 또는 유사 CI 경로에 `warn -> block` 승격 규칙 작성
- 모델/프로바이더 변경 시 관련 스킬 문서를 강제 동기화
- 의도적 제외 항목만 waiver로 허용
- 스킬 문서, hook, script 변경은 동일한 핵심 키(`id`, `status`)로 매핑하고, 누락/변경 항목을 release-block 이벤트로 노출
- `.tmp/release-bundle`만 검사하는 루트에서 `source=.` 검증 스킵 이슈를 막는 방어선도 함께 정의

## 현재 블로커

- `TASK-AR-213`의 `TASK-AR-209/212` 분류 정규화가 끝나지 않으면 `TASK-AR-204`의 block 규칙을 최종 적용할 수 없음.
- `TASK-AR-214` 질의/쿼리 계약이 모델/프로바이더/데이터 변경 전환 기준을 정의하기 전에는 최종 release-block 기준은 확정되지 않음.
- `MIGRATION-COMPAT-MAP`의 `scripts-source-only`, `scripts-runtime-extra` 등 핵심 항목이 `approved_by`/`expiry`/`justification`으로 정리되지 않으면 `TASK-AR-204`는 `TASK-AR-218`이 완료될 때까지 블로킹.

## 결과물

- `SKILL-DATA-MAP` 스키마 파일(또는 `example` 확장)
- 치환 규칙(오퍼레이션 변경 감지 규칙)
- CI 차단 룰 설명서

## 수행 전략(추가)

- 핵심 artifact 집합:
  - `agents/project/SKILL-DATA-MAP.yml`
  - `agents/project/MIGRATION-COMPAT-MAP.yml`
  - `agents/project/CONTEXT-SOURCES.yml`
  - `agents/project/DATASET-CATALOG.yml`
- 동기화 누락은 `warn`가 아닌 `block`으로 처리

## 의존성

- 선행 완료 필요: `TASK-AR-201`
- BLOCKED: `TASK-AR-201`의 필수 메타 완결을 전제

## 완료 조건

- 스킬/모델/데이터 항목 변경 감지 시 관련 문서 미변경이면 release가 block되어야 함
- 예외는 `approved_by`, `justification`, `expiry`가 있어야만 pass
- `TASK-AR-215`에서 오버레이 연결고리 누락을 탐지하면 즉시 block 처리
- `MIGRATION-COMPAT-MAP` 항목은 `TASK-AR-218`이 매핑 결재 정책과 정렬되기 전까지 릴리스 gate 통과에서 제외.

완료 조건(추가):

- `TASK-AR-218`에서 승인 근거가 채워진 항목은 `approved_by`/`justification`/`expiry`가 모두 존재해야 함.
- `approved_by`가 채워지지 않았던 항목(`approved_by: TBD`)은 존재하면 즉시 block되며 `TASK-AR-210`으로 이관.

## 비고

- `TASK-AR-204` 완료 후 `TASK-AR-209`의 마이그레이션 감사 결과를 게이트 입력으로 병합.

## Completion Log: Co-Location Enforcement Gate (2026-06-09)

- Executable gate: `scripts/co_location_gate.py`.
- Evidence report: `reviews/CO-LOCATION-GATE-2026-06-09-task-ar-204.json`.
- Inputs checked:
  - `agents/project/SKILL-DATA-MAP.yml`
  - `agents/project/MIGRATION-COMPAT-MAP.yml`
  - `agents/project/CONTEXT-SOURCES.yml`
  - `agents/project/DATASET-CATALOG.yml`
- Result: `status=pass`, `release_route=ready_for_release_redecision`, `findings=0`.
- Enforcement behavior: missing owner/approval/expiry/justification, missing artifact paths, missing `TASK-AR-204` links, or invalid dataset/source metadata blocks release.
- Release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-colocation-ready --check` returned `findings=0`.
