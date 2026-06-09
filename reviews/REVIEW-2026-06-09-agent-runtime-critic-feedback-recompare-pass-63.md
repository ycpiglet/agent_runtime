# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-63.md

## Bottom Line

`PASS-63`에서 `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH`를 명시 경로로 지정한 경우
`rejection_log_path`가 그대로 기록되는지 검증해 관측성 경로의 결정성 보존을 확보했다.

## Signal

| 항목 | PASS-62 상태 | PASS-63 상태 | 근거 |
|---|---|---|---|
| 빈 경로 처리 | 빈 경로에서 로그 미기록 확인 | 유지 | `tests/test_template_message_queue.py` |
| 명시 경로 기록 | 미검증 상태 | 커스텀 경로 지정 시 실제 파일 생성 및 `rejection_log_path` 동일성 검증 | `tests/test_template_message_queue.py` |
| 경로 의도성 | 일부 시나리오만 커버 | 비어있지 않은 경로에 대한 기록 보존까지 상향 | `tests/test_template_message_queue.py` |

## Insight

- 경로 미설정/빈 문자열 모드와 달리, 지정 경로 모드에서는 관측 파일 위치가 계약값을 그대로 따라야 한다.
- `rejection_log_path`는 감사/디버깅에서 중요한 메타데이터이므로 입력값 보존이 운영 추적 신뢰도를 높인다.

## Decision

- `tests/test_template_message_queue.py`
  - `test_latency_run_id_rejection_log_path_preserves_custom_destination` 추가
  - `PASS_39_LATENCY_METRICS_RUN_ID_REJECTION_LOG_PATH`를 커스텀 로그 파일로 설정 후
    - rejection 레코드 1건 존재
    - `entries[0]["rejection_log_path"] == str(custom_path)` 검증
    - `expected_mode == "manual"` 검증
  - 다음 단계 후보: 로그 경로를 상대 경로로 지정했을 때의 기본 동작/보안 보강
