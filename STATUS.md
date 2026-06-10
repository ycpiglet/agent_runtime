# 현재 상태 보고 (agent_runtime)

## Bottom Line

- 다음 버전 업데이트는 `2026-07-02`(1차 판정) → `2026-07-09`(2차) → `2026-07-16`(최종 freeze)로 진행.
- `TASK-AR-225` source publication hygiene blocker는 완료. clean bundle 기준 `release-preflight`가 `findings=0`으로 통과했다.
- `TASK-AR-217` release rehearsal은 `in_progress`로 전환. release artifact lane은 통과했고, 남은 범위는 offline eval/live reviewer/correction/A2A/hold routing이다.
- 최신 verification bundle `.tmp/release-bundle-verify-20260609-223217` 기준 `release-preflight` 재검증 결과도 `findings=0`.
- `TASK-AR-205` offline eval lane은 실행 가능해졌고 현재 `hold_for_data`로 block. 두 골든셋 모두 `score=0.6667`로 0.90 기준 미달.
- `TASK-AR-205` goldset readiness는 보강 후 `status=pass`. 단, model-output answer accuracy 90%는 아직 미검증이다.
- `TASK-AR-205` deterministic contract-baseline prediction scoring은 `status=pass`; 두 데이터셋 모두 `score=1.0`, `findings=0`.
- Prediction scoring 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-206` live reviewer footer gate는 `status=pass`; baseline reviewer evidence 2건 모두 `score=1.0`.
- Live reviewer gate 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-207` correction collector는 `status=pass`; failed eval/reviewer report에서 correction proposal 2건 생성.
- Correction collector 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-208` A2A trace gate는 `status=pass`; request/review/decision/correction 4-event chain이 재구성됨.
- A2A trace 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-223` closeout bundle consolidation 완료. 단일 entrypoint는 `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md`.
- Closeout bundle 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-221` operating-chain integration 완료. 단일 entrypoint는 `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md`.
- Operating-chain 문서 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-210` release-state 변환 완료. 현재 allowed state는 `hold_for_data`.
- Release-state 템플릿 변경 후 publish bundle check도 `findings=0`.
- `TASK-AR-222` v0.1.8 closeout bundle 완성. 현재 closeout state는 `hold_for_data`.
- v0.1.8 closeout bundle 추가 후 publish bundle check도 `findings=0`.
- `TASK-AR-220` migration approval closure 완료. Migration `hold_for_data` 원인은 v0.1.8 baseline 기준 해소됨.
- Migration closure 후 publish bundle check도 `findings=0`.
- 공개 가능 판정은 모델 점수보다 `release-state + query contract + 오버레이 + migration evidence + reviewer/correction/A2A` 충족 증적이 우선이다.
- 다음 공개 판정 전제는 `TASK-AR-221` + `TASK-AR-222` closeout 번들 동기화 후에만 `TASK-AR-210`에서 `ready`로 전환.
- 1차 판정 이전 `TASK-AR-224`에서 공식 가이드 링크/핵심 항목 재점검이 실패하면 판정 진입 자체가 보류됨.
- 1차 판정에서 `tag_manual` 이식 누락은 `hold_for_data` 또는 `hold_for_overlay`로만 이관되어야 함.
- 공식 반영 조건: closeout 번들에는 쿼리 계약 라우팅(`clarify_required`/`reviewer_review`), trace-grading 증적, reviewer footer, A2A 추적 키(contextId/taskId), `MIGRATION-COMPAT-MAP` 승인 근거가 모두 함께 남아야 한다.
- 최종 판정 도달 조건은 `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data` 미해결이 0건이거나 모두 `TASK-AR-210` 승인/차단 이관 상태가 될 것.

## Signal

- 최신 회의/리뷰
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap.md`
  - `reviews/MEETING-2026-06-10-task-ar-201-definition-policy.md`
  - `reviews/MEETING-2026-06-12-agent-runtime-task-ar-210-gate-coordination.md`
  - `reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md`
 - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update.md`
  - `reviews/MEETING-2026-06-10-agent-runtime-task-ar-222-version-update-closeout-plan.md`
  - `reviews/RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research.md`
  - `reviews/REVIEW-2026-06-14-agent-runtime-task-ar-222-closeout-log.md`
  - `reviews/MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md`
  - `reviews/CALL-2026-06-14-agent-runtime-task-ar-222-sync-call.md`
  - `reviews/SEMINAR-2026-06-14-agent-runtime-task-ar-222-closeout-sync.md`
  - `reviews/MEETING-2026-06-14-agent-runtime-task-ar-223-closeout-planning.md`
  - `reviews/MEETING-2026-06-15-agent-runtime-task-ar-223-cycle-sync.md`
  - `reviews/RESEARCH-2026-06-15-agent-runtime-task-ar-223-hold-routing-and-overlay-edge-research.md`
  - `reviews/CALL-2026-06-15-agent-runtime-task-ar-223-sync-call.md`
  - `reviews/SEMINAR-2026-06-15-agent-runtime-task-ar-223-governance-sync.md`
