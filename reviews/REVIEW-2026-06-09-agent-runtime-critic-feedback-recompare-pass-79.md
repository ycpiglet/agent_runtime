# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-79.md

## Bottom Line

`PASS-79`에서는 템플릿 경고 요약 게이트를 운영 사전 검증 가능한 형태로 확장해, 임계치 변경 전 `--dry-run`으로 정책 변경을 시뮬레이션하고, 결과 리포트(`policy_passed/reasons`)를 운영 보고서 소비 규칙 및 알림 흐름으로 연결했다.

## Signal

| 항목 | PASS-78 상태 | PASS-79 상태 | 근거 |
|---|---|---|---|
| 사전 임계치 검증 | 문서 수준 안내만 존재 | `warning-summary-gate --dry-run` 추가로 변경 전 실패 영향 시뮬레이션 가능 | `src/agent_runtime/templates/project/scripts/message_queue.py` |
| 운영 스모크 검증 | 기존 pass/fail 경로만 존재 | dry-run fail 케이스도 템플릿 스모크에서 `return code 0 + policy_passed false`로 검증 | `tests/test_template_smoke.py` |
| 보고서 소비/알림 규칙 | 운영 운영 원칙 미정의 | QA TEST-STRATEGY에 `code_warning_limits`, 최근 실패 트렌드, dry-run 절차/샘플을 규정 | `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md` |

## Insight

- 코드별 임계치 변경 전 dry-run을 고정하면 실제 배포에서 즉시 fail하는 리스크를 줄이고, 정책 완화/강화 의사결정 근거를 남길 수 있다.
- 리포트에서 `policy_passed`와 `reasons`를 운영 소비 단위로 정리하면 알림/대시보드 연동 경로를 별도 코드 변경 없이 정합성 있게 만들 수 있다.

## Decision

- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - `warning-summary-gate`에 `--dry-run` 옵션 추가
  - dry-run 모드에서는 정책 판단은 수행하되 exit code는 0으로 고정
  - `report`에 `dry_run` 필드 추가
- `tests/test_template_smoke.py`
  - code-threshold 실패 시나리오에 대응하는 `--dry-run` 실행 검증 추가
  - `policy_passed=false`이면서 return code 0인지 확인
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - `PASS-39 경고 요약 게이트 운영`에 소비자 지표/알림 규칙, 사전 dry-run 절차, 명령 예시 추가

## Evidence

- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_smoke.py`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-80 제안: dry-run 결과를 CI에 반영하는 별도 스텝(보고서 파서 기반 경보/요약 출력) 또는 경량 대시보드/알림 소비기 스크립트 추가.
