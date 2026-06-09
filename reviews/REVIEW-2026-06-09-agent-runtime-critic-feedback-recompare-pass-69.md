# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-69.md

## Bottom Line

`PASS-69`에서 `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH` 쓰기 실패 경고를
문자열 기반에서 구조화 코드 기반으로 전환해 모니터링 집계가 쉬운 신호를 만들었다.

## Signal

| 항목 | PASS-68 상태 | PASS-69 상태 | 근거 |
|---|---|---|---|
| 경고 식별성 | 메시지 텍스트 매칭으로만 경고 확인 | `code`/메타를 가진 경고 객체로 식별 가능 | `tests/test_template_message_queue.py` |
| 경고 누적성 | 누적 개수/메시지 패턴 검증 | 누적 개수와 `code` 동등성 동시 검증 | `tests/test_template_message_queue.py` |
| 운영 가시성 | 문구 변경 시 테스트 깨짐 가능 | `code` 중심으로 집계/필터링 가능한 신호 확보 | `tests/test_template_message_queue.py` |

## Insight

- 텍스트 경고는 운영에서 규칙 매칭 시 깨지기 쉬워, 코드 기반 경고 객체가 경고 채널의 안정성과 재사용성을 높인다.
- 주 채널(`ValueError`)은 유지하고 보조 채널은 구조화 경고로 분리하면 장애 대응 자동화 규칙을 만들기 수월해진다.

## Decision

- `tests/test_template_message_queue.py`
  - `_Pass39LatencyRunIdRejectionLogWarning` 추가
  - `_record_run_id_rejection`에서 쓰기 실패 시 문자열이 아닌 경고 객체(`RuntimeWarning` 하위) 발행
    - `code`: `PASS_39_LATENCY_RUN_ID_REJECTION_LOG_WRITE_FAILURE`
    - `reason`, `log_path`, `error` 메타 포함
  - `test_latency_run_id_rejection_log_path_unwritable_does_not_mask_rejection`
    - `warnings.catch_warnings`로 경고 객체 타입/`code`/`reason` 검증 추가
  - `test_latency_run_id_rejection_log_path_unwritable_warns_accumulate_across_failures`
    - 다중 실패 시 경고 객체 코드가 반복되는지 검증으로 누적 집계 가능성 확인

## Evidence (pass-69)

- `tests/test_template_message_queue.py`
  - `_Pass39LatencyRunIdRejectionLogWarning`
  - `_record_run_id_rejection`
  - 경고 관련 테스트 2건

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "rejection_log_path_" -q`
- 결과: `7 passed, 36 deselected`

## Next Step

- PASS-71 제안: 경고 코드 요약 레코드에 `run_id`/`event`/타임 윈도우를 추가해
  파이프라인 집계에서 다중 run/job 컨텍스트를 분리할 수 있게 확장.
