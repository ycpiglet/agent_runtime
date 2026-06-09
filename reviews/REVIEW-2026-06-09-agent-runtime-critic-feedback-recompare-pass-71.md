# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-71.md

## Bottom Line

`PASS-71`에서 경고 집계 레코드를 `run_id`/`event_name`/`window_*` 컨텍스트와 함께
저장하도록 확장해, 다중 run/job의 집계가 분리되도록 정합성을 만들었다.

## Signal

| 항목 | PASS-70 상태 | PASS-71 상태 | 근거 |
|---|---|---|---|
| 컨텍스트 정합성 | 단일 컨텍스트 요약만 검증 | run/context/window 기반 다중 레코드 분리 검증 | `tests/test_template_message_queue.py` |
| 집계 포맷 | 코드/총계만 기록 | 코드/총계 + run_id/event_name/window_start/window_end | `tests/test_template_message_queue.py` |
| 운영 가시성 | 요약 레코드 구분 기준 불명확 | 파이프라인 식별 필드를 통해 컨텍스트 분기 집계 가능 | `tests/test_template_message_queue.py` |

## Insight

- 동일 경고 코드라도 run/job가 다르면 병합 정책이 달라야 한다.
- 창(window) 메타가 있으면 일괄 집계/알람 임계치 계산이 자동화되기 쉬워 실제 운영 연동성이 높다.

## Decision

- `tests/test_template_message_queue.py`
  - `_build_pass39_warning_summary_record` 추가:
    - `schema_version`, `warning_code_counts`, `total_warnings` 외에 `run_id`, `event_name`, `window_start`, `window_end` 추가
  - `test_latency_run_id_rejection_warning_codes_are_aggregateable` 업데이트:
    - 컨텍스트 필드 포함한 요약 레코드 생성/검증
  - `test_latency_run_id_rejection_warning_summary_is_partitioned_by_context` 추가:
    - 서로 다른 `GITHUB_RUN_ID`/`GITHUB_EVENT_NAME` 및 윈도우 값으로 2개 요약 레코드 생성
    - run/event/window 조합별 분리됨을 검증

## Evidence (pass-71)

- `tests/test_template_message_queue.py`
  - `_build_pass39_warning_summary_record`
  - `test_latency_run_id_rejection_warning_codes_are_aggregateable`
  - `test_latency_run_id_rejection_warning_summary_is_partitioned_by_context`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "rejection_log_path_ or warning_codes_are_aggregateable or warning_summary_is_partitioned_by_context" -q`
- 결과: `9 passed, 36 deselected`

## Next Step

- PASS-75 제안: PASS-74에서 하위/미래 호환 혼재 규칙을 실제 경고 요약 경로의 생성-저장-판정
  흐름으로 확장해 회귀를 점검.
