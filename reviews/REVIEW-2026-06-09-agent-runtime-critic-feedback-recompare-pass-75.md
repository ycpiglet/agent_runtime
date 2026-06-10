# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-75.md

## Bottom Line

`PASS-75`에서는 실제 경고 요약 저장 흐름을 흉내낸 JSONL 파이프라인을 통해
`pass39-warning-summary` 혼재 스키마(v1/v0/legacy) 레코드를 한 번의 읽기/병합/정책 평가 경로로
검증하도록 확장했다.

## Signal

| 항목 | PASS-74 상태 | PASS-75 상태 | 근거 |
|---|---|---|---|
| 엔드투엔드 결속 | 단일 함수를 직접 호출해 병합/정책 검증 | 저장 파일 쓰기(`warning_summary_path`)와 재로드 후 `coalesce` + 정책 평가를 한 시나리오로 통합 | `tests/test_template_message_queue.py` |
| 스키마 혼재 회귀 | v1/v0/legacy 혼재 병합만 분리 검증 | 혼재 레코드가 JSONL에서 실제로 읽힌 뒤에도 `run`/`event`/`window` 폴백 병합 및 `schema_version` 갱신 검증 | `tests/test_template_message_queue.py` |
| 정책 판단 연동 | 병합 결과를 바로 policy에 전달 | 병합 결과를 `_evaluate_warning_summary_policy`에 투입해 컨텍스트별 fail 판단을 검증 | `tests/test_template_message_queue.py` |

## Insight

- 실제 생성/저장 파이프라인에 들어가면 스키마 호환성 버그가 더 자주 드러나므로,
  단위 병합 로직만 아니라 파일 I/O 후 `coalesce`·정책 라우팅까지 회귀 포인트로 유지해야 한다.
- 임계치 실패 구간을 함께 검증하면 병합 로직 변경이 운영 가드에 미치는 영향을 즉시 포착할 수 있다.

## Decision

- `tests/test_template_message_queue.py`
  - `test_latency_warning_summary_schema_mixed_records_survive_end_to_end_write_read_and_policies` 추가
    - 혼재 스키마(v1/v0/legacy) 레코드를 JSONL로 저장 후 재로드
    - `run`/`event`/`window` 폴백을 통한 키 정규화 확인
    - `max_warnings_per_context` 임계치와 연계한 정책 fail 판정 확인

## Evidence (pass-75)

- `tests/test_template_message_queue.py`
  - `test_latency_warning_summary_schema_mixed_records_survive_end_to_end_write_read_and_policies`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "warning_summary_schema_mixed_records_survive_end_to_end_write_read_and_policies or warning_summary_schema_compatibility_keeps_aggregation_stable or warning_summary_records_are_coalesced_by_context or warning_summary_policy_evaluation_is_context_aware or warning_summary_is_partitioned_by_context" -q`
- 결과: `5 passed, 44 deselected`

## Next Step

- PASS-76 제안: 현재 PASS-75 파이프라인을 실제 템플릿 런타임 경고 수집 엔트리포인트로 이식하고,
  경고 요약이 CI/운영 정책 게이트에서 직접 사용되도록 스키마 정합성 체크를 추가.
