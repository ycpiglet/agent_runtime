# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-31.md

## Bottom Line

`PASS-30`에서 남겨둔 `R1`/`R2` 잔여 항목을 검증까지 진행해, 이번 사이클에서는
`agent_tools` 우회 차단(고급 인코딩 포함)과 `message_queue` claim 재시도 경로가
실제 테스트에서 안정적으로 통과함을 확인했다.
`PASS-31` 기준으로는 미결 리스크를 "추가 fuzz 확장 필요"로만 축소하고,
현재 스냅샷에서 실행 블로커는 해소되었다.

## Signal

| 항목 | PASS-30 상태 | PASS-31 상태 | 근거 |
|---|---|---|---|
| 템플릿 self-contained | ✅ 닫힘 | ✅ 유지 | 기존 증적 유지 |
| 템플릿 CI 누락 | ✅ 닫힘 | ✅ 유지 | 기존 증적 + `tests` 통과 |
| ToolRunner command sandbox (R1) | 🔧 진행 | ✅ 확장 통과 | `%uXXXX`, `\uXXXX`, 이중/다중 디코드 변형 테스트 통과 |
| 병렬 claim 정합성 | ✅ 유지 | ✅ 유지 | 기존 병렬/회수 테스트 통과 |
| 분산/원격 FS robust 처리 (R2) | 🔧 진행 | ✅ 검증 통과 | transient create-failure 재시도 테스트 통과 |
| 의존성 계약 | ✅ 닫힘 | ✅ 유지 | 기존 증적 유지 |

## Evidence (pass-31)

- 단일 보강 테스트:
  - `tests/test_template_agent_tools.py` 전체: `30 passed`
  - `tests/test_template_message_queue.py` 전체: `15 passed`
  - `tests/test_template_agent_tools.py::test_run_command_blocks_unicode_escape_bypass_vectors`: 통과
- 전체 회귀:
  - `tests -q`: `141 passed`
- 템플릿/도구 보안/런타임 게이트:
  - `agent_runtime.cli sanitize --root . --check`: `findings=0`
  - `agent_runtime.cli publish-check --root . --check`: `findings=0`
  - `agent_runtime.cli publish-bundle --source . --dest .tmp/public-source-pass31 --check`: `findings=0`

## Implementation delta since pass-30

- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
  - `\uXXXX` 문구의 docstring 이스케이프 처리.
- `tests/test_template_message_queue.py`
  - 전역 `open` 시뮬레이션을 안전하게 `builtins.open` 대상으로 변경.
  - 메시지 큐 경합 보강 테스트는 유지.

## Remaining risk

- `R1`은 실무 플랫폼 조합에서 추가 fuzzer 조합으로 확장 예정.
- `R2`는 SMB/NFS/네트워크 FS 환경에서의 지연분포 기반 지표 수집을 다음 사이클에서 반영 가능.

## Decision

- `PASS-31`에서는 현재 미요구 결함을 기준으로 "차단/회귀는 닫힘"으로 판단.
- 다음 사이클은 `PASS-32`에서:
  1) `message_queue`에 분산 파일시스템 특화 지연 주입 테스트를 추가,
  2) `agent_tools` 금지 패턴을 seed 기반 fuzz로 자동 확장,
  3) 기존 review 체인에 cycle evidence만 갱신.

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-30.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_agent_tools.py`
- `tests/test_template_message_queue.py`
