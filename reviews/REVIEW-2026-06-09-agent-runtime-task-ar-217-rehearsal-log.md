# REVIEW-2026-06-09-agent-runtime-task-ar-217-rehearsal-log

## Bottom Line

리허설 로그는 패스/폴스만 기록하는 파일이 아니라 다음 판정이 재현 가능한 형태의 의사결정 체인을 남겨야 한다.

## Signal

- 판정 실패는 즉시 root-cause(쿼리 계약 미정의, 오버레이 누락, 메트릭 미충족, trace 부재)로 분해되어야 한다.
- 실패 후 `reviewer`/`correction`/`decisions` 링크가 서로 단절되면 이후 판정에서 동일 실수가 반복된다.

## Recorded Structure

- rehearsal timestamp
- release-preflight result: source / findings / blockers
- offline_eval summary: domain / score / failed_cases
- live verification: footer coverage / reviewer verdict / risk tags
- correction events: id / severity / owner / due_date
- a2a trace: correlation_id / request_id / decision_id
- `hold` 라벨: `hold_for_data` / `hold_for_query_contract` / `hold_for_overlay` / `hold_for_reviewers`

## Decision

- 로그는 완료 즉시 `TASK-AR-216`과 `TASK-AR-217`에 링크하고, 다음 세션 `Handoff Checklist`의 상단 항목으로 반영한다.

## Completion Evidence Bundle (2026-06-10)

- `release-preflight` baseline:
  - `TASK-AR-225` clean bundle result: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-223217 --check` → `findings=0` (referenced in `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-log.md`).
- 오프라인 90% 게이트:
  - `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json` → `status=pass`, `project-overlay-routing-gold=1.0`, `gov-metadata-gold=1.0`.
- 라이브 reviewer footer:
  - `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json` → `status=pass`, `score=1.0`, footer 필드 존재(`source_tier`, `confidence`, `risk`, `ambiguity`, `freshness_sla`).
- correction 수집:
  - `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json` → `status=pass`, `written=2`, 제안 파일 경로:
    - `agents/project/corrections/2026-06-09-offline-eval-2026-06-09-task-ar-217-1-goldset-metadata-completion.md`
    - `agents/project/corrections/2026-06-09-live-reviewer-gate-2026-06-09-task-ar-207-failure-sample-1-reviewer-footer-failure.md`
- A2A trace:
  - `reviews/A2A-TRACE-GATE-2026-06-09-task-ar-208.json` → `status=pass`, `events=4`, `chains=1`, chain=`request -> review -> decision -> correction`.

## Decision

- Rehearsal evidence is complete at the baseline pass level and ready for TASK-AR-210 release-state translation as a closed `TASK-AR-217` lane bundle.
- Pending release blockers for `TASK-AR-210` are no longer artifact-lane specific; they are now bound to remaining migration/overlay/governance routes (`hold_for_data` or `hold_for_overlay`) in `TASK-AR-210`.
