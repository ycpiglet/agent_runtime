# Backlog (agent_runtime, 진행 우선순위 기준)

## 2026-06-11 TASKSET-AR-OPS-FEEDBACK-ANALYSIS Registration

- New task set: `TASKSET-AR-OPS-FEEDBACK-ANALYSIS` (Feedback Analyst).
- Purpose: 2026-06-11 Owner 운영 정비 세션의 feedback/plan/analysis 산출물 등록 — 구현/개발 없음.
- Registered tasks: `TASK-AR-306` (completed, 세션 closeout 기록), `TASK-AR-307` (planned, 전사 구조 개선 후속 계획), `TASK-AR-308` (planned, 기능·비전 전략 우선순위), `TASK-AR-309` (planned, UI 배포 경로 가드 계획).
- Conversation record: `reviews/REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session.md`.
- Branch cleanup manifest: `reviews/REVIEW-2026-06-11-agent-runtime-branch-cleanup-sha-manifest.md`.
- Session outcomes: 로컬/원격 브랜치 25개 정리(main만 잔존), UI 미반영 근본 원인 해결(editable 재설치 + 구버전 서버 재시작), Claude Code 플러그인 4종 비활성화(serena/discord/telegram/github), tag_manual 라이브 참조 제거(감사 YAML은 보존), .tmp 73.8MB 정리.
- Boundary: MIGRATION-COMPAT-MAP.yml 등 마감된 감사 증거와 reviews/ 역사 기록은 수정하지 않는다.

## 2026-06-11 TASKSET-AR-RSI-OPERATING-SYSTEM Registration

- New planned task set: `TASKSET-AR-RSI-OPERATING-SYSTEM`.
- Purpose: implement A안, an Evidence-to-Proposal OS that captures trace/eval/grader/A2A/correction/review/retro/failure/compound/conversation evidence, dedupes it, measures proposal quality, routes council review, and applies only through bounded gates.
- Registered planned tasks: `TASK-AR-297` through `TASK-AR-305`.
- Plan entrypoint: `docs/superpowers/plans/2026-06-11-rsi-operating-system-taskset.md`.
- Owner brief: `AGENT_RUNTIME_RSI_OPERATING_SYSTEM_BRIEF.md`.
- Conversation record: `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md`.
- Registration evidence: `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration.md`.
- New registry scaffolds: `agents/project/evidence/` and `agents/project/casebooks/`.
- Boundary: this does not reopen `TASKSET-AR-RSI-PLANNING`, does not claim A2A end-to-end execution, and keeps C-mode as a latent future option until repeated B-mode evidence justifies promotion.

## 2026-06-11 TASKSET-AR-CONTEXT-KNOWLEDGE Closeout

- Completed local context knowledge task set: `TASKSET-AR-CONTEXT-KNOWLEDGE`.
- Closed task records: `TASK-AR-201`, `TASK-AR-202`, `TASK-AR-203`, `TASK-AR-204`, `TASK-AR-211`, `TASK-AR-214`, and `TASK-AR-215`.
- Added executable closeout gate: `scripts/context_knowledge_gate.py`.
- Evidence: `reviews/CONTEXT-KNOWLEDGE-GATE-2026-06-11-final.json`, `reviews/OVERLAY-SIMULATION-GATE-2026-06-11-context-knowledge-final.json`, `reviews/OFFLINE-EVAL-2026-06-11-context-knowledge-final.json`, and `reviews/OFFLINE-PREDICTION-SCORE-2026-06-11-context-knowledge-final.json`.
- Owner closeout: `reviews/REVIEW-2026-06-11-agent-runtime-context-knowledge-taskset-closeout.md`.
- Boundary: local contract/eval/gate evidence is complete; provider-live or remote release evidence remains separate.

## 2026-06-11 TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION Closeout

- Completed local task set: `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION`.
- Purpose: prevent repeat cleanup drift around session closeout, late dirty work, stash/archive refs, issue pointers, worktrees, active branches, and Owner-gated completion claims.
- Completed tasks: `TASK-AR-292` through `TASK-AR-296`.
- Plan entrypoint: `docs/superpowers/plans/2026-06-11-session-closeout-automation.md`.
- Registration evidence: `reviews/REVIEW-2026-06-11-session-closeout-automation-registration.md`.
- Closeout evidence: `reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md`.
- Implemented: `scripts/session_baseline.py`, `scripts/dirty_intake.py`, `skills/session-closeout/SKILL.md`, `scripts/verify_session_closeout_taskset.py`, and `.codex/hooks.json` lifecycle wiring.
- Boundary: this task set must not auto-merge, force-delete, push secrets, or apply archived work without explicit Owner-approved policy. It should classify and preserve first, then route to commit/PR/issue/archive.
- Relationship: complements `TASKSET-AR-COLLAB-CONCURRENCY`, `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE`, and Owner governance; it does not replace those gates.

## 2026-06-11 TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE Closeout

- Completed local task set: `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE`.
- Purpose: verify live multi-pane runtime operation across pane census, process compliance, event logging, role coverage, waiver lifecycle, timeline drift, stale worktrees, UI visibility, and Owner closeout.
- Completed tasks: `TASK-AR-285` through `TASK-AR-291`.
- Plan entrypoint: `docs/superpowers/plans/2026-06-11-multipane-runtime-assurance.md`.
- Registration evidence: `reviews/REVIEW-2026-06-11-multipane-runtime-assurance-registration.md`.
- Closeout evidence: `reviews/REVIEW-2026-06-11-multipane-runtime-assurance-closeout.md`.
- Implemented: `scripts/multipane_census.py`, `scripts/multipane_process_audit.py`, `scripts/multipane_drift_gate.py`, `agents/project/MULTIPANE-PROCESS-POLICY.yml`, lifecycle gate checks, and UI assurance surface.
- Boundary: do not reopen `TASKSET-AR-PANE-PROGRESS` or `TASKSET-AR-COLLAB-CONCURRENCY`; this is the missing assurance layer for actual multi-pane operation.
- Active pointer boundary: `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` is now closed locally; remaining open work is `TASKSET-AR-RSI-OPERATING-SYSTEM`.

## 2026-06-11 TASKSET-AR-UI-DESIGN-IMPLEMENTATION Completion

- Completed local task set: `TASKSET-AR-UI-DESIGN-IMPLEMENTATION`.
- Purpose: keep design implementation visible in the live backlog instead of hiding it inside completed design-system evidence.
- Completed tasks: `TASK-AR-278` through `TASK-AR-284`.
- Relationship: `TASKSET-AR-UI-DESIGN-SYSTEM` remains completed research/design evidence; this task set tracks actual pane-by-pane application and visual QA.
- Closeout: `TASK-AR-284` records final visual QA and Owner handoff for the live UI console.
- Research entrypoint: `reviews/RESEARCH-2026-06-11-ui-design-implementation-gap.md`.
- Plan entrypoint: `docs/superpowers/plans/2026-06-11-ui-design-implementation.md`.
- Closeout evidence: `reviews/REVIEW-2026-06-11-agent-runtime-ui-design-implementation-final-handoff.md`.

## 2026-06-11 TASKSET-AR-TASK-IDENTITY Completion and Omission Audit

- Completed local task identity hardening as `TASKSET-AR-TASK-IDENTITY`.
- Completed task records: `TASK-AR-20260611-001000-815e18ab` through `TASK-AR-20260611-001300-56389c0e`.
- Added collision-proof `task_uid` and lifecycle metadata enforcement through `scripts/task_identity.py`.
- Wired task identity into Owner governance and generated backlog archive visibility.
- Added Owner-facing closeout review `reviews/REVIEW-2026-06-11-agent-runtime-task-identity-taskset-closeout.md`.

## 2026-06-11 TASKSET-AR-UI-DESIGN-SYSTEM Restoration and Closeout

- Restored missing UI design-system work as `TASKSET-AR-UI-DESIGN-SYSTEM`.
- Registered and closed `TASK-AR-264` through `TASK-AR-270`.
- Captured the UI research synthesis and selected Linear-like operator console direction.
- Added `docs/design/agent-runtime/DESIGN.md` as the project-specific UI design guide.
- Applied the first visual implementation pass to `src/agent_runtime/ui_console.py` while preserving existing DOM/API contracts.
- Added UI token assertions to `tests/test_ui_console.py`.
- Added Owner-facing closeout review `reviews/REVIEW-2026-06-11-agent-runtime-ui-design-taskset-closeout.md`.
- Reconciled `agents/project/NEXT-SESSION-POINTER.yml` and `owner-docs.yml` so the latest completed taskset is resumable.

