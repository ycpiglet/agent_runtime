# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-89.md

## Bottom Line

`PASS-89`에서는 `workflow_call`/`workflow_dispatch`에서 전달되는 `warning_summary_gate_strict_refs`를 `\\r` 제거 후 정규화해 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`로 반영하고, 반영된 값을 요약 단계 로그에 출력해 재현 실행의 정책 drift 추적성을 높였다.

## Signal

| 항목 | PASS-88 상태 | PASS-89 상태 | 근거 |
|---|---|---|---|
| 입력 정규화 | 입력값 사용 시 정규화 부재 | `\\r` 정규화(`CRLF -> LF`) 적용 | `.github/workflows/test.yml` Resolve step |
| 폴백 동작 | 비입력 이벤트는 빈값 처리 후 기본값 유지 가정 | 비입력 이벤트의 기본값을 job env에서 직접 사용하여 우발적 공백/빈 값 의존성 제거 | `.github/workflows/test.yml` `else` 분기 업데이트 |
| 추적성 | 적용 정책 로그 미노출 | 적용된 strict-ref 정책 문자열 출력 로그 추가 | `.github/workflows/test.yml` `Resolved PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 출력 |

## Insight

- 워크플로우 입력은 호출자 환경에 따라 개행/공백 표현이 다를 수 있어, 정규화하지 않으면 prefix match가 오작동할 수 있다.
- 비입력 이벤트에서 입력값을 빈 문자열로 두는 기존 처리 대신 기존 job env를 그대로 기준으로 삼으면 정책 재사용성이 유지된다.
- 정책 문자열을 런타임 로그에 남기면, 재현/재실행 시 어떤 strict-ref 집합이 실제 적용됐는지 즉시 확인된다.

## Decision

- `.github/workflows/test.yml`
  - `Resolve warning summary strict refs input` 스텝에서 `workflow_call`/`workflow_dispatch`이 아닌 경우에도 기본 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`를 읽어 폴백
  - 입력 문자열의 `\r` 제거 후 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`에 재주입
  - 적용 정책 문자열 출력 로그 추가
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-89 항목을 통해 정규화/추적성 보강 문서화

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 실행 기반: 워크플로우 호출/수동 실행에서 정책 문자열 출력 로그 존재 여부 및 `--require-send-targets` 판별 변화 확인 필요.
- 정적: `git diff`로 변경된 스텝/문서 반영 범위를 확인.
