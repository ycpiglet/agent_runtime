# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-111.md

## Bottom Line

`PASS-111`에서는 `agent_runtime release-preflight` CLI에서 경로 인자 전달 계약을 고정했다. `source/host-root` 미지정 시 `Path.cwd()`로 기본값이 전달되고, 사용자 지정 경로 역시 `run_preflight`로 그대로 전달됨을 회귀 고정했다.

## Signal

| 항목 | PASS-110 상태 | PASS-111 상태 | 근거 |
|---|---|---|---|
| 경로 계약 | strict-ref 경계만 고정 | `source`/`host-root` 기본값 + 모든 경로 인자 명시값 전달을 고정 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-110 기록 존재 | PASS-111 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `run_preflight`에 값이 도달하기 전 CLI 레이어에서 경로 기본값이 바뀌면, 현재 함수 계약은 그대로 있어도 실제 실행 경로가 변경될 수 있다.
- 기본값(CWD) 및 전체 경로 인자 전달을 함께 고정하면, 릴리스 프리플라이트의 입력 계약을 CLI부터 종료 코드 계약까지 단일 플로우로 검증할 수 있다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_cli_default_paths_forward_to_preflight` 추가: `--source/--host-root/디렉토리 인자 미지정` 시 기본값 `Path.cwd()` 계열 경로가 그대로 전달되는지 확인.
  - `test_release_preflight_cli_explicit_paths_forward_to_preflight` 추가: 모든 경로 인자 지정값이 그대로 전달되는지 확인.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-111 연계(CLI 경로 전달 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
