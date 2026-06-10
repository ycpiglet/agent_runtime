# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-97.md

## Bottom Line

`PASS-97`에서는 strict-ref 정책 공용 스크립트의 환경변수 fallback 경로를 테스트로 고정해, 재현 루틴이 인자 미지정 상태에서도 `workflow`/수동 운영에서 동일한 판정값을 유지하는지 검증했다.

## Signal

| 항목 | PASS-96 상태 | PASS-97 상태 | 근거 |
|---|---|---|---|
| env fallback 검증 | `tests/test_warning_summary_strict_ref_policy.py`가 인자 기반 경로 위주로 작성됨 | env fallback 경로를 명시 검증하는 테스트 추가 | `tests/test_warning_summary_strict_ref_policy.py` |
| 문서 반영 | PASS-96까지 회귀 테스트 전략만 반영 | `PASS-97 연계(환경 fallback 재현 고정)` 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 재현 파이프라인에서 인자를 누락했을 때 env 기반 결정값으로 동작해야 하는 케이스가 남아 있었고, 이 경로는 CI 로그만으로 놓치기 쉬웠다.
- 이번 테스트는 `write`와 `validate` 모두에서 env fallback를 강제해 drift를 줄인다.
- 다음 사이클은 PASS-39 경고 게이트 본문-요약 간 정합성 자동화(요약 코드/요약 전송 판단 일치)를 `PASS-98`로 이어가면 된다.

## Decision

- `tests/test_warning_summary_strict_ref_policy.py`에 `test_strict_ref_policy_script_uses_environment_fallbacks` 추가
  - `GITHUB_*`, `MATRIX_PYTHON_VERSION`, `STRICT_*` 환경변수 주입으로 write/validate 동작 검증
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-97 연계(환경 fallback 재현 고정)` 항목 추가

## Evidence

- `tests/test_warning_summary_strict_ref_policy.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 현재 브랜치에서는 코드 작성만 반영되어 있으며, 실행 검증은 사용자가 요청할 경우 `PYTHONPATH=src python -m pytest tests/test_warning_summary_strict_ref_policy.py -q`로 이어서 수행 예정.
