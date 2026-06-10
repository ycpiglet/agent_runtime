---
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - STATUS.md
  - agents/project/ROADMAP.md
  - agents/project/LINKS.md
  - agents/project/SKILL-GOVERNANCE.md
  - agents/project/CONTEXT-SOURCES.yml
  - agents/project/MIGRATION-COMPAT-MAP.yml
  - agents/project/SKILL-DATA-MAP.yml
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-governance-cycle.md
  - reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-multi-agent-sync-seminar.md
  - reviews/CALL-2026-06-10-agent-runtime-task-ar-221-handoff-call.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-version-update-and-official-guidance-refresh.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-start.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-sync.md
  - reviews/CALL-2026-06-10-agent-runtime-task-ar-221-cycle-sync-call.md
  - reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-release-governance-seminar.md
  - reviews/RESEARCH-2026-06-10-agent-runtime-official-release-governance-research.md
  - reviews/MEETING-2026-06-10-agent-runtime-task-ar-222-version-update-closeout-plan.md
  - reviews/RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research.md
  - reviews/REVIEW-2026-06-14-agent-runtime-task-ar-222-closeout-log.md
  - reviews/MEETING-2026-06-14-agent-runtime-task-ar-223-closeout-planning.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-223-217-rehearsal-integration-research.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-log.md
  - reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-release-state-bridge.md
  - reviews/OFFLINE-EVAL-2026-06-10-taskset-quality-loop-final.json
  - reviews/OFFLINE-PREDICTION-SCORE-2026-06-10-taskset-quality-loop-final.json
  - reviews/LIVE-REVIEWER-GATE-2026-06-10-taskset-quality-loop-final.json
  - reviews/CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final.json
  - reviews/A2A-TRACE-GATE-2026-06-10-taskset-quality-loop-final.json
  - reviews/REVIEW-2026-06-10-agent-runtime-task-ar-221-quality-loop-closeout.md
id: TASK-AR-221
status: completed
completed_at: 2026-06-10T23:22:00+09:00
started_at: 2026-06-09T18:00:00+09:00
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 16
est_tokens: 3200
task_set_id: TASKSET-AR-QUALITY-LOOP
tags:
  - architecture
  - cross-project
  - quality-governance
  - query-contract
  - offline-eval
  - live-review
  - a2a
  - migration-provenance
trigger_meeting: yes
created: 2026-06-09
---

## 목표

에이전트 런타임을 한 번에 재사용 가능한 MVP/멀티 프로젝트 운영 구조로 정리한다.
공식 가이드(Claude/Codex/OpenAI 권고)에 맞추어 아래 1~16 항목을
`라우터→쿼리 계약→평가→교정→오버레이→릴리스 게이트` 하나의 운영 체인으로 고정한다.
`v0.1.8` 공개 판정 일정(2026-07-02/2026-07-09/2026-07-16) 기준을 본 TASK의 완료 기준에 포함한다.

1. 지식 Skill 최상위 라우터
2. runbook(질문 명확화/자료 탐색/실행/적대적 검토/검증)
3. 창고 문서 표준(빠른 참조/차원설명/핵심테이블/주의사항 및 패턴/연결고리)
4. 스킬 문서와 코드/데이터 동기화 강제
5. 오프라인 eval 90% 게이트
6. 실시간 reviewer + 출처/태그 footer
7. 자동 교정 이벤트 수집
8. context-first + 인간 정의 책임
9. 규칙 강제(강제 없는 규칙은 실패)
10. 질의 정제
11. SSoT 정렬
12. 정확도-속도-비용 트레이드오프
13. 메타데이터 스키마 고정
14. 팀/로드맵/조직 연결(오버레이)
15. 프로젝트 이식 시 최소 오버레이 교체
16. A2A 메시지 버스와 증적 재구축성

## 작업 내용

- v0.1.8 판정 일정(2026-07-02/2026-07-09/2026-07-16)과 동일 문구를
  `BACKLOG`/`STATUS`/`ROADMAP`/`TASK-AR-210`에 고정.
- `TASK-AR-201`~`TASK-AR-215`에서 빠진 게이트 조건을 추적해
  공식 가이드 대응 항목(`release_state`, `decision_deadline`, `tradeoff`, `clarify_required`, `hold_for_*`)이
  `TASK-AR-210` 차단 체인에 즉시 이관되게 정합.
