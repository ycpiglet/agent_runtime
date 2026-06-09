# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-87.md

## Bottom Line

`PASS-87`에서는 warning-summary 게이트 요약 정책 상수(`PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`)를 요약 단계와 `release-preflight` 점검으로 함께 전달해 배포 전 정책 형식 drift를 감시하도록 정렬했다.

## Signal

| 항목 | PASS-86 상태 | PASS-87 상태 | 근거 |
|---|---|---|---|
| 정책 상수 동기화 | 워크플로우 내 상수 선언 후 `--require-send-targets` 조건화 | 동일 상수값을 `release-preflight`가 환경 변수로 받아 정합성 검사 |
| drift 방지 | `PASS_86`는 워크플로우 범위 한정 | `release-preflight` 체크 항목으로 정책 누락/형식 오류를 preflight 결과에 노출 |
| 문서 정합성 | PASS-86 정책 정규화만 기록 | PASS-87에서 preflight 동기화 항목 추가 |

## Insight

- 정책 상수를 한 군데서 정의하고 사후 검증이 가능한 preflight 체크까지 연결하면, 향후 CI 수정 시 "요약 단계만은 반영되고 릴리스 준비에서는 누락"되는 drift를 줄일 수 있다.
- `release-preflight`는 릴리스 전 마지막 허용점검 구간이므로, 정책 문자열 검증 항목을 포함하는 것이 배포 안정성 측면에서 비용 대비 효과가 높다.

## Decision

- `src/agent_runtime/release_preflight.py`
  - `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 환경 변수를 읽어 정책 문자열을 파싱/검증하는 체크 항목 추가
  - `warning-summary-gate-strict-refs` 체크를 결과에 추가
- `.github/workflows/test.yml`
  - release-preflight 단계에 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`를 명시적으로 전달
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-87 항목(릴리스-프리플라이트 동기화) 문서화

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/release_preflight.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `python -m pytest tests/test_warning_summary_gate_report_summary.py -q`
- `PYTHONPATH=src python -m pytest tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`

## Next Step

- PASS-88 제안: 정책 문자열이 `workflow_call`/`workflow_dispatch` 입력에서 들어오는 경우를 지원해 수동 실행이나 재현 실행에서도 동일 상수를 재사용할 수 있게 확장.
