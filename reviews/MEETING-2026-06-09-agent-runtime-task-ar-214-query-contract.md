# MEETING-2026-06-09-agent-runtime-task-ar-214-query-contract

## Bottom Line

`TASK-AR-214`는 질의 계약 메타 강제와 오답 예방 루프를 가동하기 위한 선행 작업으로 즉시 착수한다.

## Signal

- 질의 필드(`business_scope`, `time_window`, `tolerance`, `query_tolerance`, `access_check`, `tradeoff_preference`) 누락은 즉시 `clarify_required`로 간주.
- `TASK-AR-204`에서 `query contract violation`은 기본 경고가 아니라 `block`으로 처리.
- 기존 오버레이 문서에 `SKILL-GOVERNANCE`와 `EVAL-POLICY` 참조만 존재해도 실행 기준은 충분히 설정 가능.

## Insight

- `TASK-AR-214` 완료 시점의 증빙은 `TASK-AR-210` 블로커 룰에서 즉시 참조 가능해야 한다.
- 오버레이 누락이 있어도 질의 계약이 완결되면 1차 실행은 가능하나 `TASK-AR-215`에서 context packet이 완료되면 재평가한다.

## Decision

1. `TASK-AR-214` 산출물을 `CONTEXT-SOURCES.yml` + `SKILL-GOVERNANCE.md` + `EVAL-POLICY.yml`에 반영하고, 태스크 로그에 링크.
2. 고위험 질의 시 `reviewer_review`를 우선 처리하고, 통과 후에만 종료 상태로 간주.
3. 다음 사이클에서 `TASK-AR-215`를 바로 착수한다.
