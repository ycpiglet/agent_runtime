# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-35.md

## Bottom Line

`PASS-35`에서는 R2 분산/원격 FS 리스크를 한 단계 더 축소하기 위해 시계 스큐(노드별 시간 왜곡) 조건을 포함한 claim 복구-획득 경로를 추가 검증했다.

`recover_stale_claim`의 시계 오차 내성(노드 시점 주입)과, 노드별 시간 왜곡을 가진 다중 프로세스 경합(복구→재획득)에서 단일 winner가 보장되는지를 실측해 `tests/test_template_message_queue.py` 커버리지를 보강했다.

## Signal

| 항목 | PASS-34 상태 | PASS-35 상태 | 근거 |
|---|---|---|---|
| 분산/원격 FS claim robustness (R2) | ✅ 강화됨 | ✅ 추가 강화 | 시계 스큐/지연 경합을 포함한 stale recovery 경로 테스트 추가 |
| 다중 노드 경합 안전성 | ✅ 통과 | ✅ 확장 통과 | `multiprocess + clock skew` 테스트에서 winner 정확히 1개 유지 |
| 메시지 큐 write 경로 회복성 | ✅ 통과 | ✅ 유지 | 기존 `_write_text_atomic` 시뮬레이션은 PASS-34에서 유지됨 |
| 템플릿 self-contained/CI 게이트 | ✅ 통과 | ✅ 유지 | PASS-35 전체 게이트 재실행 결과 유지 |

## Insight

- 시계 기반 의사결정은 `_is_stale_claim`의 경계값(`<= now`) 동작 때문에 노드 간 스큐가 실제 `recover_stale_claim` 동작을 결정한다. 이번 테스트로 `now` 의존 경로를 노출해 운영 환경에서의 drift 조건을 더 투명하게 재현했다.
- 이미 존재하던 `claims`/frontmatter 경로와 결합해, 경합 시 `stale` 판정과 `claim` 생성이 상호배타적으로 동작해 두 프로세스 동시 실행 하에서도 최종 claimed 상태가 단일 소유로 유지됨을 확인했다.
- `PASS-34`의 임시쓰기/rename 실패 검증과 결합하면, 실제 원격/분산 파일시스템에서 흔한 두 축(타이밍 오차, write-fs 오류)을 동시에 다루는 실질적 회귀 방어가 형성되었다.

## Decision

- `PASS-35`로 `R2`를 기존의 replace 실패 시나리오에서 `clock skew + stale recovery 경합` 시나리오로 확장해 한 단계 더 축소했다.
- 다음 사이클(`PASS-36`)에서는 다중 메시지(동시 여러 `inbox` 항목)에서의 병렬 복구/응답 경합과 리플레이 지연 분포를 확장해 `claim/답변` 경로의 throughput 한계와 starvation 가능성까지 추적한다.

## Evidence (pass-35)

- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests/test_template_message_queue.py -q`
  - `21 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests -q`
  - `148 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli sanitize --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-check --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source-pass35 --check`
  - `findings=0`

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-34.md`
- `tests/test_template_message_queue.py`
- `src/agent_runtime/templates/project/scripts/message_queue.py`
