# REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan

## Bottom Line

`TASK-AR-217`은 1차/2차/3차 판정의 반복 가능성 때문에 모든 게이트 증적을 단일 bundle에 고정한다.

## Signal

- gate rehearsal에는 `release-preflight`, 오프라인 90% 게이트, reviewer/correction/A2A 재현이 모두 포함되어야 함.
- 실패 사유는 `TASK-AR-210`의 `blocked_by` 사유 구조와 동일 형식으로 저장해야 재심에서 복원성이 생김.

## Insight

- 릴리스 판정은 단일 명령 성공/실패가 아니라, 재심 시나리오(07-02/07-09/07-16)마다 실패/보완/재심 흐름을 남기는지 여부로 판단한다.
- 오버레이, 쿼리 contract, 문서 freshness는 각각 독립 블록이 아니라 하나의 정합 사슬로 관리되어야 함.

## Decision

1. `release-preflight`는 `.tmp`/`source .` 두 경로 모두로 실행해 교차 검증 로그를 남긴다.
2. 도메인별 오프라인 점수는 실패 케이스를 correction 이벤트로 연결하고, correction 이벤트는 approval 없이 자동 반영되지 않도록 한다.
3. `reviewer footer`와 `A2A trace`가 누락되면 `rehearsal-block` 라벨로 분리해 다음 세션 우선순위 상단에 고정한다.
