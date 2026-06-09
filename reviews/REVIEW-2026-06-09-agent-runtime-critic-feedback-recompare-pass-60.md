# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-60.md

## Bottom Line

`PASS-60`에서 `run-id` rejection 로그의 `expected_mode` 집계를
실패 경로별로 검증하도록 보강해 CI/수동 구분이 바로 확인되도록 했다.

## Signal

| 항목 | PASS-59 상태 | PASS-60 상태 | 근거 |
|---|---|---|---|
| `expected_mode` 분류 규칙 | `run-*`이면 무조건 `ci`로 분류 | 공백 포함 `run-*`는 `manual`, 정상 `run-*`는 `ci`, 나머지는 `manual`로 분류 | `tests/test_template_message_queue.py` |
| 집계 테스트 | 분포값 하드코딩(수동 개수/CI 개수만 비교) | 집계뿐 아니라 각 `run_id`별 `expected_mode` 정합성까지 검증 | `tests/test_template_message_queue.py` |
| 리뷰 아티팩트 | PASS-59 리뷰 없음 | PASS-60 리뷰 추가 | `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-60.md` |

## Insight

- `run-*` 문자열 자체보다 rejection 사유/포맷 정합성이 중요하다. 공백 포함 ID를 수동 모드로 분리하면 잘못된 CI 형식과 구분이 명확해진다.
- 집계 테스트를 `Counter` 기반으로 `expected_mode`를 `run_id`별 기대값과 결합하면 로그 회귀를 빠르게 탐지할 수 있다.

## Decision

- `tests/test_template_message_queue.py`
  - `_expected_mode_for_run_id` 분류 규칙을 명시적으로 보강
  - `test_latency_run_id_rejection_modes_are_aggregatable`에서 `run_id`별 기대 `expected_mode` + `expected_mode` 집계 동시 검증
- PASS-60 리뷰 문서를 생성해 변경 이력을 정리
