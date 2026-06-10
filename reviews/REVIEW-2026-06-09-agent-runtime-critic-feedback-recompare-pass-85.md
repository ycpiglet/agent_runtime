# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-85.md

## Bottom Line

`PASS-85`에서는 warning-summary 게이트 요약 보고서 소비기의 CI 실행을 `monitoring 우선/Slack critical-only` 정책으로 고정하고, 릴리스 계열 브랜치에서만 송신 대상 유효성 엄격 검증을 적용하도록 `.github/workflows/test.yml`를 정렬했다.

## Signal

| 항목 | PASS-84 상태 | PASS-85 상태 | 근거 |
|---|---|---|---|
| CI 라우팅 정책 | 기본값과 동일하게 Slack/monitoring 임계치 미분리 | CI에서 `--monitoring-threshold 1`, `--slack-threshold 3` 고정 |
| 경로별 엄격 모드 | CI가 항상 경량화(스킵 허용) | release 계열 브랜치에서 `--require-send-targets` 적용 조건부 적용 |
| 운영 문서 | PASS-84 옵션/테스트 정리 | PASS-85 정책(채널 기본 임계치, release-only 엄격 모드) 추가 |

## Insight

- 기본 게이트를 모니터링 중심으로 유지하고 Slack은 높은 실패 임계치에서만 사용하면 노이즈를 줄이면서도 위험 신호 전파는 보장할 수 있다.
- `--require-send-targets`를 모든 브랜치에서 강제하면 fork PR/개발 브랜치에서 false positive가 늘 수 있어, 적용 범위를 릴리스 계열로 제한하는 설계가 실무적으로 합리적이다.

## Decision

- `.github/workflows/test.yml`
  - 요약 실행이 `--monitoring-threshold 1`과 `--slack-threshold 3`을 항상 전달하도록 변경
  - `main`, `release/*`, `refs/tags/*`에서만 `--require-send-targets`를 조건부로 부여
  - Slack/모니터링 secret 환경변수 항목을 workflow env로 명시
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`
  - PASS-85 CI 라우팅 정책 동작을 문서화
- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-85.md`
  - 이번 순환의 근거/증거/요약 기록 추가

## Evidence

- `.github/workflows/test.yml`
- `src/agent_runtime/templates/project/agents/qa/TEST-STRATEGY.md`

## Validation

- `python -m pytest tests/test_warning_summary_gate_report_summary.py -q`
- `PYTHONPATH=src python -m pytest tests/test_template_smoke.py -k "warning_summary_gate_runs_in_template_runtime_and_survives_mixed_schema_contexts" -q`

## Next Step

- PASS-86 제안: summary 단계에서 release-only 브랜치 감지 로직을 더 명시적인 repository 정책(예: `release` 접두사 태그/브랜치 목록 변수)으로 추출해 중복/누락 가능성을 줄인다.
