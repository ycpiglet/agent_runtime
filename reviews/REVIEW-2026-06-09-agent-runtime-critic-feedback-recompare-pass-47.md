# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-47.md

## Bottom Line

`PASS-47`에서는 `main` 브랜치 strict 게이트를 Python `3.10` 단일 실행기에서
Python `3.11`까지 1단계로 확장해 강제 차단 정책의 범위를 넓혔다.

`warning-only` 기본 게이트는 유지한 채 3.10/3.11 조합에서 `fail-on-warning` 실행을 병행해
운영 추적 구간을 늘린다.

## Signal

| 항목 | PASS-46 상태 | PASS-47 상태 | 근거 |
|---|---|---|---|
| main strict 범위 | `main` push + `3.10`만 | `main` push + `3.10` 및 `3.11` | `.github/workflows/test.yml` 조건식 |
| schedule strict 범위 | `schedule` + `3.10` | 변경 없음 (`3.10` 유지) | 동일 fail-on-warning schedule 스텝 |
| 문서 | 3.10 위주 기술 | 3.10/3.11으로 업데이트 | `README.md` |
| 재현성 확인 | warning/fail 수동 검증 | warning/fail 수동 검증 재실행 | 타깃 테스트 실행 로그 |

## Insight

- main strict 범위를 3.11까지 확장해 런타임 버전 편차에서의 지연 경고 차단 규칙을 조기에 점검할 수 있다.
- 3.10 schedule 경로는 유지해 노이즈를 통제하면서도 정기 점검을 유지한다.
- 아티팩트 분리 정책이 이미 분리되어 있어 버전 확장의 추적비용이 낮아진 상태다.

## Decision

- PASS-47은 `main` strict 게이트의 1단계 버전 확장(3.11 추가)을 완료했다.
- 다음 순환은 `schedule` 3.11 추가 또는 `max_warning_count`를 1로 상향·하향하는 정책 실험을
  분리된 이벤트/버전 아티팩트로 판단해 적용한다.

## Evidence (pass-47)

- `.github/workflows/test.yml`
  - `Run latency policy gate (fail-on-warning) on main push` 조건 변경:
    - `matrix.python-version == '3.10' || matrix.python-version == '3.11'`
- `README.md`
  - 운영 안내에 `main push` strict가 3.10 및 3.11임을 반영
- 로컬 검증
  - warning-only 모드 타깃 테스트 1개 통과
  - fail-on-warning 모드 타깃 테스트 1개 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-46.md`
- `tests/test_template_message_queue.py`
