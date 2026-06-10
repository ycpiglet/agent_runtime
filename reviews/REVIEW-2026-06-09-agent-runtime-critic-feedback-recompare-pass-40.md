# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-40.md

## Bottom Line

`PASS-40`에서는 `PASS-39`에서 추가한 지연 KPI 아티팩트 정책을 정형화해, 경고 산출물을 안정적인 스키마 형태로 기록 가능한 형태로 확장했다.

`_maybe_write_latency_metrics`는 경로 확장자에 따라 단일 JSON 또는 JSONL 누적 레코드로 저장되며, `run_id`/`created_at`/`schema_version`을 항상 포함하도록 했다. `PASS-39` 헬퍼 테스트는 기존 단일 JSON 형식을 검증하고, `PASS-40`에서는 JSONL 형식/누적 기록과 스키마 유효성 검사 경로를 추가했다.

## Signal

| 항목 | PASS-39 상태 | PASS-40 상태 | 근거 |
|---|---|---|---|
| 지표 아티팩트 형식 | 기본 JSON만 지원 | JSON/JSONL 모두 지원 | suffix가 `.jsonl`이면 append, 그 외는 pretty JSON |
| 기록 메타데이터 | 파일명 지정만 기록 | `schema_version`, `run_id`, `created_at` 메타데이터 추가 | `_maybe_write_latency_metrics` 내부 payload 강화 |
| 스키마 검증 | 없음 | `_assert_latency_metric_payload` 추가 | `test_latency_metric_artifact_supports_jsonl_schema`에서 레코드 검증 |
| 설정/추적성 | env 설정 및 경로 지원 | `PASS_39_LATENCY_METRICS_RUN_ID` 추가로 실행 단위 추적 | 레코드에 `run_id` 포함 |

## Insight

- JSONL 누적 경로 지원으로 다중 실행을 분해 보존하면서도, 같은 실행의 연속 기록을 그대로 남길 수 있다.
- 메타데이터 표준화는 CI/운영 스크립트에서 아티팩트를 단순 파일이 아닌 계약된 레코드 집합으로 처리할 수 있게 만든다.
- 이번 패스는 PASS-39의 정책 유연화에 “회귀 시 계측 원본 보존”을 덧붙인 상태로, 다음 단계는 이 스키마를 문서/CI에 연결하면 된다.

## Decision

- `PASS-40`은 PASS-39 지표 아티팩트를 단일/누적 형식 모두 지원하도록 일반화해, 수집된 성능 근거를 재현 가능한 이벤트 로그화 하였다.
- 다음 사이클에서는 이 레코드 위치 규약, 보존 기간, 게이트 조건(예: 경고 수치 초과 시 fail 정책)까지 문서화해 운영 규칙을 완성한다.

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-39.md`
- `tests/test_template_message_queue.py`
