# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-66.md

## Bottom Line

`PASS-66`에서 `PASS_39_LATENCY_METRICS_RUN_ID` 유효성 실패 시
`PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH` 쓰기 오류가
`ValueError` 전파를 가로막지 않도록 정책을 고정했다.

## Signal

| 항목 | PASS-65 상태 | PASS-66 상태 | 근거 |
|---|---|---|---|
| 기록 실패 정책 | 쓰기 실패가 즉시 예외 전파되어 기본 에러와 섞일 위험 | `OSError`를 catch해 `run-id` 검증 예외 우선 유지 | `tests/test_template_message_queue.py` |
| 장애 주입 검증 | 경로 문자열 보존/생성 성공성만 검증 | 쓰기 실패 주입 시 검증 실패 예외(`ValueError`)만 확인 | `tests/test_template_message_queue.py` |
| 감사 추적 보존 | 파일 쓰기 실패 시 감사로그 자체 부재 가능성 | 실패를 로깅 정책 분기에서 분리해 기존 검증 경로 보존 | `tests/test_template_message_queue.py` |

## Insight

- `run-id` 규격 위반은 주 경로(Validation)이며, 보조 경로(리젝션 로그) 실패는
  검증 실패를 은닉하지 않도록 격리돼야 실제 장애 진단이 왜곡되지 않는다.
- 향후 필요 시 경로 쓰기 실패를 위한 별도 메트릭/경고 채널을 두어 감사 추적 손실을 가시화할 수 있다.

## Decision

- `tests/test_template_message_queue.py`
  - `_record_run_id_rejection`에서 `_append_jsonl_record` 호출을 `OSError` 예외로 감싸고 무시
  - `test_latency_run_id_rejection_log_path_unwritable_does_not_mask_rejection` 추가
  - 주입 실패( `PermissionError`) 상황에서도 `PASS_39_LATENCY_METRICS_RUN_ID must not contain whitespace` `ValueError`가 유지됨을 검증

## Evidence (pass-66)

- `tests/test_template_message_queue.py`
  - `_record_run_id_rejection`
  - `test_latency_run_id_rejection_log_path_unwritable_does_not_mask_rejection`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "rejection_log_path_" -q`
- 결과: `6 passed, 36 deselected`

## Next Step

- PASS-68 제안: 경고 채널이 실제 파이프라인/모니터로 누적되는지
  (예: 경고 집계 또는 stderr 수집)까지 회귀로 확장.
