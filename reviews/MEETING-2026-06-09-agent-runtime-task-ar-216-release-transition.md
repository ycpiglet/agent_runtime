# MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition

## Bottom Line

`TASK-AR-216`의 의사결정 이관 룰은 v0.1.8 판정 창(07-02/07-09/07-16)을 기준으로 `TASK-AR-210`와 정합되도록 정리한다.

## Signal

- 기존 `v0.1.7` 미통과 항목은 “결과 부족”이 아니라 “이관되지 않은 블로커”로 남아 있었음.
- `release-state`(hold / hold_for_* / ready) 기반 상태 체계를 넣지 않으면 문서 간 판정 불일치가 계속 발생.
- `TASK-AR-214`, `TASK-AR-215` 미해결 사유가 재심 시점마다 동일 기준으로 복사되지 않음.

## Insight

- 판정 전환은 `request_for_v0.1.8`가 선행되어야 하고, 차단 사유가 `TASK-AR-210`에서 바로 라우팅되어야 함.
- Owner 승인 템플릿은 최소 필드(`blocked_by`, `owner`, `decision_deadline`, `impact`)를 항상 요구해야 한다.

## Decision

1. `BACKLOG.md`/`STATUS.md`/`PROJECT-CONTEXT.yml`/`ROADMAP.md`의 일정 문구를 07-02/07-09/07-16로 정렬한다.
2. `TASK-AR-210` 차단 사유 블록마다 `release-state`를 명시하고 미해결 사유는 그대로 보존한다.
3. 다음 액션은 `TASK-AR-217`에서 rehearsal 결과를 받으면 자동 이어진다.
