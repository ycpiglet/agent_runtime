# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-84.md

## Bottom Line

`PASS-84`에서는 warning-summary 게이트 소비기의 송신 경로를 임계치별 채널 라우팅으로 정리하고, 비밀값 미제공/오염 URL에 대한 안전 스킵 규칙을 추가해 CI에서 오탐 실패 없이 동작하게 했다.

## Signal

| 항목 | PASS-83 상태 | PASS-84 상태 | 근거 |
|---|---|---|---|
| 채널 라우팅 | 임계치 일괄 적용(알림 대상 공통) | Slack/monitoring 채널별 threshold(`--slack-threshold`, `--monitoring-threshold`) 분리 |
| 비밀값 오염 가드 | 존재하지 않음 | URL placeholder/무효 형식 감지 후 전송 생략 |
| 엄격 모드 | 미정의 | `--require-send-targets`로 유효 대상 미구성 시 실패 |

## Insight

- 임계치별 라우팅은 alert와 healthy 구간에서 채널별 메시지 비용/소음 비용을 줄여 운영 비용을 줄일 수 있다.
- 운영에서는 시크릿 미제공이 흔하므로, 기본은 오탐 경보를 피하도록 전송 생략 + 경고 출력이 적절하며, 필요 시 `--require-send-targets`로 강제 실패 전환 가능해야 한다.

## Decision

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
  - `_looks_like_placeholder_or_invalid_url` 추가: placeholder/무효 URL 차단
  - 채널별 전송 임계치: `--slack-threshold`, `--monitoring-threshold`
  - `--require-send-targets` 추가: 전송 필요 시 유효 대상 누락 시 실패
- `tests/test_warning_summary_gate_report_summary.py`
  - `test_warning_summary_gate_send_routing_by_threshold_only_monitoring` 추가
  - `test_warning_summary_gate_invalid_targets_are_safe_skipped` 추가
  - `test_warning_summary_gate_invalid_targets_fail_when_required` 추가
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-84 옵션 및 실패 동작 설명 반영

## Evidence

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
- `tests/test_warning_summary_gate_report_summary.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_warning_summary_gate_report_summary.py -q`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-85 제안: CI 단계에서 `--require-send-targets` 적용 조건(예: release 브랜치만) 및 채널별 라우팅 기본값 정책(기본 모니터링 only, Slack은 critical-only) 고정.