- 판정 템플릿(`release-state`, `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`)의 1차/2차/최종 문구를
  `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에서 통일.
- 공식 가이드 반영 증거 번들 추가:
  - query contract(질문 스키마) 미달 시 `clarify_required` 또는 `reviewer_review`
  - 오프라인 골든셋 실패 시 `correction` 생성
  - 실시간 고위험 결과의 `reviewer_verdict + source_footer + source_tier/ambiguity/confidence` 필수
- `MIGRATION-COMPAT-MAP.yml`의 `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`,
  `skills-pack`을 근거 레벨(`owner`, `approved_by`, `justification`, `expiry`)로 다시 정렬.
- 스킬 문서는 코드/데이터와 동일한 오버레이 구조로 동기화하고,
  모델/provider 변경 시 문서 갱신이 없으면 `warn`가 아닌 `block`.
- 스케줄러형 correction 스캔을 명시하고, 교정 이벤트 재적용 주기를
  `TASK-AR-210`/`release gate`에서 추적하도록 체크리스트화.
- 오버레이 누락은 즉시 `hold_for_overlay`, 질의 계약 누락은 즉시 `hold_for_query_contract`로 이동.

## 완료 조건

- `TASK-AR-219`, `TASK-AR-220`, `TASK-AR-216`, `TASK-AR-217` 산출이 `AGENTIC_KNOWLEDGE_EVAL_PLAN.md` 실행 순서와 정합.
- `TASK-AR-222` closeout 번들이 요구사항 1~16 + 공식 권고 + migration 근거를 단일 감사 번들로 묶어 `TASK-AR-210`으로 이관.
- `TASK-AR-205` 도메인별 오프라인 90% 미달 시 해당 도메인 블로커가 `release-state`로 남음.
- `TASK-AR-206` 고위험 리뷰와 `TASK-AR-208` A2A chain 재구축이 연동됨.
- 스킬 문서 동기화/마이그레이션 차단이 `release-preflight`에서 실제 block 신호를 남김.
- `TASK-AR-204`에서 `approved_by/justification/expiry` 미입력 상태가 즉시 block로 연결됨.
- 2026-07-02 판정에서 1차/2차/최종 판정 문구가 4개 핵심 문서(BACKLOG/ROADMAP/STATUS/TASK-AR-210)에 동일.
- 1차/2차/최종 판정 템플릿(판정문구/hold사유/오너 승인 포인트)이 문서 간 누락 없이 일치.
- `TASK-AR-214` 쿼리 계약의 `source_tier/owner/access_level/freshness_sla/lineage/ambiguity_level` 필드가 실사용에서 기록됨.
- `MIGRATION-COMPAT-MAP.yml` 미완 항목의 분류와 보류 사유가 태스크 이관 경로와 1:1 대응됨.

## Cycle Log (2026-06-10)

- 선행 협업 로그 생성: MEETING/CALL/SEMINAR/RESEARCH 1회 이상 동기화 완료.
- 다음 단계 선점: `TASK-AR-219` 문구 정합, `TASK-AR-220` 마이그레이션 근거 재정렬, `TASK-AR-216` state/이관 라우팅 교차 점검.
- `TASK-AR-221` 완료 조건 중 1차 판정 템플릿 정합 점검을 "cycle-1"으로 설정하고 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`의 동일성은 보존.
- `TASK-AR-223` closeout 통합 문서 기준으로 산출물 교차체계(1차/2차/최종 판정 템플릿)를 재점검.

## Cycle Log (2026-06-14)

- `TASK-AR-220`에서 지적된 migration 근거 미완 항목을 `MIGRATION-COMPAT-MAP.yml`에서 보강 완료하여
  `TASK-AR-222` closeout 번들 증적 강건성 확보.
- `MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md`,
  `CALL-2026-06-14-agent-runtime-task-ar-222-sync-call.md`,
  `SEMINAR-2026-06-14-agent-runtime-task-ar-222-closeout-sync.md`를
  `TASK-AR-221` 증적 번들로 반영.

## Cycle Log (2026-06-09)

