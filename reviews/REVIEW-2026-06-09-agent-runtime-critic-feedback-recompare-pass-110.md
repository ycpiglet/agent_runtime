# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-110.md

## Bottom Line

`PASS-110`에서는 `agent_runtime release-preflight` CLI가 strict-ref 입력을 `run_preflight`로 정확히 전달하는지 계약을 고정했다.

## Signal

| 항목 | PASS-109 상태 | PASS-110 상태 | 근거 |
|---|---|---|---|
| CLI 전달 경계 | `--check` 전달 경계만 고정 | `warning_summary_gate_strict_refs` 미지정/빈 문자열 전달 경계 추가 고정 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-109 기록 존재 | PASS-110 항목을 전략 문서에 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `warning_summary_gate_strict_refs`는 `None`/`""` 구분이 정책 폴백/우선순위의 핵심이므로, 함수 단위 단정만으로는 CLI 진입점 경계 누수를 막지 못한다.
- CLI 레이어에서 값 그대로 전달되는지를 고정하면 운영 입력(`--warning-summary-gate-strict-refs`)과 `run_preflight` 계약이 양방향으로 안전하게 고정된다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_cli_default_strict_refs_is_none` 추가: strict-ref 옵션 미지정 시 `run_preflight`가 `None` 받음.
  - `test_release_preflight_cli_empty_string_strict_refs_forwards_to_preflight` 추가: `--warning-summary-gate-strict-refs ""`가 `""`로 전달.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-110 연계(CLI strict-ref 전달 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
