# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-70.md

## Bottom Line

`PASS-70`에서 경고 코드 기반 집계가 가능하도록 경고 집계 헬퍼와 산출물을 추가해,
`PASS_39` 경고를 운영 집계 파이프라인으로 이어붙일 수 있는 형태로 정리했다.

## Signal

| 항목 | PASS-69 상태 | PASS-70 상태 | 근거 |
|---|---|---|---|
| 경고 집계 방식 | 경고 객체 타입/코드 검증만 수행 | `_summarize_pass39_warning_codes`로 코드별 카운트 생성 | `tests/test_template_message_queue.py` |
| 집계 산출물 | 없음 | warning summary JSONL 레코드 생성으로 직렬화 검증 | `tests/test_template_message_queue.py` |
| 운영 연동성 | 코드 존재성만 확인 | 코드별 count + total_warnings를 end-to-end로 기록/파싱 | `tests/test_template_message_queue.py` |

## Insight

- 문자열/카운트 추출을 테스트 내부 로컬에서 끝내면 모니터링 연동성이 약하다.
- `warning_code_counts`를 가진 JSONL 레코드로 추출하면 경고 정책 엔진이나 CI 요약기에 바로 입력할 수 있어 실제 운영성도가 높아진다.

## Decision

- `tests/test_template_message_queue.py`
  - `_Pass39LatencyRunIdRejectionLogWarning` 유지
  - `_summarize_pass39_warning_codes` 추가
  - `test_latency_run_id_rejection_warning_codes_are_aggregateable` 추가
    - 쓰기 실패 유도 후 경고 코드별 집계 수행
    - 코드 집계 결과를 `pass39-warning-summary-v1` JSONL 레코드로 저장/파싱 검증

## Evidence (pass-70)

- [테스트 헬퍼/테스트 케이스]
  - `_summarize_pass39_warning_codes`
  - `test_latency_run_id_rejection_warning_codes_are_aggregateable`

## Validation

- `C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest C:/Users/ycpig/agent_runtime/tests/test_template_message_queue.py -k "rejection_log_path_ or warning_codes_are_aggregateable" -q`
- 결과: `8 passed, 36 deselected`

## Next Step

- PASS-72 제안: run/event/window 메타 기반 경고 요약 병합/임계치 판정 엔드투엔드를 추가.
