# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-68.md

## Bottom Line

`PASS-68`에서 `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH` 쓰기 실패 경고가
연속 실패 케이스에서도 누적되는지 검증해, 경고 기반 모니터링의 신호 보존을 강화했다.

## Signal

| 항목 | PASS-67 상태 | PASS-68 상태 | 근거 |
|---|---|---|---|
| 경고 누적성 | 단일 실패 케이스 경고 동시 검증 | 다중 실패에서 경고 갯수/메시지 누적 검증 | `tests/test_template_message_queue.py` |
| 장애 탐지 정확성 | 단발성 경고 존재 여부만 확인 | 연속 2회 실패 시 2건 경고가 모두 기록되는지 확인 | `tests/test_template_message_queue.py` |
| 운영 가시성 | 경고 메시지 존재만 보장 | 경고 메시지 텍스트 패턴의 반복 관측 증명 | `tests/test_template_message_queue.py` |

## Insight

- 단건 검증은 존재성에 그칠 수 있어, 연속 실패에서 누락이 있어도 못 잡는다.
- `warnings.catch_warnings(..., record=True)`로 카운트/내용을 함께 보관하면 운영 모니터링 채널 누락(예: 반복 배치 실패)을 더 빨리 탐지할 수 있다.

## Decision

- `tests/test_template_message_queue.py`
  - `test_latency_run_id_rejection_log_path_unwritable_warns_accumulate_across_failures` 추가
  - `_append_jsonl_record`를 실패 주입(`PermissionError`)으로 monkeypatch
  - 2회 연속 실패 상황에서:
    - `_maybe_write_latency_metrics`에서 `ValueError` 두 번 발생
    - `_append_jsonl_record` 호출 2회
    - `RuntimeWarning` 캡처 2건
    - 각 경고 메시지에 `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH write failed` 포함 검증

## Evidence (pass-68)

- `tests/test_template_message_queue.py`
  - `test_latency_run_id_rejection_log_path_unwritable_warns_accumulate_across_failures`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "rejection_log_path_" -q`
- 결과: `7 passed, 36 deselected`

## Next Step

- PASS-70 제안: 구조화 경고 코드를 운영 집계 포맷(경고 코드별 카운터)으로 연결해 end-to-end 가시성을 마무리.
