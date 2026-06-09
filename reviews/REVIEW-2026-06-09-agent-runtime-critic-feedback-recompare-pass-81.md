# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-81.md

## Bottom Line

`PASS-81`에서는 경고 요약 리포트 소비기를 대시보드/알림 소비 포맷으로 확장해, `warning-summary` 정책 실패를 즉시 기계 판독 가능한 이벤트와 Slack 바디로 생성하도록 연결했다.

## Signal

| 항목 | PASS-80 상태 | PASS-81 상태 | 근거 |
|---|---|---|---|
| 대시보드 연동 | 요약 텍스트 + 경고 annotation만 존재 | `--dashboard-json`/`--slack-payload`로 소비형 payload 출력 추가 | `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py` |
| CI 아티팩트 | 원본 report 아티팩트만 보관 | dashboard/slack payload를 함께 artifact 업로드 | `.github/workflows/test.yml` |
| 회귀 검증 | 소비기 변경 미검증 | dedicated 테스트 추가로 경보/건전 상태 payload 검증 | `tests/test_warning_summary_gate_report_summary.py` |

## Insight

- 텍스트 출력만으로는 운영 자동화 연동이 어렵기 때문에, 동일 스크립트에서 alert payload를 함께 생성하면 파이프라인 소비를 즉시 통합할 수 있다.
- 기존 `--alert-threshold`(기본 1)로 fail count 임계치를 운영 정책과 분리해 점진적으로 조정 가능하다.

## Decision

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
  - `--dashboard-json` 추가: 경보 payload(`status`, `policy_failures`, `incidents`) 저장
  - `--slack-payload` 추가: Slack 전송용 JSON 바디 생성
  - `--alert-threshold` 추가: alert 임계치 분리 설정
- `tests/test_warning_summary_gate_report_summary.py`
  - `test_warning_summary_gate_dashboard_and_slack_payloads`
  - `test_warning_summary_gate_dashboard_no_failure_stays_ok`
- `.github/workflows/test.yml`
  - warning-summary 리포트 소비 스텝을 dashboard/slack payload 생성으로 확장
  - 업로드 artifact 항목에 payload JSON 포함
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-81 연계 소비기 사용법/예시 추가

## Evidence

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
- `tests/test_warning_summary_gate_report_summary.py`
- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_warning_summary_gate_report_summary.py -q`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-82 제안: Slack 알림을 실제 수신 채널과 연동(예: webhook/봇 호출)하거나 모니터링 시스템 ingestion 스키마와 매핑 테스트를 추가.
