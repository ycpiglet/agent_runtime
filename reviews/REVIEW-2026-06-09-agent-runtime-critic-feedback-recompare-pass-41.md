# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-41.md

## Bottom Line

`PASS-41`에서는 PASS-40 아티팩트 스키마를 운영 관측 관점에서 실사용 가능하게 만들기 위해, 저장된 지연 메트릭 레코드의 집계/정합성 점검 함수를 추가했다.

`_load_latency_metric_records`와 `_summarize_latency_metric_records`를 통해 JSON/JSONL 경로에서 레코드를 읽고, warning 레코드 개수·최대 경고 수·실패 후보(run_id) 집계를 계산해 CI/운영에서 정책 판단 가능한 형태로 정리한다.

## Signal

| 항목 | PASS-40 상태 | PASS-41 상태 | 근거 |
|---|---|---|---|
| 아티팩트 판독 | 기록 포맷 분기 없음 | JSON/JSONL 판독기 및 요약 유틸 추가 | ` _load_latency_metric_records`, `_summarize_latency_metric_records` 추가 |
| 정책 판단 | 테스트 내 단일 레코드 판정 | 다중 레코드 경고 집계 지원 | `warning_records`, `max_warning_count`, `failed_records`, `all_ok` 요약 |
| 운영성 | 경고만 테스트 경계 | 경고 기반 정책 전개를 위한 중간 계층 확보 | `test_latency_metric_policy_summary_allows_warning_mode` 추가 |

## Insight

- PASS-40에서 쌓인 raw 메트릭을 그대로 해석해 정책화할 수 있는 최소 단위를 마련했다.
- warning 레코드는 메시지 단위가 아닌 실행(run_id) 단위로 추적되므로, 여러 실행을 연속 처리하는 CI 환경에서 실패 판단 로직으로 쉽게 확장 가능하다.
- 다음 단계는 이 요약을 실제 CI 경고/차단 규칙(예: warning-only 모드 vs fail-on-warning 모드)로 바인딩하는 것입니다.

## Decision

- PASS-41은 PASS-40 산출물의 운영 집계 정리 레이어를 추가했다.
- 현재 테스트는 다중 레코드 경고 요약 동작을 증명하고, 다음 순환에서 이를 CI 정책으로 연결한다.

## Evidence (pass-41)

- `tests/test_template_message_queue.py`
  - `_load_latency_metric_records` 추가
  - `_summarize_latency_metric_records` 추가
  - `test_latency_metric_policy_summary_allows_warning_mode` 추가

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-40.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-39.md`
