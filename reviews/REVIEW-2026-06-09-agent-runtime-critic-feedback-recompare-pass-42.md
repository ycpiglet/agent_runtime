# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-42.md

## Bottom Line

`PASS-42`에서는 지연 KPI 아티팩트를 CI/운영 정책으로 연결하기 위한 최소 결정 규칙을 추가했다.

`PASS-39~41`로 축적한 기록 레이어에 대해 `warning` 레코드 처리 전략을 환경변수로 바인딩할 수 있게 하여, 향후 워크플로우에서 `warning-only`와 `fail-on-warning` 모드 전환이 가능하도록 했다.

## Signal

| 항목 | PASS-41 상태 | PASS-42 상태 | 근거 |
|---|---|---|---|
| 경고 정책 인터페이스 | 집계만 존재 | 정책 평가 유틸 추가 | `_evaluate_latency_policy` 추가 |
| 정책 모드 | 미정의 | 환경변수 기반 모드 파싱 추가 | `_policy_mode_from_env` 추가 |
| 실행 가능성 | 요약만 반환 | pass/fail + reason 리포트 반환 | `_evaluate_latency_policy`가 정책별 `passed/report`를 반환 |
| 정책 검증 | 없음 | 기본/실패/최대 경고 상한 테스트 추가 | `test_latency_policy_allows_warning_mode_by_default`, `test_latency_policy_fail_mode_blocks_warning_records`, `test_latency_policy_max_warning_count_guard` 추가 |

## Insight

- 정책을 코드에 직접 얽히지 않고, `PASS_39_LATENCY_POLICY`와 `max_warning_count` 파라미터로 제어하면 CI에서 경고 민감도 조절이 쉬워진다.
- 경고 레코드의 `max_warning_count`까지 포함해 다중 경고가 누적되는 시나리오를 쉽게 가드할 수 있다.
- 다음 사이클은 이 정책 함수의 반환값을 실제 워크플로우/릴리즈 게이트 단계(예: warning-only 기본, fail-on-warning 점진 도입)에 매핑해야 한다.

## Decision

- `PASS-42`는 경고 메트릭을 CI 정책과 연결하는 핵심 뼈대를 완성했다.
- 보고서 순서를 유지해 PASS-42 리뷰를 완료했으며, 다음 순환은 실제 배포 게이트/리포트 아티팩트 사용 규칙을 문서 + 워크플로우로 고정한다.

## Evidence (pass-42)

- `tests/test_template_message_queue.py`
  - `_evaluate_latency_policy` 추가
  - `_policy_mode_from_env` 추가
  - `test_latency_policy_allows_warning_mode_by_default`
  - `test_latency_policy_fail_mode_blocks_warning_records`
  - `test_latency_policy_max_warning_count_guard`

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-41.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-40.md`
- `tests/test_template_message_queue.py`