- 핵심 문서
  - `BACKLOG.md` (버전 스케줄 + P0 우선순위)
  - `AGENTIC_KNOWLEDGE_EVAL_PLAN.md` (쿼리/평가/교정 체인)
  - `agents/project/MIGRATION-COMPAT-MAP.yml` (tag_manual 이식 근거)
  - `agents/project/MIGRATION-HOLD-ROUTING.yml` (`scripts-source-only` 53건 hold 분류)
  - `agents/project/RELEASE-GATE-TEMPLATE.yml` (`TASK-AR-210` 판정 필드 템플릿)
  - `agents/project/ROADMAP.md`
  - `agents/project/PROJECT-CONTEXT.yml`
  - `agents/project/CONTEXT-SOURCES.yml`
  - `agents/project/SKILL-DATA-MAP.yml`
  - `agents/project/LINKS.md`
  - `agents/lead_engineer/tasks/TASK-AR-223.md`
  - `agents/lead_engineer/tasks/TASK-AR-224.md`
  - `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-224-sync-call.md`
  - `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-224-governance-seminar.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-overlay-gate-sync.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md`
  - `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-223-217-rehearsal-integration-research.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-223-217-sync-call.md`
  - `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-223-217-release-seminar.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-log.md`
  - `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json`
  - `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-rerun.json`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-offline-eval-gate-log.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-offline-eval-block-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-205-offline-eval-followup-call.md`
  - `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-goldset-expansion-log.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-goldset-readiness-sync.md`
  - `reviews/OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217.json`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-prediction-scoring-log.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-prediction-scoring-sync.md`
  - `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-206-live-reviewer-gate-log.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-206-live-reviewer-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-206-live-reviewer-followup-call.md`
  - `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-207-correction-collector-log.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-207-correction-collector-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-207-correction-followup-call.md`
  - `reviews/A2A-TRACE-GATE-2026-06-09-task-ar-208.json`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-208-a2a-trace-gate-log.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-208-a2a-trace-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-208-a2a-followup-call.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-handoff-call.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-operating-chain-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-221-operating-chain-handoff-call.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-210-release-state-translation.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-210-release-state-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-210-release-state-handoff-call.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-222-v018-closeout-bundle.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-222-v018-closeout-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-222-v018-closeout-handoff-call.md`
  - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure.md`
  - `reviews/MEETING-2026-06-09-agent-runtime-task-ar-220-migration-approval-sync.md`
  - `reviews/CALL-2026-06-09-agent-runtime-task-ar-220-migration-approval-handoff-call.md`

## Insight

- 멀티 프로젝트 재사용의 핵심은 런타임 자체보다 오버레이(`VISION/ROADMAP/ORG/LINKS/TEAMS`) 동기화 강도이다.
- `tag_manual` 이식은 `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper`, `skills-pack` 근거를
분리해 정렬하지 않으면 재사용 시 같은 실수를 반복한다.
- 요구사항 1~16 closeout는 `TASK-AR-222`로 묶어 다음 판정까지 추적한다.
- 오프라인 90%와 live reviewer/교정/A2A는 동시에 남지 않으면 실제 정확도 보장은 불가하다.
- 질문 자체가 애매하면 데이터 정합만으로는 해소되지 않는다. 정확도 = 맥락 + 검증.
- 규칙은 경고 단계만으로 두면 2~3개월 내 강하게 역류한다. `warn`는 추적, `block`은 종료 조건이어야 함.
- `tag_manual` 이식 항목은 `MIGRATION-COMPAT-MAP.yml`에서 `approved_by/expiry/justification`이 모두 채워진 항목만 pass로 전환; 미비 항목은 `TASK-AR-220`로 되돌아가서 이유 보강 후 재평가한다.
- `MIGRATION-COMPAT-MAP.yml` 기준 이식 요약: `scripts-source-only` 53건, `scripts-runtime-extra` 2건(런타임 확장), `hooks-wrapper` 1건, `scripts-core` 계열은 kept/changed로 분류.
- `TASK-AR-224`는 공식 가이드/스펙과 tag_manual 이식 결측을 한 번에 점검하는 “source-control gate” 라인으로 유지.
- `TASK-AR-224` 현재 상태는 `in_progress`; packet proof는 성공했고 release-preflight는 실행됐으나 `findings=358`로 block. 다음 미완 항목은 source publication hygiene blocker 해소 계획이다.
- `TASK-AR-225`는 완료. `release-preflight findings=358`은 clean bundle release path, sanitizer 보정, generic template sanitization, fixture lock refresh로 해소됐다.
- 공개용 source는 repo root가 아니라 `publish-bundle` 산출물이어야 한다. repo root에는 host governance/task/review 기록이 남는 것이 정상이다.
- `TASK-AR-217`의 release artifact evidence는 확보됐지만, 정확도/검증/교정/A2A evidence는 아직 별도 증명이 필요하다.
- 이번 사이클의 문서 변경 후 sanitizer test는 `95 passed`, publish bundle은 `findings=0`, fixture lock은 `findings=0`, release-preflight는 `findings=0`.
- Offline eval gate는 `scripts/offline_eval_gate.py`로 실행됐고, 현재 block 원인은 도구 결함이 아니라 goldset 데이터 부족이다.
- Goldset 데이터 부족은 해소됐다. 현재 남은 offline blocker는 actual prediction scoring 부재다.
- Offline prediction scoring 부재도 deterministic contract baseline 기준으로 해소됐다. provider-specific score는 별도 release decision일 때만 추가한다.
- Live reviewer footer 부재도 baseline evidence 기준으로 해소됐다. 남은 rehearsal lane은 correction collector와 A2A trace다.
- Correction collector lane도 baseline evidence 기준으로 해소됐다. 남은 rehearsal lane은 A2A trace reconstruction이다.
- A2A trace baseline도 해소됐다. 이제 남은 핵심 작업은 `TASK-AR-223` closeout bundle consolidation과 `TASK-AR-221` 운영 정합 통합이다.
- `TASK-AR-223` closeout bundle은 `ready_for_governance_review`를 권고하지만, 이는 최종 release state가 아니다. `TASK-AR-210`에서 allowed state로 변환해야 한다.
- `TASK-AR-221` map은 baseline validation pass와 governance boundary를 분리했다. 다음 결정은 `TASK-AR-210` allowed state 변환이다.
- `TASK-AR-210`은 `ready_for_governance_review`를 `hold_for_data`로 변환했다. `ready`/`release`는 아직 금지.
- `TASK-AR-222`는 이 상태를 closeout bundle로 고정했다. 다음 작업은 추가 검증 lane이 아니라 boundary closure다.
- Migration boundary는 닫혔다. 남은 release blockers는 overlay simulation과 co-location enforcement다.
- 새 root evaluator script 추가 후 publish bundle check는 `findings=0`으로 통과했다.

