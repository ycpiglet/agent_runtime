---
id: TASK-AR-206
display_id: TASK-AR-206
task_uid: 739ed262-4fe4-4c3b-bac7-6daa9ac98cf5
registered_at: 2026-06-11
created_at: 2026-06-11
started_at: 2026-06-11
updated_at: 2026-06-11T00:00:00+09:00
status: completed
completed_at: 2026-06-10T22:04:00+09:00
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 10
est_tokens: 1800
task_set_id: TASKSET-AR-QUALITY-LOOP
tags:
  - live-verification
  - reviewer-agent
  - adversarial
  - output-footer
trigger_meeting: yes
created: 2026-06-11
audit_log:
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - BACKLOG.md
  - agents/project/EVAL-POLICY.yml
  - agents/project/live_review/live-review-baseline-2026-06-09.jsonl
  - scripts/live_reviewer_gate.py
  - reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-206-live-reviewer-gate-log.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-206-live-reviewer-sync.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-206-live-reviewer-followup-call.md
  - reviews/LIVE-REVIEWER-GATE-2026-06-10-task-ar-206-current.json
  - reviews/REVIEW-2026-06-10-agent-runtime-task-ar-206-claim-closeout.md
---

## 목표
라이브 작업 종료 시 reviewer agent의 적대적 검토를 강제하고, 답변에 근거/태그를 붙인다.

## 작업 내용

- reviewer 결과 schema(결론, 근거, risk, uncertainty, recommend_action)
- human-in-loop 임계치 정책 설계(위험도/정확도/비용 균형)
- `answer footer` 표준( source / confidence / source_tier / risk / ambiguity )

## 결과물

- reviewer 이벤트 스키마
- live trace + verdict 저장 규칙
- 고위험 요청에 대한 승인 정책

## 완료 조건

- reviewer 없이 종료된 고위험 항목이 차단되거나 escalate되어야 함
- 출처/태그가 없는 답변은 review/accept가 불가해야 함
- review verdict가 `high-risk`이면 owner 또는 independent-auditor 확인 필요
- reviewer 결과는 `evidence + confidence + source_tier + risk + ambiguity` 필드로 저장

## 비고

- 선행: `TASK-AR-205` 또는 `TASK-AR-204`의 policy 동기화

## Cycle Log (2026-06-09)

- Added `scripts/live_reviewer_gate.py`.
- Added baseline live reviewer evidence: `agents/project/live_review/live-review-baseline-2026-06-09.jsonl`.
- Ran live reviewer gate:
  - Command: `python scripts/live_reviewer_gate.py --out reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json`
  - Result: `status=pass`, `score=1.0`, `records=2`.
  - `live-001`: `score=1.0`, `findings=0`.
  - `live-002`: `score=1.0`, `findings=0`.
- Boundary: this proves baseline live reviewer/footer schema enforcement, not live provider behavior.
- Verification: live reviewer gate rerun returned `status=pass`; publish bundle check after live reviewer artifacts returned `findings=0`.
- Next lane: `TASK-AR-207` correction collector.

## Claim Closeout (2026-06-10)

- Current claim: `agents/runtime/task_claims/CLAIM-20260610-212814-task-ar-206-7388.json`.
- Current verification: `python scripts/live_reviewer_gate.py --out reviews/LIVE-REVIEWER-GATE-2026-06-10-task-ar-206-current.json` returned `status=pass`, `score=1.0`, `findings=0`.
- Closeout review: `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-206-claim-closeout.md`.
- Boundary: baseline reviewer/footer enforcement is complete; live provider-specific behavior remains a separate release decision.