## 2026-06-10 TASKSET-AR-GOVERNANCE-OPS Registration

- New active task set: `TASKSET-AR-GOVERNANCE-OPS`.
- Purpose: burn down collaboration waivers, clean lifecycle drift, measure skill/hook/trigger/gate/script usage and reuse, enforce realtime backlog/status/pointer sync, split broad pytest hygiene, and publish recurring governance operations reports.
- Registered tasks: `TASK-AR-257` through `TASK-AR-263`.
- Immediate implementation lane: `TASK-AR-258` root capability promotion and `TASK-AR-260` runtime asset usage metrics.
- Completion boundary: do not mark this topic closed until waiver count, lifecycle watch count, runtime asset usage metrics, state sync, and verification tiers have direct gate/report evidence.
- 2026-06-10 closeout: `TASK-AR-257` through `TASK-AR-263` completed for local enforcement scope.
- Verification: focused tests `17 passed`; Owner gate `status=pass`; runtime asset usage `assets=14`, `block=0`, `watch=0`; state sync `findings=0`; collaboration governance `block=0`, `watch=5`, `waived=1`.
- Remaining watch: real scribe claim/log evidence and low-frequency monitored roles.

## 2026-06-10 TASK-AR-210 Release Steward Reconciliation

- Current TASK-AR-210 route: `release_evidence_ready` for `v0.1.8` local release evidence.
- Current release_state chain: historical `hold_for_data` -> `ready` -> local `release` evidence.
- Reporting boundary: local release evidence does not by itself prove external GitHub publish. Remote publish is `remote_publish_deferred_out_of_scope`; claims require separate PR/tag/CI evidence and must not be inferred from `release_execution_gate.py`.
- Evidence entrypoint: `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-210-release-steward-snapshot.md`.
- Gate evidence: release execution, owner approval, pending-release guard, readiness summary, task-set work gate, and parallel worktree gate all passed with `findings=0` during the Release Steward lane.

## 기준 일정

- 기준일: 2026-06-09 (수요일, Asia/Seoul)
- v0.1.7 공개 판정 창: 2026-06-18
- 미충족 fallback: 2026-06-25(1차), 2026-06-30(2차)
- v0.1.8 후보 창(재설정): 2026-07-02(1차), 2026-07-09(2차), 2026-07-16(최종)
- v0.1.8 버전 업데이트 실행 규칙:
  - 다음 판정 창: 2026-07-02(1차) → 2026-07-09(2차) → 2026-07-16(최종 freeze)
  - 공개 판정은 `release_state`가 `release`로 변환되는 순간까지 `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`를 모두 정리해야 성립. 2026-06-10 기준 local release evidence는 이 조건을 통과했으며, external publish evidence는 별도 경계로 남긴다.
  - 문구, hold 사유, 결정 주체는 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에서 동일해야 함.
  - 미충족 항목은 즉시 `hold_for_query_contract`/`hold_for_overlay`/`hold_for_data`로 분리해 `TASK-AR-223` closeout 번들에서 재평가.
  - 2026-07-02 판정 통과 시 1차 `release-preflight` 증적 번들을 확정해 공개 준비로 이동.
  - 2026-07-02 판정 미통과 시 2026-07-09까지 `hold_for_*` 보류 재작업 후 재판정.
  - 2026-07-09 판정 미통과 시 2026-07-16 최종 freeze로 전환하고 미충족 블로커 이관 상태만 유지.
  - 2026-07-16 이후 미충족 항목은 `TASK-AR-216` 이관 및 판정 정합 후 다음 릴리스 후보로 이동.
- v0.1.8 공개 판정 규칙:
  - 1차(2026-07-02) 판정 실패 시 `hold_for_*`로 연장
  - 2차(2026-07-09) 판정 실패 시 보완 항목 보강
  - 3차(2026-07-16) 판정 실패 시 `ready` 동결
  - 실무 규칙:
    - 판정 오탈자/버전 불일치/경고 미해결은 `warn`가 아니라 `hold_*` 라우팅.
    - `release_state`·`release_cause`·`decision_deadline`은 4개 핵심 문서의 판정 필드와 매 판정일 대조.
  - `tag_manual` 이식 이력이 완전 정렬되어야 함:
    - `MIGRATION-COMPAT-MAP.yml` 기준: `scripts-source-only` 53, `scripts-runtime-extra` 2, `hooks-wrapper` 1건.
    - 미결 항목이 남아 있으면 `approved_by/expiry/justification` 보완 또는 `hold_for_data`/`hold_for_overlay` 라우팅으로만 통과.
- 핵심 제약:
  - `TASK-AR-210` 최종 판정/차단사유 확정 + `TASK-AR-213` parity lock 증빙이 동시 완료되어야 유효
  - v0.1.7 미통과 항목은 `TASK-AR-216`을 통해 v0.1.8 판정 사유로 이관
- 현재 게이트 해석: 2026-07-02 1차 판정 → 2026-07-09 2차(보류 연장) → 2026-07-16 3차(최종 이관)
- 원칙: 릴리스 판정은 모델 성능보다 `query contract + cross-project overlay + evidence + gate matrix`를 우선한다.
  - 판정 문구 정합: 2026-07-02/07-09/07-16 판정 결론은 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에 동일 문구로 남아야 함.
- v0.1.8 closeout 실행 순서:
  - `TASK-AR-221`에서 요구사항 1~16의 항목별 증거 체인 수렴
  - `TASK-AR-219` 공식 가이드 정합 + 템플릿 고정
  - `TASK-AR-220` 이식 근거 마감 + migration-map 사유 정렬
  - `TASK-AR-223`로 위 항목을 closeout 번들에서 재수합
  - `TASK-AR-216` -> `TASK-AR-217` -> `TASK-AR-210` 이관 루틴 완료

## 버전 릴리스 계획

- v0.1.6 공개 후보
  - 목표일: 2026-06-13
  - 상태: 공개 전 마지막 조정
  - 다음 사유로 HOLD:
    - `TASK-AR-201`~`205` 미완결
    - `TASK-AR-204` source 정책 및 co-location 고정 미완
    - `TASK-AR-210` 판정 이관 템플릿 미정합

- v0.1.7 공개 목표
  - 목표일: 2026-06-18
  - 상태: 보류 판정 완료
  - 미충족 시 fallback: 2026-06-25 / 2026-06-30
  - 최소 조건:
    - `TASK-AR-210` 버전 게이트 승인/차단 사유가 남음
    - `TASK-AR-201`~`205` 및 `TASK-AR-206`~`208` 게이트 통합
    - `TASK-AR-209`~`213` 마이그레이션 블로커 분류 고정
    - `release-preflight --source .` / `--source .tmp/release-bundle --check`에서 block 상태 해소
    - `release-preflight --source .`의 source 정책 미충족은 `P0-1`로 재판정

- v0.1.8 공개 목표
  - 목표일: 2026-07-02 (가중치 보완 1차)
  - 상태: local release evidence 통과; remote publish boundary는 별도 증거 필요
  - 공개 창:
    - 1차 판정: 2026-07-02
    - fallback-1: 2026-07-09
    - fallback-2: 2026-07-16
  - 최소 릴리스 조건:
    - `TASK-AR-216` request_for_v0.1.8 이관 + `release-state` 동기화
    - `TASK-AR-218` migration-map 승인 미정 0건
    - `TASK-AR-217` release rehearsal에서 preflight + 오프라인 + reviewer/correction/A2A 1체인 증적 확보
    - `TASK-AR-219` official guidance 정합 템플릿이 판정 문구에 반영
    - `TASK-AR-220` 이식 근거 미정/누락 항목의 보류 사유 분리
    - `TASK-AR-205` 도메인별 90% + 오답 라벨링된 오프라인 골든셋 증거
    - `TASK-AR-206`~`208` 라이브 검증/교정/A2A 추적이 고위험에서 모두 동작
    - `TASK-AR-214` 질의 계약 미달 항목이 `clarify-required` 또는 `reviewer_review`로 이관
    - `TASK-AR-215` 오버레이 누락이 `hold_for_overlay`로 즉시 이관
  - 해석 규칙:
    - 판정문구는 템플릿 기반으로 강제 생성되어야 하며 `ready`는 1차/2차/3차 문구의 동시 정합 시만 허용.
    - `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`는 각각 질의 계약, 오버레이, 데이터/이식 증거 결손 경로로만 종료.

