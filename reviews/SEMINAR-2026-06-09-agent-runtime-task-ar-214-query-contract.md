# SEMINAR-2026-06-09-agent-runtime-task-ar-214-query-contract

## Bottom Line

질의 계약은 단일 스코어 기준이 아니라 `context + verification + review` 합산으로 운영한다는 합의가 유지된다.

## Signal

- `clarify` 선결 조건이 없는 자동 실행은 오탐/오해율을 키움.
- `source_footer`에서 메타 누락이 있으면 사용자 신뢰와 감사가 함께 붕괴됨.
- `accuracy` 목표만 높여도 비용/속도 트레이드오프를 무시하면 운영 안정성에 손해가 큼.

## Insight

- 고모호성 질의는 `clarify_required` 루프를 통해 질문을 쪼개야 함.
- `TASK-AR-214` 체크는 `release-preflight`의 정량 게이트와 별도 추적이 필요.

## Decision

1. `TASK-AR-214`는 `TASK-AR-210` 블로커 필드(`query contract violation`)와 연동.
2. `TASK-AR-214` 증빙 문서는 `TASK-AR-210`의 block/allow matrix에 반영.
3. `TASK-AR-215`는 context packet 적용 이전이라도 214의 검증 루프를 유지한 상태로 운영한다.
