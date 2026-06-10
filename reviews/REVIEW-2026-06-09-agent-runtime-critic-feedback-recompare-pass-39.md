# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-39.md

## Bottom Line

`PASS-39`에서는 `test_parallel_recover_and_answer_latency_distribution_and_starvation_guard`의 성능 경계값을 하드코드에서 분리해 운영/CI 조정 가능한 SLO 파라미터로 전환했고, 지표 산출물을 파일 아티팩트로 남길 수 있게 해 관측성과 지속 기록성을 보강했다.

`PASS-39`는 PASS-38의 `p95/p99/failure_ratio` 경보 규칙을 유지하면서도 환경변수 오버라이드와 JSON 메타데이터 기록을 추가해, 동일 테스트를 환경별 정책으로 운영할 수 있게 했다.

## Signal

| 항목 | PASS-38 상태 | PASS-39 상태 | 근거 |
|---|---|---|---|
| KPI 임계치 관리 | 상수 하드코드 | 환경변수 기반 오버라이드 추가 | `PASS_39_MAX_P95_MS`, `PASS_39_MAX_P99_MS`, `PASS_39_MAX_FAILURE_RATIO` 반영 |
| 성능 관측 기록 | 표준 출력 경고만 존재 | JSON 스냅샷 파일 아티팩트 추가 | `PASS_39_LATENCY_METRICS_PATH` 지정 시 지표/경고 저장 |
| 헬퍼 검증 | 없음 | 단일 테스트에서 env/아티팩트 헬퍼 검증 추가 | `test_latency_metric_helpers_respect_env_overrides_and_emit_artifact` 추가 |
| 공개 게이트 | 통과 | 유지 | 기존 게이트 연계 방식 유지 |

## Insight

- 임계치가 코드 상수로 묶여 있으면 장기 운영에서 환경별 튜닝이 어렵기 때문에, 이번 패스를 통해 외부 설정 드리븐 SLO 관리로 전환했다.
- 경고만 print로 남기던 구조에 아티팩트를 더해, 추후 CI 메트릭 집계/회귀 분석에서 바로 읽을 수 있는 원 데이터가 생겼다.
- 기존 `PASS-38` 동시성 테스트 본질은 유지되어 안정성 회귀 없이 관측성만 개선되는 방향이다.

## Decision

- `PASS-39`에서 지표 임계치와 실패 정책을 고정값이 아닌 환경변수로 이동해 정책 유연성을 확보한다.
- 현재 테스트 구성에서는 기본값(2500/3500/0.85) 유지되어 기존 동작 호환성을 유지한다.
- 다음 사이클은 수집된 JSON 아티팩트 경로 규약(`.jsonl`/스키마, 보관 위치)과 임계치 기반 알림/리포팅 정책(예: CI 알림 기준)을 정식으로 정리한다.

## Evidence (pass-39)

- `tests/test_template_message_queue.py` 헬퍼 수정 및 추가
  - `_env_float`, `_maybe_write_latency_metrics` 추가
  - `test_parallel_recover_and_answer_latency_distribution_and_starvation_guard`에서 환경변수 기반 SLO 값 사용
  - `test_latency_metric_helpers_respect_env_overrides_and_emit_artifact` 신규 추가
- `PASS-39` 임계치 env 적용 및 경고 아티팩트 기록 테스트 경로 구현

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-38.md`
- `tests/test_template_message_queue.py`
