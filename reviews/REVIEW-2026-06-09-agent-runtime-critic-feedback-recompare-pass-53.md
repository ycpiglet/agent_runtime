# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-53.md

## Bottom Line

`PASS-53`에서는 latency 정책 아티팩트의 `PASS_39_LATENCY_METRICS_RUN_ID`를
GitHub 이벤트/실행 맥락 기반으로 주입해, CI 내 추적성(재현성)을 고정했다.

기존 `main`/`schedule` strict의 허용치 분리를 유지하면서, 경고 게이트 결과 레코드가
실행 단위를 따라 고유하게 식별되도록 보강했다.

## Signal

| 항목 | PASS-52 상태 | PASS-53 상태 | 근거 |
|---|---|---|---|
| run_id 주입 | 미설정(옵션) | strict/warning 스텝 모두 run-id 주입 | `.github/workflows/test.yml` |
| 경로 구분 | `event-python-strict(-countN)` | 동일(수정 없음) | `.github/workflows/test.yml` |
| 문서화 | 변수 의미 정리 | run-id 주입 패턴 설명 추가 | `README.md` |
| 검증 | warning/fail 테스트 통과(전 단계) | 경로/변수 템플릿 변경 반영 후 재실행 | 로컬 타깃 테스트 |

## Insight

- run-id 주입은 같은 이벤트/버전 경로에서도 누적 실행 충돌을 분리해 감사/사건 재구성 비용을 낮춘다.
- 경로 분리에 추가로 run-id가 붙으면, 정책 변경 실험(허용치 수치 조정 등) 간 레코드 혼입을 줄일 수 있다.

## Decision

- PASS-53은 `PASS_39_LATENCY_METRICS_RUN_ID`의 CI 주입을 정식화해 아티팩트 재현성 규칙을 강화했다.
- 다음 순환은 run-id 패턴(`github.sha` 또는 날짜 기반 태그)의 일관성 유지와
  규칙이 실제 레코드 파일(`.tmp/pass39-...jsonl`)에 반영되는지 상시 점검을 추가한다.

## Evidence (pass-53)

- `.github/workflows/test.yml`
  - warning-only 스텝:
    - `PASS_39_LATENCY_METRICS_RUN_ID: run-${{ github.run_id }}-${{ github.event_name }}-py${{ matrix.python-version }}-warning`
  - main strict 스텝:
    - `run-${{ github.run_id }}-${{ github.event_name }}-main-py${{ matrix.python-version }}-fail-${{ github.sha }}`
  - schedule strict 스텝:
    - `run-${{ github.run_id }}-${{ github.event_name }}-schedule-py${{ matrix.python-version }}-fail`
- `README.md`
  - run-id 주입 패턴(재현성) 설명 추가
- 로컬 검증
  - 경고 모드 타깃 테스트 1개 통과
  - fail-on-warning 타깃 테스트 1개 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-52.md`
- `tests/test_template_message_queue.py`
