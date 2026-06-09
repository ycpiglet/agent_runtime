# RESEARCH-2026-06-09-agent-runtime-task-ar-215-cross-project-overlay

## Bottom Line

멀티 프로젝트 적용에서 공통 런타임 유지 + 오버레이 교체 전략이 가장 빠르게 재사용성을 확보한다.

## Signal

- 오버레이 문서는 구성만으로 끝나지 않고 `roadmap/org/links/team` 연결이 유지되어야 함.
- 문서 누락은 즉시 라우팅 누락으로 이어져 오탐/허위 답변 확률을 높임.
- 오버레이 시뮬레이션은 release gate 전 단계에서 반드시 1건 이상 수행되어야 함.

## Insight

- `TASK-AR-215`는 단기적으로는 `TASK-AR-204` 차단 지표를 풍부하게 해주고, 중기적으로는 프로젝트 확장을 가속.
- `TASK-AR-214` 메타 계약 없이는 오버레이 품질이 보장되지 않으므로 병렬 병행 검증이 필요.

## Decision

1. `LINKS.md`를 프로젝트별 패킷 인덱스로 사용하고, 증빙 산출물은 `TASK-AR-215`/`TASK-AR-210`에 상호 링크.
2. context packet 시뮬레이션 결과를 `BLOCK` 판단 자료로 반영.
3. 오버레이 변경은 공용 런타임 변경 없이 실행 가능해야 함.
