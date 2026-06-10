# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-78.md

## Bottom Line

`PASS-78`에서는 PASS-77 확장된 템플릿 경고 요약 게이트를 템플릿 운영 문서(`agents/qa/TEST-STRATEGY.md`)와 연결해, 코드별 임계치 조정 절차와 롤백 조건을 문서화했다.

## Signal

| 항목 | PASS-77 상태 | PASS-78 상태 | 근거 |
|---|---|---|---|
| 운영 문서 정합성 | 구현은 있으나 운영 운영 절차 미기록 | `PASS-39 경고 요약 게이트 운영` 섹션 추가로 임계치/리포트/롤백 루틴 정리 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |
| 임계치 변경 가시성 | 코드별 임계치 의미가 텍스트로 분리되지 않음 | `--code-threshold` 및 `--report-path` 연동 운영 기준을 단계별로 명시 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 구현된 게이트가 실제 CI에서 동작하더라도 운영 문서가 없으면 변경 승인/복구 판단이 느려질 수 있다.
- `PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH` 기반 아티팩트 보존 규칙을 문서화해 재현성과 감사 추적을 높일 수 있다.

## Decision

- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-39 경고 요약 게이트 운영` 섹션 추가
  - `--summary-path`, `--run-id`, `--event-name`, `--warning`, `--max-warnings-per-context`, `--code-threshold`, `--report-path` 운영 의미 정리
  - `PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH` 우선 주입 규칙과 코드별 임계치 변경/롤백 절차 명시

## Evidence

- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`
- 현재 세션에서는 테스트를 실행하지 않았습니다.

## Next Step

- PASS-79 제안: 템플릿 경고 요약 리포트 소비자(알림/운영 대시보드) 연동 및 임계치 변경 전 사전 dry-run 워크플로우 정의
