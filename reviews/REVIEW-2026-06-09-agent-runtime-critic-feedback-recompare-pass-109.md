# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-109.md

## Bottom Line

`PASS-109`에서는 `agent_runtime release-preflight` CLI 진입점에서 `--check` 플래그 전달 경계를 고정해, 기본 실행은 `check=False`, `--check` 사용 시 `check=True`가 `run_preflight`에 정확히 전달되도록 검증했다.

## Signal

| 항목 | PASS-108 상태 | PASS-109 상태 | 근거 |
|---|---|---|---|
| 종료 코드 계산 범위 | `run_preflight` 반환값 경계 고정 | CLI 진입점 전달 경계 추가 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-108 기록 존재 | PASS-109 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `check` 경계는 `run_preflight`만 고정해두면 CLI 기본값 변화나 파서 변경이 실제 실행 모드에 영향을 주는 것을 놓칠 수 있다.
- `--check` 플래그 전달 계약을 UI 진입점까지 고정하면, 운영자가 의도한 non-blocking/checking 모드가 실행되어야 할 경계가 분명해진다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_cli_default_check_is_non_blocking` 추가 (기본 실행 시 `check=False` 전달 확인).
  - `test_release_preflight_cli_check_flag_forwards_to_preflight` 추가 (`--check` 지정 시 `check=True` 전달 확인).
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-109 연계(CLI check 플래그 전달 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
