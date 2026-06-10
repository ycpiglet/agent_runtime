---
id: TASK-AR-222
status: in_progress
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 14
est_tokens: 2800
task_set_id: TASKSET-AR-RELEASE-STEWARD
tags:
  - release-closeout
  - official-guidance
  - migration-verification
  - cross-project-operating-model
  - validation-stack
trigger_meeting: yes
created: 2026-06-09
---

## 목표

`v0.1.8` 1차 판정(2026-07-02)을 위해 요구사항 1~16 및 공식 권고를 하나의 판정 번들로 정합한다.
특히 `agent_runtime`을 단일 런타임 + 다중 프로젝트 오버레이 모델로 유지하면서,
쿼리 정의·메타데이터·검증·교정·A2A 추적이 다음 항목에 모두 남도록 한다.

1. 지식 Skill 최상위 라우터(질문 정합/오너/접근권한/신선도/계보 순위)
2. 베테랑 runbook(명확화 → 자료 탐색 → 실행 → 적대적 검토 → 검증 → 기록)
3. 창고 문서 템플릿(빠른 참조/차원설명/핵심테이블/주의사항/패턴/연결고리)
4. 스킬 문서와 코드·데이터·모델 동시 갱신 강제(CI block)
5. 오프라인 평가(도메인별 90% + 모호성/접근권한/경계조건)
6. 실시간 리뷰(고위험에서 reviewer footer + 출처/태그 필수)
7. 자동 교정 수집(예약 스캔 + 오답 라우팅)
8. human definition 책임(질문 contract, 결정 위임, 쿼리 모호성 기록)
9. 강제 규칙은 경고가 아닌 차단으로 동작
10. 질문 계약 필드 정합성(질문, scope, time_window, tolerance, ambiguity, source_tier)
11. SSoT 정렬(단일 출처 우선 순위 + lineage + history + context)
12. 정확도-속도-비용 트레이드오프 기록
13. 메타데이터 필수성(owner/lineage/freshness/confidence/access_level/expiration)
14. 팀/로드맵/조직/연결고리(context packet) 매핑
15. 프로젝트 투입은 오버레이 교체 우선
16. A2A 메시지 버스(trace_id/decision_cycle_id/retry/idempotency)
17. tag_manual 이식 증거의 유형별 재분류(이식/변형/의도적 제외/누락/재평가)

## 작업 패키지

- `2026-07-02` 판정용 closeout 번들 템플릿 확정:
  - 판정 문구, Hold 사유, release-state, release_cause
  - 오프라인/라이브/교정/A2A 증적 교차 링크
  - 결정 주체(owner)/차단 사유(blocked_by)/재작업 기한(decision_deadline)
- `tag_manual` 이식 점검 강화:
  - `MIGRATION-COMPAT-MAP.yml`의 `scripts-source-only`/`scripts-runtime-extra`/`hooks-wrapper`/`skills-pack` 항목을
    `status` + `approved_by` + `expiry` + `justification` + `decision_date` 5개 축으로 재정렬
  - 이식되지 않은 항목을 전부 `hold_for_data` 또는 `hold_for_overlay`로 이관하고 근거 링크 남김
  - 실제 분류근거가 없다면 `block` 처리
- 연구·공식 가이드 반영:
  - OpenAI trace-grading / agent eval / running Codex safely
  - Anthropic eval tool / Claude Code 보안 가이드
  - 최신 오픈연구에서 교차실험·재현성·실험 편향 관리 포인트를 "패턴 후보군"으로 반영
- Cross-project 운영 체크:
  - `PROJECT-CONTEXT.yml`, `ROADMAP.md`, `ORG.md`, `LINKS.md`, `TEAMS.md`, `TEAMS.md` 경계 변경 시
    런타임 코어 수정 없이 오버레이만 변경되는지 확인
  - 오버레이 누락 시 즉시 hold 경로로 이관되는지 검증
- 교차 채널 자동 교정:
  - `EVAL-POLICY.yml`의 correction scan 채널을 통해 `agents/messages`, `reviews`, `tasks`의 오답 패턴을
    `correction` 이벤트로 재생성
- 감사 번들 고정:
  - `reviews/MEETING-2026-06-10-agent-runtime-task-ar-222-version-update-closeout-plan.md`
  - `reviews/RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research.md`
  - `reviews/REVIEW-2026-06-14-agent-runtime-task-ar-222-closeout-log.md`

## 완료 조건

- `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`의 판정 문구와 일시가 2026-07-02/07-09/07-16으로 동일.
- 요구사항 1~16 + 공식 권고( trace-tracing, 승인 경로, allowlist/denylist, HITL )가
  오프라인/라이브/교정/A2A 번들로 수렴.
- `MIGRATION-COMPAT-MAP.yml`의 미완 항목 `missing`/`changed`/`deprecated`/`dropped`이 모두
  `TASK-AR-204` 또는 `TASK-AR-213` 라우트로 즉시 이관되거나 승인 완료.