## Decision

1. v0.1.8 판정 스케줄은 2026-07-02, 2026-07-09, 2026-07-16.
2. 다음 세션 집행 순서:
    - `TASK-AR-223` closeout 통합: 질문 계약/오버레이/migration 근거를 1개 번들로 고정
    - `TASK-AR-221` 운영 정합 통합
    - `TASK-AR-215` cross-project overlay simulation
    - `TASK-AR-204` co-location enforcement executable gate
    - `TASK-AR-219` 공식 권고 반영/판정 근거 고정
    - `TASK-AR-220` 이식 근거 마감
    - `TASK-AR-222` v0.1.8 closeout 증적 번들화
   - `TASK-AR-216` 판정 이관 상태 정렬
   - `TASK-AR-218` migration hardening
   - `TASK-AR-217` release rehearsal
   - `TASK-AR-214` 질의 계약
   - `TASK-AR-215` 오버레이 연결고리 시뮬레이션
   - `TASK-AR-220` scripts-source-only / scripts-runtime-extra / hooks-wrapper 분류 재검증(의도적 제외 vs 누락)
   - `TASK-AR-210` 최종 gate 템플릿 완성
   - `TASK-AR-204` co-location block 규칙 반영
3. `TASK-AR-204`/`TASK-AR-210`/`TASK-AR-220`에서 `approved_by/justification/expiry` 미입력 항목은 즉시 block.
4. `TASK-AR-224`를 통해 공식 가이드(Claude hook/A2A/trace grading/Codex 안전)와 migration 근거를 먼저 정합한 뒤 1차 판정 순환에 진입.

## Remaining Risk

- `P0-1`은 clean bundle 기준으로 해소됐지만, 이후 누군가 repo root를 공개 source로 다시 사용하면 동일 유형의 실패가 재발한다.
- 오버레이 stale/누락이 `release-preflight`에서 경고로만 남으면 `TASK-AR-215` 적용이 약화됨.
- 오프라인 골든셋 도메인 라벨이 `query contract`와 연결되지 않으면 90% 수치의 해석 오류 발생 가능.
- correction 자동 수집은 스케줄러 주기가 느리면 이슈 반영이 늦어짐.

## Handoff Checklist (Next Session)

1. `PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/release-bundle --apply`
2. `PYTHONPATH=src python -m agent_runtime.cli release-preflight --source .tmp/release-bundle --check`
3. `TASK-AR-225` 증적(`reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md`)을 `TASK-AR-217` rehearsal와 `TASK-AR-223` closeout 번들에 편입.
4. `TASK-AR-223` closeout 통합 번들 1건으로 고정: `MEETING/RESEARCH/CALL/SEMINAR(2026-06-15)` + `TASK-AR-224/225` cycle 증적 + hold 라우팅 + clean bundle preflight 통과 결과 정합.
5. `TASK-AR-221` 운영 정합 통합: 1~16 항목이 backlog/task/status/roadmap/decision_logs 일치
6. `TASK-AR-215` cross-project overlay simulation
7. `TASK-AR-204` co-location enforcement executable gate
8. `TASK-AR-210` 재판정
9. `TASK-AR-219` 판정 근거(07-02/07-09/07-16 문구)와 공식 가이드 링크 동기
10. `TASK-AR-220` 이식 근거(`scripts-source-only`/`scripts-runtime-extra`/`hooks-wrapper`) 보류/승인 정리
11. `TASK-AR-216` release-state/decision_deadline/blocked_by 이관 상태 점검
12. `TASK-AR-218` migration hardening 정합 확인(approved_by/expiry/justification)
11. `TASK-AR-214` 질의 계약 로그(clarify/reviewer/rework)가 로그에 남는지 점검
12. `TASK-AR-222` closeout 번들에서 오프라인/실시간/교정/A2A 증적이 하나의 audit bundle로 남는지 점검
13. `TASK-AR-223` closeout 번들 기준 테스트: 오버레이 stale + hold route + migration 미해결 항목 정합 점검
14. `TASK-AR-215` cross-project 오버레이 시뮬레이션 1건 실행
15. `TASK-AR-210` 버전 게이트 템플릿에 `release-state`와 이관 사유 재기록
16. 2026-07-02 공개 판정일 기준으로 `publish-check` + `release-preflight` + live reviewer/correction/A2A bundle를 `TASK-AR-221` 증적로 남긴다.

## Notes for Continuity

