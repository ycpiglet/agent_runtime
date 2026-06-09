# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-93.md

## Bottom Line

`PASS-93`에서는 strict-ref 정책 판정(`source`, `strict_refs`, `require_send_targets`)을 JSON 아티팩트로 영구 보존해 워크플로우 재현/검증에서 사람이 눈으로 summary만으로 놓칠 수 있는 판단 근거를 보완했다.

## Signal

| 항목 | PASS-92 상태 | PASS-93 상태 | 근거 |
|---|---|---|---|
| 판정 보존성 | summary 출력/로그만 존재 | `.tmp/warning-summary-strict-ref-policy.json` 파일로 판단 근거를 아티팩트에 저장 | `.github/workflows/test.yml` `Write warning-summary strict-ref policy decision artifact` |
| 재현 증빙 | 재현 로그를 수동 확인해야 함 | artifact가 matrix마다 생성되어 외부 리뷰/자동 분석에 즉시 사용 가능 | `.github/workflows/test.yml` artifact 업로드 경로 추가 |
| 문서 정합성 | 정책 재현 가이드 존재 | 테스트 전략/README에 artifact 항목 반영 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`, `README.md` |

## Insight

- summary 텍스트만 남기면 만료/로그 손실 시 판단 근거가 소실될 수 있어, 아티팩트 파일로 저장하는 편이 운영 증빙에 유리하다.
- 다중 matrix 실행에서 동일 스키마(JSON)로 남기면 후속 분석 자동화가 쉬워진다.

## Decision

- `.github/workflows/test.yml`
  - `Write warning-summary strict-ref policy decision artifact` step 추가
  - `warning-summary-strict-ref-policy.json` 생성: `github_event_name`, `github_ref`, `run_id`, `job_attempt`, `matrix_python_version`, `strict_refs_source`, `strict_refs`, `require_send_targets`
  - 아티팩트 업로드 목록에 해당 파일 추가
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-93 연계(워크플로우 실행 증빙 아티팩트)` 항목 추가
- `README.md`
  - 재현 가이드에 artifact 항목 반영

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
- `README.md`

## Validation

- 실환경 workflow_dispatch 실행 후 생성된 아티팩트에서 `warning-summary-strict-ref-policy.json`의 `require_send_targets` 값과 summary/log의 결정값 일치 여부 확인.
