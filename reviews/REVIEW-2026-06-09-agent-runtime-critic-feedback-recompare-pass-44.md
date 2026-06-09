# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-44.md

## Bottom Line

`PASS-44`에서는 `PASS-43`에서 연결한 지연 정책 게이트를 운영적으로 단계화했다.

경고-only 기본 동작은 유지하면서, `main` 브랜치 푸시에만 Python `3.10` 실행기로
`fail-on-warning` 모드를 추가 실행하여 점진적인 차단 게이트 전환 경로를 확보했다.

## Signal

| 항목 | PASS-43 상태 | PASS-44 상태 | 근거 |
|---|---|---|---|
| CI 정책 단계 | warning-only만 존재 | warning-only + main-push fail-on-warning 단계 추가 | `.github/workflows/test.yml`에 두 단계 구성 |
| 브랜치/실행기 가드 | 없음 | `push` + `refs/heads/main` + `python-version==3.10` 조건 |
| 운영 문서 | 완화 모드 명시 | 분기별 게이트 동작을 문서화 | `README.md` latency policy 섹션 보강 |
| 재현성 검증 | PASS-43에서 warning-only만 실행 | warning-only + fail-on-warning 모두 단일 테스트로 검증 | `python ... -k parallel_recover...` 두 번 실행 |

## Insight

- `warning-only`는 PR/기본 회귀 보호에 그대로 두고, `fail-on-warning`은 주 브랜치에서만 단계적으로 적용해 운영 충격을 줄일 수 있다.
- 같은 타겟 테스트를 재현/재확인해 실제 경보-차단 전환이 정상 동작함을 확인했다.
- 다음 사이클은 실패 경보가 반복될 경우 `max_warning_count`/브랜치/실행기 범위를 조정해 점진 강화 범위를 확장할 수 있다.

## Decision

- PASS-44를 완료해 정책 게이트의 **운영 전개 경로**(warning-only default → main strict)를 고정했다.
- 다음 순환은 실제 운영 경보 빈도를 바탕으로 `fail-on-warning` 범위를 `main` 외 특정 이벤트(예: schedule)로 확장하고,
  경보 임계치 튜닝의 근거를 리뷰로 정량화한다.

## Evidence (pass-44)

- `.github/workflows/test.yml`
  - `Run latency policy gate (warning-only) for queue metrics`
  - `Run latency policy gate (fail-on-warning) on main push` 추가
- `README.md`
  - latency 정책 섹션에 main-푸시 strict 운영 경로 문구 추가
- 로컬 검증
  - `PASS_39_LATENCY_POLICY=warning-only`로 test 실행: pass
  - `PASS_39_LATENCY_POLICY=fail-on-warning`로 test 실행: pass

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-43.md`
- `tests/test_template_message_queue.py`
