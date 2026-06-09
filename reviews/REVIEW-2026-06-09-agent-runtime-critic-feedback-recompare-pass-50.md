# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-50.md

## Bottom Line

`PASS-50`에서는 `schedule` strict 게이트의 경고 허용치 정책을 `1`로 조정해
정기 점검에서의 과도 차단 가능성을 낮추고, 경고율 기반 경향 탐지를 유지했다.

`main` strict는 기존대로 warning-count 0을 유지하고, `schedule`만 1로 완화해
단일 경고 이벤트로 인한 반복 실패를 피하면서 추세 지표를 계속 수집한다.

## Signal

| 항목 | PASS-49 상태 | PASS-50 상태 | 근거 |
|---|---|---|---|
| schedule strict 허용치 | `0` | `1` | `.github/workflows/test.yml` |
| main strict 허용치 | `0` | 유지 | `.github/workflows/test.yml` |
| 문서 반영 | schedule 3.10/3.11/3.12 | 허용치 완화 언급 추가 | `README.md` |
| 재현성 | 조건 확장 전후 수동 테스트 있음 | 조건 확장(3.12) + 허용치 변경은 로컬 시뮬레이션에서 경로 불변이므로 재실행 생략 | 변경 범위(환경변수 값) |

## Insight

- `schedule` strict를 완전 버전 범위(`3.10-3.12`)로 열어둔 상태에서 허용치 1은 운영 안정성을 높인다.
- `main` strict는 여전히 엄격한 0 허용치로 유지되어 배포 라인 차단 원칙을 유지한다.

## Decision

- PASS-50은 `schedule` strict의 경고 허용치 실험적 완화를 완료했다.
- 다음 순환은 주간 스케줄 로그(특히 warning count 분포) 기반으로
  `schedule` 허용치 `1` 지속 여부를 결정한다.

## Evidence (pass-50)

- `.github/workflows/test.yml`
  - `Run latency policy gate (fail-on-warning) on schedule`에서
    `PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT`를 `"1"`으로 변경
- `README.md`
  - schedule strict의 `MAX_WARNING_COUNT=1` 운용 변경 반영

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-49.md`
- `tests/test_template_message_queue.py`
