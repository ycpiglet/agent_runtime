# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-114.md

## Bottom Line

`PASS-114`에서는 `agent_runtime release-preflight`의 `main()` 엔트리에서 `--remote-url` 미지정 시 `SystemExit(code=2)`가 발생함을 고정해, 필수 인자 누락 경계가 parser 호출뿐 아니라 실제 CLI 진입점까지 일관되게 유지되도록 했다.

## Signal

| 항목 | PASS-113 상태 | PASS-114 상태 | 근거 |
|---|---|---|---|
| 필수 인자 경계 | `parser.parse_args`에서 `--remote-url` 필수성만 확인 | `main()` 호출 시 `SystemExit(2)`까지 추가 고정 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 문서 정합성 | PASS-113 기록 존재 | PASS-114 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `--remote-url` 누락을 parser 단에서만 검증하면, 실제 CLI 진입점 실패 시그널(`main` 경계)의 정합성이 놓칠 수 있다.
- 본 경계는 사용자 오동작 시점(명령 실행 즉시)에 대한 실패 코드를 명확히 하여 자동화/CI에서 예측 가능한 실패 동작을 보장한다.

## Decision

- `tests/test_release_preflight_warning_summary_source_precedence.py`
  - `test_release_preflight_main_exits_when_remote_url_is_missing` 추가: `cli_module.main(["release-preflight"])` 호출 시 `SystemExit(2)` 발생 고정.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-114 연계(CLI main 엔트리 경계 고정)` 항목 추가.

## Evidence

- `tests/test_release_preflight_warning_summary_source_precedence.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_release_preflight_warning_summary_source_precedence.py -q`
  - Result: `18 passed in 0.50s` (with `PYTHONPATH=src` 환경).
