# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-76.md

## Bottom Line

`PASS-76`에서는 PASS-75에서 검증한 `pass39-warning-summary` 혼재 스키마 처리 규칙을 템플릿 런타임으로 끌어올려,
`message_queue` 스크립트에 실제 경고 요약 게이트 엔트리포인트를 추가하고,
템플릿 스모크/CI에서 혼재 스키마 + 정책 임계치 경로를 직접 실행하도록 연결했다.

## Signal

| 항목 | PASS-75 상태 | PASS-76 상태 | 근거 |
|---|---|---|---|
| 경고 요약 런타임 경로 | 테스트 전용 유틸에 한정 | `templates/project/scripts/message_queue.py`에 `warning-summary-gate` CLI 및 공용 병합/정책 헬퍼 이식 | `src/agent_runtime/templates/project/scripts/message_queue.py` |
| 스키마 정합성 | 단위 병합 검증만 | 스모크 테스트에서 `v0/v1/legacy` 기존 레코드를 파일 I/O 후 재로드해서 coalesce + 정책 게이트 실행 | `tests/test_template_smoke.py` |
| 운영/CI 게이트 | 템플릿 검증은 있었으나 warning-summary 임계치 직접 노출 제한 | `warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts` 스모크 추가 및 CI step로 분리 실행 | `.github/workflows/test.yml` |

## Insight

- 템플릿 런타임 엔트리포인트로 경고 요약 정책을 배치하면, 테스트만 통과하던 혼재 스키마 이슈가 배포 템플릿 경로에서 바로 드러난다.
- `coalesce`가 `window/run/event` 폴백을 처리하는 한편 `policy_passed` 판단까지 같은 실행에서 잡아주기 때문에, 운영 임계치 변경이 바로 CI 실패로 반영된다.

## Decision

- `src/agent_runtime/templates/project/scripts/message_queue.py`
  - PASS-39 warning summary 유틸(스키마 정규화/병합/정책판단/기록/로더) 추가
  - `warning-summary-gate` CLI entrypoint 추가
    - `--summary-path`, `--run-id`, `--event-name`, `--window-start`, `--window-end`, `--warning`, `--max-warnings-per-context` 처리
    - 임계치 초과 시 비정상 종료
- `tests/test_template_smoke.py`
  - `test_warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts` 추가
  - `tmp`에 `v0/v0-legacy` 혼재 레코드를 선적재한 뒤 `warning-summary-gate` 실행으로 coalesce+정책 경로 확인
  - 임계치 통과/실패 양쪽 경로를 같은 스모크에서 검증
- `.github/workflows/test.yml`
  - PASS-76 전용 템플릿 스모크 게이트 스텝 추가

## Evidence (pass-76)

- `src/agent_runtime/templates/project/scripts/message_queue.py`
- `tests/test_template_smoke.py`
- `.github/workflows/test.yml`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`
- 현재 세션에서는 테스트 실행을 수행하지 않았습니다.

## Next Step

- PASS-77 제안: 템플릿 런타임 경고 게이트의 출력 형식(summmary report)을 CI 아티팩트로 저장하고, 운영 정책 변경 시 경고 코드별 임계치 매핑도 CI에서 검증