- `TASK-AR-225` release-source proof를 통합 게이트 입력으로 편입.
- `TASK-AR-217` rehearsal은 clean bundle preflight proof를 이미 충족한 것으로 보고, 남은 범위를 offline eval/live reviewer/correction/A2A/hold routing으로 축소하지 않고 명시적으로 분리했다.
- 공식 근거 매핑은 trace grading, datasets/evals, tool approval/guardrail, Claude Code permission/security, A2A context/task continuity를 release evidence field로 변환한다.

## 산출물(예정)

- `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update.md`
- `agents/project/SKILL-DATA-MAP.yml` / `agents/project/MIGRATION-COMPAT-MAP.yml` co-location 규칙 정합
- `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`/`BACKLOG.md`/`ROADMAP.md`/`STATUS.md` 갱신
- `TASK-AR-219`, `TASK-AR-220`, `TASK-AR-216`, `TASK-AR-217` 이관 증거 번들


## Input from TASK-AR-223 Closeout Bundle (2026-06-09)

- Entry point: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md`.
- Baseline evidence lanes accepted for operating-chain integration:
  - release artifact
  - offline scoring
  - live reviewer footer
  - correction collector
  - A2A trace reconstruction
- Remaining operating-chain checks:
  - map requirements 1-16 to the bundle evidence.
  - confirm migration approval closure or route to `hold_for_data`.
  - confirm overlay cross-project simulation or route to `hold_for_overlay`.
  - translate recommendation into `TASK-AR-210` allowed release state.

## Operating Chain Integration (2026-06-09)

- Created operating-chain mapping: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md`.
- Supporting records:
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-operating-chain-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-221-operating-chain-handoff-call.md`
- Mapped `TASK-AR-223` closeout bundle to requirements 1-16.
- Baseline pass lanes: release artifact, offline scoring, live reviewer, correction collector, A2A trace.
- Remaining governance boundaries: migration approval closure, overlay cross-project simulation, co-location block enforcement, provider/live transport policy.
- Next route: `TASK-AR-210` release-state translation.
- Verification: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-operating-chain --check` returned `findings=0`.

## Release-State Feedback from TASK-AR-210 (2026-06-09)

- `TASK-AR-210` translated `ready_for_governance_review` to `hold_for_data`.
- Operating-chain implication: requirements 5-7 and 16 have baseline evidence, but requirements 4, 14, 15 and migration governance keep the release out of `ready`.
- Next operating-chain focus: co-location enforcement, overlay simulation, and migration approval closure.

## Release-State Bridge from TASK-AR-223 (2026-06-10)

- Entry point: `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-release-state-bridge.md`.
- Operating-chain interpretation: the `TASK-AR-223` bundle remains the requirements 1-16 evidence tree, and later closure evidence from `TASK-AR-220`, `TASK-AR-215`, and `TASK-AR-204` removes the local `hold_for_data` / `hold_for_overlay` blockers.
- Current local-evidence route: `release_evidence_ready` through `TASK-AR-210`.
- Remote publication boundary: external GitHub publish remains `remote_publish_deferred_out_of_scope` and is not an operating-chain completion claim.
- Next operating-chain focus: preserve the boundary in final handoff so local release evidence is not confused with PR/tag/CI publication.

## Quality Loop Closeout (2026-06-10)

- Closeout review: `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-221-quality-loop-closeout.md`.
- Offline eval gate: `reviews/OFFLINE-EVAL-2026-06-10-taskset-quality-loop-final.json`, `status=pass`, all datasets `score=1.0`.
- Prediction score gate: `reviews/OFFLINE-PREDICTION-SCORE-2026-06-10-taskset-quality-loop-final.json`, `status=pass`, all datasets `score=1.0`.
- Live reviewer gate: `reviews/LIVE-REVIEWER-GATE-2026-06-10-taskset-quality-loop-final.json`, `status=pass`, `score=1.0`.
- Correction collector: `reviews/CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final.json`, `status=pass`, `written=2`.
- A2A trace gate: `reviews/A2A-TRACE-GATE-2026-06-10-taskset-quality-loop-final.json`, `status=pass`, `events=4`, `chains=1`, `findings=0`.
- Boundary: this closes the local Quality Loop operating-chain evidence; remote publication and provider-live behavior remain separate approval-backed evidence.
