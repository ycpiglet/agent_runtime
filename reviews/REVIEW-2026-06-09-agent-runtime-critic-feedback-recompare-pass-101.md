# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-101.md

## Bottom Line

`PASS-101`에서는 `release-preflight`의 strict-ref 입력 소스 우선순위를 명시화해, CLI 옵션이 env 기반 값보다 우선 적용되도록 고정했다.

## Signal

| 항목 | PASS-100 상태 | PASS-101 상태 | 근거 |
|---|---|---|---|
| 우선순위 경로 | preflight 환경값만 사용 | CLI 옵션 + env fallback 분리 | `src/agent_runtime/cli.py`, `src/agent_runtime/release_preflight.py` |
| 입력 검증 | parser/체크 범위 미확장 | parser 및 실행경로 단위 테스트 추가 | `tests/test_release_preflight_warning_summary_source_precedence.py` |
| 렌더 영향 | 단순 상태/상세 검증만 존재 | 입력 source 변경 시 plan 반영 경로를 별도 회귀로 분리 | `tests/test_release_preflight_warning_summary_source_precedence.py` |

## Insight

- `release-preflight`가 env만 읽으면 CI 재현에서 수동 지정값을 반영하기 어려우며, 이번 변경은 사람/자동화가 쓰는 입력 경로를 분리한다.
- run_preflight 단에서 `warning_summary_gate_strict_refs` fallback을 일원화해 호출부가 명시값 전달/미지정 fallback를 정확히 처리하게 했다.

## Decision

- `src/agent_runtime/cli.py`
  - `--warning-summary-gate-strict-refs` 옵션 추가
  - `release-preflight` 실행시 옵션 값을 `run_preflight`에 전달
- `src/agent_runtime/release_preflight.py`
  - `run_preflight`에서 인자가 없을 때만 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` fallback 사용
  - `build_parser`에 동일 옵션 추가
- `tests/test_release_preflight_warning_summary_source_precedence.py` 추가
  - CLI 값 > env 우선
  - env fallback 확인
  - parser 노출값 확인

## Evidence

- `src/agent_runtime/cli.py`
- `src/agent_runtime/release_preflight.py`
- `tests/test_release_preflight_warning_summary_source_precedence.py`

## Validation

- 실행 검증 완료:
  - `py -3 -m pytest tests/test_release_preflight_warning_summary_source_precedence.py -q`
  - `py -3 -m pytest tests/test_release_preflight_warning_summary_gate_strict_refs.py tests/test_release_preflight_warning_summary_source_precedence.py -q`
  - 결과: `8 passed`
