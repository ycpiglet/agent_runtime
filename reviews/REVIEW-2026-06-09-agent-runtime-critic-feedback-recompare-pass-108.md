# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-108.md

## Bottom Line

`PASS-108`에서는 `agent_runtime release-preflight`의 `run_preflight`가 `check=False`일 때 finding이 있어도 종료코드 `0`을 유지하도록 계약을 고정했다.

## Signal

| 항목 | PASS-107 상태 | PASS-108 상태 | 근거 |
|---|---|---|---|
| 종료코드 경계 | `check=True` 기준으로 0/1 분기 고정 | `check=False`에서도 종료코드가 `0`인지 테스트로 고정 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-107까지 기록 | PASS-108 항목을 전략 문서에 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 기존 회귀 방어는 `check=True` 경로만 다루었고, `check=False`는 별도 계약이 없어 나중에 기본값 변경이 섞일 여지가 있었다.
- `check` 플래그의 의미를 종료코드 계약으로 분리해 두면, 경량 검토(`--check` 비사용)와 실제 차단 실행을 구분해 운영 판단 오류를 줄일 수 있다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_run_preflight_returns_zero_when_check_is_disabled` 추가 (`check=False`, finding 존재 시 `0` 기대).
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-108 연계(비-체크 모드 종료코드 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