## P0 - Release Decision Lock (우선)

- P0-0: `v0.1.7` 공개일 최종 판정
  - 상태: Hold (조건형), 2026-06-18 기준 점검
  - 완료 조건:
    - `TASK-AR-201` 라우터 메타(source_tier/owner/access/ freshness/lineage) 증빙
    - `TASK-AR-204`/`209`/`212`/`213` 블로커 분류 완료
    - `TASK-AR-205` 오프라인 90% 이상
    - `TASK-AR-206`~`208` live review/correction/A2A 연동
    - `release-preflight --source .` source 정책 정합
  - 미달 시: `TASK-AR-210`에 `blocked_by`/`impact`/`next_action` 기록 후 `2026-06-25` 재판정

- P0-1: `release-preflight` source 정책 정합화
  - 목적: `source=.` 기준 실패 재현을 멈추게.
  - 상태: 완료(`TASK-AR-225`)
  - 기본 방향: `source=.`은 working source로 유지하고, 공개 판정은 `publish-bundle`로 생성한 clean bundle을 source로 검사한다.
  - 완료 증적: `.tmp/public-source` 기준 `release-preflight --host-root tests/fixtures/host --check` 결과 `findings=0`.

- P0-2: `TASK-AR-201` Knowledge Skill Router
  - 목적: 최상위 라우터 + owner/접근권한/신선도/계보 SSoT 메타 고정
  - 상태: 완료(`TASKSET-AR-CONTEXT-KNOWLEDGE` closeout)
  - 완료 조건:
    - `source_tier`, `owner`, `access_level`, `freshness_sla`, `lineage`, `definition_policy`, `query_policy` 출력
    - 질문은 `question / business_scope / time_window / tolerance / ambiguity_level`으로 고정
    - `TASK-AR-202` runbook 단계(clarify/retrieve/execute/review/verify/record) 연결

- P0-3: `TASK-AR-202` Runbook Skill Contract
  - 목적: 질문 명확화-자료 탐색-실행-적대적 검토-검증 패턴을 runbook 스키마로 고정
  - 상태: 완료(`TASKSET-AR-CONTEXT-KNOWLEDGE` closeout)
  - 완료 조건:
    - 6단계 증거 없이 완료 처리 금지
    - `verified pattern`이 없으면 completion 불가
    - `TASK-AR-204` gate와 동일 체인

- P0-4: `TASK-AR-203` Warehouse Document Standard
  - 목적: `빠른 참조/차원설명/핵심테이블/주의사항 및 패턴/연결고리` 템플릿 고정
  - 상태: 완료(`TASKSET-AR-CONTEXT-KNOWLEDGE` closeout)
  - 완료 조건:
    - 템플릿 채택
    - stale/staleness 경고가 CI에 연결
    - 최소 1개 문서가 템플릿 기준으로 대체

- P0-5: `TASK-AR-204` Skill/Data Co-Location Enforcement
  - 목적: skill 문서와 코드/데이터/모델 변경 동시 갱신 강제
  - 상태: 완료(`TASKSET-AR-CONTEXT-KNOWLEDGE` closeout; 기존 co-location gate 완료)
  - 완료 조건:
    - `SKILL-DATA-MAP.yml` 스키마 확정
    - 스킬 문서는 코드/모델/데이터와 동일 오버레이 트리에서 관리
    - `source`/`provider`/`dataset` 변경 시 문서 미갱신을 warn가 아닌 block 처리
    - waiver는 `approved_by/decision_date/expiry`가 없으면 reject

- P0-6: `TASK-AR-205` Offline Eval Gate
  - 목적: 정답 보유 영역은 골든셋 기반 재현 평가
  - 상태: 진행 준비
  - 완료 조건:
    - 도메인별 정확도 90% 이상
    - 실패 케이스를 `correction` 이벤트와 연결
    - 오답 라벨링에 `query_type/tradeoff/access_level/ambiguity` 포함

- P0-7: `TASK-AR-206` Live Verification and Adversarial Review
  - 목적: 실시간 reviewer와 answer footer 의무화
  - 상태: 진행 준비
  - 완료 조건:
    - `source_footer`/`confidence`/`source_tier`/`risk`/`ambiguity` 누락 시 high-risk 종료 금지
    - 비용-정확도-속도 트레이드오프 태그 기록

- P0-8: `TASK-AR-207` Auto Correction Collector
  - 목적: 채팅/리뷰/메시지 순회 기반 자동 교정 수집
  - 상태: 진행 준비
  - 완료 조건:
    - 주기형 스캐너로 오답·누락 감지 시 교정 제안 생성
    - 제안은 owner 승인 라우팅 뒤 반영

- P0-9: `TASK-AR-208` A2A Message Bus Hardening
  - 목적: request/review/decision/correction 추적성과 재현성 확보
  - 상태: 진행 준비
  - 완료 조건:
    - envelope/retry/access control/idempotency가 chain reconstruct 가능하게 정합
    - 미승인 event는 reject + audit 남김

- P0-10: `TASK-AR-209` tag_manual Migration Audit
  - 목적: 이식 누락/변경/의도적 제외를 분리 보관
  - 상태: 진행 중
  - 완료 조건:
    - `kept/changed/deprecated/dropped/missing` 분류 완료
    - `kept`/`missing`/`runtime-only` 이유별 보류 근거 분리
    - `MIGRATION-COMPAT-MAP` 동기화

- P0-11: `TASK-AR-210` Release Gate Governance
  - 목적: v0.1.6/0.1.7 공개 판단과 v0.1.8 이관 사유 고정
  - 상태: 진행 중
  - 완료 조건:
    - block/allow matrix 완료
    - Owner 승인 템플릿 표준화
    - `BACKLOG`/`ROADMAP`/`STATUS`/`TASK` 참조 정합
  - 2026-06-10 완료: local `v0.1.8` release evidence는 `release_evidence_ready`; remote GitHub publish는 `remote_publish_deferred_out_of_scope`로 별도 증거 없이는 완료로 간주하지 않는다.

- P0-12: `TASK-AR-211` Project Overlay Standardization
  - 목적: 공통 런타임 + 프로젝트 고유 오버레이 분리
  - 상태: 완료(`TASKSET-AR-CONTEXT-KNOWLEDGE` closeout)
  - 완료 조건:
    - `vision/roadmap/org/links/team/communication` 오버레이 반영
    - 오버레이 누락이 `high-risk` 또는 `clarify`로 이관

- P0-13: `TASK-AR-212` Migration Evidence Closure
  - 목적: 이식 증빙 분류를 릴리스 블로커로 이관
  - 상태: 진행 중
  - 완료 조건:
    - scripts/hook/skill 누락 항목의 owner/rationale/approval 보강
    - `TASK-AR-204`와 release-preflight 연동

- P0-14: Multi-team context packet definition chain
  - 목적: 팀/조직/로드맵/의사소통 기록을 오버레이로 즉시 반영
  - 상태: 완료(`TASKSET-AR-CONTEXT-KNOWLEDGE` closeout)
  - 완료 조건:
    - 오버레이 파일 변경만으로 프로젝트 이식 가능
    - 누락 시 경고 없이 `TASK-AR-204` 경유차단

- P0-15: `TASK-AR-213` migration parity lock
  - 목적: 이식 차이를 release lock 규칙으로 고정
  - 상태: 진행 중
  - 완료 조건:
    - `TASK-AR-209`와 5분류 동기화
    - 미승인 `missing`/`changed` 즉시 block

- P0-16: `TASK-AR-216` v0.1.8 후보 gate freeze 및 판정 이관
  - 목적: v0.1.7 미통과 항목을 v0.1.8 판정으로 정리
  - 상태: 다음 세션 우선
  - 필수 출력:
    - `release-state`, `request_for_v0.1.8`, `decision_deadline`, `owner`, `blocked_by` 고정
    - `hold_for_data`/`hold_for_query_contract`/`hold_for_overlay` 경로 정합

- P0-17: `TASK-AR-217` v0.1.8 release rehearsal
  - 목적: preflight + offline + reviewer/correction/A2A 하나의 번들로 검증
  - 상태: 다음 세션 우선
  - 완료 조건:
    - `release-preflight --source .` / `--source .tmp/release-bundle` 결과 캡처
    - 도메인별 90% + 실패 케이스 correction 연결
    - reviewer/verdict + footer + A2A trace 동시 증빙

