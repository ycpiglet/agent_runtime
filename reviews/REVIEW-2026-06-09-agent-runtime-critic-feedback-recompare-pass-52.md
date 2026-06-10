# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-52.md

## Bottom Line

`PASS-52`에서는 strict latency 정책 아티팩트 경로를 이벤트/버전/허용치 단위로
명시적으로 분리해, 경고 임계치 정책 변경 시 기록 오염 없이 추적할 수 있게 정리했다.

`main` strict(0 허용치)와 `schedule` strict(1 허용치)의 분리가 경로에서 즉시 식별되므로
운영 관측성과 배포 게이트 판독성이 개선됐다.

## Signal

| 항목 | PASS-51 상태 | PASS-52 상태 | 근거 |
|---|---|---|---|
| strict 아티팩트 경로 | `...-strict.jsonl` | `...-strict-count0.jsonl`, `...-strict-count1.jsonl` 분리 | `.github/workflows/test.yml` |
| 이벤트별 허용치 | main:0, schedule:1 텍스트로만 정리 | 경로명/정책명에 `count0/count1` 반영 | `.github/workflows/test.yml`, `README.md` |
| 문서화 | 버전/허용치 혼재 서술 | 정책별 경로 템플릿 명시 | `README.md` |
| 재검증 | warning/fail 로컬 1회씩 통과 | warning/fail 로컬 1회씩 통과 | 타깃 테스트 실행 |

## Insight

- 아티팩트 경로가 허용치까지 반영되면 정책 변경(예: schedule를 2로 올릴 때)으로 인한 이전 기록 혼입을 방지할 수 있다.
- 운영 노트에서 `main=0`, `schedule=1` 분기를 텍스트와 경로 양쪽에서 확인할 수 있어 검증 추적이 쉬워짐.

## Decision

- PASS-52는 strict 정책 수집의 분해도를 높였고, 파이프라인 의사결정 시 오해 가능성을 줄였다.
- 다음 순환에서는 `PASS_39_LATENCY_METRICS_RUN_ID`를 주간 이벤트별 고정값으로 채워
  감사 재현성을 추가하는 것을 우선 권장한다.

## Evidence (pass-52)

- `.github/workflows/test.yml`
  - `Run latency policy gate (fail-on-warning) on main push`:
    - 경로 `.tmp/pass39-latency-metrics-${{ github.event_name }}-${{ matrix.python-version }}-strict-count0.jsonl`
  - `Run latency policy gate (fail-on-warning) on schedule`:
    - 경로 `.tmp/pass39-latency-metrics-${{ github.event_name }}-${{ matrix.python-version }}-strict-count1.jsonl`
- `README.md`
  - 정책/허용치별 경로 명명 규칙(`event-python-strict-countN.jsonl`) 및 main/schedule 허용치 구분 추가
- 로컬 검증
  - warning-only 모드 타깃 테스트 1개 통과
  - fail-on-warning 모드 타깃 테스트 1개 통과

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-51.md`
- `tests/test_template_message_queue.py`
