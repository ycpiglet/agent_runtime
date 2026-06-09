# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-90.md

## Bottom Line

`PASS-90`에서는 `workflow_call`/`workflow_dispatch`에서 전달되는 `warning_summary_gate_strict_refs`가 비어 있거나 공백만 있는 경우 기본 strict-ref 정책으로 안전하게 폴백되도록 보강하고, 라인 단위 공백/빈 라인을 정규화해 `--require-send-targets` prefix match 신뢰도를 높였다.

## Signal

| 항목 | PASS-89 상태 | PASS-90 상태 | 근거 |
|---|---|---|---|
| 빈 입력 처리 | `workflow_call`/`workflow_dispatch` 입력이 비면 빈 값 그대로 반영될 수 있음 | 기본값 env를 보관해 비어있으면 fallback | `.github/workflows/test.yml` `Resolve warning summary strict refs input` |
| 라인 정규화 | `\r` 제거만 수행 | 좌우 공백 trim + 빈 라인 제거까지 추가 | `.github/workflows/test.yml` `sed` 기반 정규화 파이프라인 |
| 추적성 | 입력 정책 출력은 존재 | 기존 로그 유지하고, 정규화된 정책이 로그에 반영되도록 동작 지속 | `.github/workflows/test.yml` 출력 스텝 |

## Insight

- 워크플로우 input이 오염되었을 때 strict-ref 집합이 비정상적으로 비워지면 엄격 경로 판별이 사라져 release 알림 보강이 누락될 수 있다.
- 라인 trim/빈 줄 제거는 사용자가 수동/재사용 호출 시 들어오는 포맷 차이를 흡수해 정책 경로의 false-negative를 줄인다.

## Decision

- `.github/workflows/test.yml`
  - `DEFAULT_STRICT_REFS` 캐시 후 입력이 비거나 빈줄만 있을 때 기본 정책으로 폴백
  - `sed`로 CR 제거, 라인 trim, 빈 줄 제거 정규화
  - 정규화된 strict-ref 문자열을 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`로 재주입
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-90 연계` 항목 추가

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 실행 검증은 GitHub Workflow dispatch/call 환경에서 입력 문자열의 빈/공백/개행 형태별 동작을 확인해 수행.
- 현재 단계는 정적 변경 근거를 기록한 상태이며, 실환경 실행에서는 `Resolved PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 로그로 회귀를 추적.
