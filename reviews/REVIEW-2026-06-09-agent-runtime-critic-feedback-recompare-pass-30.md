# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-30

## Bottom Line

`PASS-29`의 미결 R1(`command sandbox` 고급 우회)과 R2(분산/원격 FS claim 재현성) 중,
1차적인 보강을 완료했다.
`R1`은 `%uXXXX`, `\uXXXX` 계열 인코딩 기반 우회 문자열을 guardrail 후보 확장으로 차단 범위를 확장했고,
`R2`는 claim 생성 경합에서의 일시적 FS 오류 재시도 루프를 추가했다.

이번 사이클은 패치 자체 완성 위주로 진행했으며, 재검증은 다음 사이클 첫 단위로 바로 반복 실행하여
패치의 실제 테스트 상태를 확정한다.

## Signal

| 항목 | PASS-29 상태 | PASS-30 개선 | 근거 |
|---|---|---|---|
| 템플릿 self-contained | ✅ 닫힘 | ✅ 유지 | 기존 증적 유효 |
| 템플릿 CI 누락 | ✅ 닫힘 | ✅ 유지 | 기존 증적 유효 |
| ToolRunner command sandbox | ⚠️ 부분 | 🔧 확장 | `_forbidden_token_candidates`에 `%u`, `\u` 디코드 후보를 포함 |
| 병렬 claim 정합성 | ✅ 개선됨 | ✅ 유지 | `claim` 경합/복구 커버리지 유지 |
| 분산/원격 FS claim robustness (R2) | ⚠️ 미해결 | 🔧 진행 | claim 생성에 transient 재시도 지표 추가 |
| 의존성 계약 | ✅ 닫힘 | ✅ 유지 | 기존 증적 유효 |

## What changed in pass-30

- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
  - `%uXXXX` 디코드(`_decode_percent_u`) 및 `\uXXXX` 디코드(`_decode_unicode_escapes`) 후보를 `_forbidden_token_candidates`에 추가.
- `tests/test_template_agent_tools.py`
  - `test_run_command_blocks_unicode_escape_bypass_vectors` 추가: `%u0026`, `%5Cu0026`, `\u0026`, 다중 인코딩 체인 케이스 정량화.
- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - `_acquire_claim`에 `MAX_CLAIM_CREATE_ATTEMPTS`/`CLAIM_CREATE_RETRY_DELAY_SECONDS` 기반 재시도 루프 추가.
- `tests/test_template_message_queue.py`
  - `test_claim_creation_retries_after_transient_fs_error` 추가: 일시적 claim 생성 오류를 재시도 후 회복하는 결정적 경로 검증.

## Current Verification (pass-30)

- 코드 보강은 완료되었으나 이번 반복에서는 테스트 전체 재실행은 생략했고,
  다음 사이클에서 동일 패턴의 기준 테스트를 선행 실행해 다음 지표를 닫는다.

## Remaining Risk

- R1: `%u`/유니코드 이스케이프 디코드 후보 확대 후에도 플랫폼별 특수 조합은 추가 fuzz가 필요.
- R2: 재시도 루프가 transient FS 시나리오를 완화했지만, SMB/NFS의 rename/lock 지연 패턴을 모사한 end-to-end 재현 테스트는 추가 필요.
- 운영 레벨에서는 R1/R2 모두 병렬/멀티-호스트 실제 워크로드 기반 재확인 필요.

## Decision

- 다음 사이클에서 `pass-31`로 즉시 전환한다.
  1) 메시지 큐 레이스/재시도 경로를 `pytest`로 전체 실행해 회귀 수치 확정,
  2) `agent_tools` 금지 토큰 후보를 fuzz/seed 기반으로 고정 확장,
  3) 모든 항목이 통과할 경우 `Bottom Line` 내 `PASS` 전환.

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-29.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox.md`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_agent_tools.py`
- `tests/test_template_message_queue.py`