- `BACKLOG`→`ROADMAP`→`TASK`→`REVIEW/RESEARCH`의 증빙 체인을 끊지 말 것.
- 현재는 `TASK-AR-221` 진행 상태에서 `TASK-AR-219` → `TASK-AR-220` 순으로 증빙 동기화를 진행 중.
- 오버레이 변경은 `agents/project/*` 중심으로만 수행하고 런타임 공용 코어 코드는 직접 변경하지 않는다.
- 2026-06-10 멀티에이전트 사이클(회의/연구/세미나/콜) 시작:
  - `reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-start.md`
  - `reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-sync.md`
  - `reviews/CALL-2026-06-10-agent-runtime-task-ar-221-cycle-sync-call.md`
  - `reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-release-governance-seminar.md`
  - `reviews/RESEARCH-2026-06-10-agent-runtime-official-release-governance-research.md`

## Cycle Update: TASK-AR-215 Overlay Simulation Closure (2026-06-09)

Bottom Line

- `TASK-AR-215` is completed for the v0.1.8 baseline.
- The runtime core remains unchanged; project-specific context is represented by overlay files under `agents/project/overlays/simulations/mvp-client-2026-06-09/`.
- Complete overlay packet routes to `ready_for_overlay_use`.
- Missing communication context routes to `hold_for_overlay`, escalates through `TASK-AR-204`, and hands off through `TASK-AR-216`.
- Publish bundle check for this change returned `findings=0`.

Decision

1. Overlay simulation is no longer a release blocker.
2. The next release boundary is `TASK-AR-204` co-location enforcement executable gate.
3. `TASK-AR-210` may be re-evaluated only after `TASK-AR-204` closes or receives explicit owner-approved waiver.

Verification Evidence

- `scripts/overlay_simulation_gate.py`: `status=pass`, `cases=2`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-overlay-simulation --check`: `files=209`, `findings=0`.

## Cycle Update: TASK-AR-204 Co-Location Closure and TASK-AR-210 Ready Re-Decision (2026-06-09)

Bottom Line

- `TASK-AR-204` is completed for the v0.1.8 baseline.
- Co-location gate result: `status=pass`, `release_route=ready_for_release_redecision`, `findings=0`.
- `TASK-AR-210` release state is now `ready` for governance review.
- `release` is not selected yet; owner approval and release execution evidence are still required.

Decision

1. Migration, overlay, and co-location boundaries are closed for `ready` governance review.
2. `RELEASE-GATE-TEMPLATE.yml` now carries `release_state: ready` and `blocked_by: []`.
3. Next cycle should prepare final owner approval/release execution evidence or keep the state at ready.

Verification Evidence

- `scripts/co_location_gate.py`: `status=pass`, `route=ready_for_release_redecision`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-colocation-ready --check`: `files=209`, `findings=0`.

## Cycle Update: v0.1.8 Ready Pending Owner Approval (2026-06-09)

Bottom Line

- `TASK-AR-216` is completed.
- v0.1.8 is ready for governance review but not released.
- Release execution gate result: `status=pass`, `route=ready_pending_owner_approval`, `target=v0.1.8`, `package=0.1.6`, `findings=0`.
- Owner approval is intentionally pending in `agents/project/release/OWNER-APPROVAL-v0.1.8.yml`.

Decision

1. Keep package version at `0.1.6` until owner approval.
2. Do not create git tag `v0.1.8` or publish externally without owner approval.
3. Next cycle can prepare local release smoke or wait for owner approval before version bump/release execution.

Verification Evidence

- `scripts/release_execution_gate.py`: `status=pass`, `route=ready_pending_owner_approval`, `target=v0.1.8`, `package=0.1.6`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-release-execution-boundary --check`: `files=209`, `findings=0`.

## Cycle Update: v0.1.8 Local Smoke Plan Readiness (2026-06-09)

Bottom Line

- v0.1.8 local tag smoke plan is ready with `findings=0`.
- This was a non-mutating `--check`; no local tag, install, external push, or package version bump was performed.
- Release route remains `ready_pending_owner_approval`.

Decision

1. Keep local smoke execution deferred until owner approval or explicit release execution instruction.
2. Continue preserving `0.1.6` package version until the release execution boundary is crossed.

Verification Evidence

- `scripts/release_execution_gate.py`: `status=pass`, `route=ready_pending_owner_approval`, `target=v0.1.8`, `package=0.1.6`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-local-smoke-plan --check`: `files=209`, `findings=0`.

## Cycle Update: v0.1.8 Owner Approval Gate (2026-06-09)

Bottom Line

- Owner approval boundary is now executable.
- Gate result: `status=pass`, `decision_route=owner_approval_pending`, `findings=0`.
- Release execution gate remains `ready_pending_owner_approval`.

Decision

1. Pending approval is valid handoff, not release authorization.
2. Next release execution step requires explicit owner decision in `OWNER-APPROVAL-v0.1.8.yml`.

Verification Evidence

