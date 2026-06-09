# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-67.md

## Bottom Line

`PASS-67`에서 `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH` 쓰기 실패 시
`run-id` 검증 실패를 가리지 않되, 실패 사실을 `RuntimeWarning`으로 가시화한다.

## Signal

| 항목 | PASS-66 상태 | PASS-67 상태 | 근거 |
|---|---|---|---|
| 쓰기 실패 관측성 | `OSError` 무시로 무음 처리 | `RuntimeWarning`으로 실패 원인 로그 남김 | `tests/test_template_message_queue.py` |
| 예외 우선순위 | `ValueError`는 유지되나 경고 부재 | `PASS_39...` `ValueError`와 함께 경고 동시 발생 검증 | `tests/test_template_message_queue.py` |
| 장애 탐지 비용 | 경로 쓰기 실패가 추적 불가 | 경고 메시지로 후속 조치 트리거 가능 | `tests/test_template_message_queue.py` |

## Insight

- 쓰기 실패를 swallow-only로 두면 운영 모니터링에서 silent failure가 누적될 수 있다.
- `ValueError` 본래 목적(입력 계약 위반)은 그대로 두고, 부수 채널은 경고로 분리하면 진단이 쉬워진다.

## Decision

- `tests/test_template_message_queue.py`
  - `_record_run_id_rejection`에서 `_append_jsonl_record` `OSError` 예외를 `RuntimeWarning`으로 알림 처리
  - `test_latency_run_id_rejection_log_path_unwritable_does_not_mask_rejection`를 경고 검증으로 확장
    - `pytest.warns(RuntimeWarning, match="write failed")` + `pytest.raises(ValueError, ...)` 동시 확인

## Evidence (pass-67)

- `tests/test_template_message_queue.py`
  - `_record_run_id_rejection`
  - `test_latency_run_id_rejection_log_path_unwritable_does_not_mask_rejection`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "rejection_log_path_" -q`
- 결과: `6 passed, 36 deselected`

## Next Step

- PASS-68 제안: 경고가 실제 로그/메트릭으로 누적되는지 확인하는 엔드투엔드 테스트(예: `stderr` 캡처 또는 `warnings` 집계) 추가.
