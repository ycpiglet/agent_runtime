---
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - STATUS.md
  - agents/project/MIGRATION-COMPAT-MAP.yml
  - agents/project/MIGRATION-COMPAT-MAP.example.yml
  - agents/lead_engineer/tasks/TASK-AR-209.md
  - agents/lead_engineer/tasks/TASK-AR-213.md
  - agents/lead_engineer/tasks/TASK-AR-218.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md
  - reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-release-governance-seminar.md
  - reviews/CALL-2026-06-10-agent-runtime-task-ar-221-cycle-sync-call.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-start.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-sync.md
  - reviews/MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md
  - reviews/CALL-2026-06-14-agent-runtime-task-ar-222-sync-call.md
  - reviews/SEMINAR-2026-06-14-agent-runtime-task-ar-222-closeout-sync.md
id: TASK-AR-220
status: in_progress
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2200
started_at: 2026-06-10T09:15:00+09:00
tags:
  - migration-audit
  - provenance
  - cross-project
  - skill-hook-script
trigger_meeting: yes
created: 2026-06-09
---

## 목표

`tag_manual`에서 `agent_runtime`으로 이동할 때 skill/hook/script 누락·변형·의도적 제외가
의도된 이유인지, 기술적 누락인지가 한 번에 판별되도록
이식 근거 체인을 마무리한다.

## 작업 내용

- `TASK-AR-209`/`TASK-AR-213`/`TASK-AR-218`의 분류값(`kept`, `changed`, `deprecated`,
  `dropped`, `missing`)을 근거 레벨(`owner`, `decision`, `justification`, `expiry`)으로
  재정렬.
- 분류를 `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`, `skills-pack` 단위에서
  `query-risk`/`cost/latency`/`data freshness`가 필요한 항목과 분리해 기록.
- `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`에 대해
  의도적 제외/회귀 위험/보류 사유를 별도 분류로 분리해 `TASK-AR-204`와 `TASK-AR-210`으로
  자동 이관.
- skill 문서/코드/데이터를 동일 프로젝트 디렉터리에서 관리한다는 `co-location` 기준을 명시.
- `TASK-AR-215` 컨텍스트 오버레이 누락 시 라우팅이 고위험으로 이동되는지
  1건 이상 교차 검증.
- 3축 매핑 문서 작성:
  - `tag_manual` 원본 경로
  - `agent_runtime` 템플릿 경로
  - 이식 판단 사유(`approved_by`/`expiry`/`owner`)
- CI/릴리스에서 skill/hook/script 변경은 코어 스킬문서·스키마 동반 변경 없으면
  block 되도록 감사증거를 고정.

## 완료 조건

- 미이식 항목(`source-only`)이 단일 사유로만 정리되지 않고
  최소 1개 이상의 사유군(보안·운영범위·중복도입·개념부재)으로 분리.
- `MIGRATION-COMPAT-MAP.yml` 항목별 `justification` 누락이 0건이거나 남은 항목은
  `hold_for_data`/`hold_for_overlay`로 이관되어 `release-state` 문서화됨.
- `TASK-AR-204`의 문서 동기화 차단 규칙이 skill/hook/script에서 동일하게 작동.
- `TASK-AR-218` 완료 조건(`approved_by`/`justification`/`expiry` 미정 0건)에 실질 연계.
  - `TASK-AR-221`와 `TASK-AR-219`의 1~16 게이트 항목에서 `migration provenance`가 추적되어야 함.
  - `TASK-AR-223` 통합 산출에서 `TASK-AR-220` 누락/변형/의도적 제외 결손이 closeout bundle 이관 경로로 정합.

## Cycle Log (2026-06-10)

- `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`의 근거/승인/만료를
  `TASK-AR-204`/`TASK-AR-213`/`TASK-AR-210` 경로로 재이관할 체크리스트를 활성화.
- 동기화된 회의/연구/세미나/콜 증거를 `TASK-AR-221` 및 `TASK-AR-219` 번들로 연결.
- 남은 블로커가 있다면 `hold_for_data` 또는 `hold_for_overlay`로 즉시 분기하고 증적 잔량을 기록.

## Cycle Log (2026-06-14)

- `MIGRATION-COMPAT-MAP.yml` 항목 `scripts-core-kept`, `scripts-core-changed`, `scripts-runschedule-legacy`, `skills-pack`에
  `justification` + `expiry` 보강 완료.
- `TASK-AR-204`/`TASK-AR-213`/`TASK-AR-210`으로 이관 경로를 추적하는 closeout 동기화를 위해
  `MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md`,
  `CALL-2026-06-14-agent-runtime-task-ar-222-sync-call.md`,
  `SEMINAR-2026-06-14-agent-runtime-task-ar-222-closeout-sync.md` 생성.
- 완료 조건 재점검: `approved_by/justification/expiry` 미기재 0건 방향으로 갱신(남은 항목은 `hold` 경로 유지).

## 산출물(예정)

- `reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md`
- `agents/project/MIGRATION-COMPAT-MAP.yml` 근거 주석 보강
- 이식 누락/의도적 제외 추적 표(`TASK-AR-220` 완료 로그)
- `TASK-AR-213`/`TASK-AR-204`/`TASK-AR-210` 교차 링크 증적


## Migration Approval Closure (2026-06-09)

- Decision entrypoint: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure.md`.
- Updated `agents/project/MIGRATION-HOLD-ROUTING.yml` from `release_state: hold_for_data` to `release_state: ready`.
- Added group-level exit metadata: `target_state`, `approved_by`, `decision_date`, `expiry`, `justification`.
- Updated `agents/project/MIGRATION-COMPAT-MAP.yml` for `scripts-source-only`, `scripts-runtime-extra`, and `hooks-wrapper` with release-blocking metadata.
- Result: migration source-only boundary is closed for the v0.1.8 baseline; source-only capabilities remain tracked as optional/plugin/overlay/follow-up work.
- Verification: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-migration-closure --check` returned `findings=0`.
