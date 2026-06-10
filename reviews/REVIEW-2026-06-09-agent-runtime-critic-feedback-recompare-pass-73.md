# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-73.md

## Bottom Line

`PASS-73`에서 동일 `(run_id, event_name, window_start, window_end)` 컨텍스트 레코드를 병합해
중복 집계 발생 시 과대 집계를 방지하는 규칙을 추가했다.

## Signal

| 항목 | PASS-72 상태 | PASS-73 상태 | 근거 |
|---|---|---|---|
| 컨텍스트 병합 | 단일/분리 컨텍스트만 검증 | 동일 컨텍스트 키 병합 헬퍼 추가 | `tests/test_template_message_queue.py` |
| 중복 카운트 | 중복 레코드에 대한 합산 고려 없음 | 동일 컨텍스트에서는 `total_warnings`/코드 count를 `max`로 병합 | `tests/test_template_message_queue.py` |
| 정책 평가 | 병합 전 레코드 기반 정책 판정만 존재 | 병합 후 정책 판정(`coalesce -> evaluate`) 경로 검증 | `tests/test_template_message_queue.py` |

## Insight

- 동일 컨텍스트의 경고 요약이 중복 적재되면 경고 임계치 정책이 과장될 수 있다.
- 중복 병합을 `context key` 기준으로 먼저 수행한 뒤 정책을 적용하면 운영 알람 안정성이 올라간다.

## Decision

- `tests/test_template_message_queue.py`
  - `_coalesce_warning_summary_records` 추가
    - 키: `(run_id, event_name, window_start, window_end)`
    - 같은 키에서 `warning_code_counts`와 `total_warnings`는 `max` 병합
  - `test_latency_warning_summary_records_are_coalesced_by_context` 추가
    - 동일 키 2건(1, 3)를 병합해 최종 `total_warnings=3` 및 count=3로 수렴 확인
    - 병합된 레코드에 대해 정책 평가 후 run_id=2001이 초과로 fail 판단됨을 확인

## Evidence (pass-73)

- `tests/test_template_message_queue.py`
  - `_coalesce_warning_summary_records`
  - `test_latency_warning_summary_records_are_coalesced_by_context`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "coalesced_by_context or warning_summary_is_partitioned_by_context or warning_summary_policy_evaluation_is_context_aware" -q`
- 결과: `3 passed, 44 deselected`

## Next Step

- PASS-75 제안: PASS-74에서 안정화한 병합/스키마 호환성 규칙을 경고 요약 생성/저장 파이프라인에
  end-to-end로 반영해 운영 알림 정책 경로까지 이어서 검증.
