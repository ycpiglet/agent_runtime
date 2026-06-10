# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-92.md

## Bottom Line

`PASS-92`에서는 strict-ref 정책 해석과 `require-send-targets` 판정을 한 단계에서 계산한 뒤 workflow summary/로그에 함께 출력해, 재현 실행에서 판별/적용 불일치 가능성을 줄였다.

## Signal

| 항목 | PASS-91 상태 | PASS-92 상태 | 근거 |
|---|---|---|---|
| 판별 중복 | 요약 단계에서 별도 prefix loop 수행 | `Resolve` 스텝에서 `require_send_targets`를 계산해 output으로 공유 | `.github/workflows/test.yml` `resolve_warning_summary_strict_refs` |
| 로그/요약 추적 | source/refs 출력만으로 판정 신호가 간접적 | `source`, `strict_refs`, `require_send_targets`를 summary/log에서 함께 출력 | `.github/workflows/test.yml` `Summarize template warning-summary gate reports` |
| 실행 재현 가시성 | 테스트 전략에 검증 가이드만 존재 | README에 `workflow_dispatch` 재현 명령과 기대 출력 항목 추가 | `README.md` `warning-summary strict-ref policy inputs` |

## Insight

- prefix-match 판별을 두 군데에서 실행하면 실수로 조건이 어긋날 수 있어, 해석 스텝에서 단일 계산 후 공유하는 편이 안정적이다.
- `require-send-targets`를 step output으로 고정하면 summary/로그/재현 체크를 하나의 판단 근거로 묶을 수 있다.
- 운영 문서(README)에 재현 명령을 두면 리뷰/인수 단계에서 사람-재현 루프가 줄어든다.

## Decision

- `.github/workflows/test.yml`
  - `resolve_warning_summary_strict_refs`에서 `require_send_targets` 산출 후 `GITHUB_OUTPUT`에 기록
  - 요약 단계에서 loop 재판별 제거 후 output 기반으로 `--require-send-targets` 추가
  - Summary에 `source`, `strict_refs`, `require-send-targets`를 기록
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-92 연계(단일 판별 채널 단일화)` 추가
- `README.md`
  - `workflow_dispatch` 재현 명령 및 기대 로그 항목 추가

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
- `README.md`

## Validation

- 실환경 실행 기반으로 `workflow_dispatch`에서 입력 값을 바꿔 summary의 `source`/`strict_refs`/`require_send_targets`와 실제 `--require-send-targets` 동작 일치 여부를 검증하는 것을 다음 반복에서 수행.
