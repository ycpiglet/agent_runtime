# MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-packet

## Bottom Line

`TASK-AR-215`는 다른 프로젝트 투입 시 오버레이 패키지만 변경해 `vision/roadmap/org/links/team` 맥락이 반영되도록 `context packet` 표준을 정리한다.

## Signal

- `agents/project/*`는 런타임 동작과 분리된 오버레이 경로로 유지.
- 오버레이 누락(또는 상충) 시 `TASK-AR-204` high-risk 차단 후보로 처리.
- `TASK-AR-213` parity evidence는 `TASK-AR-215` 시뮬레이션 결과와 교차 링크되어야 함.

## Insight

- 오버레이의 정합은 문서 완성도보다 링크 체계(`LINKS.md`) 일관성이 중요.
- 기존 버전/경로 정합이 깨진 상태에서도 `context packet` 시뮬레이션을 통해 실제 라우팅 위험을 검출 가능.

## Decision

1. `PROJECT-CONTEXT`, `ROADMAP`, `ORG`, `TEAMS`, `LINKS`, `VISION` 묶음을 컨텍스트 패키지로 고정.
2. `TASK-AR-204`/`TASK-AR-213`와 이탈/이의결정 경로를 링크로 남김.
3. 다음 단계는 cross-project 시뮬레이션 1건 작성 후 결과를 `TASK-AR-210` 보조 문서에 반영.
