# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-104.md

## Bottom Line

`PASS-104`에서는 `tests/test_inventory_sync_sanitize.py`에서 `Check release preflight` 블록을 분리 점검해, strict-ref 입력이 `--warning-summary-gate-strict-refs "${{ steps.resolve_warning_summary_strict_refs.outputs.strict_refs }}"`로만 전달되고 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` env 문자열이 블록에 노출되지 않음을 고정했다.

## Signal

| 항목 | PASS-103 상태 | PASS-104 상태 | 근거 |
|---|---|---|---|
| 실행 블록 정합성 | CLI 예시 문서화만 반영 | 워크플로우 실행 블록에 CLI 값 존재와 env 미노출을 같이 검증 | `tests/test_inventory_sync_sanitize.py` |
| 기록 정렬 | PASS-103 항목 존재 | PASS-104 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `release-preflight`가 실제로 CLI 값을 받는지 확인하려면, 커맨드 문자열 전체가 아닌 실행 블록 단위로 고정해야 다른 단계의 env 정의와 오탐을 줄일 수 있다.
- 이 정합성 체크는 정책 계산·해석·실행 입력 경로가 서로 일치하는지, 운영에서 재현 가능한 형태로 유지하는 데 기여한다.

## Decision

- `tests/test_inventory_sync_sanitize.py`
  - `test_github_workflow_runs_publish_gates_against_clean_bundle`에서 `- name: Check release preflight` 블록을 추출해 검증.
  - 해당 블록에 `--warning-summary-gate-strict-refs "${{ steps.resolve_warning_summary_strict_refs.outputs.strict_refs }}"` 존재 검증.
  - 동일 블록에서 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 미포함 검증.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-104 연계(CI release-preflight 호출 블록 경로 고정)` 항목 추가.

## Evidence

- `tests/test_inventory_sync_sanitize.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 단계에서는 별도 수행하지 않았습니다.
