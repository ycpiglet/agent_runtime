# SEMINAR (2026-06-09) - TASK-AR-224 governance seminar

## 의제

- 공식 가이드와 migration 근거를 release gate에서 어떻게 강제할 것인가
- 다른 프로젝트가 `agent_runtime`을 가져가도 공통 스킬이 변질되지 않게 만드는 구조
- A2A/교정/reviewer/eval 증적을 같은 decision cycle에 묶는 방식

## 공유 내용

- 멀티프로젝트 적용에서 핵심은 runtime core 수정이 아니라 project overlay, skill-data map, migration map의 분리다.
- `SKILL-DATA-MAP.yml`은 모델/provider/data 변경 시 문서 동기화를 강제하는 기준이며, `MIGRATION-COMPAT-MAP.yml`은 tag_manual 이식 차이를 release에서 설명하는 기준이다.
- 공식 가이드는 단일 모델 성능보다 trace, eval dataset, approval boundary, telemetry, A2A continuity를 함께 운영하라는 방향으로 수렴한다.

## 합의

- `TASK-AR-224`는 `TASK-AR-223` closeout 전에 반드시 실행되는 source-control gate로 유지한다.
- `scripts-source-only` 53건은 세분류 전까지 release-ready 근거가 아니며, 승인 또는 hold 이관 증거가 필요하다.
- overlay-only 시뮬레이션은 다음 cycle에서 최소 1회 기록한다.
