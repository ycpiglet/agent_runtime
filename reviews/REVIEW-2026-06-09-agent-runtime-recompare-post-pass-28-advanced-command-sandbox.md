# REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox

## Bottom Line

PASS-27에서 남겨둔 `command sandbox` 미결 항목을 한 단계 실해결했다.
`ToolRunner`에 다중 인코딩 감지와 정규화형 토큰 검사(최대 3단계 디코드 추적)를 넣고 회귀 테스트를 추가해,
`agent_runtime` 템플릿 실행 경로의 우회 가능성 중 한 축을 수치화해 닫았다.

## Signal

| 항목 | 이전 상태(PASS-27) | 현재 상태 | 근거 |
|---|---|---|---|
| R1-우회 방어 | `%XX` 위주 단일 패턴 + 일부 shell token | 다중 인코딩(재귀 디코드) + 추가 벡터 테스트로 강화 | `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`, `tests/test_template_agent_tools.py` |
| R2-분산 claim | 남아있음 | 미해결(동일) | `src/agent_runtime/templates/project/scripts/message_queue.py`, `tests/test_template_message_queue.py` |
| 병렬 worker 안정성 | 거의 완화됨 | 유지(단일 winner 보장 테스트 포함) | `tests/test_template_message_queue.py` |
| CI 게이트 | 통과 | 유지 | `tests/test_template_smoke.py`, `tests/test_template_agent_tools.py` |

## What changed in pass-28

- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
  - `_collect_forbidden_tokens` 추가: 원문 + 최대 3회 `urllib.parse.unquote` 디코드 후보에서 금지 토큰/패턴 탐지.
  - `_has_forbidden_token`/`_pretty_forbidden_tokens`가 후보 전개 기반으로 동작하도록 변경.
  - `%0A`, `&`, `${}`류 토큰 외에 인코딩 체인 형태의 은닉 패턴도 탐지되게 확장.
- `tests/test_template_agent_tools.py`
  - `test_run_command_blocks_multistep_decoding_bypass_vectors` 추가.
  - 다중 인코딩 구분자, 혼합 shell 토큰 사례를 포함해 명시적 block 경로 회귀.

## Current Verification

- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_agent_tools.py -q`
  → `14 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests/test_template_message_queue.py tests/test_doctor.py tests/test_template_smoke.py -q`
  → `26 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q`
  → `138 passed`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli sanitize --root . --check`
  → `findings=0`
- `PYTHONPATH=src C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m agent_runtime.cli publish-check --root . --check`
  → `findings=0`

## Remaining Risk

- `R2`(분산/원격 FS claim 정합성 주입 테스트)은 여전히 남아있다.
  - 특히 파일시스템 락 지연/rename 실패/네트워크 지연 환경에서의 lease race 회수 성능은 다음 사이클로 넘긴다.

## Decision

- 다음 주기는 `message_queue`를 **분산/원격 FS 악화 시나리오**에 맞춘 회귀로 진행한다.
- `ToolRunner`는 현재로서 "단일 인코딩 + 중첩 인코딩" 축은 고정된 회귀로 닫혔다고 판단한다.

## Cross-Reference

- `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare.md`
- `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-27-review-cycle.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `tests/test_template_agent_tools.py`
