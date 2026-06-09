# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-113.md

## Bottom Line

`PASS-113`에서는 `agent_runtime release-preflight` CLI의 `remote-url` 계약을 고정해, 실행 경로의 필수 인자 전달 및 누락 실패를 동시에 회귀 고정했다.

## Signal

| 항목 | PASS-112 상태 | PASS-113 상태 | 근거 |
|---|---|---|---|
| 필수 인자/전달 | `tag` 전달 경계까지 확장 | `remote-url` 전달과 parser 필수 인자 경계 추가 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-112 기록 존재 | PASS-113 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `release-preflight`는 원격 URL이 핵심 실행 인자이므로 CLI 경로 계약에서 이를 고정하지 않으면 기본값 오인식 또는 parser 규약 누수로 실제 실행 대상이 어긋날 수 있다.
- 전달 계약의 완결은 `run_preflight` 직접 단위 경계만으로는 부족하며, parser 레벨의 필수 인자 실패 경계까지 잡아야 한다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_cli_remote_url_forwards_to_preflight` 추가: `remote-url`이 그대로 `run_preflight`에 전달됨.
  - `test_release_preflight_cli_remote_url_required` 추가: `release-preflight` 명령에서 `remote-url` 누락 시 `SystemExit` 발생.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-113 연계(CLI remote-url 전달/필수성 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
