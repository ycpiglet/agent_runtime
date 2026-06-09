# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-91.md

## Bottom Line

`PASS-91`에서는 strict-ref 정책 해석 결과를 `step output`으로 노출해 워크플로우 요약/로그에서 source/값을 추적 가능하게 하고, 문서에 재현 테스트 케이스를 명시해 수동/재사용 실행의 거버넌스 검증성을 높였다.

## Signal

| 항목 | PASS-90 상태 | PASS-91 상태 | 근거 |
|---|---|---|---|
| 적용 근거 노출 | 로그 출력만 존재 (`Resolved ...`) | `resolve_warning_summary_strict_refs` step outputs(`strict_refs_source`, `strict_refs`) + Summary 노트 반영 | `.github/workflows/test.yml` `Resolve warning summary strict refs input` + summary append |
| 추적 용이성 | 입력 소스/적용값이 분리되어 기록되지 않음 | `workflow_call`/`workflow_dispatch` 입력 출처가 step output으로 보존 | `.github/workflows/test.yml` `strict_refs_source` |
| 재현 검증 가이드 | 추상적 제안 수준 | PASS-91 문서에서 기본/수동 입력 케이스를 명시적으로 구분 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 값은 출력되더라도 출처까지 남겨야 오탐/누락 이슈를 운영에서 빠르게 판별한다.
- 재현 실행에서 입력을 비워둔 케이스까지 테스트 케이스로 두면 release/모니터링 경로 강제 적용(`--require-send-targets`) 누락 리스크를 줄일 수 있다.

## Decision

- `.github/workflows/test.yml`
  - `Resolve warning summary strict refs input` 스텝에 `id` 부여 및 `strict_refs_source`, `strict_refs` output 추가
  - 요약 단계에서 출처/규칙을 로그 및 `GITHUB_STEP_SUMMARY`에 기록
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-91 연계(재현 실행 추적성 검증)` 추가: 기본/수동 입력 재현 케이스와 기대 동작 기록

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 실환경 실행에서 `workflow_dispatch`/`workflow_call`로 입력 케이스별 실행 후 Summary에 source/refs가 출력되는지 확인.
- `require-send-targets` 판정과 출력된 strict-ref 정책이 일치하는지 로그로 교차검증.
