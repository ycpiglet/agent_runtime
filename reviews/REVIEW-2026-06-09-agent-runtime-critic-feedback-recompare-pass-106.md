# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-106.md

## Bottom Line

`PASS-106`에서는 `run_preflight`의 strict-ref 입력 우선순위에서 CLI 빈 문자열이 env fallback를 덮어쓰지 않도록 전달되도록 유지됨을 테스트로 고정했다.

## Signal

| 항목 | PASS-105 상태 | PASS-106 상태 | 근거 |
|---|---|---|---|
| 우선순위 경계 | CLI/ENV precedence 테스트 존재 | CLI 빈 문자열(`""`)이 env fallback를 덮는 시나리오 추가 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 항목 기록 | PASS-105까지만 기록 | PASS-106 항목 추가로 테스트-문서 추적성 유지 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 기존 우선순위 계약에서 `None`은 env fallback이지만, 빈 문자열은 명시적 입력으로 해석되는 게 일관적이다.
- CLI 사용자가 값을 의도적으로 비워 전달하는 상황에서도 env가 대체로 쓰이는 경우를 막아 재현성/기대 동작을 명확히 할 수 있다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_cli_empty_string_disables_env_fallback` 추가.
  - env에 값이 있는 상태에서 `warning_summary_gate_strict_refs=""`가 그대로 plan 입력으로 전달되는지 확인.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-106 연계(CLI 빈 문자열 우선 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
