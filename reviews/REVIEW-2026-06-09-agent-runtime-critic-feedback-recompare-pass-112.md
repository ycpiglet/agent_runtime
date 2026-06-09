# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-112.md

## Bottom Line

`PASS-112`에서는 `agent_runtime release-preflight` CLI에서 `tag` 값이 기본값/명시값 모두 `run_preflight`로 정확히 전달되는지 계약을 고정했다.

## Signal

| 항목 | PASS-111 상태 | PASS-112 상태 | 근거 |
|---|---|---|---|
| 경로/체크/Strict-ref | `source/host-root` 및 경로/strict-ref 전달 경계 고정 | `tag` 전달 경계까지 확장 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-111 기록 존재 | PASS-112 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `tag`는 릴리스 플로우에서 핵심 식별자이므로 CLI 기본값과 전달값의 보장이 없어지면 `release-preflight`와 실제 릴리스 대상이 일치하지 않을 수 있다.
- `parser` 기본값과 동치 검증을 이용해 기본값 경계와 전달 경계를 동시에 고정하면 향후 기본 태그 변경 시 회귀 포착이 더 쉬워진다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_cli_default_tag_forwards_to_preflight` 추가: `--tag` 미지정 시 parser 기본값을 그대로 전달.
  - `test_release_preflight_cli_explicit_tag_forwards_to_preflight` 추가: `--tag v2.0.0`이 그대로 전달.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-112 연계(CLI tag 전달 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
