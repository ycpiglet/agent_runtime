# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-96.md

## Bottom Line

`PASS-95`에서 표준화된 strict-ref 재현 스크립트가 추가된 뒤, `PASS-96`에서는 그 스크립트 회귀를 패키지 테스트로 고정해 `write/validate` 정합성 경로가 자동으로 검증되도록 보강했다.

## Signal

| 항목 | PASS-95 상태 | PASS-96 상태 | 근거 |
|---|---|---|---|
| 회귀 방지 | 워크플로우/README에서 재현 표준화만 반영 | `tests/test_warning_summary_strict_ref_policy.py`로 핵심 동작을 반복 검증 | `tests/test_warning_summary_strict_ref_policy.py` |
| strict-ref 정규화 | CR/공백/빈 줄 정규화 구현 | 정규화 동작을 테스트 케이스로 고정 | `tests/test_warning_summary_strict_ref_policy.py` |
| 실패 탐지 | 정합성 실패 조건이 문서화만 존재 | mismatch, artifact 누락 실패 케이스를 테스트로 고정 | `tests/test_warning_summary_strict_ref_policy.py` |

## Insight

- 재현 스크립트를 바꿨을 때 단순 문서 수정으로는 drift가 다시 생길 수 있으므로, 최소 테스트셋으로 lock-in이 필요했다.
- `validate` 경로에서 strict-ref 비교 실패/누락 실패를 모두 명시하면, PASS-94/95에서 해결한 drift 리스크를 조기에 감지한다.
- 이제부터는 리허설 없이도 CI 파이프라인에서 동일 함수로 재현 가능한지 객관적으로 점검 가능하다.

## Decision

- 추가된 테스트:
  - `tests/test_warning_summary_strict_ref_policy.py`
    - write/validate roundtrip
    - strict_refs 정규화 비교 성공
    - strict_refs_source mismatch fail
    - artifact missing fail
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-96 연계(회귀 차단 테스트)` 항목 추가
- 다음 사이클로 이동하기 위한 다음 항목:
  - `PASS-95~96` 커버리지 기준을 충족한 뒤, 기존 PASS-39 경고 게이트 정책/요약 산출물에 대한 추가 검증 자동화 여부를 검토.

## Evidence

- `tests/test_warning_summary_strict_ref_policy.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 로컬 실행 없이도 코드 리뷰 상 변경사항이 명확하며, 회귀 테스트 스위트가 신규 스크립트의 핵심 의도를 커버함.
- 실 실행은 다음 작업 사이클에서 `PYTHONPATH=src python -m pytest tests/test_warning_summary_strict_ref_policy.py -q`로 이어갈 예정.
