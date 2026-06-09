# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-98.md

## Bottom Line

`PASS-98`에서는 warning-summary 게이트 요약기의 `--require-send-targets` 동작을 커버해, 전송 판정이 비활성일 때는 예외를 강제하지 않고, 전송이 실제로 활성화될 때만 target 결손을 실패로 처리하도록 회귀를 고정했다.

## Signal

| 항목 | PASS-97 상태 | PASS-98 상태 | 근거 |
|---|---|---|---|
| 전달 대상 결함 강제 조건 | `--require-send-targets` 자체 동작은 수동 점검 위주로 존재 | non-send/ send-on-ok 두 경로를 분기 테스트로 고정 | `tests/test_warning_summary_gate_report_summary.py` |
| 요약-전송 게이트 정합성 | strict-ref 요약과는 별도 라인에서만 추적됨 | `PASS-98 연계` 항목으로 QA 전략에 분기 기준 정리 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- `--require-send-targets`의 의미는 “항상 전송 대상이 있어야 함”이 아니라 “보내려는 경우에만 유효 target 필요”인데, 분기 경계를 테스트로 고정하지 않으면 의도와 다르게 알람 실패로 오탐될 수 있다.
- 실제 CI 경로에서는 `fail-on-warn` 임계치, `send-on-ok` 조합이 존재하므로, 두 모드를 모두 보강해야 재현성 문제가 적다.
- 다음 단계에서는 strict-ref source 출력 정합성(요약 페이지/artifact)까지 함께 점검하는 PASS-99로 연결하면 됩니다.

## Decision

- `tests/test_warning_summary_gate_report_summary.py`에 `test_warning_summary_gate_require_send_targets_only_enforced_when_send_is_needed` 추가
  - 실패가 없는 비전송 조건에서는 정상 종료
  - send-on-ok 조건에서 invalid target 시 실패
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-98 연계(요약 게이트 전송 판단 정합성)` 항목 추가

## Evidence

- `tests/test_warning_summary_gate_report_summary.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- 현재는 테스트 실행 없이 코드/문서 수정 상태로 기록.
- 다음 사이클은 `PYTHONPATH=src python -m pytest tests/test_warning_summary_gate_report_summary.py -q`로 PASS-98 대상 테스트 1개를 실행해 통과 검증 가능.
