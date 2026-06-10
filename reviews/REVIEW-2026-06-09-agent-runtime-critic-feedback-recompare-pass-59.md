# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-59.md

## Bottom Line

`PASS-59`에서 `run-id` rejection 로그에 집계용 `expected_mode`를 추가해
CI 패턴/수동 모드 분류를 바로 조회할 수 있게 했다.

## Signal

| 항목 | PASS-58 상태 | PASS-59 상태 | 근거 |
|---|---|---|---|
| rejection 스키마 | `expected_pattern`/경로 기록만 존재 | `expected_mode`(`ci`/`manual`) 추가 | `tests/test_template_message_queue.py` |
| 수동/CI 구분 | 패턴 문자열로 간접 분류 | `expected_mode` 필드로 직접 집계 가능 | `tests/test_template_message_queue.py` |
| smoke 검증 | `.tmp` 로그 존재성/스키마 검증 | `expected_mode`까지 회귀 검증 | `tests/test_template_message_queue.py` |

## Insight

- rejection 로그를 분석할 때 문자열 검색보다 정규화 키가 있으면 대시보드 집계가 단순해진다.
- `run-*` 값은 CI 패턴 계열에서 발생한 실패로 보고(`expected_mode: ci`), 수동 ID는 운영 예외 경로로 구분(`expected_mode: manual`)되어 실패 성격을 빠르게 구분할 수 있다.

## Decision

- `tests/test_template_message_queue.py`
  - `_expected_mode_for_run_id` 추가
  - `_record_run_id_rejection` payload에 `expected_mode` 추가
  - `test_latency_metric_invalid_run_id_is_rejected`에서 `expected_mode=="manual"` 검증
  - `test_latency_run_id_patterns_differentiate_ci_and_manual_cases`에서 잘못된 `run-*` 케이스 `expected_mode=="ci"` 검증

## Evidence (pass-59)

- `tests/test_template_message_queue.py`
  - `_expected_mode_for_run_id`
  - `_record_run_id_rejection`
  - `test_latency_metric_invalid_run_id_is_rejected`
  - `test_latency_metric_rejection_log_smoke_path`
  - `test_latency_run_id_patterns_differentiate_ci_and_manual_cases`

## Next Step

- PASS-60 제안: `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH`를 스모크/리트리트 테스트에서 `.tmp` 경로 패턴 고정과 정책 허용치(`PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT`) 간 상관관계까지 같이 검증해 관측성 패키지를 완성.
