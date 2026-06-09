# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-74.md

## Bottom Line

`PASS-74`에서 경고 요약 병합(`coalesce`)이 `window` 단일 키, 대체 키(`run`/`event`/`window_end_time`),
`schema_version` 혼재 환경에서 동일 컨텍스트(`run_id`, `event_name`, `window_start`, `window_end`)를
안정적으로 합치도록 보강했다.

## Signal

| 항목 | PASS-73 상태 | PASS-74 상태 | 근거 |
|---|---|---|---|
| 스키마 호환성 | `window_start`/`window_end` 단일 스키마만 검증 | `window`, `run`, `event`, `window_end_time` 폴백을 통해 혼재 입력 병합 허용 | `tests/test_template_message_queue.py` |
| 병합 안전성 | 코드 카운트/합계 규칙은 정수 가정 | 카운트 병합에 안전 변환 적용으로 비정수/누락 입력에 강건화 | `tests/test_template_message_queue.py` |
| 회귀 테스트 | PASS-73 경로 테스트 3건 | v1/v0/legacy 혼재 3건이 단일 컨텍스트로 합쳐짐을 검증하는 새 테스트 추가 | `tests/test_template_message_queue.py` |

## Insight

- `window` 범위 문자열 입력과 별도 필드 입력이 섞이는 현실 데이터에서, 키 분할이 다르면 동일 컨텍스트가 분리되어 정책 fail이 과대/과소 계산될 수 있다.
- 컨텍스트 키 파싱을 단일 진입점으로 정규화하면 스키마 진화기에서 생기는 혼선을 크게 줄일 수 있다.

## Decision

- `tests/test_template_message_queue.py`
  - `_coalesce_warning_summary_records`
    - `window` 문자열을 `start/end`로 파싱해 `window_start`, `window_end`를 보완하는 로직 추가
    - `warning_code_counts` 병합 시 `_safe_int` 기반 강건한 정수 정규화 적용
  - `test_latency_warning_summary_schema_compatibility_keeps_aggregation_stable` 추가
    - `pass39-warning-summary-v1`, `pass39-warning-summary-v0`, `pass39-warning-summary-legacy` 혼재 시
      `coalesce` 결과가 1개로 수렴하는지 검증
    - `total_warnings`/`warning_code_counts`/정책 실패 사유(run 기반)가 안정적임을 확인

## Evidence (pass-74)

- `tests/test_template_message_queue.py`
  - `_coalesce_warning_summary_records`
  - `test_latency_warning_summary_schema_compatibility_keeps_aggregation_stable`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "coalesce or schema_compatibility or warning_summary_is_partitioned_by_context or warning_summary_policy_evaluation_is_context_aware" -q`
- 결과: `4 passed, 44 deselected`

## Next Step

- PASS-76 제안: PASS-75에서 검증한 혼재-schema 경고 요약 경로를 템플릿 경량 실행/CI 정책 게이트와
  운영 기준(임계치/알람 루틴)으로 연결하는 실환경 연동 작업.
