# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-100.md

## Bottom Line

`PASS-100`에서는 `release-preflight`가 `warning-summary-gate-strict-refs` 항목의 상태/상세를 report 렌더 결과와 함께 일관되게 노출하도록 테스트를 강화했다.

## Signal

| 항목 | PASS-99 상태 | PASS-100 상태 | 근거 |
|---|---|---|---|
| strict-ref 파서 테스트 | 파서/invalid 케이스는 별도 파일로 분리 | preflight check+render 경로로 확장 | `tests/test_inventory_sync_sanitize.py` |
| 렌더 일치 | 상태/상세 검증이 렌더 문자열 레벨에서 미확인 | `render()` 결과 문자열에 preflight 행 존재 검증 | `tests/test_inventory_sync_sanitize.py`, `release_preflight.render` |
| 오탐지 경로 | invalid refs는 반환된 finding 자체로만 확인 | preflight check blocked + rendering row 동시 확인 | `tests/test_inventory_sync_sanitize.py` |

## Insight

- 파서 단위 테스트만으로는 release-preflight 출력 포맷이 깨지는 회귀를 잡기 어렵다.
- `render` 문자열 검증을 함께 두면서 팀 운영에서 보는 보고서 라인(표) 일관성을 함께 고정했다.

## Decision

- `tests/test_inventory_sync_sanitize.py`에 테스트 추가:
  - strict-ref 유효 입력 시 `warning-summary-gate-strict-refs`가 `ok`/`refs=...`로 렌더링
  - invalid 입력 시 `blocked` + finding kind + 렌더 행 존재 검증
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-100 연계(Preflight 렌더 보고서 정합성)` 항목 추가

## Evidence

- `tests/test_inventory_sync_sanitize.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
- `src/agent_runtime/release_preflight.py`(render/check 경로)

## Validation

- 현재는 작성 단계이며, 실행 검증은 다음 단계에서
  `PYTHONPATH=src python -m pytest tests/test_inventory_sync_sanitize.py -k "release_preflight" -q`
  로 이어갈 수 있음.
