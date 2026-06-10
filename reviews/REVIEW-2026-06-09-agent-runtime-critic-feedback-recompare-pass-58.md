# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-58.md

## Bottom Line

`PASS-58`에서 `PASS_39` run-id 실패 로그를 분석 관점으로 강화했다.

이제 `PASS_39_LATENCY_METRICS_RUN_ID` 유효성 실패 시 기록되는 JSONL 레코드에
`expected_pattern`과 `rejection_log_path`가 포함되며, 워크플로는 run-id rejection 로그를
`.tmp` 경로로 항상 수집한다.

## Signal

| 항목 | PASS-57 상태 | PASS-58 상태 | 근거 |
|---|---|---|---|
| rejection 로그 스키마 | `kind/run_id/reason` 최소 항목 | `expected_pattern`, `rejection_log_path` 추가 | `tests/test_template_message_queue.py` |
| 실패 수집 경로 | job-level env 경로 주입 없음/단일 형태 | CI job-level env 주입 + `.tmp` 경로 고정 | `.github/workflows/test.yml` |
| 추적성 smoke | 공통 테스트만 존재 | rejection 로그 존재/스키마 smoke 테스트 추가 | `tests/test_template_message_queue.py` |

## Insight

- 실패 원인만 남기면 재현 문맥이 부족하다. 실패 예상 패턴과 실제 저장 경로까지 남기면 자동 분석/이벤트 상관관계 추적이 쉽다.
- `_tmp` 경로는 CI에서 아카이빙 가능한 위치이므로 run-id 예외도 게이트 실패 분석 대상으로 남길 수 있다.

## Decision

- `_record_run_id_rejection`을 스키마 확장:
  - `expected_pattern`: 허용 가능한 패턴 힌트 (`run-*` CI 3형태 또는 whitespace 규칙)
  - `rejection_log_path`: 로그 파일 경로
- `_build_latency_metric_run_id`에서 공백 오류 및 CI 패턴 불일치 시
  `expected_pattern`을 함께 기록.
- 테스트 보강:
  - `test_latency_metric_invalid_run_id_is_rejected`: `expected_pattern`에 whitespace 제약 포함 확인
  - `test_latency_metric_rejection_log_smoke_path`: `.tmp` rejection 로그 파일 생성/경로 기록 확인
  - `test_latency_run_id_patterns_differentiate_ci_and_manual_cases`: 잘못된 `run-*` 케이스별 로그 `expected_pattern` 포함 확인
- 워크플로 업데이트:
  - `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH` 기본값을
    `.tmp/pass39-latency-metrics-run-id-rejections-${{ github.event_name }}-${{ matrix.python-version }}.jsonl`로 고정

## Evidence (pass-58)

- `tests/test_template_message_queue.py`
  - `_expected_ci_run_id_patterns`
  - `_record_run_id_rejection`
  - `_build_latency_metric_run_id`
  - `test_latency_metric_rejection_log_smoke_path`
- `.github/workflows/test.yml`
  - job-level `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH`

## Next Step

- PASS-59 제안: 실패 로그의 `expected_pattern` 값을 CI 패턴/수동모드 분류 키(`expected_mode`)로 정규화해 규칙 기반 후처리기에서 바로 집계 가능하게 한다.