- `scripts/owner_approval_gate.py`: `status=pass`, `route=owner_approval_pending`, `target=v0.1.8`, `approval=pending_owner_approval`, `findings=0`.
- `scripts/release_execution_gate.py`: `status=pass`, `route=ready_pending_owner_approval`, `target=v0.1.8`, `package=0.1.6`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-owner-approval-gate --check`: `files=209`, `findings=0`.

Next Boundary

- Only explicit owner decision remains before release execution.

## Cycle Update: v0.1.8 Pending Release Guard (2026-06-09)

Bottom Line

- v0.1.8 owner-pending state now has a dedicated no-mutation guard.
- Guard result: `status=pass`, `route=hold_at_ready_pending_owner`, `package=0.1.6`, `findings=0`.
- Release remains blocked pending explicit owner decision.

Decision

1. Run pending release guard before release-adjacent edits while approval is pending.
2. Version bump, `release_state=release`, or execution state mutation remains blocked until owner approval.

Verification Evidence

- `scripts/pending_release_guard.py`: `status=pass`, `route=hold_at_ready_pending_owner`, `owner=pending_owner_approval`, `release_state=ready`, `package=0.1.6`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-pending-release-guard --check`: `files=209`, `findings=0`.

## Cycle Update: v0.1.8 Release Readiness Summary (2026-06-09)

Bottom Line

- v0.1.8 readiness evidence is consolidated into one summary report.
- Summary result: `status=pass`, `release_route=ready_pending_owner_decision`, `findings=0`.
- Remaining boundary: explicit owner decision only.

Decision

1. Use `reviews/RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8.json` as the next-session entrypoint.
2. Do not bump version or release until `OWNER-APPROVAL-v0.1.8.yml` changes from pending to approved.

Verification Evidence

- `scripts/release_readiness_summary.py`: `status=pass`, `route=ready_pending_owner_decision`, `target=v0.1.8`, `findings=0`.
- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-readiness-summary --check`: `files=209`, `findings=0`.

## Cycle Update: v0.1.8 Automation Policy Implementation and Local Release (2026-06-09)

Bottom Line

- Implemented the requested automation policy upgrades and released local v0.1.8 evidence.
- Branch/commit/PR/merge automation is now the default for routine, noncritical work.
- Routine patch/minor releases can be approved by an agent release council when critical flags are absent.
- Executive BRIEF v2 is defined for concise, human-centered, machine-readable reporting.
- Package version is now `0.1.8`.
- Local tag smoke installed `agent_runtime-0.1.8` successfully.

Decision

1. Local release evidence is complete.
2. External GitHub publish remains a separate remote execution step.

## 2026-06-09 - v0.1.8 released
- Status: released through autonomous PR path.
- PR: https://github.com/ycpiglet/agent_runtime/pull/3
- Merge commit: `54a04a58b9f53c845fee281aea70a9e7ffee955a`
- Tag: `v0.1.8`
- CI: GitHub Actions run `27200245237`, Python `3.10`, `3.11`, `3.12` passed.
- Smoke: GitHub tag install returned `agent_runtime.__version__ == 0.1.8`.
- Next: host projects can move to `ref: v0.1.8` and run sync/lock.
- Post-merge CI: GitHub Actions run `27200314376`, conclusion `success` on main commit `54a04a58b9f53c845fee281aea70a9e7ffee955a`.

## 2026-06-09 - Autofolio issue triage and README follow-up
- Checked remote GitHub state for `ycpiglet/agent_runtime`.
- Open issue: `#1` Autofolio host integration report.
- Open PR: `#2` clean-install fix, now superseded by `v0.1.8`/PR `#3` content.
- README updated locally with host-first onboarding, overlay file map, issue `#1` disposition, host smoke checks, and `v0.1.8` pin.
- Next remote action: publish README docs PR, then comment on `#1` with reflected/residual items and close or mark `#2` superseded.
- Remote complete: PR `#4` merged at `2e0638a3646c33918f923b0f26987c32ac2f3e26`.
- Remote complete: main push CI run `27201582022` succeeded.
- Remote complete: issue `#1` commented with reflected/residual items; PR `#2` closed as superseded.
- Current remote queue: no open PRs; issue `#1` remains open for follow-up design items.

## 2026-06-09 - Backlog BRIEF format drift compound
- Issue: `백로그 띄워줘` was answered as a plain compressed list, not the established decision-oriented BRIEF/decision-board format.
- Recurrence: user confirmed this is not the first occurrence and that rules had already been forced.
- Cause: documentation rules existed, but the live response path did not enforce them before answering.
- Compound record: `agents/lead_engineer/compound_log.md` (`COMPOUND-2026-06-09-001`).
- Review record: `reviews/REVIEW-2026-06-09-backlog-brief-format-drift-compound.md`.
- Correct default: backlog/report/status/plan outputs use `Bottom Line -> Signal -> Insight -> Decision -> Priority/Action Board -> Next` unless the user explicitly asks for raw/minimal output.
- Next action: implement an executable response/artifact format gate so this does not remain prose-only policy.

## 2026-06-09 - Owner Backlog / Report Format Restoration

### Bottom Line

- Summary: prior backlog decision-board style restored with clearer `Action / Ask / Review / Later / Done` labels.
- Status: `BACKLOG-BOARD.md` generated with all 25 current TASK files.
- Gate: Owner document format check passed for `BACKLOG-BOARD.md`.

### Signal

- Issue: backlog/report output drifted from Owner decision format.
- Cause: prose rules existed without executable generation and validation.
- Fix: generator plus gate added at root and project-template level.

### Decision

- Decision: Owner-facing backlog starts from `BACKLOG-BOARD.md`.
- Decision: Owner-facing documents preserve `Bottom Line / Signal / Insight / Decision` before action tables.
- Decision: task rows include difficulty, token/time cost, value, importance, team, agent, decision, and summary.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Generate all-task board | lead-engineer | codex | `tasks=25` |
| Done | Pass format gate | lead-engineer | codex | `findings=0` |
| Done | Record review | lead-engineer | codex | `reviews/REVIEW-2026-06-09-backlog-board-restoration-owner-format-gate.md` |

