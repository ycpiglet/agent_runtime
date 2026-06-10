# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-57.md

## Bottom Line

`PASS-57`에서 `PASS_39` latency run-id 유효성 실패 시 추적 로그를 생성하도록 보강해
실패 원인(공백/패턴 불일치)을 CI `.tmp` 아티팩트로 즉시 재현 가능한 형태로 남겼다.

## Signal

| 항목 | PASS-56 상태 | PASS-57 상태 | 근거 |
|---|---|---|---|
| run-id 실패 추적성 | invalid run-id는 에러만 발생 | 실패 시 `_tmp` JSONL 리젝션 로그 기록 | `tests/test_template_message_queue.py` |
| 수동/CI 모드 구분 로그 | 패턴 검증만 수행 | `run-` 오입력 케이스별 리젝션 레코드 개수/내용 검증 | `tests/test_template_message_queue.py` |
| 정합 증적 | 정합 규칙은 PASS-56까지 적용 | invalid 패턴 실패 로그/기록 형식 추가 검증 | `tests/test_template_message_queue.py` |

## Insight

- 단순 예외만으로는 CI 재현성이 약하다. 오류 발생 당시 `run_id`, `reason`, GitHub 실행 context를 함께 저장하면
  실패 원인 추적이 훨씬 빨라진다.
- 동일 테스트 안에서 valid/invalid 케이스를 분리해 로그 수와 run_id 매핑을 검증하면
  로그 누락/초과 기록도 함께 방어할 수 있다.

## Decision

- `_record_run_id_rejection` 추가:
  - `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH` 경로에 JSONL 레코드를 append
  - 로그 스키마: `pass39-latency-run-id-rejection-v1`, `kind`, `run_id`, `reason`, `github_run_id`, `github_event_name`
- `_build_latency_metric_run_id`의 실패 분기(공백, 형식 오입력)에 `_record_run_id_rejection` 호출 추가
- 테스트 보강:
  - `test_latency_metric_invalid_run_id_is_rejected`: 공백 오류 로그 검증
  - `test_latency_run_id_patterns_differentiate_ci_and_manual_cases`: 잘못된 `run-` 패턴 3건 로그 개수/내용 검증

## Evidence (pass-57)

- `tests/test_template_message_queue.py`
  - `_append_jsonl_record`
  - `_record_run_id_rejection`
  - `_assert_latency_metric_run_id_is_expected` / `_build_latency_metric_run_id`에서 rejection 로그 연동
  - `test_latency_metric_invalid_run_id_is_rejected`
  - `test_latency_run_id_patterns_differentiate_ci_and_manual_cases`

## Next Step

- PASS-58 제안: 워크플로에서 `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH`를 `.tmp/pass39-latency-metrics-run-id-rejections.jsonl`로 고정 주입해 운영 로그를 항상 수집.
