# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-82.md

## Bottom Line

`PASS-82`에서는 경고 요약 게이트 소비기의 모니터링 인입(ingestion) 스키마 매핑 경로를 추가해 CI/운영에서 수집기 연동이 가능하도록 정형 페이로드 출력을 고정했다.

## Signal

| 항목 | PASS-81 상태 | PASS-82 상태 | 근거 |
|---|---|---|---|
| 수집기 스키마 매핑 | dashboard/slack 출력만 존재 | monitoring payload (`schema_version`, `status`, `metrics`, `alerts`) 추가 |
| CI 보존 | 대시보드/슬랙 payload만 업로드 | monitoring payload 아티팩트 경로 추가 |
| 회귀 검증 | 수집기 페이로드 미검증 | monitoring payload 스키마/상태 매핑 테스트 추가 |

## Insight

- 경보 임계치 해석(`policy_failures`, `alert_threshold`)을 단일 소비 포맷으로 고정하면 운영/모니터링 시스템과의 연동 비용을 줄일 수 있다.
- PASS-81의 텍스트 중심 연산은 유지하면서, `schema_version` 기반의 소비기 스키마를 분리하면 채널별 의존도를 낮추고 테스트 포인트를 늘릴 수 있다.

## Decision

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
  - `--monitoring-json` 추가: 정형 모니터링 이벤트 출력 경로
  - `--monitoring-source` 추가: 수집기 source 라벨 지정
  - `_build_monitoring_payload` 추가: `status`, `metrics`, `alerts`, `top_codes`, `top_reasons` 포함
- `tests/test_warning_summary_gate_report_summary.py`
  - `test_warning_summary_gate_monitoring_payload_schema_and_mapping` 추가
- `.github/workflows/test.yml`
  - 요약 단계에 `--monitoring-json` 전달
  - artifact 업로드 경로에 `.tmp/template-warning-summary-gate-monitoring.json` 추가
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-82 연계(관측 수집기) 사용 옵션/예시 추가

## Evidence

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
- `tests/test_warning_summary_gate_report_summary.py`
- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_warning_summary_gate_report_summary.py -q`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-83 제안: `--slack-webhook`/실채널 전송(또는 모니터링 엔드포인트 직접 수신) 옵션을 추가해, ingestion payload를 실제 채널로 발신하는 end-to-end 경로를 검증한다.