- P0-18: `TASK-AR-218` Migration Integrity Hardening
  - 목적: migration-map 근거/승인 미정이 릴리스에서 block로 반영되게 정합
  - 상태: 진행 중
  - 완료 조건:
    - `MIGRATION-COMPAT-MAP.yml` 승인 근거 미정 0건 또는 `hold` 이관
    - stale/overlay 누락 시 `hold_for_overlay` 경로 적용

- P0-19: `TASK-AR-219` 공식 권고·버전 판정 정합
  - 목적: 공식 가이드 반영 문구가 1차/2차/최종 판정에 동일하게 고정
  - 상태: 진행 준비
  - 완료 조건:
    - `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210` 판정 문구 동기
    - 오프라인 90%/live reviewer/correction/A2A/overlay/migration evidence 번들 증빙
    - `release-state` 상태 머신이 판정로그에 남음

- P0-20: `TASK-AR-220` tag_manual 이식 근거 마감
  - 목적: 누락·의도적 제외·미확정 항목 분리와 block 경로 정합
  - 상태: 진행 준비
  - 완료 조건:
    - `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper` 근거 보강
    - `MIGRATION-COMPAT-MAP`와 `TASK-AR-204`/`TASK-AR-210`/`TASK-AR-213` 동기
    - `hold_for_data` / `hold_for_overlay` 이관 규칙이 실제 차단으로 동작

- P0-21: `TASK-AR-221` 운영 정합 통합
  - 목적: 요구사항 1~16을 `query contract + overlay + evaluation + migration evidence`로 묶은 통합 게이트
  - 상태: 진행 준비
  - 완료 조건:
    - `TASK-AR-201`~`218`/`219`/`220` 산출물이 동일 release bundle에서 재현 가능
    - 스킬 문서 변경이 모델/provider/data 변경과 함께 변경되지 않으면 block
    - `TASK-AR-221` 실행 후 `TASK-AR-210` 이관 사유 템플릿에서 누락 항목 0건

- P0-22: `TASK-AR-221` 기반 버전 업데이트 판정 고정
  - 목적: 1차/2차/최종 판정 문구를 단일 템플릿으로 고정하고, 미충족 항목은 `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`로 즉시 경로 이관
  - 상태: 진행 준비
  - 완료 조건:
    - `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`의 2026-07-02/07-09/07-16 판정 문구 일치
    - 1차 판정 실패 사유가 `release-state` 필드와 `release_cause`로 추적
    - `TASK-AR-219` 공식 가이드 반영 항목이 `TASK-AR-217`/`220`/`205`/`206`/`207`/`208` 증적과 1:1 연결

- P0-23: `TASK-AR-222` v0.1.8 closeout 번들
  - 목적: 요구사항 1~16의 운영 체인을 v0.1.8 판정으로 동기화
  - 상태: 진행 준비
  - 완료 조건:
    - 요구사항 1~16이 오프라인, live review, correction, A2A, migration 근거에 모두 연결됨
    - `TASK-AR-221`/`TASK-AR-219`/`TASK-AR-220`/`TASK-AR-216`/`TASK-AR-218`/`TASK-AR-217` 결과가 `TASK-AR-210` 판정 템플릿에 반영됨
    - 2026-07-02/07-09/07-16 판정 텍스트/hold 경로/decision_deadline가 `release-state`와 정합
    - `TASK-AR-222` 산출물(요건 매핑표 + migration 이관표 + closeout 번들 증적)이 1개로 고정
    - `tag_manual` 이식 누락/변경/의도적 제외 항목이 `approved_by/expiry/justification`으로 미해결 0건

- P0-24: `TASK-AR-223` 멀티프로젝트 버전 업데이트 closeout 통합
  - 목적: one-runtime multi-project 운영 원칙에 맞춰 오버레이/강제 규칙/migration 근거를 closeout 번들로 고정
  - 상태: 진행 중
  - 완료 조건:
    - `TASK-AR-221`~`222`/`219`~`220` 증적 번들이 1개 closeout bundle로 재수합
    - 질문 계약 미달은 즉시 `hold_for_query_contract`, 오버레이 누락은 `hold_for_overlay`, migration 결손은 `hold_for_data`로 분기
    - `TASK-AR-204` 강제 규칙이 warn를 넘어 block로 실제 판정에 반영
    - 오버레이 변경만으로 다른 프로젝트 투입 시뮬레이션이 1건 이상 완료
    - 태스크, 리뷰, 리서치 산출의 링크가 `closeout-bundle` 단일 체인으로 정합
    - `TASK-AR-211`~`214`의 오버레이·쿼리 계약·정확도/속도/비용 트레이드오프가 `TASK-AR-223` 번들에서 1회 이상 재증적

- 2026-06-17: `TASK-AR-223` 공식 채널 정합 강화.
  - Claude hook 결정 병합 규칙(deny가 우선)과 A2A 연속성(`contextId/taskId`)을 closeout 템플릿에 반영.
  - trace grading/trace 이력 기반 실시간/오프라인 평가 교차 링크를 `TASK-AR-221`~`222` 산출로 묶음.
  - `TASK-AR-220` 이식 항목의 `approved_by/expiry/justification`이 없는 항목은 재이관 보류만 허용되도록 조정.

## 운영 사이클 이력

- 2026-06-09: `TASK-AR-225` source publication hygiene blocker 해소.
  - `release-preflight` 초기 `findings=358`을 sanitizer/template/clean-bundle/fixture-lock 순서로 해소.
  - 최종 clean bundle preflight 결과: `findings=0`.
  - 다음 릴리스 판단은 `TASK-AR-223` closeout bundle과 `TASK-AR-221` 통합 게이트로 이동.
- 2026-06-09: `TASK-AR-223` -> `TASK-AR-217` closeout/rehearsal integration cycle 시작.
  - 신규 기록: `RESEARCH`, `MEETING`, `CALL`, `SEMINAR`, `REVIEW` 각 1건 추가.
  - `TASK-AR-217` 상태를 `in_progress`로 전환.
  - release artifact lane은 `TASK-AR-225` clean bundle preflight `findings=0`로 수락.
  - 최신 검증용 번들 `.tmp/release-bundle-verify-20260609-223217`에서도 release-preflight `findings=0` 확인.
  - 다음 미완 lane: offline eval 90%, live reviewer footer, correction collector, A2A trace, hold routing.
- 2026-06-09: `TASK-AR-205` offline eval gate 실행.
  - `scripts/offline_eval_gate.py` 추가.
  - 결과: `status=block`; 두 골든셋 모두 `score=0.6667`, `cases=2`, `findings=4`.
  - release route: `hold_for_data`.
  - 생성 증적: `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json`, `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-rerun.json`, correction proposal.
- 2026-06-09: `TASK-AR-205` goldset readiness 보강.
  - `overlay-routing-v1.jsonl`, `gov-metadata-v1.jsonl`을 각각 5건으로 확장.
  - 필수 case types(`typical`, `edge`, `adversarial`, `ambiguous`, `access-controlled`)와 `source_refs`/`query_contract` 보강.
  - goldset readiness gate 결과: `status=pass`, 두 데이터셋 모두 `score=1.0`, `findings=0`.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-goldset --check` 결과 `findings=0`.
  - 경계: model-output answer accuracy 90%는 아직 미검증. 다음 작업은 prediction scoring.
- 2026-06-09: `TASK-AR-205` prediction scoring 추가.
  - `scripts/offline_prediction_score.py`와 `agents/project/evals/predictions/contract-baseline-2026-06-09.jsonl` 추가.
  - 결과: `status=pass`; 두 데이터셋 모두 `score=1.0`, `cases=5`, `findings=0`.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-prediction --check` 결과 `findings=0`.
  - 경계: deterministic contract baseline 기준 통과이며, 외부 provider/model 정확도 주장은 아님.
  - 다음 lane: `TASK-AR-206` live reviewer footer.
- 2026-06-09: `TASK-AR-206` live reviewer footer gate 추가.
  - `scripts/live_reviewer_gate.py`와 baseline evidence `agents/project/live_review/live-review-baseline-2026-06-09.jsonl` 추가.
  - 결과: `status=pass`, `score=1.0`, `records=2`, `findings=0`.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-live-reviewer --check` 결과 `findings=0`.
  - high-risk reviewer record는 owner/auditor route 없이는 통과 불가.
  - 다음 lane: `TASK-AR-207` correction collector.
- 2026-06-09: `TASK-AR-207` correction collector 추가.
  - `scripts/correction_collector.py`와 실패 reviewer 샘플 추가.
  - 결과: `status=pass`, correction proposal `written=2`.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-correction --check` 결과 `findings=0`.
  - proposal은 자동 반영 금지; owner/accountable human sign-off 필요.
  - 다음 lane: `TASK-AR-208` A2A trace reconstruction.
