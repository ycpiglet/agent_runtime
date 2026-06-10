# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-102.md

## Bottom Line

`PASS-102`에서는 `release-preflight`의 strict-ref 정책을 워크플로우에서 직접 CLI arg(`--warning-summary-gate-strict-refs`)로 전달하도록 고정해, 정책 결정 지점과 실제 검사 지점의 입력 경로를 일치시켰다.

## Signal

| 항목 | PASS-101 상태 | PASS-102 상태 | 근거 |
|---|---|---|---|
| 전달 경로 | env fallback 기반 호출 | CLI 직접 전달 + 테스트 고정 | `.github/workflows/test.yml` |
| 검증 고정 | workflow 문자열에는 `release-preflight` 실행만 검증 | CLI strict-ref arg 존재를 고정 검증 | `tests/test_inventory_sync_sanitize.py` |
| 사용 가이드 | 기본 CLI 항목만 노출 | README에 strict-ref 옵션 사용 예시 추가 | `README.md` |

## Insight

- `release-preflight` 호출부가 env fallback에만 의존하면, `--warning-summary-gate-strict-refs`와 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`의 경로가 분리되어 추적성이 약해질 수 있다.
- 동일 워크플로우 내에서 정책 해석 출력(`STRICT_REFS`)을 그대로 CLI로 전달하면, 실제 점검 동작과 워크플로우 로그/요약의 일치성을 명시적으로 보장할 수 있다.

## Decision

- `.github/workflows/test.yml`
  - `release-preflight` 실행 단계에 `--warning-summary-gate-strict-refs "${{ steps.resolve_warning_summary_strict_refs.outputs.strict_refs }}"` 추가.
- `tests/test_inventory_sync_sanitize.py`
  - `test_github_workflow_runs_publish_gates_against_clean_bundle`에 CLI strict-ref arg 존재 검증 추가.
- `README.md`
  - `release-preflight --warning-summary-gate-strict-refs` 사용 예시 라인을 명시.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-102` 연계 항목 추가.

## Evidence

- `.github/workflows/test.yml`
- `tests/test_inventory_sync_sanitize.py`
- `README.md`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 변경 검증은 문서/워크플로우/테스트 고정성 수정으로 기록되었으나, 이번 단계에서 코드 실행 테스트는 별도 수행하지 않았습니다.