### Risks / Blockers

- Risk: future manual edits bypass generator/gate.
- Risk: old TASK files may contain partial or malformed metadata.
- Blocker: none for current handoff.

### Next Steps

- Wire format gate into CI/hook/release flow.
- Normalize task frontmatter where inferred values repeat.

## 2026-06-09 - Owner Format Gate Hook / CI / Release Enforcement

### Bottom Line

- Summary: `1-2-3` enforcement complete: hook, CI, release-preflight.
- Status: clean bundle release-preflight passed with `findings=0`.
- Gate: `owner-doc-format` appears in release-preflight and passed with `findings=0`.

### Signal

- Hook proof: `.githooks/pre-commit` runs `scripts/owner_doc_format_gate.py --manifest owner-docs.yml`.
- CI proof: `.github/workflows/test.yml` includes `Check Owner document format`.
- Release proof: clean bundle preflight output includes `owner-doc-format | ok`.
- Bundle proof: publish bundle selected `BACKLOG-BOARD.md`, `owner-docs.yml`, owner review, and gate script.

### Decision

- Decision: `owner-docs.yml` is the Owner document enforcement manifest.
- Decision: clean bundle path is the release-valid preflight path.
- Decision: `.codex/` config remains excluded because sanitizer blocks `.codex/` in public source.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Hook gate | lead-engineer | codex | `.githooks/pre-commit` |
| Done | CI gate | cicd-engineer | codex | `.github/workflows/test.yml` |
| Done | Release gate | agent-runtime-core | codex | `src/agent_runtime/release_preflight.py` |
| Done | Fixture lock refresh | cicd-engineer | codex | `tests/fixtures/host/agent_runtime.lock.json` |

### Risks / Blockers

- Risk: docs outside `owner-docs.yml` are not hard-gated yet.
- Risk: legacy report migration should be staged to avoid mass blocking.
- Blocker: none for current handoff.

### Next Steps

- Add each newly migrated Owner-facing report to `owner-docs.yml`.
- Keep generated backlog board and review docs passing the manifest gate.

## 2026-06-09 - Hooks and State Machine Enforcement

### Bottom Line

- Summary: `hooks.json`, Git hook, CI, release-preflight, and state-machine SSoT are enforced.
- Signal: pass.
- Score: 100.
- Release proof: clean bundle release-preflight passed with `findings=0`.

### Signal

| Gate | Signal | Score | Result |
| --- | --- | --- | --- |
| Owner governance gate | pass | 100 | `findings=0` |
| Public sanitize | pass | 100 | `findings=0` |
| Publish check | pass | 100 | `findings=0` |
| Release preflight | pass | 100 | `findings=0` |
| State machines | pass | 100 | `state-machines | ok` |

### Decision

- Decision: `pass/watch/block + score` is the shared status language.
- Decision: `agents/project/STATE-MACHINES.yml` is the lifecycle SSoT.
- Decision: local Git hook is configured via `core.hooksPath=.githooks`.
- Decision: `.codex/hooks.json` is permitted as a public-safe hook config exception.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Codex hook config | cicd-engineer | codex | `.codex/hooks.json` |
| Done | Git hook enforcement | cicd-engineer | codex | `.githooks/pre-commit` |
| Done | State-machine schema | agent-runtime-core | codex | `schemas/state-machines.schema.json` |
| Done | State-machine template | agent-runtime-core | codex | template `STATE-MACHINES.yml` |
| Done | Release preflight integration | agent-runtime-core | codex | `state-machines` preflight check |

### Risks / Blockers

- Risk: local Git hooks can be bypassed manually; CI/release gates cover repo-level enforcement.
- Risk: Codex hook support depends on active runtime behavior.
- Blocker: none for current handoff.

### Next Steps

- Treat new lifecycle states as schema-first changes.
- Keep Owner-facing docs in `owner-docs.yml` only after format migration.

## 2026-06-10 - Worktree Cleanup and Backlog Cycle Handoff

### Bottom Line

- Summary: completed `TASK-AR-233`; cleanup work is committed and pushed on a branch.
- Branch: `codex/ui-console-backlog-cleanup`.
- Remote: `origin/codex/ui-console-backlog-cleanup`.
- Commit: `f9a3347` (`chore: register ui console backlog and governance gates`).
- State machine: `cycle=completed`, `task=TASK-AR-233 completed`, `gate=pass`, `document=published`.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Remote sync | pass | `origin/main` fetched; local `main` was behind 2 commits |
| Preservation | pass | local work stashed as `ui-console-backlog-pre-sync` before branch switch |
| Conflict resolution | pass | publish/release/reporting/fixture-lock conflicts resolved |
| UI backlog registration | pass | `TASK-AR-226` through `TASK-AR-232` created |
| Cycle map | pass | `reviews/REVIEW-2026-06-10-agent-runtime-worktree-cleanup-cycle-map.md` created |
| Local verification | pass | `pytest tests -q`: 218 passed; owner governance/sanitize/publish-check/diff-check passed |
| Remote publication | pass | branch pushed to `origin/codex/ui-console-backlog-cleanup` |

### Decision