- 2026-06-09: `TASK-AR-208` A2A trace reconstruction gate 추가.
  - `scripts/a2a_trace_gate.py`와 baseline trace `agents/project/a2a/a2a-trace-baseline-2026-06-09.jsonl` 추가.
  - 결과: `status=pass`, `events=4`, `chains=1`, `findings=0`.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-a2a --check` 결과 `findings=0`.
  - reconstructed chain: `request -> review -> decision -> correction`.
  - 다음 단계: `TASK-AR-223` closeout bundle에 release artifact/offline/live/correction/A2A evidence 수렴.
- 2026-06-09: `TASK-AR-223` closeout bundle consolidation 완료.
  - 단일 entrypoint: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md`.
  - 수렴 lane: release artifact, offline scoring, live reviewer, correction collector, A2A trace.
  - 판정: `ready_for_governance_review` 권고. 단, 최종 release state는 `TASK-AR-210` allowed states로 변환 필요.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-closeout --check` 결과 `findings=0`.
  - 남은 경계: migration approval closure, overlay cross-project simulation, provider/live transport evidence 필요 여부.
- 2026-06-09: `TASK-AR-221` operating-chain integration 완료.
  - 단일 entrypoint: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md`.
  - 요구사항 1~16을 `TASK-AR-223` closeout bundle, hold routes, `TASK-AR-210` 판정 입력에 매핑.
  - baseline validation lanes는 pass로 정렬.
  - 남은 governance boundaries: migration approval closure, overlay simulation, co-location enforcement, provider/live transport policy.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-operating-chain --check` 결과 `findings=0`.
- 2026-06-09: `TASK-AR-210` release-state 변환 완료.
  - `ready_for_governance_review`를 allowed state `hold_for_data`로 변환.
  - primary cause: `migration_or_dataset_evidence_gap`.
  - blocked_by: `TASK-AR-220`, `TASK-AR-215`, `TASK-AR-204`.
  - `RELEASE-GATE-TEMPLATE.yml` 갱신.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-release-state --check` 결과 `findings=0`.
  - 다음 단계: `TASK-AR-222` v0.1.8 closeout bundle 완성.
- 2026-06-09: `TASK-AR-222` v0.1.8 closeout bundle 완성.
  - 단일 entrypoint: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-222-v018-closeout-bundle.md`.
  - current release_state: `hold_for_data`.
  - accepted baseline lanes: release artifact, offline, live reviewer, correction, A2A.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-v018-closeout --check` 결과 `findings=0`.
  - 다음 단계: `TASK-AR-220`, `TASK-AR-215`, `TASK-AR-204` boundary closure.
