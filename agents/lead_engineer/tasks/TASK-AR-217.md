---
id: TASK-AR-217
status: in_progress
owner: lead-engineer
priority: P0
difficulty: L
est_hours: 14
est_tokens: 2800
tags:
  - release-rehearsal
  - release-gate
  - offline-eval
  - live-verification
  - correction-loop
  - a2a
trigger_meeting: yes
created: 2026-06-09
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - agents/project/ROADMAP.md
  - agents/project/PROJECT-CONTEXT.yml
  - agents/project/EVAL-POLICY.yml
  - agents/project/SKILL-GOVERNANCE.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-223-217-rehearsal-integration-research.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-sync.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-223-217-sync-call.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-223-217-release-seminar.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-log.md
  - scripts/offline_eval_gate.py
  - reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json
  - reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-rerun.json
  - reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-offline-eval-gate-log.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-goldset-expansion-log.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-goldset-readiness-sync.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-offline-eval-block-sync.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-205-offline-eval-followup-call.md
---

## 목표

`v0.1.8` 공개 후보(2026-07-02/07-09/07-16)를 가정한
`release-preflight`, 오프라인 90% 게이트, reviewer footer/correction/A2A 증적을
동일 루틴으로 재현 가능한 형태로 점검한다.

## 작업 내용

- `publish-bundle` 산출물을 release source로 사용한 `release-preflight` 실행 증적 수집
- `source=.`은 working source로만 해석하고, host governance/task/review 파일이 포함되므로 공개 release source로 사용하지 않음
- `TASK-AR-205` 도메인별 오프라인 평가 JSONL + 실패 케이스를 `correction` 채널 이벤트로 링크
- `TASK-AR-206` reviewer footer 태그(`source_tier`, `confidence`, `risk`, `ambiguity`, `freshness_sla`)
  보유 여부 점검
- `TASK-AR-207` 자동 교정 이벤트 수집 로그와 `TASK-AR-208` A2A trace의 idempotency/재시도 경로 재현
- `TASK-AR-204`/`TASK-AR-213`/`TASK-AR-210` 블로커 이동 경로가 실제로 차단되는지 검사
- `TASK-AR-214`/`TASK-AR-215` 미충족 시 `hold_for_*` 상태로 이관 여부 확인

## 실행 체크(리허설)

1. release-preflight 패턴:
   - `python -m agent_runtime.cli publish-bundle --source . --dest .tmp/release-bundle --apply`
   - `PYTHONPATH=.tmp/release-bundle/src python -m agent_runtime.cli release-preflight --source .tmp/release-bundle --check`
   - repo root `source=.` 실패는 release failure가 아니라 working-source hygiene signal로 분류한다.
2. 오프라인 90% 패턴:
   - 골든셋(도메인별) 실행 로그와 정확도 요약 저장
3. 라이브 검증 패턴:
   - high-risk 시나리오에서 reviewer verdict + footer + correction 이벤트 유무 확인
4. 메시지 추적 패턴:
   - request/review/decision/correction chain 재구성 가능성 확인

## 완료 조건

- `release-preflight` 핵심 gate에서 `findings=0` 또는 미충족 블로커가 명시적으로 정렬됨
- 오프라인 평가는 도메인별 90% 이상 충족 또는 실패 사유가 보완 계획으로 기록됨
- reviewer/correction/A2A 증적이 `rehearsal bundle`에 남고 `TASK-AR-210`으로 재연결됨
- 실패 시 `rehearsal-block` 태그와 다음 액션이 `BACKLOG.md`/`STATUS.md`에 동시에 반영됨

## 산출물

- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-runbook.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-rehearsal-log.md`

## Cycle Log (2026-06-09)

- `TASK-AR-225` clean bundle preflight result(`findings=0`)를 rehearsal 입력으로 편입.
- release source는 `publish-bundle` 산출물로 고정하고, repo root는 working source로 분리.
- rehearsal의 남은 범위는 offline 90%, live reviewer footer, correction event, A2A trace, hold routing 재현이다.
- 최신 문서 변경 후 검증용 번들 `.tmp/release-bundle-verify-20260609-223217` 기준 release-preflight 재실행 결과 `findings=0`.
- targeted sanitizer test 재실행 결과 `95 passed in 5.51s`.
- Offline eval lane executed with `scripts/offline_eval_gate.py`; result `status=block`.
- Current blocker: both committed goldsets scored `0.6667`, below `0.90`, with insufficient case coverage and missing case metadata.
- Next rehearsal lane remains live reviewer footer only after the offline goldset gap is recorded as `hold_for_data`.
- Goldset readiness gap was corrected:
  - `overlay-routing-v1.jsonl`: 5 cases, required case types covered, `score=1.0`.
  - `gov-metadata-v1.jsonl`: 5 cases, required case types covered, `score=1.0`.
- Updated offline report: `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json`, `status=pass`.
- Boundary: offline eval lane still requires model-output/prediction scoring before claiming domain answer accuracy >= 0.90.

## Rehearsal Input: TASK-AR-205 Prediction Scoring

- 2026-06-09: Offline prediction scoring executed against `contract-baseline-2026-06-09.jsonl`.
- Evidence: `reviews/OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217.json`.
- Result: `status=pass`, both datasets `score=1.0`, `findings=0`.
- Boundary: offline lane is baseline-passed for deterministic contract output. Provider-specific output scoring remains a separate release decision if `TASK-AR-210` requires it.
- Next rehearsal lane: `TASK-AR-206` live reviewer footer.

## Rehearsal Input: TASK-AR-206 Live Reviewer Footer

- 2026-06-09: Live reviewer/footer gate executed against baseline reviewer evidence.
- Evidence: `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json`.
- Result: `status=pass`, `score=1.0`, `records=2`, `findings=0`.
- Boundary: proves baseline reviewer/footer contract enforcement. Live provider behavior remains separate if required by `TASK-AR-210`.
- Next rehearsal lane: `TASK-AR-207` correction collector.

## Rehearsal Input: TASK-AR-207 Correction Collector

- 2026-06-09: Correction collector executed against one offline eval block report and one live reviewer failure sample.
- Evidence: `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json`.
- Result: `status=pass`, `written=2`.
- Generated proposals:
  - `agents/project/corrections/2026-06-09-offline-eval-2026-06-09-task-ar-217-1-goldset-metadata-completion.md`
  - `agents/project/corrections/2026-06-09-live-reviewer-gate-2026-06-09-task-ar-207-failure-sample-1-reviewer-footer-failure.md`
- Boundary: proposals are not auto-applied; owner approval remains required.
- Next rehearsal lane: `TASK-AR-208` A2A trace reconstruction.

## Rehearsal Input: TASK-AR-208 A2A Trace

- 2026-06-09: A2A trace reconstruction gate executed against baseline request/review/decision/correction chain.
- Evidence: `reviews/A2A-TRACE-GATE-2026-06-09-task-ar-208.json`.
- Result: `status=pass`, `events=4`, `chains=1`, `findings=0`.
- Reconstructed chain: `ctx-v018-rehearsal / TASK-AR-217 / cycle-20260609-validation`.
- Covered events: `request -> review -> decision -> correction`.
- Boundary: baseline trace reconstruction passes. Provider/network transport behavior remains separate if required.
- Rehearsal status: release artifact, offline baseline scoring, live reviewer footer, correction collector, and A2A trace lanes now all have baseline evidence.
