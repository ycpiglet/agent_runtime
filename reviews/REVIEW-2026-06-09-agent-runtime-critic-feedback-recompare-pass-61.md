# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-61.md

## Bottom Line

`PASS-61`에서 `run-id` rejection 로그와 레이턴시 정책 임계치의 상관관계를 한 번에 검증해,
`.tmp` 관측 경로 및 수동 모드 분류가 정책 판단에 반영되는지 검증했다.

## Signal

| 항목 | PASS-60 상태 | PASS-61 상태 | 근거 |
|---|---|---|---|
| 관측 로그/경로 검증 | `.tmp` 경로 존재성만 개별 확인 | rejection 로그의 `.tmp` 경로 고정 + 정책 집계/임계치 통합 검사 추가 | `tests/test_template_message_queue.py` |
| 정책 임계치 검증 | `max_warning_count` 분리 테스트만 존재 | rejection 이후 생성된 metric 기록을 정책 모드(`warning-only`)와 조합해 `max_warning_count` 초과/통과 시나리오 모두 검증 | `tests/test_template_message_queue.py` |
| `expected_mode` 집계 연계 | PASS-60에서 집계 검증 추가 | PASS-61에서 rejection 모드(`manual`) + 정책 요약 경로를 동일 플로우로 연결 | `tests/test_template_message_queue.py` |

## Insight

- rejection 로그는 관측 경로(로그 위치)와 정책 요약을 분리해서 보기보다,
  동일 플로우에서 함께 보아야 운영에서 원인 분석이 빠르다.
- `PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT`는 `warning-only` 모드에서 특히 유의미하게 동작하며,
  경고 누적 지표가 임계치 초과 시 즉시 거절 신호와 결합해 모니터링 신뢰도를 높인다.

## Decision

- `tests/test_template_message_queue.py`
  - `test_latency_rejection_log_and_policy_thresholds_are_observably_correlated` 추가
  - rejection 로그의 경로 고정(`.tmp/pass39-latency-metrics-run-id-rejections.jsonl`) 확인
  - 수동 모드(`manual`) rejection + `warning-only` 정책에서 `max_warning_count=1` 실패, `=2` 통과 시나리오 검증
