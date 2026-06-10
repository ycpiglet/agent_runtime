---
id: TASK-AR-224
status: completed
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 8
est_tokens: 1600
task_set_id: TASKSET-AR-MIGRATION-PARITY
tags:
  - official-guidance
  - migration-audit
  - release-governance
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - STATUS.md
  - agents/project/ROADMAP.md
  - agents/lead_engineer/tasks/TASK-AR-223.md
  - agents/project/MIGRATION-COMPAT-MAP.yml
  - agents/project/MIGRATION-HOLD-ROUTING.yml
  - agents/project/RELEASE-GATE-TEMPLATE.yml
  - agents/project/SKILL-DATA-MAP.yml
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-224-sync-call.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-224-governance-seminar.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-overlay-gate-sync.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md
created: 2026-06-19
---

## 목표

`v0.1.8` 판정에서 공통 정합 규칙(공식 가이드 반영, migration 근거, tag_manual 이식 누락 처리)이 줄지 않게 동작하도록
공식/이식 점검을 closeout 번들에서 선행 강제한다.

## 작업 내용

- 공식 가이드 정합
  - Claude hook 우선순위(deny > ask > allow), trace-grading 근거, A2A 연속성, Codex 안전 원칙을 단일 규칙 템플릿에 고정.
- 이식 근거 정합
  - `MIGRATION-COMPAT-MAP.yml`의 `scripts-source-only`(53), `scripts-runtime-extra`(2), `hooks-wrapper`(1) 상태를
    `approved_by/expiry/justification`와 hold 라우팅으로 강제.
  - 누락/의도적 제외/보류 항목이 미정리 상태로 남지 않게 `TASK-AR-210` 이관 규칙에 연결.
- 규칙 강제성
  - `TASK-AR-204` 변경 동기화 누락은 warn가 아니라 block으로 수렴되도록 증적 고정.
- 멀티프로젝트 투입성
  - `TASK-AR-215`/`TASK-AR-211` 기준 오버레이만 교체하는 1회 이상 시나리오를 closeout 번들에 추가.

## 완료 조건

- `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`의 1차/2차/최종 판정 문구 일치.
- `TASK-AR-223` closeout 번들에서 공식 가이드 근거 링크 1개 이상 + migration hold 이관 경로 1개 이상이 trace key로 연결.
- `TASK-AR-220`의 미정리 항목이 `MIGRATION-HOLD-ROUTING.yml`에서 `hold_for_data`/`hold_for_overlay`로만 분기되고, approved_by/decision_date/expiry 미입력 항목 0건.
- `TAG_MANUAL` 누락 이슈가 스킬/스크립트/훅로 구분돼 재발 방지 증적으로 남음.
- `RELEASE-GATE-TEMPLATE.yml`의 required fields가 `TASK-AR-210` 판정 필드와 일치.
- overlay-only 증거가 review 또는 실행 로그로 `TASK-AR-223` closeout에 연결.

## 산출물

- `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md`
- `reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync.md`
- `reviews/CALL-2026-06-09-agent-runtime-task-ar-224-sync-call.md`
- `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-224-governance-seminar.md`
- `agents/project/MIGRATION-HOLD-ROUTING.yml`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md`
- `reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-overlay-gate-sync.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md`
- `agents/project/RELEASE-GATE-TEMPLATE.yml`

## 산출물(예정)

- `reviews/RESEARCH-2026-06-19-agent-runtime-official-and-migration-sync-research.md`
- `reviews/MEETING-2026-06-20-agent-runtime-task-ar-224-gate-sync.md` (예정)
- `TASK-AR-223` closeout 번들 증적에 `TASK-AR-224` 링크 추가

## Cycle Log (2026-06-09)

- 공식 근거 확인을 `RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md`에 기록.
- meeting/call/seminar 기록을 추가해 `TASK-AR-224`를 `planned`에서 `in_progress`로 전환.
- `scripts-source-only` 53건은 release-ready가 아니라 `hold_for_data` 후보로 유지하고, 다음 cycle에서 세분류 routing table을 작성하기로 결정.
- `agents/project/MIGRATION-HOLD-ROUTING.yml` 초안 작성: placeholder 1, external/deploy 10, project-report/docs 3, runtime-gap 6, legacy 1, test-only 32.
- 아직 완료 조건으로 남은 항목: overlay-only 시뮬레이션, 실제 release-preflight block 증적, `TASK-AR-210` 판정 템플릿 대조.

## Cycle Log (2026-06-09, overlay/gate)

- `REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md` 작성: normal overlay/document-level PASS, different-project overlay PARTIAL, stale/missing overlay `hold_for_overlay` PASS.
- `RELEASE-GATE-TEMPLATE.yml` 작성: `release_state`, `release_cause`, `decision_deadline`, `owner`, `blocked_by`, `impact_on_version`, `evidence_bundle`, `next_action` required fields 고정.
- `TASK-AR-210` 대조 결과: 판정 템플릿 필드는 문서상 정합하지만, 실행 증거(`release-preflight`/packet generation)는 아직 없음.
- 남은 항목: executable overlay packet proof, release-preflight proof, final `TASK-AR-210` decision record.

## Cycle Log (2026-06-09, executable proof)

- packet proof 실행 성공: Python310 경로로 `agent_context_packet.py --role lead-engineer --format json` 실행, project overlay 문서가 packet에 포함됨.
- check-only 실행 성공: `OK: role 'lead-engineer' and task '(none)' resolve cleanly`.
- repo root를 host로 둔 release-preflight는 `agent_runtime.yml not found`로 실패: package source와 host project 경계를 확인하는 blocker 증거로 기록.
- fixture host 기준 release-preflight는 실행됐지만 `findings=358`로 block:
  - sanitize 29
  - publish-bundle 29
  - local-tag-smoke-plan 29
  - github-publish-plan 270
  - host-lock 1
- 판정: executable proof는 생성됐으나 release-ready 아님. `TASK-AR-223` closeout에서 source publication hygiene blocker로 이관.

## Cycle Log (예정)

- `TASK-AR-224`는 다음 세션 시작 시 즉시 `TASK-AR-219`/`TASK-AR-220` 문헌·마이그레이션 항목 정합점을 확인하고, `TASK-AR-223` 번들로 재수합한다.

## Cross-task Update: TASK-AR-225

- 2026-06-09: `TASK-AR-225` closed the source publication hygiene blocker discovered by this task's executable proof.
- Evidence: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md`.
- Final result: clean bundle `release-preflight --source .tmp/public-source --host-root tests/fixtures/host --check` returned `findings=0`.
- Next route: feed this evidence into `TASK-AR-223` closeout and `TASK-AR-217` rehearsal; do not use repo root as public release source.