- 2026-06-09: `TASK-AR-220` migration approval closure 완료.
  - `MIGRATION-HOLD-ROUTING.yml` release_state를 `hold_for_data`에서 `ready`로 전환.
  - source-only 53건은 group별 target_state/approved_by/decision_date/expiry/justification으로 승인.
  - migration release blocker는 v0.1.8 baseline 기준 해소.
  - release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-migration-closure --check` 결과 `findings=0`.
  - 남은 release boundaries: `TASK-AR-215` overlay simulation, `TASK-AR-204` co-location enforcement.
- 2026-06-10: `TASK-AR-221`/`TASK-AR-219`/`TASK-AR-220` 사이클 킥오프 완료.
  - 신규 협업 기록: `MEETING`, `CALL`, `SEMINAR`, `RESEARCH` 각 1건 추가.
  - 다음 단계 진입 준비: `TASK-AR-216` 이관 조건 정합 점검 후 `TASK-AR-218`/`TASK-AR-217` 진행.
- 2026-06-09: `TASK-AR-224` 공식/이식 근거 동기화 cycle 시작.
  - `RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md`, `MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync.md`, `CALL-2026-06-09-agent-runtime-task-ar-224-sync-call.md`, `SEMINAR-2026-06-09-agent-runtime-task-ar-224-governance-seminar.md` 생성.
  - `MIGRATION-HOLD-ROUTING.yml` 생성: `scripts-source-only` 53건을 placeholder/external-deploy/project-report/runtime-gap/legacy/test-only로 1차 세분류.
  - `REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md` 및 `RELEASE-GATE-TEMPLATE.yml` 생성.
  - `REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md` 생성: packet proof 성공, release-preflight 실행 결과 `findings=358` block.
  - 다음 cycle은 source publication hygiene blocker 해소 계획.
- 2026-06-10: `TASK-AR-222` closeout 계획 프레임워크 추가.
  - 요구사항 1~16(쿼리 계약, 오프라인 평가, live 리뷰, 교정/A2A, migration/provenance)과 공식 권고 반영을 판정 한 번의 번들로 묶음.
- 2026-06-14: `TASK-AR-220` migration 근거 정합 사이클 진행.
  - `MIGRATION-COMPAT-MAP.yml`의 scripts-core-kept/scripts-core-changed/scripts-runschedule-legacy/skills-pack 항목에 `justification`·`expiry` 보강 완료.
- 2026-06-15: `TASK-AR-223` closeout 통합 체인 정합.
  - 06-15 회의/연구/콜/세미나 산출을 closeout 감사 체인으로 고정.
  - `hold_for_query_contract` / `hold_for_overlay` / `hold_for_data` 라우팅을 판정 문자열/decision_deadline와 연결.
- 2026-06-19: 공식 가이드 근거 최신화 반영.
  - Claude hook precedence/trace-grading/A2A multi-turn continuity 규칙을 `TASK-AR-223` closeout 템플릿에 고정.
  - `MIGRATION-COMPAT-MAP.yml`의 `source-only`/`runtime-only`/`hooks-wrapper` 분류와 hold routing의 1:1 매핑을 closeout 체인에 반영.

- P0-25: `TASK-AR-224` 공식 소스 리뷰 동기화
  - 목적: 공식 문서 기반 운영 규칙 변화(Claude hooks, OpenAI trace, Codex 안전, A2A)를 릴리스 템플릿에 즉시 반영.
  - 상태: 진행 중
  - 완료 조건:
    - `official-research` 근거 링크가 `TASK-AR-223` closeout 번들에 1회 이상 추가.
    - `warn`/`allow` 오탐 오해로 인한 허가 오판은 허용 없이 `block`으로 차단.
    - 문서 stale/metadata freshness 항목이 `TASK-AR-210` 이관 템플릿에 정합.
    - `scripts-source-only`/`scripts-runtime-extra`/`hooks-wrapper` 미이행 항목이 `hold_for_data` 또는 `hold_for_overlay`로만 이관되고 미정리 0건.

- P0-26: `TASK-AR-225` source publication hygiene blocker 해소
  - 목적: `TASK-AR-224` 실행 증거에서 나온 `release-preflight findings=358`을 release-ready 가능한 원인군으로 분리하고 해소.
  - 상태: 완료
  - 완료 조건:
    - host-only TASK/review 파일이 package-public source에서 제외되거나 명시적 hold로 라우팅.
    - migration docs의 absolute local path 제거 또는 host-only 분류.
    - template example의 host-history reference 제거.
    - fixture host lock이 갱신되거나 승인된 waiver로 기록.
  - 완료 증적:
    - `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md`
    - clean bundle preflight result: `findings=0`

## v0.1.8 closeout 요구사항 매핑(요구사항 1~16 + 공식 반영)

- 1) 지식 스킬 최상위 라우터: `TASK-AR-201`
- 2) Runbook(명확화-탐색-실행-적대적검토-검증-기록): `TASK-AR-202`
- 3) 창고 문서 템플릿: `TASK-AR-203`
- 4) 스킬 문서/코드 동기화 강제: `TASK-AR-204`, `TASK-AR-210`
- 5) 오프라인 90% eval + 오답 라벨링: `TASK-AR-205`
- 6) 실시간 reviewer/footer + 태그: `TASK-AR-206`
- 7) 자동 교정 수집: `TASK-AR-207`
- 8) 정의/맥락/정답성 인식: `TASK-AR-201`, `TASK-AR-214`
- 9) 강제 규칙(비경고 단정): `TASK-AR-204`, `TASK-AR-210`
- 10) 쿼리 정제 및 질의 계약: `TASK-AR-214`
- 11) SSoT 정렬(공식 계보): `CONTEXT-SOURCES.yml`, `DATASET-CATALOG.yml`, `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`
- 12) 정확도-속도-비용 트레이드오프: `TASK-AR-205`, `TASK-AR-206`, `TASK-AR-207`
- 13) 메타데이터 필수화: `SKILL-DATA-MAP.yml`, `CONTEXT-SOURCES.yml`
- 14) 멀티 프로젝트 맥락(vision/roadmap/org/links/communication/team): `TASK-AR-211`, `TASK-AR-215`
- 15) SSoT 신뢰순위 + lineage/history/semantic layer: `TASK-AR-219`, `TASK-AR-220`
- 16) A2A 메시지 버스 및 재구성성: `TASK-AR-208`, `TASK-AR-223`

## P1 - 운영화

- P1-1: release-artifact 정합성 운영 SOP 고정
  - 상태: 진행 중
  - 내용: publish-bundle → release-preflight → lock/write-back → 결과 리뷰
- P1-2: 태스크-리뷰-근거 링크 강제
  - 상태: 진행 중
  - 내용: 새 TASK는 최소 하나의 review/research/meeting 링크를 audit log에 고정
- P1-3: host overlay 운영 확산
  - 상태: 진행 중
  - 내용: PROJECT-CONTEXT, ROADMAP, ORG, LINKS, TEAMS 템플릿 확산

## UI Console Initiative - `AGENT_RUNTIME_UI_CONSOLE_BRIEF.md`

- 목적: CLI에 반복해서 backlog/status/log/task detail을 물어보는 흐름을 웹 기반 런타임 컨트롤룸으로 대체한다.
- 원칙: Runtime is the source of truth, UI is the control room. UI는 상태를 시각화하고 안전한 명령을 제출하되, 런타임 파일을 임의로 직접 변조하지 않는다.
- MVP 완료 정의:
  - UI가 backlog, current tasks, kanban, agent status, event log, message log, goal status, task detail을 읽기 전용으로 보여준다.
  - 이후 task create/edit/reorder/assign, agent prompt, pause/resume 등 쓰기 동작은 runtime API 또는 command outbox를 통해서만 수행한다.

- P0-UI-0: `TASK-AR-226` UI Runtime Data Map
  - 상태: completed
  - 내용: tasks/agents/messages/events/goals/logs/state-machine/evidence의 실제 저장 위치와 안전한 read/write 경계를 `docs/UI_RUNTIME_DATA_MAP.md`로 고정.
- P0-UI-1: `TASK-AR-227` UI State API / File Adapter
  - 상태: completed
  - 내용: `GET /api/state`, tasks, agents, messages, events, goals 또는 동일 shape의 local adapter를 구현해 UI가 runtime state를 안정적으로 읽게 함.
- P0-UI-2: `TASK-AR-228` Read-Only Web Console MVP
  - 상태: completed
  - 내용: dashboard, backlog/kanban, agent cards, message log, event timeline, task detail drawer를 읽기 전용으로 구현.
- P1-UI-3: `TASK-AR-229` Task CRUD and Backlog Ordering
  - 상태: completed
  - 내용: create/edit/status/priority/assignee/reorder/comment를 runtime API 또는 `.ui_outbox/COMMAND-*.json`로 제출하고 task order를 보존.
- P1-UI-4: `TASK-AR-230` Runtime Command Controls
  - 상태: completed
  - 내용: send prompt to agent, send task to runtime, request review/meeting, start/pause/resume/stop goal을 안전 경계와 함께 UI에서 제출.
- P1-UI-5: `TASK-AR-231` Live Updates, Logs, Replay, Evidence
  - 상태: completed
  - 내용: freshness 표시, event filtering, logs/errors/evidence panel, replay/daily brief 기반을 추가. polling 우선, SSE는 후속.
- P2-UI-6: `TASK-AR-232` Graph, State Machine, Roadmap Views
  - 상태: completed
  - 내용: agent communication graph, state-machine stepper, roadmap/goals/milestones hierarchy, workload heatmap/command palette 후보를 post-MVP로 구현.

## RSI Planning Loop Initiative - `AGENT_RUNTIME_RSI_PLANNING_BRIEF.md`

- 목적: 사이클 반복, task 마무리, 릴리스/평가/리뷰 진척을 근거로 스스로 planning scan을 수행하고, 새 task/plan/doc 수정안을 제안하는 bounded RSI 루프를 만든다.
- 원칙: B-mode는 read-only scan + proposal outbox + review/apply gate. C-mode는 반복 검증 후 low-risk planning hygiene에만 제한적으로 승격한다.
- 안정성 기준:
  - trace/eval/grader/correction/A2A evidence가 없는 제안은 watch-only.
  - release/version/external/destructive/prod-data/owner-only 변경은 자동 적용 금지.
  - 제안은 source refs, trace id, dedupe key, risk tier, rollback path, verifier list를 가져야 한다.
  - 다양성 council은 비판/옹호/탐색/안정화 관점을 제공하되 최종 출력은 pass/watch/block와 next action으로 수렴한다.

- P0-RSI-1: `TASK-AR-234` Planning Loop Contract And State Machine
  - 상태: planned
  - 내용: `planning_loop`/`rsi_improvement` 상태와 proposal schema, B/C 경계를 고정.
- P0-RSI-2: `TASK-AR-235` Read-only Planning Scan JSON
  - 상태: planned
  - 내용: backlog/status/roadmap/task/review/eval/trace/release/state-machine drift를 read-only JSON으로 보고.
- P0-RSI-3: `TASK-AR-236` Proposal Outbox And Draft Task Writer
  - 상태: planned
  - 내용: findings를 canonical mutation 전 proposal/draft task로 보관.
- P0-RSI-4: `TASK-AR-237` Planning Gate, Hook, Schedule, And UI Trigger Integration
  - 상태: planned
  - 내용: task/cycle 종료, schedule, Stop hook, UI command에서 proposal-only scan을 안전하게 실행.
- P1-RSI-5: `TASK-AR-238` UI Planner Panel And Proposal Review
  - 상태: planned
  - 내용: planning scan/proposal/evidence/disagreement/risk tier를 UI에서 검토.
- P0-RSI-6: `TASK-AR-239` Approved Proposal Apply/Verify Flow
  - 상태: planned
  - 내용: 승인된 proposal만 task/backlog/status/roadmap에 적용하고 gate를 재실행.
- P0-RSI-7: `TASK-AR-240` Version And Release Consistency Steward
  - 상태: planned
  - 내용: 버전, 릴리스 상태, 태그, owner approval, release evidence 정합을 점검.
- P1-RSI-8: `TASK-AR-241` Review/Compound/Retro Synthesizer
  - 상태: planned
  - 내용: 과거 이력/review/compound/retro에서 재발 가능 문제와 예방 task를 제안.
- P1-RSI-9: `TASK-AR-242` Agent Department And Diversity Council Model
  - 상태: planned
  - 내용: planning/release/rsi/eval/risk/diversity 부서와 관점별 reviewer 계약 정의.
- P0-RSI-10: `TASK-AR-243` Trace/Eval/Grader Evidence Integration
  - 상태: planned
  - 내용: trace grading, graders, eval, correction, live review, A2A evidence를 proposal 근거로 연결.
- P0-RSI-11: `TASK-AR-244` Stability, Budget, Drift, And Non-Divergence Guardrails
  - 상태: planned
  - 내용: proposal cap, scan frequency, token/time budget, self-weakening gate block, kill switch 고정.
- P1-RSI-12: `TASK-AR-245` Long-term Auto Planner C-Mode Promotion Gate
  - 상태: planned
  - 내용: C-mode 승격/강등 조건과 auto-apply 허용/금지 범위를 gate로 정의.
- P0-RSI-13: `TASK-AR-246` Parallel Worktree Task Claim Dispatcher
  - 상태: planned
  - 내용: task별 git worktree/branch/claim 생성과 해제, role instance/callsite 구분, handoff/log 포인터 강제를 구현.

## 다음 세션 우선순위

1. `TASK-AR-234` RSI planning loop contract/state machine부터 proposal-only B-mode 설계 착수
2. `TASK-AR-235` read-only planning scan으로 현재 backlog/status/release/eval drift를 먼저 계측
3. `TASK-AR-223` 버전 업데이트 closeout 통합(강제 규칙/오버레이/마이그레이션 재수합)
4. `TASK-AR-221` 운영 정합 통합(Task-합의 마감)
5. `TASK-AR-240` version/release consistency steward를 C-mode 선행 조건으로 설계
6. `TASK-AR-243` trace/eval/grader evidence를 planning proposal 근거로 연결
7. `TASK-AR-244` non-divergence guardrail을 planning gate와 연결
8. `TASK-AR-246` parallel worktree/task claim dispatcher 구현
9. `TASK-AR-210` 재판정: boundaries closure 후 `ready` 가능 여부 확인
10. `TASK-AR-219` 공식 권고 반영 및 판정 근거 고정
11. `TASK-AR-220` tag_manual 이식 근거 마감(스크립트/훅/스킬 누락·의도적 제외 정렬)
12. `TASK-AR-216` v0.1.8 후보 이관 사유 정렬
13. `TASK-AR-222` v0.1.8 closeout 번들 완성
14. `TASK-AR-218` migration 무결성 정합 + migration-map block rule 정비
15. `TASKSET-AR-CONTEXT-KNOWLEDGE`는 완료/아카이브 상태로 유지하고, 새 canonical task 없이는 재오픈하지 않음
16. `TASK-AR-214`/`TASK-AR-215`/`TASK-AR-204`는 context knowledge closeout 증거로 완료됨
17. `scripts/context_knowledge_gate.py --check`를 future context/query/warehouse 변경 전후에 유지
18. `TASK-AR-213` migration parity lock 완료
19. `TASK-AR-202`/`TASK-AR-203`은 runbook/warehouse closeout으로 완료됨
20. 멀티 프로젝트 오버레이 시뮬레이션은 `OVERLAY-SIMULATION-GATE-2026-06-11-context-knowledge-final.json`로 완료됨

## Done Log

- 2026-06-13: `MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md` 반영 (멀티 프로젝트 오버레이·버전 게이트 정합)
- 2026-06-13: `TASK-AR-211` 오버레이 패키지 1차 반영 (vision/roadmap/org/links/team)
- 2026-06-09: `MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md` 작성
- 2026-06-09: `TASK-AR-216`/`217`/`218`/`219`/`220` 산출물 연결 규칙 초안 반영
- 2026-06-14: `MEETING-2026-06-14-agent-runtime-task-ar-223-closeout-planning.md` 반영 (closeout bundle 통합/hold 규칙/overlay + migration 이관 경로)
- 2026-06-15: `MEETING-2026-06-15-agent-runtime-task-ar-223-cycle-sync.md`, `RESEARCH-2026-06-15-agent-runtime-task-ar-223-hold-routing-and-overlay-edge-research.md`, `CALL-2026-06-15-agent-runtime-task-ar-223-sync-call.md`, `SEMINAR-2026-06-15-agent-runtime-task-ar-223-governance-sync.md` 반영
- 2026-06-10: `AGENT_RUNTIME_RSI_PLANNING_BRIEF.md`, `TASK-AR-234`~`TASK-AR-245` 등록 (B-C RSI planning loop, version/release steward, trace/eval/grader, diversity council, non-divergence guardrail)
- 2026-06-10: `AGENT_RUNTIME_PARALLEL_SESSION_PROTOCOL.md`, `TASK-AR-246`, `parallel_worktree_gate.py` 등록 (per-task worktree, role instance metadata, handoff/log pointer gate)


## Operating Cycle Update (2026-06-09): TASK-AR-215 Overlay Simulation Closure

- `TASK-AR-215` cross-project overlay simulation completed.
- Added executable gate: `scripts/overlay_simulation_gate.py`.
- Added MVP client overlay simulation under `agents/project/overlays/simulations/mvp-client-2026-06-09/`.
- Result: complete overlay packet routes to `ready_for_overlay_use`; missing communication context routes to `hold_for_overlay` through `TASK-AR-204` and `TASK-AR-216`.
- Release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-overlay-simulation --check` returned `findings=0`.
- Remaining release boundary before `TASK-AR-210` redecision: `TASK-AR-204` co-location enforcement executable gate.

