# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-80.md

## Bottom Line

`PASS-80`에서는 템플릿 경고 요약 게이트 리포트 소비 경로를 CI에 추가해, `warning-summary-gate`의 JSONL 결과를 파싱해 실패 요약/알림 근거를 생성하도록 연결했다.

## Signal

| 항목 | PASS-79 상태 | PASS-80 상태 | 근거 |
|---|---|---|---|
| 리포트 소비기 | 운영 소비 규칙 텍스트 설명 수준 | `summarize_warning_summary_gate_report.py` 추가로 JSONL 파서/요약기 구현 | `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py` |
| CI 반영 | smoke 테스트가 실행만 하고 종료 | 워크플로우에 `Summarize template warning-summary gate reports` 스텝 추가 | `.github/workflows/test.yml` |
| 운영 연계 문서 | dry-run/임계치 변경 규칙만 존재 | 운영 전략 문서에 소비기 경로/옵션/경고 연동 (`--github-annotations`) 추가 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 리포트가 쌓이는 즉시 파싱되어야 운영 알림/대시보드 연동이 가능하다.
- 실패 케이스를 정책적으로 바로 차단하지 않더라도 경고(annotation)로 노출하면 안전하게 관측성만 선행 확보할 수 있다.

## Decision

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
  - warning-summary 게이트 JSONL을 읽어 정책 실패 건수/빈도(`policy_failures`, `failed_codes_top`, `failed_reasons_top`, `recent_contexts`)를 집계
  - `--json`, `--last`, `--github-annotations` 옵션 지원
- `.github/workflows/test.yml`
  - `Summarize template warning-summary gate reports` step 추가 (`--last 10 --github-annotations --json`)
  - `if: always()` 적용으로 리포트 스냅샷은 실패 유무와 무관하게 수집
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - 경고 요약 리포트 소비기 사용 방식, 입력/출력, CI 경고 연동 옵션을 운영 지침에 포함

## Evidence

- `src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py`
- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`
- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe src/agent_runtime/templates/project/scripts/summarize_warning_summary_gate_report.py --path C:/path/to/template-warning-summary-gate-report.jsonl --json`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-81 제안: summarize 스크립트를 운영 대시보드 수집기(예: 메트릭 JSON/Slack 알림)와 연결하고, 정책 실패 경보 기준을 문서+테스트로 고정.
