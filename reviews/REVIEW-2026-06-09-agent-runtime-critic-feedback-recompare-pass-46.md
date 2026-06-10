# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-46.md

## Bottom Line

`PASS-46`에서는 지연 정책 게이트의 결과 아티팩트를 이벤트 타입(`push`/`schedule`)과
Python 매트릭스(`3.10`/`3.11`/`3.12`)별로 분리 저장하도록 CI를 정비했다.

경고 모드는 유지하고, `main push`와 `schedule`의 `fail-on-warning`은 각 실행기별 엄격 아티팩트
경로를 사용하므로 추적성/사후 분석성이 개선됐다.

## Signal

| 항목 | PASS-45 상태 | PASS-46 상태 | 근거 |
|---|---|---|---|
| 경로 추적성 | 엄격/비엄격 게이트가 동일 기본 경로 사용 | 경로를 `event-python-strict`로 분리 저장 | `.github/workflows/test.yml` |
| 게이트 스텝 구조 | `main+schedule`을 단일 조건식 스텝으로 결합 | `main`/`schedule` fail-on-warning을 개별 스텝으로 분리 | 워크플로우 조건식 단순화 및 추적 쉬움 |
| 문서화 | strict 이벤트 범위만 기술 | 이벤트별 분리 아티팩트 저장 명시 | `README.md` |
| 재현성 검증 | warning-only/fail-on-warning 수동 확인 | 두 모드 재실행으로 PASS 지속 확인 | `parallel_recover...` 1개 테스트 |

## Insight

- 경로 분리는 동일 테스트 이름이 여러 트리거/버전에서 실행될 때 아티팩트 오염을 줄여
  운영 리포트의 원인 추적을 쉽게 만든다.
- 개별 스텝 분리는 이벤트별 정책 이력 해석이 쉬워 `fail-on-warning` 범위 확장(예: 버전/허용치 조정) 의사결정의 근거가 된다.

## Decision

- PASS-46은 운영 게이트의 추적성 보강을 완료했다.
- 다음 순환은 `pass-46` 산출로 얻은 이벤트/버전별 지연 정책 레코드를 기반으로
  실패 패턴(분산 경고, 실패비율)만 골라 강제 게이트 대상을 추가 확정한다.

## Evidence (pass-46)

- `.github/workflows/test.yml`
  - `PASS_39_LATENCY_METRICS_PATH`를 이벤트/매트릭스별 동적 경로로 변경
  - `fail-on-warning on main push`와 `fail-on-warning on schedule`을 분리
- `README.md`
  - 이벤트/파이썬 매트릭스별 아티팩트 분리 저장 문구 추가
- 로컬 검증
  - warning-only 모드 타깃 테스트 1개 통과
  - fail-on-warning 모드 타깃 테스트 1개 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-45.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-44.md`
- `tests/test_template_message_queue.py`
