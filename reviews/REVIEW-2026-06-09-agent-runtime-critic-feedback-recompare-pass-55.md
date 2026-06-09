# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-55.md

## Bottom Line

`PASS-55`에서 `PASS_39` latency 아티팩트 `run_id`를 CI 패턴 기반으로 추적하는 규칙을 테스트 레벨에서 고정했다.

이제 `PASS_39_LATENCY_METRICS_RUN_ID`는 형식 위반 값(공백 포함)에서 즉시 실패하고,
워크플로 템플릿 문자열 자체도 테스트로 감시되므로, 경고/정상(strict) 경로 변경으로 인한 추적성 손실을 조기에 막는다.

## Signal

| 항목 | PASS-54 상태 | PASS-55 상태 | 근거 |
|---|---|---|---|
| run_id 형식 가드 | run_id 값 패턴 서브스트링만 검증 | 공백 포함 run_id에 대한 방어 처리 추가 (`ValueError`), 빈 run_id 기본값 fallback 검증 | `tests/test_template_message_queue.py` |
| 워크플로 템플릿 고정 | 정책 변경만 반영 | CI 템플릿 문자열(warning/main/schedule) 직접 존재 여부 검증 테스트 추가 | `tests/test_template_message_queue.py` |
| 문서화 | PASS-54 기록 완료 | PASS-55로 회귀 규칙 축적 | `reviews/...-pass-55.md` |

## Insight

- run_id는 생성 시점 문자열만 바뀌어도 회귀 탐지가 어렵다. 기본값 fallback + 형식 검사 결합은 누락과 오입력의 두 가지 실패 모드를 분리해 드러낸다.
- 워크플로 템플릿 문자열을 테스트에 직접 박는 방식은 실수로 환경변수 표현식이 손상되었을 때 즉시 적발한다.

## Decision

- PASS-55를 종료하고 `PASS_39_LATENCY_METRICS_RUN_ID`는 다음 두 가지 불변 조건으로 운영:
  1. 공백/개행이 있는 값은 실패 처리
  2. 템플릿 문자열은 `.github/workflows/test.yml`에서 warning/main/schedule 형식으로 존재
- 다음 패스는 `PASS-55` 커버리지를 바탕으로 실패 보고 시 실제 `run-id` 예외를 CI 실행 로그 경로(`.tmp` 아티팩트 + review artifact)로 역추적하는 절차를 추가한다.

## Evidence (pass-55)

- `tests/test_template_message_queue.py`
  - `_build_latency_metric_run_id` 추가
  - `test_latency_metric_invalid_run_id_is_rejected`
  - `test_ci_workflow_latency_run_id_template_patterns_are_declared`
  - 기존 `test_latency_metric_artifact_allows_ci_run_id_variants` 유지(패턴 회귀 확인)

- `tests/test_template_message_queue.py` 수정 내역
  - `_maybe_write_latency_metrics`의 `run_id` 생성 경로가 `_build_latency_metric_run_id`로 중앙화

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-54.md`
- `.github/workflows/test.yml`
- `README.md`
- `tests/test_template_message_queue.py`
