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
