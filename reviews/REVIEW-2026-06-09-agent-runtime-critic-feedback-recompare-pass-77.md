# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-77.md

## Bottom Line

`PASS-77`에서는 템플릿 경고 게이트를 운영 검증용으로 확장해, 경고 요약 실행 리포트를 고정 경로에 저장하고
코드별 임계치 규칙을 정책 판단에 반영했다.

## Signal

| 항목 | PASS-76 상태 | PASS-77 상태 | 근거 |
|---|---|---|---|
| 리포트 보존 | stdout 출력만 존재 | `--report-path`를 통해 JSONL 리포트가 누적 기록되도록 확장 | `src/agent_runtime/templates/project/scripts/message_queue.py` |
| 코드별 임계치 | 총건수 임계치만 확인 | `--code-threshold`로 코드별 경고 상한을 반영해 정책 실패 사유를 출력 | `src/agent_runtime/templates/project/scripts/message_queue.py` |
| CI 아티팩트 | 경고 게이트 실행 결과가 CI로 직접 남지 않음 | 스모크 스텝에서 고정 경로로 리포트 저장 후 Artifacts 업로드 단계 추가 | `.github/workflows/test.yml`, `tests/test_template_smoke.py` |

## Insight

- 운영 단계에서는 총 경고 건수보다 특정 코드의 과도한 빈도가 더 중요할 수 있어, 코드 단위 상한을 함께 운용해야 한다.
- CI artifact를 템플릿 테스트와 연결하면 임계치/정책 변경 시 추적 가능한 실행 흔적을 즉시 수집할 수 있다.

## Decision

- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - `warning-summary-gate`에 `--code-threshold CODE=COUNT` 추가
  - `--report-path` 추가 및 실행 리포트 JSONL append
  - 정책 엔진 `_evaluate_warning_summary_policy`에 코드별 임계치 체크 추가
- `tests/test_template_smoke.py`
  - `test_warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts`
    - report path는 `PASS_39_WARNING_SUMMARY_GATE_REPORT_PATH` 환경변수 우선 사용
    - 코드별 임계치 통과/실패 시나리오를 같은 테스트 내에서 검증
- `.github/workflows/test.yml`
  - 템플릿 경고 게이트 스텝에 리포트 경로 환경변수 주입
  - `template-warning-summary-gate-report` Arifacts 업로드 스텝 추가

## Evidence (pass-77)

- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_smoke.py`
- `.github/workflows/test.yml`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-78 제안: 경고 요약 게이트 리포트를 템플릿 런타임 운영 문서(`TEST-STRATEGY.md`)와 연결해, 코드별 임계치 변경 절차와 롤백 조건을 문서화
