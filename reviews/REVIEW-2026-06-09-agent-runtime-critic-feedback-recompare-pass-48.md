# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-48.md

## Bottom Line

`PASS-48`에서는 `schedule` strict 게이트의 버전 범위를 Python `3.10`에서 `3.10/3.11`로
확대해 정기 점검의 차단 범위를 넓혔다.

기본 `warning-only` 모드는 유지되며, 정기 스케줄 검증의 파급력을 소폭 상향해
운영 모니터링의 수렴 속도를 높였다.

## Signal

| 항목 | PASS-47 상태 | PASS-48 상태 | 근거 |
|---|---|---|---|
| 스케줄 strict 조건 | `3.10` | `3.10`, `3.11` | `.github/workflows/test.yml` |
| main strict 조건 | 변경 없음 | `3.10`, `3.11` 유지 | `.github/workflows/test.yml` |
| 문서 반영 | 3.10/3.11 main, schedule 3.10 | schedule 3.10/3.11 반영 | `README.md` |
| 재현성 검증 | warning/fail 모드 재실행 | warning/fail 모드 재실행 | 타깃 테스트 1개씩 통과 |

## Insight

- `schedule` strict의 3.11 확장은 PR/일반 푸시 경로를 건드리지 않고도 정기 점검의 버전 커버리지를 넓힌다.
- 이벤트/버전 분리 아티팩트 구조가 유지되어 주간 점검 누적 분석의 정확도가 높다.

## Decision

- PASS-48은 `schedule` strict 확장 범위를 `3.11`까지 1단계로 상향했다.
- 다음 순환은 `schedule` 경로를 Python `3.12`로 확대할지 여부를
  누적 레코드 기반으로 판단하고, 필요 시 `FAIL` 허용치(`PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT`)를 함께 실험한다.

## Evidence (pass-48)

- `.github/workflows/test.yml`
  - `Run latency policy gate (fail-on-warning) on schedule` 조건:
    - `github.event_name == 'schedule' && (matrix.python-version == '3.10' || matrix.python-version == '3.11')`
- `README.md`
  - schedule strict 실행 조건을 `3.10` 및 `3.11`로 갱신
- 로컬 검증
  - warning-only 모드 타깃 테스트 1개 통과
  - fail-on-warning 모드 타깃 테스트 1개 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-47.md`
- `tests/test_template_message_queue.py`
