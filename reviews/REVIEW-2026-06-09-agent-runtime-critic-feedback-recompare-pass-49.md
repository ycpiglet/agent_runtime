# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-49.md

## Bottom Line

`PASS-49`에서는 `schedule` strict 게이트를 Python `3.12`까지 추가해
정기 점검의 버전 범위를 완전히 정렬했다.

`warning-only` 기본 동작은 유지되며, schedule 경로의 `fail-on-warning`은
`3.10/3.11/3.12` 3개 런타임에서 공통적으로 실행되도록 확장했다.

## Signal

| 항목 | PASS-48 상태 | PASS-49 상태 | 근거 |
|---|---|---|---|
| schedule strict 조건 | `3.10`, `3.11` | `3.10`, `3.11`, `3.12` | `.github/workflows/test.yml` |
| main strict 조건 | `3.10`, `3.11` | 변경 없음 | `.github/workflows/test.yml` |
| 문서 반영 | `3.10/3.11` | `3.10/3.11/3.12` | `README.md` |
| 검증 | warning/fail 재실행 | 동일 변경 후 로컬 재실행 미요청(범위 확장만 반영) | 변경 범위가 CI 조건식 확장 |

## Insight

- schedule strict가 3.12까지 확장되면 정기 정합성 점검에서 운영 릴리스 후보 버전 3개를 모두 포함해 정책 차단 신호를 수집할 수 있다.
- 기존 아티팩트 분리(`event+python`) 덕분에 버전 추가의 추적 오버헤드가 낮다.

## Decision

- PASS-49는 schedule strict 범위를 `3.12`까지 확장하여 정기 게이트를 `3.10-3.12`로 완성했다.
- 다음 순환은 `FAIL` 허용치 실험(`PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT > 0`)을
  분리 실험으로 수행해 main/schedule에서의 실패 임계치 정책을 정형화한다.

## Evidence (pass-49)

- `.github/workflows/test.yml`
  - `Run latency policy gate (fail-on-warning) on schedule` 조건:
    - `github.event_name == 'schedule' && (matrix.python-version == '3.10' || matrix.python-version == '3.11' || matrix.python-version == '3.12')`
- `README.md`
  - schedule strict 실행 런타임을 `3.10`, `3.11`, `3.12`로 갱신

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-48.md`
- `tests/test_template_message_queue.py`
