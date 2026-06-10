# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-45.md

## Bottom Line

`PASS-45`에서는 운영 지연 정책 게이트를 `main` 푸시 외에도 정기 `schedule` 실행에서
동일한 `fail-on-warning` 경로로 확장했다.

기본 동작은 기존대로 `warning-only`를 유지하고, Python `3.10` 실행기에서만
`fail-on-warning` 경로를 실행하도록 제약해 주기 점검의 차단 신호를 안정적으로
누적할 수 있게 했다.

## Signal

| 항목 | PASS-44 상태 | PASS-45 상태 | 근거 |
|---|---|---|---|
| 스케줄 이벤트 | 없음 | `schedule` 트리거 추가 | `.github/workflows/test.yml`의 `on:` 블록 |
| 강화 게이트 범위 | `main push` 3.10만 | `main push` + `schedule` 3.10 모두 | 동일 fail-on-warning 스텝의 조건식 확장 |
| 운영 문서 | main 푸시 언급 | `schedule` 실행 언급 | `README.md` 정책 섹션 |
| 재현성 검증 | warning-only/fail-on-warning 수동 검증 | fail-on-warning 경로 추가 검증 재실행 | 로컬 테스트 1개 케이스 재실행 통과 |

## Insight

- 주간 `schedule` 실행에서 fail-on-warning을 병행하면 PR/일반 push의 노이즈를 줄이면서도
  정기적으로 지표 게이트가 차단 조건을 만족하는지 검증할 수 있다.
- 첫 단계로 `3.10`에만 한정해 리스크를 낮춘 상태에서, 경보 빈도/안정성을 보고
  `3.11/3.12`로 점진 확장 가능하다.

## Decision

- PASS-45를 완료해 게이트 확장 정책(`main` + `schedule`)을 고정했다.
- 다음 순환은 `schedule` fail-on-warning가 반복적으로 fail 비율/경고 수를 유발할 경우
  Python 버전 범위 확대 또는 별도 허용치(`PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT`) 조정으로
  단계적 강화를 이어간다.

## Evidence (pass-45)

- `.github/workflows/test.yml`
  - `on.schedule` 추가
  - `Run latency policy gate (fail-on-warning) on main push or schedule` 조건:
    - `github.event_name == 'push' && github.ref == 'refs/heads/main' && matrix.python-version == '3.10'`
    - `github.event_name == 'schedule' && matrix.python-version == '3.10'`
- `README.md`
  - latency policy 섹션에 주간 schedule strict 게이트 문구 추가
- 로컬 검증
  - `PASS_39_LATENCY_POLICY=fail-on-warning` 환경으로 타깃 테스트 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-44.md`
- `tests/test_template_message_queue.py`