- Decision: push a branch rather than direct-pushing `main`.
- Decision: exclude empty execution residue (`stdout.txt`, `stderr.txt`) from commit.
- Decision: after push, continue implementation from `TASK-AR-226 -> TASK-AR-227 -> TASK-AR-228`.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start UI Runtime Data Map | lead-engineer | `TASK-AR-226` |
| Then implement UI State API / File Adapter | lead-engineer | `TASK-AR-227` |
| Then build read-only console MVP | lead-engineer | `TASK-AR-228` |

## 2026-06-10 - UI Runtime Data Map Cycle

### Bottom Line

- Summary: completed `TASK-AR-226`; UI Console data sources and mutation boundaries are mapped before UI implementation.
- Output: `docs/UI_RUNTIME_DATA_MAP.md`.
- State machine: `cycle=done`, `task=TASK-AR-226 completed`, `gate=pass`, `document=formatted`.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Source map | pass | `docs/UI_RUNTIME_DATA_MAP.md` |
| MVP coverage | pass | backlog, current tasks, Kanban, agents, events, messages, goal status, task detail mapped |
| Safe-write boundary | pass | API first; `.ui_outbox/COMMAND-*.json` fallback; no direct browser mutation |
| Follow-up contract | pass | `TASK-AR-227` read-first adapter endpoints listed |
| Known gap | watch | durable repo-local goal JSON SSoT does not exist yet |

### Decision

- Decision: treat `docs/UI_RUNTIME_DATA_MAP.md` as the implementation contract for `TASK-AR-227`.
- Decision: keep `TASK-AR-227` read-first and side-effect-free.
- Decision: defer task reorder mutation to `TASK-AR-229` unless a canonical order field or runtime-owned order file is introduced.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start UI State API / File Adapter | lead-engineer | `TASK-AR-227` |
| Write adapter tests before production code | lead-engineer | TDD required for implementation code |
| Keep source freshness metadata in API output | lead-engineer | every normalized response includes source info |

## 2026-06-10 - UI State API / File Adapter Cycle

### Bottom Line

- Summary: completed `TASK-AR-227`; the UI Console has a read-only local adapter and CLI shaped like future `/api/*` endpoints.
- Output: `src/agent_runtime/ui_state.py`, `tests/test_ui_state.py`, and `docs/UI_STATE_API_EXAMPLES.md`.
- State machine: `cycle=done`, `task=TASK-AR-227 completed`, `gate=pass`, `document=formatted`.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Read-only adapter | pass | `agent_runtime.ui_state.build_state(root)` |
| CLI surface | pass | `agent_runtime ui-state --resource state --json` |
| Source metadata | pass | records include `source_path`, `source_kind`, `source`, `last_updated`, `freshness` |
| Optional missing sources | pass | empty arrays plus `missing_optional_source` gaps |
| Malformed records | pass | JSONL/session warnings instead of crashes |
| Targeted tests | pass | `PYTHONPATH=src pytest tests/test_ui_state.py -q` -> 5 passed |

### Decision

- Decision: build `TASK-AR-228` against `agent_runtime ui-state --root . --resource state --json`.
- Decision: keep the first web console read-only and polling-compatible.
- Decision: defer all mutation controls to `TASK-AR-229` write-through/outbox work.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start Read-Only Web Console MVP | lead-engineer | `TASK-AR-228` |
| Use adapter JSON as UI fixture | lead-engineer | `docs/UI_STATE_API_EXAMPLES.md` |
| Preserve source/freshness metadata in panels | lead-engineer | adapter response contract |

## 2026-06-10 - Read-Only UI Console MVP Cycle

### Bottom Line

- Summary: completed `TASK-AR-228`; a dependency-free local web console serves current runtime state through the `TASK-AR-227` adapter.
- Output: `src/agent_runtime/ui_console.py`, `tests/test_ui_console.py`, and `docs/UI_CONSOLE_MVP.md`.
- State machine: `cycle=done`, `task=TASK-AR-228 completed`, `gate=pass`, `document=formatted`.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Runnable UI | pass | `agent_runtime ui-console --root . --host 127.0.0.1 --port 8765` |
| Dashboard/backlog | pass | browser smoke rendered 29 task cards and 6 lanes |
| Detail drawer | pass | task click showed source and freshness metadata |
| Mobile layout | pass | 390px Chromium smoke rendered 29 cards, 6 lanes, 5 tabs |
| Empty states | pass | agents/messages/events render absent runtime dirs as empty panels |
| Mutation boundary | pass | no write controls exposed before `TASK-AR-229` |
| Full tests | pass | `PYTHONPATH=.;src pytest tests -q` -> 228 passed |

### Decision

- Decision: use `agent_runtime ui-console` as the read-only inspection surface.
- Decision: keep the console dependency-free until UI complexity justifies a larger frontend stack.
- Decision: route all future writes through `TASK-AR-229`; do not add browser file mutation.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start Task CRUD and Backlog Ordering | lead-engineer | `TASK-AR-229` |
| Define canonical task order/write-through | lead-engineer | required before drag/drop or status edits |
| Keep read-only smoke passing | lead-engineer | `tests/test_ui_console.py` and Chromium smoke |

## 2026-06-10 - Task CRUD and Backlog Ordering Cycle

### Bottom Line

