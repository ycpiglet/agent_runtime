# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-99.md

## Bottom Line

`PASS-99`에서는 release-preflight strict-ref 처리 경계를 테스트화해, strict-ref 설정 문자열의 정규화와 invalid 항목/빈값 판별이 일관되게 유지되도록 했다.

## Signal

| 항목 | PASS-98 상태 | PASS-99 상태 | 근거 |
|---|---|---|---|
| strict-ref 입력 정규화 | 요약/아티팩트 정합성 중심으로 제한 | 파서 단계에서 공백/빈 줄 제거 동작을 테스트로 고정 | `tests/test_release_preflight_warning_summary_gate_strict_refs.py` |
| 빈값 처리 구분 | `None`/empty 문자열 구분은 코드 상에만 존재 | `None` 미설정 vs empty 문자열 미설정/빈 목록 판정 케이스를 테스트 분리 | `tests/test_release_preflight_warning_summary_gate_strict_refs.py` |
| invalid ref 판정 | 파라미터 유효성은 코드 리뷰로만 점검 | invalid ref 케이스 테스트 추가 | `tests/test_release_preflight_warning_summary_gate_strict_refs.py` |

## Insight

- strict-ref 입력이 workflow/환경변수/CLI를 통해 유입되는 경로가 분기되어 있어, 파서-검증 단계 회귀가 없으면 `release-preflight`의 실패 조건이 누적되기 쉬웠다.
- 이번 테스트로 “비어있음=실패”와 “미설정=스킵”의 상태 의미를 분리해 의도한 동작을 유지한다.

## Decision

- `tests/test_release_preflight_warning_summary_gate_strict_refs.py` 추가:
  - `raw` 공백/빈 줄 정리 후 tuple 파싱
  - 유효 refs no-finding
  - `None` 입력 no-finding
  - `""` 입력에서 `missing-warning-summary-gate-strict-ref` 생성
  - invalid 항목에서 `invalid-warning-summary-gate-strict-ref` 생성
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-99 연계(Preflight strict-ref 판정 정합성)` 항목 추가

## Evidence

- `tests/test_release_preflight_warning_summary_gate_strict_refs.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 현재는 코드/테스트 추가 단계이며, 실행 검증은 다음 단계에서 `PYTHONPATH=src python -m pytest tests/test_release_preflight_warning_summary_gate_strict_refs.py -q`로 이어갈 수 있음.