## Operating Cycle Update (2026-06-09): TASK-AR-204 Co-Location Closure and Ready Re-Decision

- `TASK-AR-204` co-location enforcement executable gate completed.
- Added executable gate: `scripts/co_location_gate.py`.
- Result: `status=pass`, `release_route=ready_for_release_redecision`, `findings=0`.
- `RELEASE-GATE-TEMPLATE.yml` moved from `hold_for_data` to `ready` for governance review.
- Remaining boundary: `release` requires owner approval and final release execution evidence; do not treat `ready` as published release.
- Release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-colocation-ready --check` returned `findings=0`.

## Operating Cycle Update (2026-06-09): v0.1.8 Ready Pending Owner Approval

- `TASK-AR-216` release transition package completed.
- Added release execution gate: `scripts/release_execution_gate.py`.
- Added execution plan: `agents/project/release/RELEASE-EXECUTION-v0.1.8.yml`.
- Added owner approval template: `agents/project/release/OWNER-APPROVAL-v0.1.8.yml`.
- Result: `status=pass`, `release_route=ready_pending_owner_approval`, `package_version=0.1.6`, `findings=0`.
- Do not bump version, tag, push, or mark `release` until owner approval is explicit.

## Operating Cycle Update (2026-06-09): v0.1.8 Local Smoke Plan Readiness

- v0.1.8 local tag smoke plan check completed with `findings=0`.
- Evidence: `reviews/REVIEW-2026-06-09-agent-runtime-v018-local-smoke-plan-readiness.md`.
- No `--apply`, tag creation, install execution, GitHub push, or version bump was performed.
- Remaining gate: owner approval for release execution.

## Operating Cycle Update (2026-06-09): v0.1.8 Owner Approval Gate

- Added executable owner approval gate: `scripts/owner_approval_gate.py`.
- Result: `status=pass`, `decision_route=owner_approval_pending`, `findings=0`.
- Release execution remains blocked until owner approval changes from pending to approved.

## Operating Cycle Update (2026-06-09): v0.1.8 Pending Release Guard

- Added no-mutation guard: `scripts/pending_release_guard.py`.
- Result: `status=pass`, `guard_route=hold_at_ready_pending_owner`, `package=0.1.6`, `findings=0`.
- The guard blocks accidental version bump, `release_state=release`, or execution state mutation while owner approval is pending.

## Operating Cycle Update (2026-06-09): v0.1.8 Release Readiness Summary

- Added aggregate readiness gate: `scripts/release_readiness_summary.py`.
- Result: `status=pass`, `release_route=ready_pending_owner_decision`, `findings=0`.
- Next-session entrypoint: `reviews/RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8.json`.
- Remaining boundary: explicit owner decision only.

## Operating Cycle Update (2026-06-09): v0.1.8 Automation Policy Implementation and Local Release

- Implemented autonomous branch/commit/PR/merge policy for routine work.
- Implemented agent release council policy for noncritical releases.
- Implemented Executive BRIEF v2 format with frontmatter, tags, actions, evidence, concise bullets, and clear hierarchy.
- Version bumped to `0.1.8`.
- Local tag smoke release executed and passed for `v0.1.8`.
- External GitHub publish was not executed in this cycle.

## 2026-06-09 - Release/update queue
- Done: `v0.1.8` autonomous delivery/release-council/executive-brief policy shipped.
- Done: public PR #3 merged and tag `v0.1.8` pushed.
- Done: CI matrix and GitHub tag install smoke passed.
- Backlog: define the stricter canonical input/output schema for Executive BRIEF v2, including required frontmatter fields, footer evidence links, tag taxonomy, and sortable action metadata.
- Backlog: add a machine gate that rejects plan/report documents missing required metadata, tags, action owner/status, or evidence footer.
- Backlog: extend release council policy with explicit criticality scoring for prod data, security, irreversible external actions, and cost-bearing operations.

## 2026-06-09 - Autofolio host integration issue follow-up
- Source: GitHub issue `#1` Host Integration Report, Autofolio ↔ agent_runtime v0.1.5.
- Remote PR status: `#4` merged; `#2` closed as superseded by `v0.1.8` and `#4`.
- Done remotely: README host-first onboarding, overlay guidance, Autofolio issue disposition, and `v0.1.8` host pin example published.
- Done remotely: issue `#1` commented with reflected/residual items.
- Backlog: design managed-region / host override / `--skip-conflicts` ergonomics for unavoidable host seams.
- Backlog: document or implement role exposure adapters for Claude Code-style `.claude/agents/*.md` without duplicating `agents/<role>/SKILL.md`.
- Backlog: add an `agent_runtime init` bootstrap command proposal covering first sync, lock, hook install, and host smoke checks.

