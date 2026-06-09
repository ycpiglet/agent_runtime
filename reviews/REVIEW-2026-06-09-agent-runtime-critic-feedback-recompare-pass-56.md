# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-56.md

## Bottom Line

`PASS-56`에서는 `PASS_39_LATENCY_METRICS_RUN_ID`를 CI/수동 케이스로 구분해 정규식 기반으로 검증하도록 강화했다.

`run-` 접두어를 사용하는 값은 CI 템플릿 규칙에 맞아야만 통과하고,
`manual-*` 등 수동 식별자는 그대로 허용하도록 하여 실패 원인(형식 오입력)을 조기에 탐지한다.

## Signal

| 항목 | PASS-55 상태 | PASS-56 상태 | 근거 |
|---|---|---|---|
| run_id 형식 가드 | 공백 검사 + CI 템플릿 문자열 존재 확인 | `run-` 값에 대한 CI 정규식 유효성 검사 추가 | `tests/test_template_message_queue.py` |
| CI 템플릿 분기 구분 | 샘플 패턴 저장 순서/서브스트링 점검 | warning/main/schedule 분기별 모드 판별 함수 테스트 추가 | `tests/test_template_message_queue.py` |
| 수동/오류 케이스 | manual 검증 미정의 | 수동 식별자 허용 및 잘못된 `run-` 패턴 즉시 실패 추가 | `tests/test_template_message_queue.py` |

## Insight

- `run-` 접두어는 CI 템플릿 패턴과 충돌 가능성이 커서, 단순 문자열 길이/접두사 검사보다 분기별 정규식 분리가 훨씬 강한 경계가 된다.
- 기존처럼 공백 검사만으로는 `run-1234-something` 같은 구조적 오입력을 못 잡는데, 패턴-전용 가드로 이를 보완할 수 있다.

## Decision

- `PASS-39` 메트릭 아티팩트 run-id는 `_build_latency_metric_run_id`에서 다음을 적용:
  - 공백/개행은 실패
  - `run-` 접두어 값은 warning/main/schedule 정규식 중 하나와 일치해야 함
  - 그 외(`manual-*`)은 기존 동작(빈 값 fallback) 유지
- PASS-56 회귀 테스트를 추가해 CI 샘플 3종의 모드 구분과, 잘못된 `run-` 패턴 및 manual 케이스의 동작을 동시 검증

## Evidence (pass-56)

- `tests/test_template_message_queue.py`
  - `_CI_WARNING_RUN_ID_RE`, `_CI_MAIN_RUN_ID_RE`, `_CI_SCHEDULE_RUN_ID_RE` 추가
  - `_classify_latency_run_id`, `_assert_latency_metric_run_id_is_expected` 추가
  - `_build_latency_metric_run_id`를 CI 패턴 기반 검증 경로로 보강
  - `test_latency_run_id_patterns_differentiate_ci_and_manual_cases` 추가
    - valid: warning/main/schedule 패턴 3종
    - invalid: 잘못된 `run-` 패턴 3종
    - manual: `manual-*` 패턴 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-55.md`
- `tests/test_template_message_queue.py`
- `.github/workflows/test.yml`