- `SKILL-DATA-MAP.yml`과 `MIGRATION-COMPAT-MAP.yml`에서 모델/스킬/데이터 변경 동기화 누락이
  0건이거나 즉시 `TASK-AR-204` block로 남음.
- `TASK-AR-221`/`219`/`220`/`216`/`218`/`217` 산출물이 `TASK-AR-210`으로 단일 audit bundle 링크 1개 이상 연결.
- `TASK-AR-223` closeout 통합 산출과 연동하여 위 완료 조건이 동일 증적 채널로 재수합됨.

## 다음 액션

1. `TASK-AR-222`를 in_progress 상태로 선언하고 1차 판정 기준 증적 번들 템플릿 생성.
2. tag_manual 분기 비교 증거를 TASK 산출로 묶고, 이식 누락 유형별 승인/미승인 리스트를 완성.
3. 2026-07-02 직전까지 `TASK-AR-210` ready 전환 조건을 충족했을 때만 `release-state=ready` 허용.
4. `TASK-AR-223`에서 closeout 통합 라우팅을 받아 `hold_for_query_contract`/`hold_for_overlay`/`hold_for_data`로 재이관 증적을 통일.

## Cycle Log (2026-06-14)

- `MIGRATION-COMPAT-MAP.yml` 필수 근거 필드 `justification/expiry` 보강 완료.
- 멀티에이전트 회의/콜/세미나 로그를 closeout 증적으로 묶어 `TASK-AR-222` 감사 번들의 입력으로 확정.
- `TASK-AR-220`과 `TASK-AR-221`의 완료 조건(이관 라우트/근거 보강/교차 링크)을 `MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md`에 반영.

## Closeout Input: TASK-AR-221 Operating Chain Map (2026-06-09)

- Entry point: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md`.
- Use this map as the `v0.1.8` closeout bridge between requirements 1-16 and `TASK-AR-210` release-state translation.
- Baseline validation lanes are consolidated; governance boundaries remain explicit.

## Closeout Input: TASK-AR-210 Release-State Translation (2026-06-09)

- Entry point: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-210-release-state-translation.md`.
- Current allowed release state for v0.1.8 closeout: `hold_for_data`.
- Carry forward baseline evidence from `TASK-AR-223`, but mark migration/overlay/co-location as unresolved governance boundaries.
- `TASK-AR-222` must not describe v0.1.8 as `ready` or `release` until these boundaries are closed or owner-approved.

## v0.1.8 Closeout Bundle (2026-06-09)

- Created closeout entrypoint: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-222-v018-closeout-bundle.md`.
- Supporting records:
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-222-v018-closeout-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-222-v018-closeout-handoff-call.md`
- Current release_state: `hold_for_data`.
- Accepted baseline lanes:
  - release artifact hygiene
  - offline goldset readiness
  - offline prediction scoring
  - live reviewer footer
  - correction collector
  - A2A trace reconstruction
- Remaining boundaries:
  - `TASK-AR-220` migration approval closure
  - `TASK-AR-215` cross-project overlay simulation
  - `TASK-AR-204` co-location enforcement
- Do not mark `ready` or `release` until these boundaries are closed or owner-approved.
- Verification: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-v018-closeout --check` returned `findings=0`.

## Boundary Update: TASK-AR-220 Migration Closure (2026-06-09)

- Entry point: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure.md`.
- Migration approval closure is complete for the v0.1.8 baseline.
- `TASK-AR-222` remaining boundaries now focus on overlay simulation and co-location enforcement.

## Boundary Update: TASK-AR-215 Overlay Simulation Closure (2026-06-09)

- Entry point: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-closure.md`.
- Cross-project overlay simulation is complete for the v0.1.8 baseline.
- Accepted evidence: `scripts/overlay_simulation_gate.py`, `agents/project/overlays/simulations/mvp-client-2026-06-09/context-packet-simulation.json`, and `reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json`.
- Remaining closeout boundary: `TASK-AR-204` co-location enforcement.

## Boundary Update: TASK-AR-204 Co-Location Closure (2026-06-09)

- Entry point: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-204-co-location-gate-closure.md`.
- Co-location enforcement is complete for the v0.1.8 baseline.
- Accepted evidence: `scripts/co_location_gate.py` and `reviews/CO-LOCATION-GATE-2026-06-09-task-ar-204.json`.
- `TASK-AR-210` re-decision moved v0.1.8 from `hold_for_data` to `ready` for governance review.
- Release remains separate from ready and requires owner approval plus release execution evidence.

## Closeout Update: v0.1.8 Ready Pending Owner Approval (2026-06-09)

- `TASK-AR-216` release-state transition package is complete.
- Release execution plan and owner approval template are present under `agents/project/release/`.
- Gate result: `ready_pending_owner_approval`, `findings=0`.
- v0.1.8 remains at ready until owner approval is recorded.
