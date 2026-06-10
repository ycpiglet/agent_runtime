# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-51.md

## Bottom Line

`PASS-51`에서는 `main` strict의 Python 버전 커버리지를 `3.12`까지 확장해
`main` 브랜치 정기/배포 준비 strict 정책을 `3.10-3.12` 전체로 맞췄다.

`schedule` strict는 기존대로 `PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT=1`을 유지해
운영 관측성은 높이고, 배포선 strict(`main`)은 기존의 `0` 허용치 정책을 유지해
차단 기준을 유지한다.

## Signal

| 항목 | PASS-50 상태 | PASS-51 상태 | 근거 |
|---|---|---|---|
| main strict 조건 | `3.10`, `3.11` | `3.10`, `3.11`, `3.12` | `.github/workflows/test.yml` |
| schedule strict 조건 | `3.10/3.11/3.12` + 허용치 1 | 동일 | `.github/workflows/test.yml` |
| 문서 반영 | main 3.10/3.11, schedule 3.10/3.11/3.12 | main 3.10/3.11/3.12, schedule 값 완화 반영 | `README.md` |
| 검증 | 이전 패스에서 조건 확장 경로 검증 완료 | 워크플로우 조건식만 확장한 정책 반영 | 현재 PR diff |

## Insight

- `main` strict를 3.12까지 올리면 배포 기준 차단 로직이 릴리스 런타임 전체를 동일하게 커버한다.
- `schedule`의 완화된 허용치와 `main`의 엄격한 허용치(0) 분리를 통해 운영 관측과 배포 보호를 분리 관리할 수 있다.

## Decision

- PASS-51은 main strict 범위를 Python `3.12`로 확장하고, 운영 문구를 정합화했다.
- 다음 순환은 schedule 허용치(1) 운영 데이터를 기반으로 유지/축소 판단을 진행하고,
  필요 시 `main`에도 허용치 완화 실험을 별도 pass로 분리한다.

## Evidence (pass-51)

- `.github/workflows/test.yml`
  - `Run latency policy gate (fail-on-warning) on main push` 조건:
    - `github.event_name == 'push' && github.ref == 'refs/heads/main' && (matrix.python-version == '3.10' || matrix.python-version == '3.11' || matrix.python-version == '3.12')`
- `README.md`
  - `main` strict의 런타임 범위를 `3.10, 3.11, 3.12`로 갱신
- `README.md`
  - `schedule` max warning count 완화 항목을 그대로 유지

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-50.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-49.md`
- `tests/test_template_message_queue.py`
