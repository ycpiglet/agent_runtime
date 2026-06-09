---
id: TASK-AR-207
status: in_progress
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 12
est_tokens: 1800
tags:
  - auto-correction
  - quality-loop
  - review-pipeline
trigger_meeting: yes
created: 2026-06-11
audit_log:
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - BACKLOG.md
  - agents/project/EVAL-POLICY.yml
  - scripts/correction_collector.py
  - agents/project/live_review/live-review-failure-sample-2026-06-09.jsonl
  - reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample.json
  - reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json
  - agents/project/corrections/2026-06-09-offline-eval-2026-06-09-task-ar-217-1-goldset-metadata-completion.md
  - agents/project/corrections/2026-06-09-live-reviewer-gate-2026-06-09-task-ar-207-failure-sample-1-reviewer-footer-failure.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-207-correction-collector-log.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-207-correction-collector-sync.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-207-correction-followup-call.md
---

## 목표
채팅, 리뷰, 메시지에서 탐지된 오답/누락/모호성의 교정 제안을 자동 수집한다.

## 작업 내용

- `correction event` 템플릿 작성
- 에이전트 리뷰/메시지 로그와 연동
- 우선순위/영향범위/담당 owner 추론 규칙 설정

## 결과물

- correction 제안 스키마
- 주기형 수집 작업 명세(일/시간 단위)
- owner 승인 상태 저장 규칙

## 완료 조건

- 오답/누락 패턴이 correction 이벤트로 자동 생성되어야 함
- 제안은 승인 절차 없이 최종 반영되지 않아야 함
- correction 이벤트는 `severity`와 `owner`/`due_date` 필드를 함께 남겨야 함

## 비고

- 선행: `TASK-AR-206` 또는 `TASK-AR-204`

## Cycle Log (2026-06-09)

- Added `scripts/correction_collector.py`.
- Added failure sample evidence: `agents/project/live_review/live-review-failure-sample-2026-06-09.jsonl`.
- Ran failure sample through live reviewer gate:
  - Command: `python scripts/live_reviewer_gate.py --input agents/project/live_review/live-review-failure-sample-2026-06-09.jsonl --out reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample.json`
  - Result: `status=block`, `score=0.7059`, `findings=5`.
- Ran correction collector:
  - Command: `python scripts/correction_collector.py --report reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json --report reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample.json --summary reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json`
  - Result: `status=pass`, `written=2`.
- Generated correction proposals:
  - `agents/project/corrections/2026-06-09-offline-eval-2026-06-09-task-ar-217-1-goldset-metadata-completion.md`
  - `agents/project/corrections/2026-06-09-live-reviewer-gate-2026-06-09-task-ar-207-failure-sample-1-reviewer-footer-failure.md`
- Boundary: collector creates proposals only. Final definitions require owner/accountable human sign-off.
- Verification: collector rerun returned `status=pass`, `written=2`; publish bundle check after correction artifacts returned `findings=0`.
