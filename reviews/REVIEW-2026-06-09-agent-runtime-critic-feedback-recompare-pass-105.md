# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-105.md

## Bottom Line

`PASS-105`에서는 `tests/test_inventory_sync_sanitize.py`의 `Check release preflight` 검증을 블록 파싱 헬퍼 기반으로 보강해, workflow 문자열 분할 오탐을 줄이고 `release-preflight` 실행 헤더 정합성을 고정했다.

## Signal

| 항목 | PASS-104 상태 | PASS-105 상태 | 근거 |
|---|---|---|---|
| 검증 안정성 | `workflow.split("- name: ...")` 기반 분할 의존 | `_extract_workflow_step(...)`로 블록 범위 추출 후 검증 | `tests/test_inventory_sync_sanitize.py` |
| 블록 정합성 | strict-ref CLI 존재/환경 문자열 미노출만 확인 | `PYTHONPATH=.tmp/public-source/src python -m agent_runtime.cli release-preflight` 헤더도 동일 블록 검증 | `tests/test_inventory_sync_sanitize.py` |
| 정렬 기록 | PASS-104 항목만 존재 | PASS-105 항목 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 단순 문자열 검색보다 스텝 경계 파싱이 정확해질수록, workflow 변경시도에서 의도치 않은 블록 간섭 가능성을 줄인다.
- 실행 헤더까지 함께 고정하면, CLI 전달 인자 검증이 `workflow 내 존재 여부`를 넘어 `실행 호출 블록 정합성`으로 강화된다.

## Decision

- `tests/test_inventory_sync_sanitize.py`
  - `_extract_workflow_step()` 헬퍼 추가.
  - `test_github_workflow_runs_publish_gates_against_clean_bundle`에서 `Check release preflight` 블록 추출 후 헤더/strict-ref/미노출 규칙을 검증.
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-105 연계(CI 테스트 보정: 스텝 추출 유틸로 릴리즈 프리플라이트 검증 강화)` 항목 추가.

## Evidence

- `tests/test_inventory_sync_sanitize.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 코드 실행 테스트는 이번 패스에서 별도 수행하지 않았다.
