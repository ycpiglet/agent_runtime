# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-86.md

## Bottom Line

`PASS-86`에서는 warning-summary 게이트 요약 단계의 strict-send 규칙을 브랜치/태그 감지 문자열에서 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 정책 상수로 추출해 중앙 관리되도록 정리했다.

## Signal

| 항목 | PASS-85 상태 | PASS-86 상태 | 근거 |
|---|---|---|---|
| 브랜치 판별 조건 | YAML run 블록 안 인라인 조건식 | `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 정책 상수로 일원화 |
| 분기 동작 | main/release/tag에서 조건부 strict 활성화(Secret 존재 여부 추가 조건) | main/release/tag prefix match 시 항상 `--require-send-targets` 적용 |
| 문서 정합성 | PASS-85 정책 기록 | PASS-86 정책 상수와 prefix match 규칙 문서화 |

## Insight

- 브랜치 판별 조건을 상수화하면 release-eligible 조건 변경 시 workflow 코드 한 곳만 갱신하면 되고, PR/포크/스케줄 케이스에서 정책 drift 위험이 줄어든다.
- `--require-send-targets`는 strict 대상 브랜치에서 항상 활성화되어야 secret 누락 자체를 배포 게이트로 처리할 수 있다.

## Decision

- `.github/workflows/test.yml`
  - 워크플로우 `job.env`에 `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS` 추가
  - 요약 단계에서 상수 배열을 읽어 `refs/heads/main`, `refs/heads/release/`, `refs/tags/` prefix match 시 `--require-send-targets` 부여
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-86 정책(브랜치 정책 정규화) 문서화
- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-86.md`
  - PASS-86 근거/결정 기록 추가

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `python -m pytest tests/test_warning_summary_gate_report_summary.py -q`
- `PYTHONPATH=src python -m pytest tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`

## Next Step

- PASS-87 제안: `PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS`를 릴리스 정책 문서와 release-preflight 체크에서 공통 상수로 선언해 워크플로우/문서 간 정책 싱크를 강제.