## 2026-06-09 - Reporting/backlog format recurrence compound
- Source: user correction after `백로그 띄워줘` output drifted from the established decision-oriented BRIEF format.
- Compound: `agents/lead_engineer/compound_log.md` (`COMPOUND-2026-06-09-001`).
- Review: `reviews/REVIEW-2026-06-09-backlog-brief-format-drift-compound.md`.
- Cause: format rules existed in docs, but the live chat/backlog response path had no execution-time format assertion.
- Decision: keep the existing BRIEF structure and add concise bullets/metadata/action tables on top; do not replace the structure.
- Backlog: implement a response/artifact format gate for backlog/report/plan outputs requiring `Bottom Line`, `Signal`, `Insight`, `Decision`, `Priority/Action Board`, and `Next`.
- Backlog: update backlog renderer contract so `백로그 띄워줘` defaults to a decision board, not a plain task list.

## 2026-06-09 Update - Owner Backlog / Report Format Restoration

### Bottom Line

- Summary: restored prior decision-board backlog style and added executable format enforcement.
- Status: completed for first pass.
- Board: `BACKLOG-BOARD.md` now shows all 25 current TASK files.

### Signal

- Issue: backlog view drifted away from Owner decision format.
- Cause: reporting rules were not tied to a generator and gate.
- Fix: `Action / Ask / Review / Later / Done` lanes plus structured cost/value/team/agent fields.

### Decision

- Decision: use `BACKLOG-BOARD.md` as the primary Owner-facing backlog view.
- Rule: preserve `Bottom Line / Signal / Insight / Decision` in backlog, review, and report outputs.
- Rule: run `scripts/owner_doc_format_gate.py` before sharing Owner-facing docs.

### Action Items

| Status | Action | Owner | Agent | Reference |
| --- | --- | --- | --- | --- |
| Done | Restore decision-board backlog | lead-engineer | codex | `BACKLOG-BOARD.md` |
| Done | Add backlog generator | lead-engineer | codex | `scripts/backlog_board.py` |
| Done | Add Owner doc format gate | lead-engineer | codex | `scripts/owner_doc_format_gate.py` |
| Done | Push rule into project template | agent-runtime-core | codex | `src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md` |
| Done | Push rule into skill governance | agent-runtime-core | codex | `src/agent_runtime/templates/project/agents/project/SKILL-GOVERNANCE.md` |

### Risks / Blockers

- Risk: malformed TASK frontmatter can still reduce metadata quality.
- Risk: manual docs can drift unless the gate is used in review/release flow.
- Blocker: none for current backlog board.

### Next Steps

- Add explicit CI/hook wiring for `owner_doc_format_gate.py` in a follow-up if release automation scope allows.
- Convert repeated inferred metadata into first-class task frontmatter fields.

## 2026-06-09 Update - Owner Format Gate Hook / CI / Release Enforcement

### Bottom Line

- Summary: completed `1-2-3` enforcement path: hook, CI, release-preflight.
- Status: clean bundle preflight passed with `findings=0`.
- Scope: Owner-facing docs listed in `owner-docs.yml`.

### Signal

- Hook: `.githooks/pre-commit` blocks manifest-listed Owner docs that miss the executive brief contract.
- CI: `.github/workflows/test.yml` runs `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml`.
- Release: `release-preflight` includes blocking `owner-doc-format` check.
- Template: new projects receive owner-doc manifest, pre-commit hook, and CI workflow.

### Decision

- Decision: `owner-docs.yml` is the SSoT for Owner-facing docs under hard format enforcement.
- Decision: expand manifest gradually after legacy docs are migrated.
- Decision: use clean bundle path for release proof, not raw repo root.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Connect hook gate | lead-engineer | codex | `.githooks/pre-commit` |
| Done | Connect CI gate | cicd-engineer | codex | `.github/workflows/test.yml` |
| Done | Connect release gate | agent-runtime-core | codex | `src/agent_runtime/release_preflight.py` |
| Done | Publish source inclusion | agent-runtime-core | codex | `src/agent_runtime/publish_bundle.py`, `src/agent_runtime/publish_check.py` |
| Done | Template propagation | agent-runtime-core | codex | `src/agent_runtime/templates/project/.github/workflows/owner-doc-format.yml` |

### Risks / Blockers

- Risk: non-manifest Owner docs remain soft-governed until migrated.
- Risk: adding legacy docs to manifest without migration will intentionally block CI/release.
- Blocker: none for current clean bundle path.

### Next Steps

- Migrate next Owner-facing report into executive brief format.
- Add migrated report path to `owner-docs.yml`.

## 2026-06-09 Update - Hooks and State Machine Enforcement

### Bottom Line

- Summary: hook config, Git hook, CI, release-preflight, and state-machine SSoT are now connected.
- Signal: pass.
- Score: 100.

### Signal

| Layer | Signal | Score | Evidence |
| --- | --- | --- | --- |
| Codex hook config | pass | 100 | `.codex/hooks.json` |
| Git hook | pass | 100 | `.githooks/pre-commit`, `core.hooksPath=.githooks` |
| CI | pass | 100 | `.github/workflows/test.yml` |
| Release preflight | pass | 100 | `owner-doc-format`, `state-machines` |
| State machine SSoT | pass | 100 | `agents/project/STATE-MACHINES.yml` |

### Decision

- Decision: use `pass/watch/block + score` instead of color labels.
- Decision: use `scripts/owner_governance_gate.py` as shared hook/CI/release entrypoint.
- Decision: `STATE-MACHINES.yml` must be updated before adding new lifecycle states.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Add Codex hook config | cicd-engineer | codex | `.codex/hooks.json` |
| Done | Configure Git hook path | cicd-engineer | codex | `git config core.hooksPath .githooks` |
| Done | Add state schema | agent-runtime-core | codex | `schemas/state-machines.schema.json` |
| Done | Add state SSoT and examples | agent-runtime-core | codex | `agents/project/STATE-MACHINES.yml` |
| Done | Add release gate | agent-runtime-core | codex | `src/agent_runtime/release_preflight.py` |

### Risks / Blockers

- Risk: Git hook remains locally bypassable; CI/release gate remains authoritative.
- Risk: Codex hook depends on runtime support for `.codex/hooks.json`.
- Blocker: none.

### Next Steps

- Add future Owner docs to `owner-docs.yml` only after they pass `signal/score` contract.
- Add future lifecycle domains to `STATE-MACHINES.yml` before implementation.

## 2026-06-10 Update - Collaboration Concurrency Task Set

### Bottom Line

- Summary: `TASKSET-AR-COLLAB-CONCURRENCY` is complete for local scope.
- Signal: pass.
- Score: 100.

### Signal

- Completed `TASK-AR-251` through `TASK-AR-256`.
- Added append-only pane event logging for replayable multi-pane status.
- Added SSoT concurrency guard for shared Owner/backlog/status files.
- Added dispatcher worktree preflight before task-set start.
- Added UI collaboration state exposure from pane event logs.
- Added owner governance integration for the concurrency gate.

### Decision

- Decision: panes write events, not shared truth files.
- Decision: shared SSoT writes require orchestrator approval.
- Decision: dispatcher-created worktrees remain the default isolation boundary for task-set execution.

### Action Items

| Status | Action | Owner | Agent | Evidence |
| --- | --- | --- | --- | --- |
| Done | Record collaboration issue/research/plan | lead-engineer | codex | `AGENT_RUNTIME_COLLAB_CONCURRENCY_BRIEF.md`, `reviews/RESEARCH-2026-06-10-realtime-collab-conflict-patterns.md`, `docs/superpowers/plans/2026-06-10-collab-concurrency.md` |
| Done | Implement pane event log | agent-runtime-core | codex | `scripts/pane_event_log.py` |
| Done | Implement SSoT concurrency gate | agent-runtime-core | codex | `scripts/collaboration_concurrency_gate.py` |
| Done | Enforce worktree-first dispatch | worktree-dispatcher | codex | `scripts/taskset_dispatcher.py` |
| Done | Expose UI collaboration status | ui-console | codex | `src/agent_runtime/ui_state.py` |

### Risks / Blockers

- Risk: existing panes must adopt `scripts/pane_event_log.py record` to get full replay coverage.
- Risk: external remote publish remains Owner-gated and was not implied by local completion.
- Blocker: none for local scope.

### Next Steps

- For future 5+ pane work, start panes through task-set dispatcher worktrees.
- Record pane lifecycle events before and after shared-state-affecting work.
- Keep `scripts/collaboration_concurrency_gate.py --check` in Owner governance gates.
