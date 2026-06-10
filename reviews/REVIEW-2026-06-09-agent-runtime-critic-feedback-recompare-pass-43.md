# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-43.md

## Bottom Line

`PASS-43`에서는 PASS-42의 정책 유틸을 실제 CI 동선에 바인딩했다.

메시지 큐 지연 메트릭 테스트에 정책 게이트를 직접 연결해 `PASS_39_LATENCY_POLICY`/`PASS_39_LATENCY_POLICY_MAX_WARNING_COUNT` 설정 값으로 pass/fail 판단을 수행하고, CI에서는 `warning-only` 정책으로 정책 단계가 아티팩트까지 포함해 실행되도록 구성했다.

## Signal

| 항목 | PASS-42 상태 | PASS-43 상태 | 근거 |
|---|---|---|---|
| 정책 적용 지점 | 정책 유틸/테스트 레이어 | 실 테스트 어서션에 정책 적용 | `test_parallel_recover_and_answer_latency_distribution_and_starvation_guard`가 `_evaluate_latency_policy`를 호출 |
| CI 정책 바인딩 | 없음 | 전용 게이트 스텝 추가 | `.github/workflows/test.yml`에 latency policy step 추가 |
| 운영 문서 | 없음 | 설정 변수 문서화 | `README.md`에 PASS-39/42 환경변수 섹션 추가 |

## Insight

- PASS-42의 내부 정책 판단을 실제 실패/통과 규칙으로 연결해, 경고가 경고 수준인지 차단 수준인지 CI 설정에서 분리 가능해졌다.
- CI 정책 게이트는 현재 `warning-only`로 설정해 기존 테스트 흐름을 깨지 않으면서 경로/아티팩트 산출을 유지한다.
- 다음 순환은 정책 모드 전환(예: fail-on-warning)을 환경/브랜치별로 점진 적용하면 된다.

## Decision

- PASS-43은 지표-정책-게이트 연결을 완료했다.
- 기본 운영 규칙은 `warning-only` + 정책 임계치 0개 이상 허용으로 두되, 필요 시 `fail-on-warning` + `max_warning_count`를 CI에서 강화한다.

## Evidence (pass-43)

- `tests/test_template_message_queue.py`
  - `_env_int` 추가
  - 병렬 latency 테스트에서 `_evaluate_latency_policy` 기반 게이트 적용
- `.github/workflows/test.yml`
  - `Run latency policy gate for queue metrics` 스텝 추가
- `README.md`
  - `Latency policy hooks (message queue PASS-39+)` 섹션 추가

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-42.md`
- `tests/test_template_message_queue.py`
