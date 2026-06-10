# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-38.md

## Bottom Line

`PASS-38`에서는 동일 테스트에 정량 KPI 경계와 경보 성격 로그를 추가해, 병렬 stale-recover 경합 구간에서 지연/실패 비율을 수치로 감시할 수 있게 했다.

`test_parallel_recover_and_answer_latency_distribution_and_starvation_guard`에 승자 지연 분포(`p95`, `p99`)와 실패율(`failure_ratio`) 계산을 붙여, 경합에서 성능 이상 징후를 실패 직전 상태로 알 수 있게 했다.

## Signal

| 항목 | PASS-37 상태 | PASS-38 상태 | 근거 |
|---|---|---|---|
| 지연 KPI 검사 | 분포 측정은 수행 | 임계치 고정 검사로 강화 | `p95 <= 2500ms`, `p99 <= 3500ms`, `failure_ratio <= 0.85` 추가 |
| 스타베이션/미응답 위험 감시 | 수렴만 검증 | 수치 임계치 기반 경고 포함 | 누적 지연 분포 및 비율 로깅 포맷 추가 |
| 중복 응답 및 정합성 | 검증됨 | 유지 | 메시지별 단건 정답/최종 상태 검사 로직 유지 |
| 공개 게이트 | 통과 | 통과 | `sanitize`, `publish-check`, `publish-bundle --check` clean 유지 |

## Insight

- 임계치 비교만으로도 “전체 실패”를 구분하기 어려운 동시성 경합 구간을 빠르게 탐지할 수 있다.
- 테스트는 기본 통과 조건을 깨지 않으면서도, p95/p99와 실패율 임계치 초과 시 경고를 표준 출력해 운영팀 관측성(조기 감지성)을 높인다.
- 성능 KPI를 인라인화했으므로, 다음 사이클에서는 임계치 완화를 단순 값 변경으로 관리하거나 정책형 분리(환경 기반 설정)로 확장하기가 쉬워진다.

## Decision

- `PASS-38`는 테스트 결과를 `winner` 지연 분포 기반 KPI와 `failure_ratio`로 정형화해, 단순 pass/fail보다 운영 감시 가능한 기준을 추가했다.
- 현재 테스트/게이트 상태를 바탕으로 `PASS-38`를 완료 처리하고, 다음 사이클에서 이 수치의 허용 범위 조정 여부와 장기 추적 저장 여부를 검토한다.

## Evidence (pass-38)

- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests/test_template_message_queue.py -k "latency_distribution_and_starvation_guard" -q`
  - `23 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests/test_template_message_queue.py -q`
  - `23 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests -q`
  - `150 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli sanitize --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-check --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source-pass38 --check`
  - `findings=0`

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-37.md`
- `tests/test_template_message_queue.py`