- Summary: completed `TASK-AR-229`; the UI console now writes through validated server routes and stores command outcomes in `.ui_outbox`.
- Output: `src/agent_runtime/ui_commands.py`, updated `src/agent_runtime/ui_console.py`, `tests/test_ui_commands.py`, and `docs/UI_WRITE_COMMANDS.md`.
- State machine: `cycle=done`, `task=TASK-AR-229 completed`, `gate=pass`, `document=formatted`.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Create/update | pass | `POST /api/tasks`, `PATCH /api/tasks/:id` |
| Reorder | pass | `POST /api/tasks/:id/reorder`, frontmatter `order` |
| Comment/message | pass | `POST /api/messages` writes queued message markdown |
| Archive | pass | `POST /api/tasks/:id/archive` writes `status: completed`, `archived: true` |
| Rejection path | pass | invalid status, missing task id, and direct-file keys fail with stored errors |
| UI write states | pass | `Writes` tab shows pending/accepted/failed command records |
| Targeted tests | pass | `PYTHONPATH=src pytest tests/test_ui_commands.py tests/test_ui_console.py tests/test_ui_state.py -q` -> 21 passed |
| Browser smoke | pass | temporary-root UI flow created, updated, archived `TASK-UI-901` |
| Full tests | pass | `PYTHONPATH=.;src pytest tests -q` -> 239 passed |

### Decision

- Decision: use `.ui_outbox/COMMAND-*.json` as the audit trail for UI-originated writes.
- Decision: use task frontmatter `order` as the first canonical UI ordering field.
- Decision: keep hard delete and runtime lifecycle controls out of `TASK-AR-229`; continue with `TASK-AR-230`.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start Runtime Command Controls | lead-engineer | `TASK-AR-230` |
| Add prompt/review/start/pause/resume/stop commands | lead-engineer | build on `ui_commands` |
| Keep mutation smoke isolated from repo root | lead-engineer | temporary runtime roots |

## 2026-06-10 - Runtime Command Controls Cycle

### Bottom Line

- Summary: completed `TASK-AR-230`; the UI console now submits runtime-safe command requests on top of `.ui_outbox`.
- Output: `runtime.*` command types, `POST /api/commands`, UI command form, safety metadata, and `docs/UI_RUNTIME_COMMANDS.md`.
- State machine: `cycle=done`, `task=TASK-AR-230 completed`, `gate=pass`, `document=formatted`.
- Boundary: UI submits commands and status metadata; it does not embed or type into Claude/Codex terminal sessions.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Previous cycle | pass | `TASK-AR-229` committed as `607df7b` and pushed |
| Current task | pass | `agents/lead_engineer/tasks/TASK-AR-230.md` |
| Command route | pass | `POST /api/commands` accepts `runtime.call_agent` |
| Message bridge | pass | safe agent prompts become queued `runtime-command` messages |
| Approval boundary | pass | commit/push/PR/install/deletion/external/long-running triggers become `approval_required` |
| Lifecycle boundary | pass | goal start/pause/resume/stop records become `pending_runtime_support` without claiming execution |
| Targeted tests | pass | `tests/test_ui_commands.py` 11 passed; `tests/test_ui_console.py` 9 passed |
| Route smoke | pass | temporary-root `runtime.call_agent` POST produced one queued command and message |

### Decision

- Decision: extend existing `ui_commands.submit_command` and `/api/commands` routing instead of adding terminal embedding.
- Decision: represent unsupported lifecycle controls explicitly in command records until a runtime executor exists.
- Decision: keep all UI-originated runtime requests auditable through `.ui_outbox/COMMAND-*.json`.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start Live Updates, Logs, Replay, Evidence | lead-engineer | `TASK-AR-231` |
| Add event filtering and freshness tests first | lead-engineer | `tests/test_ui_state.py`, `tests/test_ui_console.py` |
| Keep command execution claims separate from command submission | lead-engineer | runtime executor is a later task |

## 2026-06-10 - Live Updates, Logs, Replay, Evidence Cycle

### Bottom Line

- Summary: completed `TASK-AR-231`; the UI console now has filterable events and read-only error/evidence/replay views.
- Output: `ui_state.filter_events`, derived `errors`/`evidence`/`replay` resources, `/api/events` query filtering, and an Evidence tab.
- State machine: `cycle=done`, `task=TASK-AR-231 completed`, `gate=pass`, `document=formatted`.
- Boundary: evidence/log/replay panels stay read-only; writes still go through dedicated command paths.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Previous cycle | pass | `TASK-AR-230` committed as `70e7c32` and pushed |
| Current task | pass | `agents/lead_engineer/tasks/TASK-AR-231.md` |
| Event filtering | pass | `ui_state.filter_events` and `/api/events?...` |
| Error/evidence/replay | pass | derived `errors`, `evidence`, `replay` state resources |
| UI visibility | pass | Evidence tab plus event type/agent/task/goal/search filters |
| Targeted tests | pass | `test_ui_state.py` 6 passed; `test_ui_console.py` 10 passed; `test_ui_commands.py` 11 passed |
| Route smoke | pass | temporary-root filter returned one `agent.error`; state showed errors/evidence/replay |
| Runtime boundary | pass | polling remains active transport; SSE deferred |

### Decision

- Decision: add filterable event views and derived error/evidence/replay resources before adding any streaming transport.
- Decision: preserve source/freshness metadata on records rendered in UI panels.
- Decision: keep SSE deferred until the state API and executor state are stable enough to avoid false liveness claims.

### Next Steps

| Step | Owner | Evidence |
| --- | --- | --- |
| Start Graph, State Machine, Roadmap Views | lead-engineer | `TASK-AR-232` |
| Keep graph/state-machine views read-only first | lead-engineer | avoid direct lifecycle mutation |
| Preserve source links in visual summaries | lead-engineer | `docs/UI_LIVE_OBSERVABILITY.md` |
